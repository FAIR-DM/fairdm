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
from .managers import MeasurementQuerySet


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

    objects = PolymorphicManager.from_queryset(MeasurementQuerySet)()  # type: ignore[assignment,misc]

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

    local_id = models.CharField(
        _("Local ID"),
        max_length=255,
        help_text=_(
            "An alphanumeric identifier used by the creator/s to identify this measurement within the context of a specific dataset"
        ),
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        verbose_name = _("measurement")
        verbose_name_plural = _("measurements")
        ordering = ["-modified"]
        default_related_name = "measurements"
        permissions = [
            *CORE_PERMISSIONS,
        ]

    def __str__(self):
        """Return string representation using the measurement value."""
        return f"{self.get_value()}"

    def clean(self):
        """Validate that Measurement is not instantiated directly (only subclasses).

        Raises:
            ValidationError: If attempting to create base Measurement instance
        """
        super().clean()
        from django.core.exceptions import ValidationError

        # Prevent direct instantiation of base Measurement model
        if self.__class__ == Measurement:
            raise ValidationError(
                _(
                    "Cannot create base Measurement instances directly. Please use a specific measurement type subclass."
                )
            )

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
            A type is not obliged to nominate a pint quantity for 'value' - a plain
            number is allowed (spec Assumptions) - so uncertainty arithmetic is only
            attempted where the value actually supports it.
        """
        # Handle base Measurement class that doesn't have value/uncertainty fields
        if not hasattr(self, "value"):
            return self.name

        if (
            hasattr(self, "uncertainty")
            and self.uncertainty is not None
            and hasattr(self.value, "plus_minus")
        ):
            return self.value.plus_minus(self.uncertainty)
        return self.value

    def print_value(self):
        """Get a human-readable string representation of the value with uncertainty.

        Delegates to the framework's quantity formatter (``MyFormatter``,
        installed on the shared pint unit registry at application startup -
        see ``FairDMConfig.ready()``) rather than building a string by hand.
        That formatter already renders a pint ``Measurement`` as
        "value ± error unit"; a plain value or a plain number renders through
        its own ``str()``.

        Returns:
            The value, formatted for a person.
        """
        return str(self.get_value())

    def get_absolute_url(self):
        """Get the absolute URL for this measurement.

        This is the measurement's own, permanent address - it does not deflect to
        its sample. The view and template that render that address are separate,
        later work; this method's return value is not a placeholder.

        Returns:
            str: URL path to this measurement's own detail view.
        """
        from django.urls import reverse

        return reverse("measurement:overview", kwargs={"uuid": self.uuid})

    def get_template_name(self):
        """Get template names for rendering this measurement in card format.

        Returns:
            List of template paths to try, in order of preference.
        """
        app_name = self._meta.app_label
        model_name = self._meta.model_name
        return [f"{app_name}/{model_name}_card.html", "fairdm/measurement_card.html"]


class VocabularyGuardedSave:
    """Refuse a ``type`` outside the record's own vocabulary, even on a direct save.

    ``GenericModel.__init_subclass__`` binds ``type``'s ``choices`` to ``VOCABULARY``,
    and Django validates ``choices`` only through ``full_clean()``. A manager's
    ``create()`` and a bare ``save()`` reach the database without ever calling it, so
    a record written by either route could carry a type no vocabulary contains — which
    is how the measurement metadata came to hold values like ``"method"`` that were
    never members of anything.

    Subclasses name the noun that appears in the message; everything else is shared.
    """

    #: The noun in "'x' is not a valid Measurement <noun> type."
    VOCABULARY_NOUN = ""

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        if self.type not in self.VOCABULARY.values:
            raise ValidationError(
                {
                    "type": _("'%(type)s' is not a valid Measurement %(noun)s type.")
                    % {"type": self.type, "noun": self.VOCABULARY_NOUN}
                }
            )
        super().save(*args, **kwargs)


class MeasurementDescription(VocabularyGuardedSave, AbstractDescription):
    """Free-text description of a Measurement with type categorization.

    Supports multiple description types (e.g., methods, notes, quality control)
    as defined by the FairDM Measurement description vocabulary.
    """

    VOCABULARY = FairDMDescriptions.from_collection("Measurement")
    VOCABULARY_NOUN = "description"
    related = models.ForeignKey("Measurement", on_delete=models.CASCADE)


class MeasurementDate(VocabularyGuardedSave, AbstractDate):
    """Important dates associated with a Measurement.

    Tracks various dates (e.g., measured, analyzed, validated) as defined
    by the FairDM Measurement date vocabulary.
    """

    VOCABULARY = FairDMDates.from_collection("Measurement")
    VOCABULARY_NOUN = "date"
    related = models.ForeignKey("Measurement", on_delete=models.CASCADE)


class MeasurementIdentifier(VocabularyGuardedSave, AbstractIdentifier):
    """External identifiers for a Measurement.

    Drawn from the measurement identifier collection
    (``FairDMIdentifiers.from_collection("Measurement")``, DOI - 005 F1/F2)
    rather than the unscoped vocabulary, so a member added for another record
    type (e.g. IGSN for samples) cannot leak in here.
    """

    VOCABULARY = FairDMIdentifiers.from_collection("Measurement")
    VOCABULARY_NOUN = "identifier"
    related = models.ForeignKey("Measurement", on_delete=models.CASCADE)
