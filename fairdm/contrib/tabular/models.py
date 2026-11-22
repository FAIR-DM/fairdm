"""One record per file someone imports into a dataset."""

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class ImportJob(models.Model):
    """A file uploaded into one dataset for one record type, from upload to outcome.

    The check and the import both run in the background. The check writes nothing and keeps the
    outcome of every row, which is what the review screen shows. The import writes the same rows
    and keeps what undoing it would restore.
    """

    class Mode(models.TextChoices):
        BOTH = "both", _("Add new records and update existing ones")
        ADD = "add", _("Only add new records")
        UPDATE = "update", _("Only update existing records")

    class Empty(models.TextChoices):
        KEEP = "keep", _("Keep the stored value")
        CLEAR = "clear", _("Clear the stored value")

    class Status(models.TextChoices):
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
        "dataset.Dataset", on_delete=models.CASCADE, related_name="import_jobs"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    created = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="imports/%Y/%m/")
    filename = models.CharField(max_length=255)
    file_format = models.CharField(max_length=10)
    file_size = models.PositiveIntegerField(default=0)
    mode = models.CharField(max_length=10, choices=Mode.choices, default=Mode.BOTH)
    empty_cells = models.CharField(max_length=10, choices=Empty.choices, default=Empty.KEEP)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.MATCHING)

    #: The headings found in the file, in order.
    headers = models.JSONField(default=list)
    #: Up to five values from each column, keyed by heading.
    samples = models.JSONField(default=dict)
    #: The file's heading -> the column it fills, or "" for ignored.
    column_map = models.JSONField(default=dict)
    row_count = models.PositiveIntegerField(default=0)

    #: Counts per outcome: new, update, unchanged, skipped, problem.
    summary = models.JSONField(default=dict)
    #: One entry per row: number, outcome, label, record url, changes, problems, values.
    rows = models.JSONField(default=list)
    #: Problems with the file as a whole.
    file_problems = models.JSONField(default=list)

    checked_at = models.DateTimeField(null=True, blank=True)
    imported_at = models.DateTimeField(null=True, blank=True)
    imported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    #: created: [pk], updated: {pk: {attribute: stored string}}
    undo = models.JSONField(default=dict)
    undone_at = models.DateTimeField(null=True, blank=True)
    undone_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.filename

    @property
    def model(self):
        return self.content_type.model_class()

    @property
    def type_name(self):
        return str(self.model._meta.verbose_name_plural)

    @property
    def type_slug(self):
        return self.model._meta.model_name

    def get_absolute_url(self):
        return reverse(
            "dataset:imports-job", kwargs={"uuid": self.dataset.uuid, "job": self.pk}
        )

    @property
    def is_running(self):
        return self.status in (self.Status.CHECKING, self.Status.IMPORTING)

    @property
    def is_finished(self):
        return self.status in (
            self.Status.IMPORTED,
            self.Status.UNDONE,
            self.Status.DISCARDED,
            self.Status.FAILED,
        )

    @property
    def writes(self):
        """How many records the import writes."""
        return self.summary.get("new", 0) + self.summary.get("update", 0)
