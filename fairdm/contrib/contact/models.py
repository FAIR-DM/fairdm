"""What the portal keeps about a Contact message and a reported problem.

Prototype code for specification 027. The screens are settled here. Everything behind them is
rebuilt test-first when the feature is planned.
"""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class ContactMessage(models.Model):
    """A record that a message was sent. The text of the message is never stored.

    Attributes:
        sender: The person who wrote the message.
        content_type: The type of the record the message is about.
        object_id: The primary key of that record.
        record: The project, dataset, person or organization the message is about.
        subject: What the message is about.
        sent: When it was sent.
    """

    class Subject(models.TextChoices):
        QUESTION = "question", _("A general question")
        EARLY_ACCESS = "early-access", _("Access to the data before it is published")
        SPECIMEN = "specimen", _("Borrowing a specimen")

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contact_messages",
        verbose_name=_("sender"),
        help_text=_("The person who wrote the message."),
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("record type"),
        help_text=_("The type of the record the message is about."),
    )
    object_id = models.PositiveBigIntegerField(
        verbose_name=_("record id"),
        help_text=_("The primary key of the record the message is about."),
    )
    record = GenericForeignKey("content_type", "object_id")
    subject = models.CharField(
        _("subject"),
        max_length=20,
        choices=Subject,
        default=Subject.QUESTION,
        help_text=_("What the message is about."),
    )
    sent = models.DateTimeField(
        _("sent"),
        auto_now_add=True,
        help_text=_("When the message was sent."),
    )

    class Meta:
        verbose_name = _("contact message")
        verbose_name_plural = _("contact messages")
        ordering = ["-sent"]

    def __str__(self):
        return f"{self.sender} · {self.get_subject_display()} · {self.sent:%Y-%m-%d}"


class ProblemReport(models.Model):
    """A reader's description of something wrong with a dataset, sample or measurement.

    Attributes:
        reporter: The reader who reported the problem.
        content_type: The type of the record the report is about.
        object_id: The primary key of that record.
        record: The dataset, sample or measurement the report is about.
        dataset: The dataset whose list the report appears in.
        description: What the reader says is wrong.
        state: Open or resolved.
        created: When the report was made.
        resolved_by: Who marked it resolved.
        resolved: When it was marked resolved.
        note: What the resolver wrote for the reader.
    """

    class State(models.TextChoices):
        OPEN = "open", _("Open")
        RESOLVED = "resolved", _("Resolved")

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="problem_reports",
        verbose_name=_("reporter"),
        help_text=_("The reader who reported the problem."),
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("record type"),
        help_text=_("The type of the record the report is about."),
    )
    object_id = models.PositiveBigIntegerField(
        verbose_name=_("record id"),
        help_text=_("The primary key of the record the report is about."),
    )
    record = GenericForeignKey("content_type", "object_id")
    dataset = models.ForeignKey(
        "dataset.Dataset",
        on_delete=models.CASCADE,
        related_name="problem_reports",
        verbose_name=_("dataset"),
        help_text=_(
            "The dataset whose list of reported problems this report appears in."
        ),
    )
    description = models.TextField(
        _("description"),
        max_length=2000,
        help_text=_(
            "What is wrong, and where. Say what you expected to see if you know."
        ),
    )
    state = models.CharField(
        _("state"),
        max_length=10,
        choices=State,
        default=State.OPEN,
        help_text=_("Whether the report is still open."),
    )
    created = models.DateTimeField(
        _("reported"),
        auto_now_add=True,
        help_text=_("When the report was made."),
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_problem_reports",
        verbose_name=_("resolved by"),
        help_text=_("Who marked the report resolved."),
    )
    resolved = models.DateTimeField(
        _("resolved"),
        null=True,
        blank=True,
        help_text=_("When the report was marked resolved."),
    )
    note = models.TextField(
        _("note to the reporter"),
        max_length=1000,
        blank=True,
        help_text=_(
            "What was done about it. The person who reported the problem receives this by email."
        ),
    )

    class Meta:
        verbose_name = _("reported problem")
        verbose_name_plural = _("reported problems")
        ordering = ["-created"]

    def __str__(self):
        return f"{self.reporter} · {self.created:%Y-%m-%d}"
