import re

from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models as django_models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.functional import classproperty

# from rest_framework.authtoken.models import Token
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
from ..choices import SampleStatus
from ..utils import CORE_PERMISSIONS
from ..vocabularies import (
    FairDMDates,
    FairDMDescriptions,
    FairDMIdentifiers,
    FairDMRoles,
)
from .managers import SampleQuerySet

BASE_SAMPLE_ERROR = "Cannot create base Sample instances directly. Please use a specific sample type subclass."

# research.md R1: IGSN allocation moved to DataCite in 2023, and an IGSN today is an
# ordinary DataCite DOI spread across at least 38 registry prefixes with no shared prefix
# and no enforced suffix grammar. A prefix-anchored regex is structurally wrong, not merely
# stale, so this normalises the display forms an IGSN is commonly pasted in as, then accepts
# any DataCite DOI or the legacy pre-2023 handle form. Case carries no information and the
# suffix is never constrained - a slash inside the suffix is normal (D-016).
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
    """A sample is a physical or digital object that is part of a dataset.

    Samples represent physical specimens, digital artifacts, or observational data
    collected as part of a research dataset. This is a polymorphic model allowing
    for domain-specific sample types to be defined by inheriting from this base.

    Attributes:
        dataset: The dataset this sample belongs to
        uuid: Unique short identifier with 's' prefix
        local_id: Local identifier used by dataset creator
        status: Current status of the sample (e.g., available, destroyed)
        location: Geographic location of the sample
        contributors: Generic relation to contributor records
    """

    CONTRIBUTOR_ROLES = FairDMRoles.from_collection("Sample")
    DATE_TYPES = FairDMDates.from_collection("Sample")
    DESCRIPTION_TYPES = FairDMDescriptions.from_collection("Sample")
    # IDENTIFIER_TYPES = choices.DataCiteIdentifiers

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
        vocabulary=SampleStatus,
        default="unknown",
    )

    location = models.ForeignKey(
        "fairdm_location.Point",
        verbose_name=_("location"),
        help_text=_("The location of the sample."),
        # related_name="samples",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    # GENERIC RELATIONS
    contributors = GenericRelation("contributors.Contribution")

    # MANY-TO-MANY RELATIONSHIPS
    related = models.ManyToManyField(
        "self",
        through="SampleRelation",
        symmetrical=False,
        related_name="related_from",
        blank=True,
    )

    # CUSTOM MANAGER
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
        return f"{self.name}"

    def clean(self):
        """Validate that Sample is not instantiated directly (only subclasses).

        Raises:
            ValidationError: If attempting to create base Sample instance
        """
        super().clean()

        # Prevent direct instantiation of base Sample model. Forms and the admin call
        # full_clean() before save(), so this is what turns a bare-Sample attempt into a
        # validation error there rather than the server error the pre_save guard below raises.
        if self.__class__ == Sample:
            raise ValidationError(_(BASE_SAMPLE_ERROR))

    def get_absolute_url(self):
        """Get the absolute URL for this sample.

        Returns:
            str: URL path to sample detail view (placeholder for future implementation)
        """
        from django.urls import reverse

        # Placeholder - will be implemented when views are created
        return reverse("sample:overview", kwargs={"uuid": self.uuid})

    def get_all_relationships(self):
        """Get all SampleRelation objects where this sample is source or target.

        Returns:
            QuerySet: All SampleRelation objects involving this sample

        Example:
            >>> sample = Sample.objects.get(uuid="s_abc123")
            >>> relationships = sample.get_all_relationships()
            >>> for rel in relationships:
            >>>     print(f"{rel.source} {rel.type} {rel.target}")
        """
        return SampleRelation.objects.filter(
            django_models.Q(source=self) | django_models.Q(target=self)
        )

    def get_related_samples(self, relationship_type=None):
        """Get all samples related to this sample.

        Args:
            relationship_type: Optional filter for specific relationship type
                             (e.g., "child_of")

        Returns:
            QuerySet: Sample objects related to this sample

        Example:
            >>> parent = Sample.objects.get(uuid="s_abc123")
            >>> children = parent.get_related_samples(relationship_type="child_of")
        """
        relationships = self.get_all_relationships()

        if relationship_type:
            relationships = relationships.filter(type=relationship_type)

        # Get sample IDs from both source and target, excluding self
        related_ids = set()
        for rel in relationships:
            if rel.source_id != self.id:
                related_ids.add(rel.source_id)
            if rel.target_id != self.id:
                related_ids.add(rel.target_id)

        return Sample.objects.filter(id__in=related_ids)

    def get_children(self):
        """Get all child samples (samples where this is the target of 'child_of' relationship).

        Returns:
            QuerySet: Sample objects that are children of this sample

        Example:
            >>> parent = Sample.objects.get(uuid="s_abc123")
            >>> children = parent.get_children()
            >>> for child in children:
            >>>     print(f"{child.name} is a child of {parent.name}")
        """
        # Children are samples where this sample is the target of a "child_of" relationship
        child_ids = SampleRelation.objects.filter(
            target=self, type="child_of"
        ).values_list("source_id", flat=True)
        return Sample.objects.filter(id__in=child_ids)

    def get_parents(self):
        """Get all parent samples (samples where this is the source of 'child_of' relationship).

        Returns:
            QuerySet: Sample objects that are parents of this sample

        Example:
            >>> child = Sample.objects.get(uuid="s_abc123")
            >>> parents = child.get_parents()
            >>> for parent in parents:
            >>>     print(f"{child.name} is a child of {parent.name}")
        """
        # Parents are samples where this sample is the source of a "child_of" relationship
        parent_ids = SampleRelation.objects.filter(
            source=self, type="child_of"
        ).values_list("target_id", flat=True)
        return Sample.objects.filter(id__in=parent_ids)

    def get_descendants(self, depth=None):
        """Get all descendant samples with optional depth limit.

        Uses iterative breadth-first traversal to find descendants. Prevents
        infinite loops by tracking visited samples.

        Args:
            depth: Maximum depth to traverse (None = unlimited). Depth 1 returns
                  only direct children, depth 2 includes grandchildren, etc.

        Returns:
            QuerySet: All descendant Sample objects within depth limit

        Example:
            >>> root = Sample.objects.get(uuid="s_abc123")
            >>> direct_children = root.get_descendants(depth=1)
            >>> all_descendants = root.get_descendants()
        """
        if depth is not None and depth < 1:
            return Sample.objects.none()

        descendants = set()
        current_level = {self.id}
        visited = {self.id}
        current_depth = 0

        while current_level and (depth is None or current_depth < depth):
            # Get children of current level
            child_ids = set(
                SampleRelation.objects.filter(
                    target_id__in=current_level, type="child_of"
                ).values_list("source_id", flat=True)
            )

            # Remove already visited to prevent cycles
            child_ids = child_ids - visited

            if not child_ids:
                break

            descendants.update(child_ids)
            visited.update(child_ids)
            current_level = child_ids
            current_depth += 1

        return Sample.objects.filter(id__in=descendants)

    @classproperty
    def type_of(self):
        return Sample

    def get_template_name(self):
        app_name = self._meta.app_label
        model_name = self._meta.model_name
        return [f"{app_name}/{model_name}_card.html", "fairdm/sample_card.html"]


@receiver(pre_save, sender=Sample)
def block_base_sample_creation(sender, instance, **kwargs):
    """Refuse to save a bare ``Sample`` row, by any route.

    Scoped to ``sender=Sample`` rather than connected without a sender: a subclass instance
    sends its own class, never ``Sample``, so this never fires for a registered specimen type.
    ``pre_save`` is the one mechanism that also covers fixture loading (`django.core.serializers`
    sends it on every deserialized object) and cannot fire on the framework's own read path -
    django-polymorphic only constructs base instances there, it never saves them (research.md
    R4). ``Sample.clean()`` stays alongside this so forms and the admin still raise a validation
    error instead of the server error this receiver raises.
    """
    raise ValidationError(_(BASE_SAMPLE_ERROR))


class SampleDescription(AbstractDescription):
    """Free-text description of a Sample with type categorization.

    Supports multiple description types (e.g., abstract, methods, notes)
    as defined by the FairDM Sample description vocabulary.
    """

    VOCABULARY = FairDMDescriptions.from_collection("Sample")
    related = models.ForeignKey("Sample", on_delete=models.CASCADE)

    def clean(self):
        """Validate description_type against FairDMDescriptions vocabulary.

        Raises:
            ValidationError: If type is not in DESCRIPTION_TYPES vocabulary
        """
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
    """Important dates associated with a Sample.

    Tracks various dates (e.g., collected, processed, archived) as defined
    by the FairDM Sample date vocabulary.
    """

    VOCABULARY = FairDMDates.from_collection("Sample")
    related = models.ForeignKey("Sample", on_delete=models.CASCADE)

    def clean(self):
        """Validate date_type against FairDMDates vocabulary.

        Raises:
            ValidationError: If type is not in DATE_TYPES vocabulary
        """
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
    """External identifiers for a Sample.

    Links a sample to an external identifier system, drawn from the sample identifier
    collection (``FairDMIdentifiers.from_collection("Sample")``, IGSN and DOI - D-003, R3).
    """

    VOCABULARY = FairDMIdentifiers.from_collection("Sample")
    related = models.ForeignKey("Sample", on_delete=models.CASCADE)

    def clean(self):
        """Validate identifier_type and IGSN format.

        Raises:
            ValidationError: If type is not in IDENTIFIER_TYPES vocabulary
                           or if IGSN format is invalid
        """
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

        if self.type == "IGSN" and self.value:
            self._validate_igsn_format()

    def _validate_igsn_format(self):
        """Validate ``self.value`` against the format research.md R1/D-016 settles on.

        An IGSN today is an ordinary DataCite DOI with no shared prefix and no enforced
        suffix grammar, so this normalises the display forms an IGSN is commonly pasted
        in as, then accepts any DataCite DOI or the legacy pre-2023 handle form,
        case-insensitively.
        """
        normalised = self.value
        for prefix in IGSN_DISPLAY_PREFIXES:
            if normalised.lower().startswith(prefix.lower()):
                normalised = normalised[len(prefix) :]
                break

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
    """Through-model for sample-to-sample relationships.

    Defines typed relationships between samples (e.g., parent/child, derived from).
    This allows tracking of sample hierarchies, splits, and derivations.

    Attributes:
        type: Type of relationship (e.g., 'child_of')
        source: The sample initiating the relationship
        target: The sample being related to

    Validation:
        - Prevents self-reference (sample cannot relate to itself)
        - Prevents direct circular relationships (A→B and B→A with same type)
        - Enforces unique_together constraint on (source, target, type)
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
        """Return string representation of relationship."""
        return f"{self.source} {self.type} {self.target}"

    def clean(self):
        """Validate relationship to prevent self-reference and circular relationships."""
        from django.core.exceptions import ValidationError

        # 1. Prevent self-reference
        if self.source_id and self.target_id and self.source_id == self.target_id:
            raise ValidationError(_("Sample cannot relate to itself"))

        # 2. Prevent direct circular relationships (A→B and B→A with same type)
        if self.source_id and self.target_id and self.type:  # noqa: SIM102
            # Check if reverse relationship already exists
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
