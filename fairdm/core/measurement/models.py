from django.contrib.contenttypes.fields import GenericRelation
from django.utils.functional import classproperty

# from rest_framework.authtoken.models import Token
from django.utils.translation import gettext_lazy as _
from shortuuid.django_fields import ShortUUIDField

from fairdm.db import models

from ..abstract import (
    AbstractDate,
    AbstractDescription,
    AbstractIdentifier,
    BasePolymorphicModel,
)
from ..managers import PolymorphicManager
from ..utils import CORE_PERMISSIONS
from ..vocabularies import (
    FairDMDates,
    FairDMDescriptions,
    FairDMIdentifiers,
    FairDMRoles,
)


class Measurement(BasePolymorphicModel):
    """A measurement is a record of a specific observation or calculation made on a sample.

    Measurements represent quantitative or qualitative data collected from samples,
    such as chemical analysis results, physical measurements, or observational data.
    This is a polymorphic model allowing for domain-specific measurement types to be
    defined by inheriting from this base.

    Attributes:
        dataset: The dataset this measurement belongs to
        uuid: Unique short identifier with 'm' prefix
        sample: The sample on which the measurement was made
        contributors: Generic relation to contributor records

    Note:
        Subclasses should define 'value' and optionally 'uncertainty' fields
        for proper functionality of get_value() and print_value() methods.
    """

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
        permissions = [
            *CORE_PERMISSIONS,
        ]

    class FairDM:
        """FairDM registry configuration for Measurement model."""

        description = "A measurement is a record of a specific observation or calculation made on a sample."
        filterset_class = "fairdm.core.filters.MeasurementFilter"
        table_class = "fairdm.contrib.collections.tables.MeasurementTable"

    def __str__(self):
        """Return string representation using the measurement value."""
        return f"{self.get_value()}"

    @classproperty
    def type_of(self):
        """Return the base Measurement class for polymorphic queries."""
        # this is required for many of the class methods in PolymorphicMixin
        return Measurement

    def get_value(self):
        """Get the measurement value with uncertainty if available.

        Returns:
            The measurement value, potentially with uncertainty annotation.
            If uncertainty is defined, returns value with plus_minus notation.
            Returns the name if value attribute is not defined (base class).

        Note:
            Requires subclass to define 'value' and optionally 'uncertainty' attributes.
        """
        # Handle base Measurement class that doesn't have value/uncertainty fields
        if not hasattr(self, "value"):
            return self.name

        if hasattr(self, "uncertainty") and self.uncertainty is not None:
            return self.value.plus_minus(self.uncertainty)
        return self.value

    def print_value(self):
        """Get a human-readable string representation of the value with uncertainty.

        Returns:
            String formatted as "value ± error" if uncertainty exists,
            otherwise just the value as a string.
        """
        value = self.get_value()
        if hasattr(value, "err"):
            return f"{value.value} ± {value.err}"
        return str(value)

    def get_absolute_url(self):
        """Get the URL for this measurement (redirects to parent sample)."""
        return self.sample.get_absolute_url()

    def get_template_name(self):
        """Get template names for rendering this measurement in card format.

        Returns:
            List of template paths to try, in order of preference.
        """
        app_name = self._meta.app_label
        model_name = self._meta.model_name
        return [f"{app_name}/{model_name}_card.html", "fairdm/measurement_card.html"]


class MeasurementDescription(AbstractDescription):
    """Free-text description of a Measurement with type categorization.

    Supports multiple description types (e.g., methods, notes, quality control)
    as defined by the FairDM Measurement description vocabulary.

    Note:
        Uses Sample vocabulary collection - consider updating to Measurement-specific.
    """

    VOCABULARY = FairDMDescriptions.from_collection("Sample")
    related = models.ForeignKey("Measurement", on_delete=models.CASCADE)


class MeasurementDate(AbstractDate):
    """Important dates associated with a Measurement.

    Tracks various dates (e.g., measured, analyzed, validated) as defined
    by the FairDM Measurement date vocabulary.

    Note:
        Uses Sample vocabulary collection - consider updating to Measurement-specific.
    """

    VOCABULARY = FairDMDates.from_collection("Sample")
    related = models.ForeignKey("Measurement", on_delete=models.CASCADE)


class MeasurementIdentifier(AbstractIdentifier):
    """External identifiers for a Measurement.

    Links measurements to external identifier systems (DOI, ARK, Handle, etc.)
    to support FAIR data principles and cross-referencing.
    """

    VOCABULARY = FairDMIdentifiers()
    related = models.ForeignKey("Measurement", on_delete=models.CASCADE)
