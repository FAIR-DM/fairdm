"""The check and the import of one uploaded file.

Both phases read the file once, build the rows from the job's column matches and run
the type's resource over them. The check runs it as a dry run and keeps the outcome of
every row. The import runs it for real, inside one transaction, and writes only what
the check showed.
"""

from collections import Counter
from itertools import batched

import tablib
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from import_export.results import RowResult

from fairdm.core.dataset.models import Dataset

from .models import ImportJob, ImportRow
from .reader import FileProblem, FileReader
from .resources import RowProblem
from .undo import ImportUndo


class DatasetChanged(Exception):
    """The import found something other than what the check showed.

    Attributes:
        rows: The outcome of every row as the import found it.
    """

    def __init__(self, rows):
        """Keep the rows.

        Args:
            rows: The unsaved rows of the import's own run.
        """
        super().__init__("The dataset changed since the check.")
        self.rows = rows


class ImportRun:
    """Runs the check or the import of one job.

    Attributes:
        job: The import job.
        CHUNK: How many rows are written to the database at once.
        FRESH_CHUNK: How many written records are read back at once.
        PROGRESS_EVERY: After how many rows the progress is written to the cache.
        PROGRESS_SECONDS: How long a progress figure stays in the cache.
        UNTRACKED: The fields an undo never puts back, as the save sets them.
    """

    CHUNK = 1000
    FRESH_CHUNK = 500
    PROGRESS_EVERY = 10
    PROGRESS_SECONDS = 3600
    UNTRACKED = ("modified",)

    def __init__(self, job):
        """Keep the job.

        Args:
            job: The import job.
        """
        self.job = job

    @property
    def progress_key(self):
        """Name the cache entry that holds the job's progress.

        Returns:
            The cache key.
        """
        return f"import-progress-{self.job.pk}"

    def progress(self):
        """Read how many rows the running phase has finished.

        Returns:
            The number of rows done, as of the last ten, or None when no phase is
            writing progress.
        """
        return cache.get(self.progress_key)

    def write_progress(self, done):
        """Write the progress to the cache after every tenth row.

        Args:
            done: How many rows are finished.
        """
        if done % self.PROGRESS_EVERY == 0:
            cache.set(self.progress_key, done, self.PROGRESS_SECONDS)

    def read_file(self):
        """Read the job's file.

        Returns:
            The headings, the rows and the line each row starts on.

        Raises:
            FileProblem: The file cannot be read.
        """
        try:
            with self.job.file.open("rb") as stored:
                raw = stored.read()
        except FileNotFoundError:
            raise FileProblem(
                _("The uploaded file is no longer stored."), "unreadable"
            ) from None
        return FileReader.parse(raw, self.job.file_format)

    def run(self, dry_run, user):
        """Run the type's resource over the file's rows.

        Args:
            dry_run: True to write nothing, False to write the rows.
            user: The person whose view of the samples a measurement may name.

        Returns:
            The unsaved row of each row of the file, and for each row the import
            wrote, its record's key and the record as it was stored before.

        Raises:
            FileProblem: The file cannot be read.
        """
        job = self.job
        headings, cells, lines = self.read_file()
        wanted = [
            (index, job.column_map[heading])
            for index, heading in enumerate(headings)
            if job.column_map.get(heading)
        ]
        names = [name for position, name in wanted]
        data = tablib.Dataset(headers=names)
        for row in cells:
            data.append([row[position] for position, name in wanted])
        resource = job.definition.resource(
            job.dataset,
            mode=job.mode,
            empty=job.empty_cells,
            user=user,
            columns=names,
        )
        resource.on_row = self.write_progress
        try:
            result = resource.import_data(
                data,
                dry_run=dry_run,
                use_transactions=True,
                raise_errors=False,
                rollback_on_validation_errors=True,
                retain_instance_in_row_result=True,
            )
        finally:
            cache.delete(self.progress_key)
        if result.base_errors:
            raise result.base_errors[0].error
        rows = [
            self.row_of(number, lines[number - 1], row_result, resource)
            for number, row_result in enumerate(result.rows, start=1)
        ]
        self.mark_duplicates(rows, result, resource, data)
        written = {
            row.number: (result.rows[row.number - 1].instance.pk, original)
            for row in rows
            if row.outcome in (ImportRow.Outcome.NEW, ImportRow.Outcome.UPDATE)
            for original in [getattr(result.rows[row.number - 1], "original", None)]
        }
        return rows, written

    def row_of(self, number, line, row_result, resource):
        """Turn one row's result into an unsaved ``ImportRow``.

        Args:
            number: The row's position in the file, from 1.
            line: The line of the file the row starts on.
            row_result: The resource's result for the row.
            resource: The resource, which holds the row's notes and changes.

        Returns:
            The row, with its outcome, label, changes, problems and note.
        """
        row = ImportRow(
            job=self.job, number=number, line=line, label=_("Row %d") % number
        )
        kind = row_result.import_type
        if kind == RowResult.IMPORT_TYPE_INVALID:
            row.outcome = ImportRow.Outcome.PROBLEM
            row.problems = self.field_problems(row_result.validation_error)
        elif kind == RowResult.IMPORT_TYPE_ERROR:
            row.outcome = ImportRow.Outcome.PROBLEM
            row.problems = [self.error_problem(row_result.errors[0].error)]
        else:
            self.describe_valid(row, row_result, resource)
        return row

    def describe_valid(self, row, row_result, resource):
        """Fill in a row that was read without a problem.

        Args:
            row: The unsaved row.
            row_result: The resource's result for the row.
            resource: The resource, which holds the row's notes and changes.
        """
        instance = row_result.instance
        if instance is not None and instance.pk:
            row.label = row_result.object_repr or row.label
        if row_result.import_type == RowResult.IMPORT_TYPE_NEW:
            row.outcome = ImportRow.Outcome.NEW
            return
        if instance is not None and instance.pk:
            row.portal_id = instance.uuid
        if row_result.import_type == RowResult.IMPORT_TYPE_UPDATE:
            row.outcome = ImportRow.Outcome.UPDATE
            row.changes = resource.changes.get(row.number, [])
            return
        row.note = resource.notes.get(row.number, "")
        row.outcome = (
            ImportRow.Outcome.SKIPPED if row.note else ImportRow.Outcome.UNCHANGED
        )

    def field_problems(self, error):
        """List the problems of the cells a row failed validation on.

        Args:
            error: The row's ``ValidationError``.

        Returns:
            One dict of ``column`` and ``message`` for each message.
        """
        if hasattr(error, "message_dict"):
            return [
                {"column": "" if column == "__all__" else column, "message": message}
                for column, messages in error.message_dict.items()
                for message in messages
            ]
        return [{"column": "", "message": message} for message in error.messages]

    def error_problem(self, error):
        """Turn the error a row ended in into a problem.

        Args:
            error: The exception the row raised.

        Returns:
            A dict of ``column`` and ``message``.
        """
        if isinstance(error, RowProblem):
            return {"column": error.column, "message": str(error.message)}
        return {"column": "", "message": str(error)}

    def mark_duplicates(self, rows, result, resource, data):
        """Turn every row that is about a record another row is about into a problem.

        Rows are compared by the record they resolved to, which catches a portal ID on
        one row and the Local ID of the same record on another, and by the Local ID's
        text for rows that add a record.

        Args:
            rows: The unsaved rows, changed in place.
            result: The import's result.
            resource: The resource, which holds the stored record each row matched.
            data: The rows the import was given.
        """
        keys = {}
        for row, row_result in zip(rows, result.rows, strict=True):
            instance = row_result.instance
            pk = instance.pk if instance is not None else None
            pk = pk or resource.record_pks.get(row.number)
            if pk:
                keys.setdefault(("pk", pk), []).append(row)
            if row.outcome == ImportRow.Outcome.NEW and "local_id" in data.headers:
                text = str(data[row.number - 1][data.headers.index("local_id")] or "")
                if text.strip():
                    keys.setdefault(("local_id", text.strip()), []).append(row)
        for sharing in keys.values():
            if len(sharing) < 2:
                continue
            for row in sharing:
                row.outcome = ImportRow.Outcome.PROBLEM
                row.changes = []
                row.note = ""
                if not row.problems:
                    row.problems = [
                        {
                            "column": "portal_id" if row.portal_id else "local_id",
                            "message": _(
                                "Another row of this file is about the same record."
                            ),
                        }
                    ]

    def store(self, rows, error=""):
        """Replace the job's rows and record the outcome of a check.

        Args:
            rows: The unsaved rows.
            error: The sentence to keep on the job, or empty.
        """
        job = self.job
        counts = Counter(row.outcome for row in rows)
        with transaction.atomic():
            job.rows.all().delete()
            ImportRow.objects.bulk_create(rows, batch_size=self.CHUNK)
            job.row_count = len(rows)
            job.summary = dict(counts)
            if counts[ImportRow.Outcome.PROBLEM]:
                job.status = ImportJob.Status.PROBLEMS
            elif counts[ImportRow.Outcome.NEW] + counts[ImportRow.Outcome.UPDATE]:
                job.status = ImportJob.Status.CHECKED
            else:
                job.status = ImportJob.Status.NOTHING
            job.checked_at = timezone.now()
            job.file_problems = []
            job.error = error
            job.save(
                update_fields=[
                    "row_count",
                    "summary",
                    "status",
                    "checked_at",
                    "file_problems",
                    "error",
                ]
            )

    def check(self):
        """Check the file against the dataset and keep every row's outcome.

        Nothing is written to the dataset. A file that cannot be read ends the job as
        failed.
        """
        try:
            rows = self.run(dry_run=True, user=self.job.created_by)[0]
        except FileProblem as problem:
            self.fail(str(problem))
            return
        self.store(rows)

    def perform(self, user):
        """Write the rows the check showed, in one transaction.

        The dataset is locked first, so imports of one dataset write one at a time and
        the second reads what the first wrote. Nothing happens unless the job is
        importing once the lock is held. When the import finds anything other than
        what the check showed, nothing is saved and the job returns to the check with
        the new outcomes.

        Args:
            user: The person who started the import.
        """
        job = self.job
        try:
            with transaction.atomic():
                Dataset.all_objects.select_for_update().get(pk=job.dataset_id)
                job.refresh_from_db()
                if job.status != ImportJob.Status.IMPORTING:
                    return
                rows, written = self.run(dry_run=False, user=user)
                self.confirm(rows)
                self.record_outcomes(written)
                job.imported_at = timezone.now()
                job.imported_by = user
                job.status = ImportJob.Status.IMPORTED
                job.error = ""
                job.save(
                    update_fields=["imported_at", "imported_by", "status", "error"]
                )
                self.delete_file()
        except DatasetChanged as changed:
            self.store(
                changed.rows,
                error=_(
                    "The dataset changed since the check, so nothing was imported. "
                    "Review the new check and import again."
                ),
            )
        except FileProblem as problem:
            self.fail(str(problem))

    def confirm(self, rows):
        """Compare the import's rows with the rows the check kept.

        Args:
            rows: The unsaved rows of the import's own run.

        Raises:
            DatasetChanged: A row is a problem, or has another outcome or other changes
                than the check showed.
        """
        if any(row.outcome == ImportRow.Outcome.PROBLEM for row in rows):
            raise DatasetChanged(rows)
        stored = list(
            self.job.rows.order_by("number").values_list("outcome", "changes")
        )
        if stored != [(row.outcome, row.changes) for row in rows]:
            raise DatasetChanged(rows)

    def record_outcomes(self, written):
        """Keep what each written record holds, read back from the database.

        Args:
            written: The record's key and its stored state before the import, by row
                number, for each row the import wrote.
        """
        undo = ImportUndo(self.job)
        numbers = sorted(written)
        for chunk in batched(numbers, self.FRESH_CHUNK, strict=False):
            fresh = {
                record.pk: record
                for record in self.job.model.objects.filter(
                    pk__in=[written[number][0] for number in chunk]
                )
            }
            rows = list(self.job.rows.filter(number__in=chunk))
            for row in rows:
                pk, original = written[row.number]
                record = fresh[pk]
                row.record_pk = pk
                row.portal_id = record.uuid
                row.digest = undo.digest(record)
                if original is not None:
                    row.before = self.before_of(original, record)
            ImportRow.objects.bulk_update(
                rows, ["record_pk", "portal_id", "digest", "before"]
            )

    def before_of(self, original, record):
        """List the stored values an import replaced.

        Args:
            original: The record as it was stored before the import.
            record: The record as read back after it.

        Returns:
            The text of each replaced value, by attribute name, written with
            ``field.value_to_string`` so a restore reads it with ``field.to_python``.
            An empty value is ``None``, which a restore puts back as it is.
        """
        before = {}
        for field in record._meta.concrete_fields:
            if field.primary_key or field.name in self.UNTRACKED:
                continue
            old = field.value_to_string(original)
            if old != field.value_to_string(record):
                empty = field.value_from_object(original) is None
                before[field.attname] = None if empty else old
        return before

    def delete_file(self):
        """Delete the stored file and the example values taken from it."""
        job = self.job
        if job.file:
            job.file.delete(save=False)
        job.samples = {}
        job.save(update_fields=["file", "samples"])

    def fail(self, message):
        """End the job as failed and delete its file.

        Args:
            message: Why the file could not be read.
        """
        job = self.job
        job.rows.all().delete()
        job.status = ImportJob.Status.FAILED
        job.error = message
        job.file_problems = [message]
        job.save(update_fields=["status", "error", "file_problems"])
        self.delete_file()

    def stop(self, message):
        """Return an import that ran out of time to the check.

        Args:
            message: What to tell the person, which says nothing was written.
        """
        job = self.job
        job.status = ImportJob.Status.CHECKED
        job.error = message
        job.save(update_fields=["status", "error"])
