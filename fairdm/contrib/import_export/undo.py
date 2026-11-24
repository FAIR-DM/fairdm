"""What an import keeps so that it can be told apart from later edits, and its undoing."""

import hashlib
import json

from django.db import transaction
from django.utils import timezone

from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample

from .models import ImportJob, ImportRow


class ImportUndo:
    """The undoing of one import.

    Attributes:
        job: The import the undo is about.
        CHUNK: How many records are read or deleted at a time.
        LIMIT: How many records in the way a refusal names.
    """

    CHUNK = 500
    LIMIT = 20

    def __init__(self, job):
        """Keep the import.

        Args:
            job: The import job.
        """
        self.job = job

    def digest(self, record):
        """Describe a record's stored values in one short text.

        Every concrete field's value is written with ``field.value_to_string`` and the
        values are hashed as canonical JSON. ``modified`` is one of them, so a save
        that changes nothing still changes the digest. Read the record fresh from the
        database before calling this, so the digest describes what the database holds.

        Args:
            record: The sample or measurement, as read from the database.

        Returns:
            The SHA-256 of the values, as 64 hexadecimal characters.
        """
        values = {
            field.attname: field.value_to_string(record)
            for field in record._meta.concrete_fields
        }
        canonical = json.dumps(values, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def chunks(self, outcome):
        """Read the rows of one outcome that wrote a record, a chunk at a time.

        Args:
            outcome: The ``ImportRow.Outcome`` to read: new or update.

        Yields:
            Lists of up to ``CHUNK`` rows, in file order.
        """
        rows = self.job.rows.filter(outcome=outcome, record_pk__isnull=False)
        batch = []
        for row in rows.order_by("number").iterator(chunk_size=self.CHUNK):
            batch.append(row)
            if len(batch) == self.CHUNK:
                yield batch
                batch = []
        if batch:
            yield batch

    def conflicts(self, user, limit=LIMIT):
        """List the records that stand in the way of an undo.

        A record is in the way when it no longer exists, when its stored values differ
        from what the import left, or when it is a sample the import added and it now
        has measurements. Who may undo is the dataset's import permission, decided by
        the page, so no per-record permission is read here.

        Args:
            user: The person who would undo. Kept for the caller's sake: the rule
                reads nothing about them.
            limit: How many records to name.

        Returns:
            A dict with ``entries``, up to ``limit`` dicts of the record's ``pk``,
            its ``label`` and the ``reason`` (``deleted``, ``changed`` or
            ``measurements``), and ``more``, how many further records are in the way.
        """
        model = self.job.model
        found = []
        for outcome in (ImportRow.Outcome.NEW, ImportRow.Outcome.UPDATE):
            for rows in self.chunks(outcome):
                present = {
                    record.pk: record
                    for record in model.objects.filter(
                        pk__in=[row.record_pk for row in rows]
                    )
                }
                measured = self.measured(outcome, present)
                for row in rows:
                    record = present.get(row.record_pk)
                    if record is None:
                        reason = "deleted"
                    elif self.digest(record) != row.digest:
                        reason = "changed"
                    elif row.record_pk in measured:
                        reason = "measurements"
                    else:
                        continue
                    found.append(
                        {
                            "pk": row.record_pk,
                            "label": row.label or row.portal_id,
                            "reason": reason,
                        }
                    )
        return {"entries": found[:limit], "more": max(0, len(found) - limit)}

    def measured(self, outcome, present):
        """Find the added samples that have measurements.

        Args:
            outcome: The outcome of the rows being read.
            present: The records of the chunk that still exist, by key.

        Returns:
            The set of keys of samples with at least one measurement. Empty for rows
            that changed a record, and for a type that is not a sample.
        """
        if outcome != ImportRow.Outcome.NEW or not issubclass(self.job.model, Sample):
            return set()
        return set(
            Measurement.objects.filter(sample_id__in=list(present)).values_list(
                "sample_id", flat=True
            )
        )

    def undo(self, user):
        """Delete what the import added and restore what it changed.

        Everything happens in one transaction after the dataset is locked, so imports
        and undos of one dataset run one at a time and the second reads what the first
        wrote. Nothing is changed when any record is in the way.

        Args:
            user: The person undoing the import.

        Returns:
            None when the job is not imported, so there is nothing to undo. Otherwise
            the result of ``conflicts``, with no entries once the undo is done.
        """
        # runner imports this module, so the run is read here.
        from .runner import ImportRun

        job = self.job
        with transaction.atomic():
            Dataset.all_objects.select_for_update().get(pk=job.dataset_id)
            job.refresh_from_db()
            if job.status != ImportJob.Status.IMPORTED:
                return None
            found = self.conflicts(user)
            if found["entries"]:
                return found
            self.delete_created()
            self.restore_updated()
            ImportJob.objects.filter(
                pk=job.pk, status=ImportJob.Status.IMPORTED
            ).update(
                status=ImportJob.Status.UNDONE,
                undone_at=timezone.now(),
                undone_by=user,
            )
            job.refresh_from_db()
            ImportRun(job).delete_file()
        return found

    def delete_created(self):
        """Delete the records the import added, one ``delete()`` for each chunk.

        The delete goes through the type's manager so signals and the children of a
        polymorphic record are handled as they are for a deletion by hand.
        """
        for rows in self.chunks(ImportRow.Outcome.NEW):
            self.job.model.objects.filter(
                pk__in=[row.record_pk for row in rows]
            ).delete()

    def restore_updated(self):
        """Put back the values each changed record held before the import."""
        model = self.job.model
        fields = {field.attname: field for field in model._meta.concrete_fields}
        for rows in self.chunks(ImportRow.Outcome.UPDATE):
            records = model.objects.in_bulk([row.record_pk for row in rows])
            for row in rows:
                record = records[row.record_pk]
                for attname, value in row.before.items():
                    setattr(record, attname, fields[attname].to_python(value))
                record.save()
