"""Models for measurements and their related descriptions, dates and identifiers."""

from django.contrib.contenttypes.fields import GenericRelation
from django.utils.functional import classproperty
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
    """A record of a specific observation or calculation made on a sample.

    A polymorphic model: domain-specific measurement types inherit from this base. Subclasses
    should define ``value`` and optionally ``uncertainty`` fields for ``get_value()`` and
    ``print_value()`` to work.

    Attributes:
        CONTRIBUTOR_ROLES: The roles a contributor can hold on a measurement.
        DESCRIPTION_TYPES: The description types a measurement can carry.
        DATE_TYPES: The date types a measurement can carry.
        objects: The manager, with the ``MeasurementQuerySet`` helpers.
        dataset: The dataset this measurement belongs to.
        uuid: Unique short identifier with an ``m`` prefix.
        contributors: Generic relation to contributor records.
        sample: The sample on which the measurement was made.
        local_id: The creator's own identifier for the measurement within its dataset.
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

    contributors = GenericRelation("contributors.Contribution")

    sample = models.ForeignKey(
        "sample.Sample",
        verbose_name=_("sample"),
        help_text=_("The sample on which the measurement was made."),
        # RESTRICT, not PROTECT: PROTECT refuses even when the measurement is deleted in the
        # same operation, so no dataset holding samples and measurements could be deleted.
        on_delete=models.RESTRICT,
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
        """Show the measurement's value."""
        return f"{self.get_value()}"

    def clean(self):
        """Refuse a bare ``Measurement``, which must be created as a subclass."""
        super().clean()
        from django.core.exceptions import ValidationError

        if self.__class__ == Measurement:
            raise ValidationError(
                _(
                    "Cannot create base Measurement instances directly. Please use a specific measurement type subclass."
                )
            )

    @classproperty
    def type_of(self):
        """Return the base Measurement class for polymorphic queries."""
        # Required by many of the class methods in PolymorphicMixin.
        return Measurement

    def get_value(self):
        """Return the measurement value, with its uncertainty when there is one.

        A type is not obliged to nominate a pint quantity for ``value``, so uncertainty
        arithmetic is only attempted where the value supports it.

        Returns:
            The value with its ``plus_minus`` uncertainty applied when both exist, the plain
            value otherwise, or the name when the class defines no ``value`` (the base class).
        """
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
        """Return the value and its uncertainty as a string for a person.

        Delegates to the framework's quantity formatter, which renders a pint ``Measurement`` as
        "value ± error unit", rather than building a string by hand.

        Returns:
            The formatted value.
        """
        return str(self.get_value())

    def get_absolute_url(self):
        """Return the URL of the measurement's own detail page."""
        from django.urls import reverse

        return reverse("measurement:overview", kwargs={"uuid": self.uuid})

    def get_template_name(self):
        """Return the card templates to try for this measurement, in order of preference.

        Returns:
            The template paths.
        """
        app_name = self._meta.app_label
        model_name = self._meta.model_name
        return [f"{app_name}/{model_name}_card.html", "fairdm/measurement_card.html"]


class VocabularyGuardedSave:
    """Refuse a ``type`` outside the record's own vocabulary, even on a direct save.

    Django validates ``choices`` only in ``full_clean()``, which a manager's ``create()`` and a
    bare ``save()`` never call. Subclasses set ``VOCABULARY_NOUN`` for the error message.

    Attributes:
        VOCABULARY_NOUN: The noun in "'x' is not a valid Measurement <noun> type."
    """

    VOCABULARY_NOUN = ""

    def save(self, *args, **kwargs):
        """Refuse a ``type`` that is not in the vocabulary, then save."""
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
    """Typed free-text description of a measurement."""

    VOCABULARY = FairDMDescriptions.from_collection("Measurement")
    VOCABULARY_NOUN = "description"
    related = models.ForeignKey("Measurement", on_delete=models.CASCADE)


class MeasurementDate(VocabularyGuardedSave, AbstractDate):
    """Typed date on a measurement."""

    VOCABULARY = FairDMDates.from_collection("Measurement")
    VOCABULARY_NOUN = "date"
    related = models.ForeignKey("Measurement", on_delete=models.CASCADE)


class MeasurementIdentifier(VocabularyGuardedSave, AbstractIdentifier):
    """Typed external identifier of a measurement.

    Drawn from the measurement identifier collection rather than the unscoped vocabulary, so a
    member added for another record type (such as IGSN for samples) cannot leak in here.
    """

    VOCABULARY = FairDMIdentifiers.from_collection("Measurement")
    VOCABULARY_NOUN = "identifier"
    related = models.ForeignKey("Measurement", on_delete=models.CASCADE)
