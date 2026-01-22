from django.contrib.contenttypes.fields import GenericRelation
from django.db import models as django_models
from django.utils.functional import classproperty

# from rest_framework.authtoken.models import Token
from django.utils.translation import gettext_lazy as _
from polymorphic.managers import PolymorphicManager
from research_vocabs.fields import ConceptField
from shortuuid.django_fields import ShortUUIDField

from fairdm.db import models

from ..abstract import AbstractDate, AbstractDescription, AbstractIdentifier, BasePolymorphicModel
from ..choices import SampleStatus
from ..utils import CORE_PERMISSIONS
from ..vocabularies import FairDMDates, FairDMDescriptions, FairDMIdentifiers, FairDMRoles
from .managers import SampleQuerySet


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
    )
    local_id = models.CharField(
        _("Local ID"),
        max_length=255,
        help_text=_(
            "An alphanumeric identifier used by the creator/s to identify the sample within a specific dataset"
        ),
        null=True,
        blank=True,
    )
    status = ConceptField(
        verbose_name=_("status"),
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
    objects = PolymorphicManager.from_queryset(SampleQuerySet)()

    class Meta:
        verbose_name = _("sample")
        verbose_name_plural = _("samples")
        ordering = ["added"]
        default_related_name = "samples"
        permissions = [
            *CORE_PERMISSIONS,
        ]

    def __str__(self):
        return f"{self.name}"

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
        return SampleRelation.objects.filter(django_models.Q(source=self) | django_models.Q(target=self))

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

    @classproperty
    def type_of(self):
        return Sample

    def get_template_name(self):
        app_name = self._meta.app_label
        model_name = self._meta.model_name
        return [f"{app_name}/{model_name}_card.html", "fairdm/sample_card.html"]


class SampleDescription(AbstractDescription):
    """Free-text description of a Sample with type categorization.

    Supports multiple description types (e.g., abstract, methods, notes)
    as defined by the FairDM Sample description vocabulary.
    """

    VOCABULARY = FairDMDescriptions.from_collection("Sample")
    related = models.ForeignKey("Sample", on_delete=models.CASCADE)


class SampleDate(AbstractDate):
    """Important dates associated with a Sample.

    Tracks various dates (e.g., collected, processed, archived) as defined
    by the FairDM Sample date vocabulary.
    """

    VOCABULARY = FairDMDates.from_collection("Sample")
    related = models.ForeignKey("Sample", on_delete=models.CASCADE)


class SampleIdentifier(AbstractIdentifier):
    """External identifiers for a Sample.

    Links samples to external identifier systems (DOI, ARK, Handle, etc.)
    to support FAIR data principles and cross-referencing.
    """

    VOCABULARY = FairDMIdentifiers()
    related = models.ForeignKey("Sample", on_delete=models.CASCADE)


class SampleRelation(models.Model):
    """Through-model for sample-to-sample relationships.

    Defines typed relationships between samples (e.g., parent/child, derived from).
    This allows tracking of sample hierarchies, splits, and derivations.

    Attributes:
        type: Type of relationship (e.g., 'child_of')
        source: The sample initiating the relationship
        target: The sample being related to

    Note:
        TODO: create a custom manager that gets the related samples based on the type of relation
    """

    RELATION_TYPES = [
        ("child_of", _("child of")),
    ]
    type = models.CharField(max_length=255, verbose_name=_("type"), choices=RELATION_TYPES)
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
