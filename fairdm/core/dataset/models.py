from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from licensing.fields import LicenseField
from shortuuid.django_fields import ShortUUIDField

from fairdm.db import models
from fairdm.db.models import QuerySet
from fairdm.utils.choices import Visibility

from ..abstract import AbstractDate, AbstractDescription, AbstractIdentifier, BaseModel
from ..utils import CORE_PERMISSIONS
from ..vocabularies import (
    FairDMDates,
    FairDMDescriptions,
    FairDMIdentifiers,
    FairDMRoles,
)


def get_default_license_pk():
    """Return the pk of the portal's configured default licence (FR-007).

    Reads ``settings.FAIRDM_DEFAULT_LICENSE`` at call time - not at import
    time - so ``override_settings`` and per-portal configuration are both
    honoured. Falls back to "CC BY 4.0" where a portal states none. Returns
    ``None`` (leaving the dataset unlicensed) if the portal hasn't seeded
    its licences yet - the seeding step is FR-007a, a separate concern.
    """
    from licensing.models import License

    name = getattr(settings, "FAIRDM_DEFAULT_LICENSE", "CC BY 4.0")
    return License.objects.filter(name=name).values_list("pk", flat=True).first()

# DataCite RelationType Vocabulary for Dataset-Literature Relationships
# Source: DataCite Metadata Schema 4.4
# https://schema.datacite.org/meta/kernel-4.4/
DATACITE_RELATIONSHIP_TYPES = [
    ("IsCitedBy", _("Is Cited By")),
    ("Cites", _("Cites")),
    ("IsSupplementTo", _("Is Supplement To")),
    ("IsSupplementedBy", _("Is Supplemented By")),
    ("IsContinuedBy", _("Is Continued By")),
    ("Continues", _("Continues")),
    ("IsDescribedBy", _("Is Described By")),
    ("Describes", _("Describes")),
    ("HasMetadata", _("Has Metadata")),
    ("IsMetadataFor", _("Is Metadata For")),
    ("HasVersion", _("Has Version")),
    ("IsVersionOf", _("Is Version Of")),
    ("IsNewVersionOf", _("Is New Version Of")),
    ("IsPreviousVersionOf", _("Is Previous Version Of")),
    ("IsPartOf", _("Is Part Of")),
    ("HasPart", _("Has Part")),
    ("IsPublishedIn", _("Is Published In")),
    ("IsReferencedBy", _("Is Referenced By")),
    ("References", _("References")),
    ("IsDocumentedBy", _("Is Documented By")),
    ("Documents", _("Documents")),
    ("IsCompiledBy", _("Is Compiled By")),
    ("Compiles", _("Compiles")),
    ("IsVariantFormOf", _("Is Variant Form Of")),
    ("IsOriginalFormOf", _("Is Original Form Of")),
    ("IsIdenticalTo", _("Is Identical To")),
    ("IsReviewedBy", _("Is Reviewed By")),
    ("Reviews", _("Reviews")),
    ("IsDerivedFrom", _("Is Derived From")),
    ("IsSourceOf", _("Is Source Of")),
    ("IsRequiredBy", _("Is Required By")),
    ("Requires", _("Requires")),
    ("Obsoletes", _("Obsoletes")),
    ("IsObsoletedBy", _("Is Obsoleted By")),
]


class DatasetLiteratureRelation(models.Model):
    """
    Intermediate model for Dataset-to-LiteratureItem relationships.

    Specifies the type of relationship using DataCite RelationType vocabulary.
    """

    dataset = models.ForeignKey(
        "Dataset",
        on_delete=models.CASCADE,
        related_name="literature_relations",
        verbose_name=_("dataset"),
    )
    literature_item = models.ForeignKey(
        "literature.LiteratureItem",
        on_delete=models.CASCADE,
        related_name="dataset_relations",
        verbose_name=_("literature item"),
    )
    relationship_type = models.CharField(
        _("relationship type"),
        max_length=50,
        choices=DATACITE_RELATIONSHIP_TYPES,
        help_text=_(
            "DataCite relationship type (e.g., IsCitedBy, Cites, IsDocumentedBy)"
        ),
    )

    class Meta:
        verbose_name = _("dataset literature relation")
        verbose_name_plural = _("dataset literature relations")
        unique_together = [["dataset", "literature_item", "relationship_type"]]
        indexes = [
            models.Index(fields=["relationship_type"]),
        ]

    def __str__(self):
        return f"{self.dataset} {self.get_relationship_type_display()} {self.literature_item}"


class DatasetQuerySet(QuerySet):
    """Custom QuerySet for the Dataset model.

    Offers query optimisation helpers (`with_related`, `with_contributors`,
    `with_metadata`) plus the bounded, all-related-records load FR-030
    requires. Deliberately does **not** offer any method that claims to
    widen an already-narrowed query - `Dataset.objects` (privacy-first,
    see `DatasetManager`) already excludes PRIVATE datasets by the time a
    caller holds a queryset, and no method built on top of it can correctly
    add them back (R1). `Dataset.all_objects` is the separately named,
    unfiltered route FR-019 requires.
    """

    def with_related(self) -> "DatasetQuerySet":
        """Prefetch project and contributors (bounded, regardless of result count)."""
        return self.prefetch_related(
            "project",
            "contributors",
        )

    def with_contributors(self) -> "DatasetQuerySet":
        """Prefetch only contributors - lighter than `with_related()`."""
        return self.prefetch_related("contributors")

    def with_metadata(self) -> "DatasetQuerySet":
        """Prefetch descriptions, dates, identifiers, contributions and
        keywords in a bounded number of queries (FR-030), so a caller
        assembling a full record does not issue one query per related
        record.
        """
        return self.prefetch_related(
            "descriptions",
            "dates",
            "identifiers",
            "contributors",
            "keywords",
        )


class DatasetManager(models.Manager.from_queryset(DatasetQuerySet)):
    """The default manager for `Dataset`. Excludes PRIVATE datasets (FR-019).

    Built `from_queryset(DatasetQuerySet)` so `Dataset.objects.with_related()`
    and friends keep working on the privacy-first default manager, not only
    on the explicit `all_objects` route.

    Declared first on `Dataset` so Django treats it as `_default_manager`,
    which is what portal code, reverse relations (`project.datasets`) and
    `ModelAdmin.get_queryset()` consult unless told otherwise -
    `DatasetAdmin.get_queryset()` is overridden explicitly to use
    `all_objects`, because the administrative interface is where a portal
    is repaired and needs to see everything (FR-019a).

    Forward relations and the deletion collector go through
    `Model._base_manager` instead, which `fairdm.db.models.PrefetchBase`
    pins to `prefetch_manager` - itself unfiltered - so following a
    relation to a private dataset, or cascading a deletion to one, is
    unaffected by this manager (R1).
    """

    def get_queryset(self) -> DatasetQuerySet:
        return super().get_queryset().exclude(visibility=Visibility.PRIVATE)


class Dataset(BaseModel):
    """A dataset is the unit a portal cites and distributes.

    It sits beneath an optional project, and samples and measurements hang
    beneath it (`has_data` reports whether any do). A dataset is private
    until its visibility is set otherwise (FR-004): the default manager,
    `objects`, excludes PRIVATE datasets, and `all_objects` is the
    separately named, explicit route to every dataset regardless of
    visibility (R1). Deleting its project deletes it too - `project` is
    `on_delete=CASCADE`.

    A dataset with no licence chosen gets the portal's configured default
    (`get_default_license_pk`, FR-007) the moment it is created.

    Related records:

    - `DatasetDescription` - typed prose, one per type (US-1)
    - `DatasetDate` - typed dates, one per type (US-2)
    - `DatasetIdentifier` - typed external identifiers, globally unique (US-3)
    - `DatasetLiteratureRelation` - DataCite-typed links to literature, plus
      the single `reference` (the dataset's own data publication)
    - `contributors` - `Contribution` records carrying one or more roles
      from `CONTRIBUTOR_ROLES`, DataCite-expressible (FR-018)
    """

    CONTRIBUTOR_ROLES = FairDMRoles.from_collection("Dataset")
    DATE_TYPES = FairDMDates.from_collection("Dataset")
    DESCRIPTION_TYPES = FairDMDescriptions.from_collection("Dataset")
    IDENTIFIER_TYPES = FairDMIdentifiers().choices
    VISIBILITY_CHOICES = Visibility
    DEFAULT_ROLES = ["ProjectMember"]

    # `objects` is declared first, so Django takes it as `_default_manager`
    # (see `DatasetManager`). `all_objects` is the explicit, unfiltered
    # route FR-019 requires.
    objects = DatasetManager()
    all_objects = DatasetQuerySet.as_manager()  # type: ignore[assignment,misc]

    uuid = ShortUUIDField(
        editable=False,
        unique=True,
        prefix="d",
        verbose_name=_("UUID"),
        help_text=_(
            "A short, unique identifier generated automatically when the "
            "dataset is created. Cannot be edited afterwards."
        ),
    )

    visibility = models.IntegerField(
        _("visibility"),
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_CHOICES.PRIVATE,
        db_index=True,
        help_text=_("Visibility within the application."),
    )

    # GENERIC RELATIONS
    contributors = GenericRelation(
        "contributors.Contribution", related_query_name="dataset"
    )

    # RELATIONS
    project = models.ForeignKey(
        "project.Project",
        verbose_name=_("project"),
        help_text=_("The project associated with the dataset."),
        related_name="datasets",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    reference = models.OneToOneField(
        "literature.LiteratureItem",
        verbose_name=_("Data reference"),
        help_text=_("The data publication associated with this dataset."),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    related_literature: models.ManyToManyField = models.ManyToManyField(
        "literature.LiteratureItem",
        help_text=_("Any literature that is related to this dataset."),
        through="DatasetLiteratureRelation",
        related_name="related_datasets",
        related_query_name="related_dataset",
        blank=True,
    )
    license = LicenseField(
        null=True,
        blank=True,
        default=get_default_license_pk,
        verbose_name=_("license"),
        help_text=_(
            "The license under which the dataset's data is published. "
            "Defaults to the portal's configured license when none is chosen."
        ),
    )

    _metadata = {
        "title": "name",
        "description": "get_meta_description",
        "type": "research.dataset",
    }

    class Meta:
        verbose_name = _("dataset")
        verbose_name_plural = _("datasets")
        default_related_name = "datasets"
        ordering = ["-modified"]
        permissions = [
            *CORE_PERMISSIONS,
            ("import_data", "Can import data into dataset"),
            ("change_dataset_metadata", "Can edit dataset metadata"),
            ("change_dataset_settings", "Can change dataset settings"),
        ]

    @cached_property
    def has_data(self):
        """Whether the dataset holds any samples or measurements, checked
        in a single query (FR-008)."""
        sample_pks = self.samples.values("pk")
        measurement_pks = self.measurements.values("pk")
        return sample_pks.union(measurement_pks).exists()

    @cached_property
    def bbox(self):
        from fairdm.contrib.location.utils import bbox_for_dataset

        return bbox_for_dataset(self)


class DatasetDescription(AbstractDescription):
    """
    Typed descriptions for datasets using controlled FAIR vocabulary.

    Provides property aliases for API compatibility:
    - description_type → type
    - description → value
    """

    VOCABULARY = FairDMDescriptions.from_collection("Dataset")
    related = models.ForeignKey("Dataset", on_delete=models.CASCADE)

    class Meta(AbstractDescription.Meta):
        indexes = [
            models.Index(fields=["type"], name="dataset_desc_type_idx"),
        ]

    @property
    def description_type(self):
        """Alias for type field (API compatibility)."""
        return self.type

    @description_type.setter
    def description_type(self, value):
        """Setter for description_type alias."""
        self.type = value

    @property
    def description(self):
        """Alias for value field (API compatibility)."""
        return self.value

    @description.setter
    def description(self, value):
        """Setter for description alias."""
        self.value = value


class DatasetDate(AbstractDate):
    """
    Typed dates for datasets using controlled FAIR vocabulary.

    Provides property aliases for API compatibility:
    - date_type → type
    - date → value
    """

    VOCABULARY = FairDMDates.from_collection("Dataset")
    related = models.ForeignKey("Dataset", on_delete=models.CASCADE)

    class Meta(AbstractDate.Meta):
        indexes = [
            models.Index(fields=["type"], name="dataset_date_type_idx"),
        ]

    @property
    def date_type(self):
        """Alias for type field (API compatibility)."""
        return self.type

    @date_type.setter
    def date_type(self, value):
        """Setter for date_type alias."""
        self.type = value

    @property
    def date(self):
        """Alias for value field (API compatibility)."""
        return self.value

    @date.setter
    def date(self, value):
        """Setter for date alias."""
        self.value = value


class DatasetIdentifier(AbstractIdentifier):
    """
    Typed identifiers for datasets using controlled FAIR vocabulary.

    Provides property aliases for API compatibility:
    - identifier_type → type
    - identifier → value

    Supports DOI via identifier_type='DOI'.
    """

    VOCABULARY = FairDMIdentifiers()
    related = models.ForeignKey("Dataset", on_delete=models.CASCADE)

    @property
    def identifier_type(self):
        """Alias for type field (API compatibility)."""
        return self.type

    @identifier_type.setter
    def identifier_type(self, value):
        """Setter for identifier_type alias."""
        self.type = value

    @property
    def identifier(self):
        """Alias for value field (API compatibility)."""
        return self.value

    @identifier.setter
    def identifier(self, value):
        """Setter for identifier alias."""
        self.value = value
