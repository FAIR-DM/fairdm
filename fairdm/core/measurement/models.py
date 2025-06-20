from django.contrib.contenttypes.fields import GenericRelation
from django.utils.functional import classproperty

# from rest_framework.authtoken.models import Token
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _
from shortuuid.django_fields import ShortUUIDField

from fairdm.db import models

from ..abstract import AbstractDate, AbstractDescription, AbstractIdentifier, BasePolymorphicModel
from ..managers import PolymorphicManager
from ..vocabularies import FairDMDates, FairDMDescriptions, FairDMIdentifiers, FairDMRoles


# WARNING: PolymorphicModel must always be listed first in the inheritance list to ensure
# proper polymorphic behavior across relations and queries.
# SEE: https://github.com/jazzband/django-polymorphic/issues/437#issuecomment-677638021
class Measurement(BasePolymorphicModel):
    CONTRIBUTOR_ROLES = FairDMRoles.from_collection("Measurement")
    DESCRIPTION_TYPES = FairDMDescriptions.from_collection("Measurement")
    DATE_TYPES = FairDMDates.from_collection("Measurement")

    objects = PolymorphicManager()

    dataset = models.ForeignKey(
        "dataset.Dataset",
        verbose_name=_("dataset"),
        help_text=_("The original dataset this measurement first appeared in."),
        related_name="measurements",
        on_delete=models.CASCADE,
    )

    uuid = ShortUUIDField(
        editable=False,
        unique=True,
        prefix="m",
        verbose_name="UUID",
    )

    # GENERIC RELATIONS
    contributors = GenericRelation("contributors.Contribution")

    # RELATIONS
    sample = models.ForeignKey(
        "sample.Sample",
        verbose_name=_("sample"),
        help_text=_("The sample on which the measurement was made."),
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = _("measurement")
        verbose_name_plural = _("measurements")
        ordering = ["-modified"]
        default_related_name = "measurements"

    class FairDM:
        description = "A measurement is a record of a specific observation or calculation made on a sample."
        filterset_class = "fairdm.core.filters.MeasurementFilter"
        table_class = "fairdm.core.tables.MeasurementTable"

    def __str__(self):
        return f"{self.name}"

    @classproperty
    def type_of(self):
        # this is required for many of the class methods in PolymorphicMixin
        return Measurement

    def get_absolute_url(self):
        return self.sample.get_absolute_url()

    def get_template_name(self):
        app_name = self._meta.app_label
        model_name = self._meta.model_name
        return [f"{app_name}/{model_name}_card.html", "fairdm/measurement_card.html"]


class MeasurementDescription(AbstractDescription):
    VOCABULARY = FairDMDescriptions.from_collection("Sample")
    related = models.ForeignKey("Measurement", on_delete=models.CASCADE)


class MeasurementDate(AbstractDate):
    VOCABULARY = FairDMDates.from_collection("Sample")
    related = models.ForeignKey("Measurement", on_delete=models.CASCADE)


class MeasurementIdentifier(AbstractIdentifier):
    VOCABULARY = FairDMIdentifiers()
    related = models.ForeignKey("Measurement", on_delete=models.CASCADE)
