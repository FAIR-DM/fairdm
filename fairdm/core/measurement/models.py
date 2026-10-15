"""Models for measurements and their related descriptions, dates and identifiers."""

from typing import NamedTuple

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis import geos
from django.contrib.gis.db.models import PointField
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _
from shortuuid.django_fields import ShortUUIDField

from fairdm.db import models
from fairdm.utils.location.db import geography_index, location_constraints

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


class EffectiveLocation(NamedTuple):
    """Where a measurement is for a viewer, and whose location that is.

    Attributes:
        point: The point, in SRID 4326.
        elevation: Metres above mean sea level, or None.
        uncertainty: Metres, or None.
        source: ``"own"`` for the measurement's own location, ``"sample"`` for its sample's.
    """

    point: geos.Point
    elevation: float | None
    uncertainty: float | None
    source: str


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
        location: The point where the measurement was made, in WGS 84.
        location_elevation: Metres above mean sea level.
        location_uncertainty: Metres within which the true place lies.
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

    location = PointField(
        srid=4326,
        verbose_name=_("location"),
        help_text=_("Where the record is, as a point in WGS 84."),
        null=True,
        blank=True,
    )
    location_elevation = models.FloatField(
        verbose_name=_("elevation"),
        help_text=_(
            "Metres above mean sea level, and a negative number below it. Needs a location."
        ),
        null=True,
        blank=True,
    )
    location_uncertainty = models.FloatField(
        verbose_name=_("uncertainty"),
        help_text=_(
            "The distance in metres from the location within which the true place lies. "
            "Needs a location."
        ),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("measurement")
        verbose_name_plural = _("measurements")
        ordering = ["-modified"]
        default_related_name = "measurements"
        indexes = [
            models.Index(fields=["modified"], name="measurement_modified_idx"),
            geography_index("measurement_location_geog_idx"),
        ]
        constraints = location_constraints()
        permissions = [
            *CORE_PERMISSIONS,
        ]

    def __str__(self):
        """Show the measurement's value, else its name, else its portal ID."""
        value = self.get_value()
        if value is not None and value != "":
            return f"{value}"
        return self.name or self.uuid

    def clean(self):
        """Refuse a bare ``Measurement``, and a change of dataset that leaves nobody to manage it."""
        super().clean()
        from django.core.exceptions import ValidationError

        from fairdm.contrib.contributors.access import RecordAccess

        RecordAccess(self).refuse_move_without_manager("dataset")

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

    def effective_location_for(self, user=None):
        """Return where the measurement is for a viewer: its own location, else its sample's.

        The sample's is used only where the viewer may open the sample, by the same rule as
        ``MeasurementQuerySet.with_effective_location``.

        Args:
            user: The viewer, or ``None`` for a visitor who is not signed in.

        Returns:
            An ``EffectiveLocation`` naming the point, its elevation and uncertainty and whose
            location it is, or ``None`` when the viewer has none to be shown.
        """
        if self.location is not None:
            return EffectiveLocation(
                self.location,
                self.location_elevation,
                self.location_uncertainty,
                "own",
            )
        row = (
            Measurement.objects.filter(pk=self.pk)
            .with_effective_location(user)
            .values_list(
                "effective_location",
                "sample__location_elevation",
                "sample__location_uncertainty",
            )
            .first()
        )
        if row is None or row[0] is None:
            return None
        return EffectiveLocation(*row, "sample")

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
