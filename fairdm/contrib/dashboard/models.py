"""What the dashboard stores: how often records are opened and downloaded, and what a person hid."""

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class RecordUse(models.Model):
    """How often one project or dataset was opened and downloaded on one day.

    Opens are counted on the record's overview page and downloads on an export of its
    records table. Neither counts the record's own team.
    """

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_("record type"),
        help_text=_("Project or dataset."),
    )
    object_id = models.PositiveBigIntegerField(
        _("record"), help_text=_("The key of the project or dataset.")
    )
    record = GenericForeignKey("content_type", "object_id")
    day = models.DateField(_("day"), help_text=_("The portal's day the uses fall on."))
    views = models.PositiveIntegerField(
        _("opens"), default=0, help_text=_("How often its overview page was opened.")
    )
    exports = models.PositiveIntegerField(
        _("downloads"), default=0, help_text=_("How often its records were downloaded.")
    )

    class Meta:
        verbose_name = _("record use")
        verbose_name_plural = _("record uses")
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id", "day"], name="dashboard_one_use_per_day"
            )
        ]
        indexes = [models.Index(fields=["content_type", "object_id", "day"])]

    def __str__(self):
        return f"{self.content_type.model} {self.object_id} on {self.day}"


class DashboardState(models.Model):
    """What one person has chosen about their dashboard."""

    person = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard_state",
        verbose_name=_("person"),
        help_text=_("Whose dashboard this is."),
    )
    getting_started_hidden = models.BooleanField(
        _("getting started hidden"),
        default=False,
        help_text=_("Whether the person hid the getting-started list."),
    )

    class Meta:
        verbose_name = _("dashboard state")
        verbose_name_plural = _("dashboard states")

    def __str__(self):
        return str(self.person)
