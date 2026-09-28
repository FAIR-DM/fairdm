"""Models for samples and their related descriptions, dates, identifiers and relations."""

import re

from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models as django_models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _
from polymorphic.managers import PolymorphicManager
from research_vocabs.fields import ConceptField
from shortuuid.django_fields import ShortUUIDField

from fairdm.db import models

from ..abstract import (
    AbstractDate,
    AbstractDescription,
    AbstractIdentifier,
    BasePolymorphicModel,
)
from ..utils import CORE_PERMISSIONS
from ..vocabularies import (
    FairDMDates,
    FairDMDescriptions,
    FairDMIdentifiers,
    FairDMRoles,
    FairDMSampleStatus,
)
from .managers import SampleQuerySet

BASE_SAMPLE_ERROR = _(
    "Cannot create base Sample instances directly. Please use a specific sample type subclass."
)

# An IGSN is now an ordinary DataCite DOI with no shared prefix and no suffix grammar, so a
# prefix-anchored regex is wrong. Normalise the common display forms, then accept any DataCite
# DOI or the legacy pre-2023 handle. Case and the suffix are never constrained.
IGSN_DISPLAY_PREFIXES = (
    "https://doi.org/",
    "http://doi.org/",
    "https://igsn.org/",
    "hdl.handle.net/",
    "doi:",
    "igsn:",
)
IGSN_DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)
IGSN_LEGACY_HANDLE_PATTERN = re.compile(r"^10273/\S+$", re.IGNORECASE)


class Sample(BasePolymorphicModel):
    """A physical or digital object that is part of a dataset.

    A polymorphic model: domain-specific sample types inherit from this base. The base ``Sample``
    itself cannot be saved.

    Attributes:
        CONTRIBUTOR_ROLES: The roles a contributor can hold on a sample.
        DATE_TYPES: The date types a sample can carry.
        DESCRIPTION_TYPES: The description types a sample can carry.
        dataset: The dataset this sample belongs to.
        uuid: Unique short identifier with an ``s`` prefix.
        local_id: The creator's own identifier for the sample within its dataset.
        status: The sample's custody status, such as available or destroyed.
        location: The sample's location.
        contributors: Generic relation to contributor records.
        related: Samples related through ``SampleRelation``.
        objects: The manager, with the ``SampleQuerySet`` helpers.
    """

    CONTRIBUTOR_ROLES = FairDMRoles.from_collection("Sample")
    DATE_TYPES = FairDMDates.from_collection("Sample")
    DESCRIPTION_TYPES = FairDMDescriptions.from_collection("Sample")

    dataset = models.ForeignKey(
        "dataset.Dataset",
        verbose_name=_("dataset"),
        help_text=_("The original dataset this sample first appeared in."),
        related_name="samples",
        on_delete=models.CASCADE,
    )

    uuid = ShortUUIDField(
        editable=False,
        unique=True,
        prefix="s",
        verbose_name="UUID",
        help_text=_(
            "A unique identifier generated automatically when the sample is created. It cannot "
            "be edited."
        ),
    )
    local_id = models.CharField(
        _("Local ID"),
        max_length=255,
        help_text=_(
            "An alphanumeric identifier used by the creator/s to identify the sample within the context of a specific dataset"
        ),
        null=True,
        blank=True,
    )
    status = ConceptField(
        verbose_name=_("status"),
        help_text=_("The current custody status of the physical specimen."),
        vocabulary=FairDMSampleStatus,
        default="unknown",
    )

    location = models.ForeignKey(
        "fairdm_location.Point",
        verbose_name=_("location"),
        help_text=_("The location of the sample."),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    contributors = GenericRelation("contributors.Contribution")

    related = models.ManyToManyField(
        "self",
        through="SampleRelation",
        symmetrical=False,
        related_name="related_from",
        blank=True,
    )

    objects = PolymorphicManager.from_queryset(SampleQuerySet)()  # type: ignore[assignment,misc]

    class Meta:
        verbose_name = _("sample")
        verbose_name_plural = _("samples")
        ordering = ["added"]
        default_related_name = "samples"
        permissions = [
            *CORE_PERMISSIONS,
            ("import_data", "Can import sample data"),
        ]

    def __str__(self):
        """Use the sample's name."""
        return f"{self.name}"

    def clean(self):
        """Refuse a bare ``Sample``, which must be created as a subclass."""
        super().clean()

        # Forms and the admin call full_clean() before save(), so a bare Sample becomes a
        # validation error there rather than the server error the pre_save guard raises.
        if self.__class__ == Sample:
            raise ValidationError(BASE_SAMPLE_ERROR)

    def get_absolute_url(self):
        """Return the URL of the sample's overview page."""
        from django.urls import reverse

        return reverse("sample:overview", kwargs={"uuid": self.uuid})

    def get_all_relationships(self):
        """Return every relation in which this sample is the source or the target.

        Returns:
            A queryset of ``SampleRelation`` objects involving this sample.
        """
        return SampleRelation.objects.filter(
            django_models.Q(source=self) | django_models.Q(target=self)
        )

    def get_related_samples(self, relationship_type=None):
        """Return every sample related to this sample, as source or target.

        Args:
            relationship_type: Only follow relations of this type, such as ``"child_of"``.

        Returns:
            A queryset of the related samples, excluding this one.
        """
        relationships = self.get_all_relationships()

        if relationship_type:
            relationships = relationships.filter(type=relationship_type)

        related_ids = set()
        for rel in relationships:
            if rel.source_id != self.id:
                related_ids.add(rel.source_id)
            if rel.target_id != self.id:
                related_ids.add(rel.target_id)

        return Sample.objects.filter(id__in=related_ids)

    def get_children(self):
        """Return the samples that are children of this one.

        Returns:
            A queryset of samples with a ``child_of`` relation whose target is this sample.
        """
        child_ids = SampleRelation.objects.filter(
            target=self, type="child_of"
        ).values_list("source_id", flat=True)
        return Sample.objects.filter(id__in=child_ids)

    def get_parents(self):
        """Return the samples that are parents of this one.

        Returns:
            A queryset of samples that are the target of a ``child_of`` relation whose source is
            this sample.
        """
        parent_ids = SampleRelation.objects.filter(
            source=self, type="child_of"
        ).values_list("target_id", flat=True)
        return Sample.objects.filter(id__in=parent_ids)

    def get_descendants(self, depth=None):
        """Return the descendants of this sample, optionally to a depth limit.

        Delegates to ``SampleQuerySet.get_descendants``, the single traversal implementation.

        Args:
            depth: The maximum depth to traverse. ``None`` is unlimited, 1 is direct children only,
                2 includes grandchildren, and so on.

        Returns:
            A queryset of the descendant samples within the depth limit.
        """
        return Sample.objects.get_descendants(self, max_depth=depth)

    def get_ancestors(self, depth=None):
        """Return the ancestors of this sample, optionally to a depth limit.

        Delegates to ``SampleQuerySet.get_ancestors``, the single traversal implementation.

        Args:
            depth: The maximum depth to traverse. ``None`` is unlimited, 1 is direct parents only,
                2 includes grandparents, and so on.

        Returns:
            A queryset of the ancestor samples within the depth limit.
        """
        return Sample.objects.get_ancestors(self, max_depth=depth)

    @classproperty
    def type_of(self):
        """Return the base Sample class for polymorphic queries."""
        return Sample

    def get_template_name(self):
        """Return the card templates to try for this sample, in order of preference.

        Returns:
            The template paths.
        """
        app_name = self._meta.app_label
        model_name = self._meta.model_name
        return [f"{app_name}/{model_name}_card.html", "fairdm/sample_card.html"]


@receiver(pre_save, sender=Sample)
def block_base_sample_creation(sender, instance, **kwargs):
    """Refuse to save a bare ``Sample`` row, by any route.

    Scoped to ``sender=Sample`` because a subclass instance sends its own class, so this never
    fires for a registered sample type. ``pre_save`` also covers fixture loading, and it cannot
    fire on the framework's own read path, where django-polymorphic never saves base instances.
    ``Sample.clean()`` stays alongside so forms and the admin raise a validation error instead.

    Args:
        sender: The model class being saved.
        instance: The instance being saved.
        **kwargs: Additional signal arguments.

    Raises:
        ValidationError: Always, since a bare ``Sample`` cannot be saved.
    """
    raise ValidationError(BASE_SAMPLE_ERROR)


class SampleDescription(AbstractDescription):
    """Typed free-text description of a sample."""

    VOCABULARY = FairDMDescriptions.from_collection("Sample")
    related = models.ForeignKey("Sample", on_delete=models.CASCADE)

    def clean(self):
        """Refuse a description type outside the vocabulary."""
        super().clean()

        if self.type:
            valid_types = self.VOCABULARY.values
            if self.type not in valid_types:
                raise ValidationError(
                    {
                        "type": _("'%(type)s' is not a valid Sample description type.")
                        % {"type": self.type}
                    }
                )


class SampleDate(AbstractDate):
    """Typed date on a sample."""

    VOCABULARY = FairDMDates.from_collection("Sample")
    related = models.ForeignKey("Sample", on_delete=models.CASCADE)

    def clean(self):
        """Refuse a date type outside the vocabulary."""
        super().clean()

        if self.type:
            valid_types = self.VOCABULARY.values
            if self.type not in valid_types:
                raise ValidationError(
                    {
                        "type": _("'%(type)s' is not a valid Sample date type.")
                        % {"type": self.type}
                    }
                )


class SampleIdentifier(AbstractIdentifier):
    """Typed external identifier of a sample, from the sample identifier collection (IGSN and DOI)."""

    VOCABULARY = FairDMIdentifiers.from_collection("Sample")
    related = models.ForeignKey("Sample", on_delete=models.CASCADE)

    def clean(self):
        """Refuse an identifier type outside the vocabulary and an invalid IGSN."""
        # The IGSN check runs first because it normalises `self.value`, and the uniqueness check
        # in `super().clean()` compares it exactly. Two display variants would otherwise both pass.
        if self.type == "IGSN" and self.value:
            self._validate_igsn_format()

        super().clean()

        if self.type:
            valid_types = self.VOCABULARY.values
            if self.type not in valid_types:
                raise ValidationError(
                    {
                        "type": _("'%(type)s' is not a valid Sample identifier type.")
                        % {"type": self.type}
                    }
                )

    def _validate_igsn_format(self):
        """Normalise and validate ``self.value`` as an IGSN.

        Strips the display prefixes an IGSN is commonly pasted with, then accepts any DataCite DOI
        or the legacy pre-2023 handle, case-insensitively.

        Returns:
            None once the value is valid.

        Raises:
            ValidationError: The value is neither a DataCite DOI nor a legacy IGSN handle.
        """
        normalised = self.value
        for prefix in IGSN_DISPLAY_PREFIXES:
            if normalised.lower().startswith(prefix.lower()):
                normalised = normalised[len(prefix) :]
                break
        self.value = normalised

        if IGSN_DOI_PATTERN.match(normalised) or IGSN_LEGACY_HANDLE_PATTERN.match(
            normalised
        ):
            return

        raise ValidationError(
            {
                "value": _(
                    "'%(value)s' is not a valid IGSN. Expected a DataCite DOI "
                    "(e.g. 10.60516/AU1101) or a legacy IGSN handle "
                    "(e.g. 10273/BGRB5054RX05201)."
                )
                % {"value": self.value}
            }
        )


class SampleRelation(models.Model):
    """Typed relationship between two samples, such as parent and child.

    A sample cannot relate to itself, and A to B and B to A with the same type is refused. The
    ``unique_together`` constraint on source, target and type prevents duplicate links.

    Attributes:
        RELATION_TYPES: The relationship types offered.
        type: The type of relationship, such as ``child_of``.
        source: The sample initiating the relationship.
        target: The sample being related to.
        added: Unused, as the model records no creation time.
        modified: Unused, as the model records no modification time.
    """

    RELATION_TYPES = [
        ("child_of", _("child of")),
    ]
    type = models.CharField(
        max_length=255, verbose_name=_("type"), choices=RELATION_TYPES
    )
    source = models.ForeignKey(
        "Sample",
        verbose_name=_("source"),
        related_name="related_samples",
        on_delete=models.CASCADE,
    )
    target = models.ForeignKey(
        "Sample",
        verbose_name=_("target"),
        related_name="related_to",
        on_delete=models.CASCADE,
    )
    added = None
    modified = None

    class Meta:
        unique_together = [("source", "target", "type")]
        verbose_name = _("sample relationship")
        verbose_name_plural = _("sample relationships")

    def __str__(self):
        """Show the source, the relationship type and the target."""
        return f"{self.source} {self.type} {self.target}"

    def _refuse_self_reference_and_loop(self):
        """Raise if this relationship is a self-reference or a two-step loop.

        Both ``clean()`` and ``save()`` call this, so the refusal holds when saved directly.

        Raises:
            ValidationError: The sample relates to itself, or the reverse relationship exists.
        """
        if self.source_id and self.target_id and self.source_id == self.target_id:
            raise ValidationError(_("Sample cannot relate to itself"))

        if self.source_id and self.target_id and self.type:  # noqa: SIM102
            if (
                SampleRelation.objects.filter(
                    source_id=self.target_id, target_id=self.source_id, type=self.type
                )
                .exclude(pk=self.pk)
                .exists()
            ):
                raise ValidationError(
                    _(
                        f"Circular relationship detected: {self.target} already "
                        f"has {self.type} relationship to {self.source}"
                    )
                )

    def clean(self):
        """Refuse a self-reference or a two-step loop."""
        self._refuse_self_reference_and_loop()

    def save(self, *args, **kwargs):
        """Refuse a self-reference or a two-step loop even when saved directly."""
        # `objects.create()` and a bare `.save()` skip `clean()`. Duplicate links are left to the
        # `unique_together` constraint.
        self._refuse_self_reference_and_loop()
        super().save(*args, **kwargs)
