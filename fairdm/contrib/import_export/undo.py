"""What an import keeps to tell it from later edits, and its undoing."""

import hashlib
import json
from itertools import batched

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import transaction
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.utils import timezone
from django.utils.translation import gettext as _

from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample

from .models import ImportJob, ImportRow


class ImportUndo:
    """The undoing of one import.

    Attributes:
        job: The import the undo is about.
        done: How many records the undo has put back so far.
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
        self.done = 0

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
            Tuples of up to ``CHUNK`` rows, in file order.
        """
        rows = self.job.rows.filter(outcome=outcome, record_pk__isnull=False)
        yield from batched(
            rows.order_by("number").iterator(chunk_size=self.CHUNK),
            self.CHUNK,
            strict=False,
        )

    def conflicts(self, limit=LIMIT):
        """List the records that stand in the way of an undo.

        A record is in the way when it no longer exists, when its stored values differ
        from what the import left, or when it is a sample the import added and it now
        has measurements. A record the import added is also in the way when it has
        rows in a related table, such as descriptions, dates, identifiers,
        contributors, relations or children, as undoing would delete them with it.
        Who may undo is the dataset's import permission, decided by the page, so no
        per-record permission is read here. The records are read with a lock, which
        holds until the transaction that called this ends, so call it inside one.

        Args:
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
                    for record in model.objects.select_for_update(of=("self",)).filter(
                        pk__in=[row.record_pk for row in rows]
                    )
                }
                measured = self.measured(outcome, present)
                related = self.related(outcome, present)
                for row in rows:
                    record = present.get(row.record_pk)
                    if record is None:
                        reason = "deleted"
                    elif self.digest(record) != row.digest:
                        reason = "changed"
                    elif row.record_pk in measured:
                        reason = "measurements"
                    elif row.record_pk in related:
                        reason = "changed"
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

    def relations(self):
        """List the tables whose rows belong to a record of the job's type.

        Read from the model's options, so a relation a portal adds is included. The
        link a child type holds to its parent is left out: the import writes it.

        Returns:
            Tuples of the related model, the name of the field that holds the record's
            key and the further filter that picks the record's rows: empty for a
            foreign key, the record's content type for a generic relation.
        """
        model = self.job.model
        found = []
        for field in model._meta.get_fields(include_hidden=True):
            if isinstance(field, GenericRelation):
                kind = {
                    field.content_type_field_name: ContentType.objects.get_for_model(
                        model
                    )
                }
                found.append((field.related_model, field.object_id_field_name, kind))
            elif isinstance(field, ForeignObjectRel) and not field.many_to_many:
                if not field.field.remote_field.parent_link:
                    found.append((field.related_model, field.field.attname, {}))
        return found

    def related(self, outcome, present):
        """Find the added records that have rows in a related table.

        One query for each related table.

        Args:
            outcome: The outcome of the rows being read.
            present: The records of the chunk that still exist, by key.

        Returns:
            The set of keys of records with a related row. Empty for rows that changed
            a record, which undo keeps.
        """
        if outcome != ImportRow.Outcome.NEW:
            return set()
        found = set()
        for other, column, kind in self.relations():
            rows = other._base_manager.filter(
                **{f"{column}__in": list(present)}, **kind
            )
            keys = rows.values_list(column, flat=True).distinct()
            found.update(self.job.model._meta.pk.to_python(key) for key in keys)
        return found

    def undo(self, user):
        """Delete what the import added and restore what it changed.

        Everything happens in one transaction after the dataset is locked, so imports
        and undos of one dataset run one at a time and the second reads what the first
        wrote. Nothing is changed when any record is in the way: the job returns to
        imported with the records named in its ``error``.

        Args:
            user: The person undoing the import.

        Returns:
            None when the job is not undoing, so there is nothing to undo. Otherwise
            the result of ``conflicts``, with no entries once the undo is done.
        """
        # runner imports this module, so the run is read here.
        from .runner import ImportRun

        job = self.job
        run = ImportRun(job)
        try:
            with transaction.atomic():
                Dataset.all_objects.select_for_update().get(pk=job.dataset_id)
                job.refresh_from_db()
                if job.status != ImportJob.Status.UNDOING:
                    return None
                found = self.conflicts()
                if found["entries"]:
                    self.release(self.describe(found))
                    return found
                self.delete_created()
                self.restore_updated()
                ImportJob.objects.filter(
                    pk=job.pk, status=ImportJob.Status.UNDOING
                ).update(
                    status=ImportJob.Status.UNDONE,
                    undone_at=timezone.now(),
                    undone_by=user,
                    error="",
                )
                job.refresh_from_db()
                run.delete_file()
        finally:
            cache.delete(run.progress_key)
        return found

    def describe(self, found):
        """Write the records in the way as text, one line each.

        Args:
            found: The result of ``conflicts``.

        Returns:
            One line for each record, with the reason it stands in the way, and a last
            line counting the records beyond those named.
        """
        reasons = {
            "deleted": _("deleted since"),
            "measurements": _("has measurements"),
            "changed": _("changed since"),
        }
        lines = [f"{e['label']} · {reasons[e['reason']]}" for e in found["entries"]]
        if found["more"]:
            lines.append(_("and %(n)s more records in the way") % {"n": found["more"]})
        return "\n".join(lines)

    def release(self, message):
        """Return an undoing job to imported, with a message for the page.

        Nothing happens to a job that is not undoing.

        Args:
            message: What stopped the undo, which the job's page shows.
        """
        ImportJob.objects.filter(
            pk=self.job.pk, status=ImportJob.Status.UNDOING
        ).update(status=ImportJob.Status.IMPORTED, error=message)

    def advance(self, rows):
        """Count the records of a finished chunk and write the progress.

        Args:
            rows: The rows of the chunk.
        """
        # runner imports this module, so the run is read here.
        from .runner import ImportRun

        self.done += len(rows)
        run = ImportRun(self.job)
        cache.set(run.progress_key, self.done, run.PROGRESS_SECONDS)

    def delete_created(self):
        """Delete the records the import added, one ``delete()`` for each chunk.

        The delete goes through the type's manager so signals and the children of a
        polymorphic record are handled as they are for a deletion by hand.
        """
        for rows in self.chunks(ImportRow.Outcome.NEW):
            self.job.model.objects.filter(
                pk__in=[row.record_pk for row in rows]
            ).delete()
            self.advance(rows)

    def restore_updated(self):
        """Put back the values each changed record held before the import."""
        model = self.job.model
        fields = {field.attname: field for field in model._meta.concrete_fields}
        for rows in self.chunks(ImportRow.Outcome.UPDATE):
            records = model.objects.in_bulk([row.record_pk for row in rows])
            for row in rows:
                record = records[row.record_pk]
                for attname, value in row.before.items():
                    if value is not None:
                        value = fields[attname].to_python(value)
                    setattr(record, attname, value)
                record.save()
            self.advance(rows)
