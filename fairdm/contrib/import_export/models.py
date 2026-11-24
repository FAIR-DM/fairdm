"""The stored records of an import: one job per file and one row per row of it."""

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _


class ImportJob(models.Model):
    """A file uploaded into one dataset under one import definition.

    The job runs from upload to outcome. The check and the import both run in the
    background. The check writes nothing to the dataset and keeps the outcome of every
    row as an ``ImportRow``. The import writes the same rows and keeps what undoing it
    would restore.
    """

    class Mode(models.TextChoices):
        """What a file may do to the dataset's records."""

        BOTH = "both", _("Add new records and update existing ones")
        ADD = "add", _("Only add new records")
        UPDATE = "update", _("Only update existing records")

    class Empty(models.TextChoices):
        """What an empty cell means."""

        KEEP = "keep", _("Keep the stored value")
        CLEAR = "clear", _("Clear the stored value")

    class Status(models.TextChoices):
        """Where a job stands, named once for every page that shows it."""

        MATCHING = "matching", _("Matching columns")
        CHECKING = "checking", _("Checking")
        CHECKED = "checked", _("Ready to import")
        NOTHING = "nothing", _("Nothing to change")
        PROBLEMS = "problems", _("Needs changes")
        IMPORTING = "importing", _("Importing")
        IMPORTED = "imported", _("Imported")
        FAILED = "failed", _("Could not be read")
        UNDONE = "undone", _("Undone")
        DISCARDED = "discarded", _("Discarded")

    dataset = models.ForeignKey(
        "dataset.Dataset",
        on_delete=models.CASCADE,
        related_name="import_jobs",
        verbose_name=_("dataset"),
        help_text=_("The dataset the file is imported into."),
    )
    definition_name = models.CharField(
        _("import definition"),
        max_length=100,
        help_text=_("The name of the import definition the file was read with."),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="+",
        verbose_name=_("uploaded by"),
        help_text=_("The person who uploaded the file."),
    )
    created = models.DateTimeField(
        _("uploaded"),
        auto_now_add=True,
        help_text=_("When the file was uploaded."),
    )
    file = models.FileField(
        _("file"),
        upload_to="imports/%Y/%m/",
        blank=True,
        help_text=_("The uploaded file. Empty once the job has ended."),
    )
    filename = models.CharField(
        _("file name"),
        max_length=255,
        help_text=_("The name the file had when it was uploaded."),
    )
    file_format = models.CharField(
        _("file format"),
        max_length=10,
        help_text=_("The format the file was read as."),
    )
    file_size = models.PositiveIntegerField(
        _("file size"),
        default=0,
        help_text=_("The size of the file in bytes."),
    )
    mode = models.CharField(
        _("mode"),
        max_length=10,
        choices=Mode.choices,
        default=Mode.BOTH,
        help_text=_("What the file may do to the dataset's records."),
    )
    empty_cells = models.CharField(
        _("empty cells"),
        max_length=10,
        choices=Empty.choices,
        default=Empty.KEEP,
        help_text=_("Whether an empty cell keeps or clears the stored value."),
    )
    status = models.CharField(
        _("status"),
        max_length=12,
        choices=Status.choices,
        default=Status.MATCHING,
        help_text=_("Where the import stands."),
    )
    headers = models.JSONField(
        _("headings"),
        default=list,
        help_text=_("The headings found in the file, in order."),
    )
    samples = models.JSONField(
        _("example values"),
        default=dict,
        help_text=_(
            "Up to four values from each column, shown while matching columns. "
            "Cleared when the file is deleted."
        ),
    )
    column_map = models.JSONField(
        _("column matches"),
        default=dict,
        help_text=_(
            "Each heading of the file and the column it fills, or empty when ignored."
        ),
    )
    row_count = models.PositiveIntegerField(
        _("rows"),
        default=0,
        help_text=_("How many rows the file holds."),
    )
    summary = models.JSONField(
        _("summary"),
        default=dict,
        help_text=_("How many rows each outcome has."),
    )
    file_problems = models.JSONField(
        _("file problems"),
        default=list,
        help_text=_("Problems with the file as a whole."),
    )
    error = models.TextField(
        _("error"),
        blank=True,
        help_text=_("What went wrong when the file could not be read."),
    )
    checked_at = models.DateTimeField(
        _("checked"),
        null=True,
        blank=True,
        help_text=_("When the check last finished."),
    )
    imported_at = models.DateTimeField(
        _("imported"),
        null=True,
        blank=True,
        help_text=_("When the import finished."),
    )
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("imported by"),
        help_text=_("The person who started the import."),
    )
    undone_at = models.DateTimeField(
        _("undone"),
        null=True,
        blank=True,
        help_text=_("When the import was undone."),
    )
    undone_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("undone by"),
        help_text=_("The person who undid the import."),
    )

    class Meta:
        ordering = ["-created"]
        indexes = [
            models.Index(
                fields=["dataset", "definition_name", "created"],
                name="import_job_dataset_def_idx",
            ),
        ]

    def __str__(self):
        """Name the job by its file."""
        return self.filename

    @property
    def definition(self):
        """The import definition the file was read with.

        Returns:
            The definition, or None when the portal no longer has one of that name.
        """
        from .definitions import get_definition

        return get_definition(self.definition_name)

    @property
    def model(self):
        """The sample or measurement model the rows fill.

        Returns:
            The model class of the definition.
        """
        return self.definition.model

    @property
    def type_name(self):
        """The plural name of the type the file holds.

        Returns:
            The model's plural verbose name as text.
        """
        return str(self.model._meta.verbose_name_plural)

    @property
    def is_running(self):
        """Whether a background task is working on the job.

        Returns:
            True while the job is being checked or imported.
        """
        return self.status in (self.Status.CHECKING, self.Status.IMPORTING)

    @property
    def is_finished(self):
        """Whether the job has an outcome and nothing more happens to it.

        Returns:
            True once the job is imported, undone, discarded or failed.
        """
        return self.status in (
            self.Status.IMPORTED,
            self.Status.UNDONE,
            self.Status.DISCARDED,
            self.Status.FAILED,
        )

    @property
    def writes(self):
        """How many records the import writes.

        Returns:
            The number of rows added plus the number updated.
        """
        return self.summary.get("new", 0) + self.summary.get("update", 0)


class ImportRow(models.Model):
    """One row of a file as the check saw it. No cell of the file is kept."""

    class Outcome(models.TextChoices):
        """What the import does with a row."""

        NEW = "new", _("New")
        UPDATE = "update", _("Update")
        UNCHANGED = "unchanged", _("Unchanged")
        SKIPPED = "skipped", _("Left out")
        PROBLEM = "problem", _("Problem")

    job = models.ForeignKey(
        ImportJob,
        on_delete=models.CASCADE,
        related_name="rows",
        verbose_name=_("import"),
        help_text=_("The import the row belongs to."),
    )
    number = models.PositiveIntegerField(
        _("row number"),
        help_text=_("The row's position in the file, counting from 1."),
    )
    line = models.PositiveIntegerField(
        _("line"),
        help_text=_("The line of the file the row starts on."),
    )
    outcome = models.CharField(
        _("outcome"),
        max_length=10,
        choices=Outcome.choices,
        default=Outcome.NEW,
        help_text=_("What the import does with the row."),
    )
    label = models.CharField(
        _("label"),
        max_length=255,
        blank=True,
        help_text=_("What the row is called on the review page."),
    )
    portal_id = models.CharField(
        _("portal ID"),
        max_length=100,
        blank=True,
        help_text=_(
            "The portal ID of the record, empty for a row that adds nothing yet."
        ),
    )
    record_pk = models.PositiveBigIntegerField(
        _("record"),
        null=True,
        blank=True,
        help_text=_(
            "The key of the record the import wrote, set once it has written it."
        ),
    )
    changes = models.JSONField(
        _("changes"),
        default=list,
        help_text=_("Each changed column with its label, old value and new value."),
    )
    problems = models.JSONField(
        _("problems"),
        default=list,
        help_text=_("Each column that has a problem and the message about it."),
    )
    note = models.TextField(
        _("note"),
        blank=True,
        help_text=_("Why the row was left out."),
    )
    before = models.JSONField(
        _("values before"),
        default=dict,
        help_text=_("The stored values an undo restores. Kept for update rows only."),
    )
    digest = models.CharField(
        _("digest"),
        max_length=64,
        blank=True,
        help_text=_("A digest of the record's stored values after the import."),
    )

    class Meta:
        ordering = ["number"]
        indexes = [
            models.Index(
                fields=["job", "outcome", "number"],
                name="import_row_job_outcome_idx",
            ),
        ]

    def __str__(self):
        """Name the row by its position and outcome."""
        return f"{self.number}: {self.outcome}"


@receiver(post_delete, sender=ImportJob)
def delete_stored_file(sender, instance, **kwargs):
    """Delete a job's stored file along with the job, so no file outlives it.

    Args:
        sender: The model class, ``ImportJob``.
        instance: The job that was deleted.
        **kwargs: The rest of the signal's arguments.
    """
    if instance.file:
        instance.file.delete(save=False)
