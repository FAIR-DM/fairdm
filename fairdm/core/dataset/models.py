from typing import TYPE_CHECKING

from django.contrib.contenttypes.fields import GenericRelation
from django.db.models import QuerySet
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from licensing.fields import LicenseField
from shortuuid.django_fields import ShortUUIDField

from fairdm.contrib.location.utils import bbox_for_dataset
from fairdm.db import models
from fairdm.utils.choices import Visibility

from ..abstract import AbstractDate, AbstractDescription, AbstractIdentifier, BaseModel
from ..utils import CORE_PERMISSIONS
from ..vocabularies import FairDMDates, FairDMDescriptions, FairDMIdentifiers, FairDMRoles

if TYPE_CHECKING:
    from fairdm.core.dataset.models import Dataset


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
        help_text=_("DataCite relationship type (e.g., IsCitedBy, Cites, IsDocumentedBy)"),
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


class DatasetQuerySet(models.QuerySet):
    """
    Custom QuerySet for Dataset model with privacy-first defaults and query optimization.

    **Privacy-First Design:**

    By default, all queries EXCLUDE datasets with visibility=PRIVATE. This ensures
    that private datasets are not accidentally exposed through list views, APIs, or
    public interfaces. To access private datasets, you must explicitly call the
    `with_private()` method.

    **Query Optimization:**

    This QuerySet provides methods to reduce N+1 query problems by prefetching
    related data. Using these methods can reduce database queries by 80%+ when
    accessing related objects.

    **Methods:**

    - **with_private()**: Include PRIVATE datasets (explicit opt-in)
    - **with_related()**: Prefetch project and contributors (max 3 queries)
    - **with_contributors()**: Prefetch only contributors (max 2 queries)
    - **get_visible()**: Return only PUBLIC datasets (legacy method)

    **Method Chaining:**

    All methods return QuerySet instances and can be chained in any order:
    ```python
    Dataset.objects.with_private().filter(project=x).with_related()
    ```

    **Performance Expectations:**

    Without optimization (naive):
    ```python
    datasets = Dataset.objects.all()
    for ds in datasets:
        print(ds.project.name)  # N+1 queries!
        print(ds.contributors.count())  # N+1 queries!
    ```
    - 10 datasets = 21 queries (1 + 10 + 10)

    With optimization:
    ```python
    datasets = Dataset.objects.with_related()
    for ds in datasets:
        print(ds.project.name)  # No additional queries
        print(ds.contributors.count())  # No additional queries
    ```
    - 10 datasets = 3 queries (1 + 1 + 1) - **86% reduction**

    **Usage Examples:**

    ```python
    # Default behavior - excludes PRIVATE datasets
    public_datasets = Dataset.objects.all()  # Only PUBLIC and INTERNAL

    # Explicit private access
    all_datasets = Dataset.objects.with_private()  # Includes PRIVATE

    # Optimized queries for list views
    datasets = Dataset.objects.with_related()  # Prefetch everything

    # Optimized queries for contributor-only access
    datasets = Dataset.objects.with_contributors()  # Lighter than with_related

    # Chaining methods
    datasets = (
        Dataset.objects.with_private()  # Include private
        .filter(project=project)  # Filter by project
        .with_related()  # Optimize queries
    )
    ```

    **Integration with Views:**

    ```python
    class DatasetListView(ListView):
        def get_queryset(self):
            qs = Dataset.objects.all()  # Privacy-first default

            # If user has permission, show private datasets
            if self.request.user.has_perm("dataset.view_private"):
                qs = qs.with_private()

            # Optimize for list rendering
            return qs.with_related()
    ```

    See Also:
        - tests/unit/core/dataset/test_queryset.py: Comprehensive test suite
        - fairdm_demo/models.py: Usage examples and patterns
    """

    def with_private(self) -> QuerySet["Dataset"]:
        """
        Include PRIVATE datasets in the queryset (explicit opt-in).

        By default, the Dataset manager excludes PRIVATE datasets. Call this method
        to include them in your query results.

        This method is required to access private datasets, ensuring that sensitive
        data is not accidentally exposed through default queries.

        Returns:
            QuerySet including PUBLIC, INTERNAL, and PRIVATE datasets

        Examples:
            >>> # Get all datasets including private ones
            >>> Dataset.objects.with_private()
            <QuerySet [<Dataset: Public>, <Dataset: Private>, ...]>

            >>> # Filter private datasets by project
            >>> Dataset.objects.with_private().filter(project=my_project)
            <QuerySet [<Dataset: Private Project Dataset>, ...]>

            >>> # Chain with optimization methods
            >>> Dataset.objects.with_private().with_related()
            <QuerySet [...]>  # Optimized queries, includes private
        """
        # Use the model's _base_manager to get unfiltered queryset
        # This bypasses the privacy-first exclude() in DatasetManager.get_queryset()
        return self.model._base_manager.all()

    def get_visible(self) -> QuerySet["Dataset"]:
        """
        Return only datasets with PUBLIC visibility (legacy method).

        Note: The default manager already excludes PRIVATE datasets. This method
        further restricts to only PUBLIC datasets, excluding INTERNAL ones.

        For most use cases, the default behavior (PUBLIC + INTERNAL) is appropriate.
        Use this method only when you specifically need PUBLIC-only datasets.

        Returns:
            QuerySet containing only PUBLIC datasets

        Examples:
            >>> # Get only public datasets
            >>> Dataset.objects.get_visible()
            <QuerySet [<Dataset: Public 1>, <Dataset: Public 2>]>
        """
        return self.filter(visibility=Visibility.PUBLIC)

    def with_related(self) -> QuerySet["Dataset"]:
        """
        Prefetch project and contributors for optimized access (max 3 queries).

        This method reduces N+1 query problems by prefetching related objects.
        Use this in list views where you'll be accessing both project and
        contributor data for each dataset.

        Expected Query Count:
        - 1 query: Main dataset query
        - 1 query: Prefetch projects
        - 1 query: Prefetch contributors
        - Total: 3 queries (regardless of result count)

        Performance Impact:
        - 10 datasets without optimization: 21 queries
        - 10 datasets with optimization: 3 queries
        - Reduction: 86%

        Returns:
            QuerySet with prefetched project and contributors

        Examples:
            >>> # List view with project and contributors
            >>> datasets = Dataset.objects.with_related()
            >>> for ds in datasets:
            ...     print(f"{ds.name} in {ds.project.name}")
            ...     print(f"Contributors: {ds.contributors.count()}")
            # No additional queries above!

            >>> # Chain with filters
            >>> Dataset.objects.filter(visibility=Visibility.PUBLIC).with_related()
            <QuerySet [...]>  # Filtered and optimized
        """
        return self.prefetch_related(
            "project",
            "contributors",
        )

    def with_contributors(self) -> QuerySet["Dataset"]:
        """
        Prefetch only contributors for optimized access (max 2 queries).

        This method is lighter than with_related() - use it when you only need
        contributor data and not project information. This saves one database query.

        Expected Query Count:
        - 1 query: Main dataset query
        - 1 query: Prefetch contributors
        - Total: 2 queries (regardless of result count)

        Returns:
            QuerySet with prefetched contributors only

        Examples:
            >>> # List view with only contributors
            >>> datasets = Dataset.objects.with_contributors()
            >>> for ds in datasets:
            ...     print(f"Contributors: {', '.join(c.name for c in ds.contributors.all())}")
            # No additional queries above!

            >>> # Chain with private access
            >>> Dataset.objects.with_private().with_contributors()
            <QuerySet [...]>  # Includes private, optimized for contributors
        """
        return self.prefetch_related("contributors")


class DatasetManager(models.Manager):
    """
    Custom Manager for Dataset model implementing privacy-first defaults.

    This manager ensures that PRIVATE datasets are excluded from default queries,
    requiring explicit opt-in via the with_private() method to access them.

    **Privacy-First Behavior:**

    ```python
    Dataset.objects.all()  # Excludes PRIVATE datasets
    Dataset.objects.with_private()  # Includes PRIVATE datasets
    ```

    This design prevents accidental exposure of sensitive data in:
    - List views
    - API endpoints
    - Search results
    - Public interfaces

    **Implementation:**

    The manager overrides get_queryset() to exclude PRIVATE datasets by default.
    All queryset methods (filter, exclude, get, etc.) inherit this behavior.

    See Also:
        DatasetQuerySet: QuerySet methods and optimization
    """

    def get_queryset(self) -> DatasetQuerySet:
        """
        Return QuerySet excluding PRIVATE datasets by default.

        Override this method to change the privacy-first behavior if needed.

        Returns:
            DatasetQuerySet excluding datasets with visibility=PRIVATE
        """
        return DatasetQuerySet(self.model, using=self._db).exclude(visibility=Visibility.PRIVATE)


class Dataset(BaseModel):
    """A dataset is a collection of samples, measurements and associated metadata.

    The Dataset model is the second level in the FairDM schema hierarchy. All geographic
    sites, samples, and measurements MUST relate back to a dataset. This model enforces
    FAIR (Findable, Accessible, Interoperable, Reusable) data principles through
    comprehensive metadata fields and validation.

    **FAIR Metadata Support:**

    - **Findable**: UUID, DOI support via DatasetIdentifier, rich descriptions,
      keywords, and comprehensive search capabilities
    - **Accessible**: Visibility controls (PUBLIC/PRIVATE), license information,
      contributor attribution
    - **Interoperable**: Standard vocabularies for dates/descriptions/identifiers,
      DataCite relationship types for literature
    - **Reusable**: License field (default CC BY 4.0), clear contributor roles,
      temporal and provenance metadata

    **Visibility Controls:**

    The visibility field controls dataset access within the application:

    - **PRIVATE** (default): Only visible to project members and authorized users
    - **PUBLIC**: Visible to all authenticated users

    Visibility can only be changed individually (no bulk operations) to prevent
    accidental exposure of sensitive research data.

    **DOI Support:**

    Digital Object Identifiers (DOIs) are supported through the DatasetIdentifier
    model, not the reference field. To assign a DOI:

    ```python
    dataset.identifiers.create(type="DOI", value="10.1000/xyz123")
    ```

    The reference field is reserved for the primary data publication (LiteratureItem),
    while related_literature tracks all related citations with DataCite relationship
    types.

    **UUID Collision Handling:**

    The uuid field uses ShortUUID with a unique database constraint. In the extremely
    rare case of a collision (probability < 1 in 10^9), the database will raise an
    IntegrityError and the application should retry with a new UUID. No explicit
    collision recovery mechanism is implemented due to the negligible probability.

    **Orphaned Datasets:**

    Datasets can exist without a project (project=null) in specific scenarios:

    - Migrated legacy data without project structure
    - Datasets awaiting project assignment
    - Test/sandbox datasets

    The project field uses PROTECT to prevent accidental deletion of projects that
    have associated datasets. Portal administrators must explicitly reassign or
    delete datasets before removing a project.

    **Empty Dataset Detection:**

    The `has_data` property uses an efficient EXISTS query to check for samples or
    measurements. Empty datasets (has_data=False) may indicate incomplete data
    entry or abandoned work.

    **Image Guidelines:**

    Dataset images are displayed in Bootstrap cards, detail pages, and social media
    previews. For optimal display across all contexts:

    - **Recommended aspect ratio**: 16:9 (landscape)
    - **Recommended upload size**: 1920x1080px (Full HD)
    - **Minimum size**: 800x450px
    - **Maximum file size**: 5MB
    - **Formats**: JPEG, PNG, WebP

    The 16:9 aspect ratio was chosen because:
    1. Works well in Bootstrap card layouts
    2. Matches Open Graph standard (1.91:1) for social media
    3. Maintains proportions across all device breakpoints
    4. Suitable for charts, maps, equipment photos, and field images

    Images are automatically resized using easy-thumbnails for responsive display.

    **Role-Based Permissions:**

    FairDM uses a role-based permission system that maps contributor roles to
    Django permissions. The Dataset.CONTRIBUTOR_ROLES vocabulary defines available
    roles, which are automatically mapped to Django's permission system:

    **Permission Mapping**:

    | Role | View | Add | Change | Delete | Description |
    |------|------|-----|--------|--------|-------------|
    | **Viewer** | ✓ | ✗ | ✗ | ✗ | Read-only access to dataset |
    | **Editor** | ✓ | ✓ | ✓ | ✗ | Can view and edit dataset |
    | **Manager** | ✓ | ✓ | ✓ | ✓ | Full control over dataset |

    **Usage in Views**:

    ```python
    # Check if user can view dataset
    if user.has_perm("dataset.view_dataset", dataset):
        # Show dataset
        pass

    # Check if user can edit dataset
    if user.has_perm("dataset.change_dataset", dataset):
        # Show edit form
        pass

    # Check if user can delete dataset
    if user.has_perm("dataset.delete_dataset", dataset):
        # Show delete button
        pass
    ```

    **Integration with django-guardian**:

    Object-level permissions are managed through django-guardian. When a user is
    added as a contributor with a specific role, the corresponding Django
    permissions are automatically assigned:

    ```python
    from guardian.shortcuts import assign_perm
    from fairdm.core.dataset.models import Dataset

    # Assign Editor role (view + change permissions)
    assign_perm("view_dataset", user, dataset)
    assign_perm("change_dataset", user, dataset)

    # Check permissions
    user.has_perm("view_dataset", dataset)  # True
    user.has_perm("delete_dataset", dataset)  # False (Editor role)
    ```

    **See Also**:

    - Developer Guide > Permissions > Object-Level Access
    - specs/006-core-datasets/research/image-aspect-ratios.md

    **Metadata Models:**

    - DatasetDescription: Abstract, Methods, Technical Info, etc. (one per type)
    - DatasetDate: Created, Submitted, Available, etc. (one per type)
    - DatasetIdentifier: DOI, ARK, Handle, etc. (must be unique)
    - DatasetLiteratureRelation: DataCite relationship types (IsCitedBy, Cites,
      IsDocumentedBy, etc.)

    See Also:
        - docs/portal-development/models/dataset.md
        - docs/user-guide/datasets/creating-datasets.md
        - specs/006-core-datasets/data-model.md
    """

    CONTRIBUTOR_ROLES = FairDMRoles.from_collection("Dataset")
    DATE_TYPES = FairDMDates.from_collection("Dataset")
    DESCRIPTION_TYPES = FairDMDescriptions.from_collection("Dataset")
    IDENTIFIER_TYPES = FairDMIdentifiers().choices
    VISIBILITY_CHOICES = Visibility
    DEFAULT_ROLES = ["ProjectMember"]
    # DEFAULT_ROLES = FairDMRoles.from_collection("Dataset").get_concept("ProjectMember")

    # Role-to-permission mapping for object-level access control
    # Maps FairDM roles to Django permissions (view/add/change/delete)
    ROLE_PERMISSIONS = {
        "Viewer": ["view_dataset"],
        "Editor": ["view_dataset", "add_dataset", "change_dataset"],
        "Manager": ["view_dataset", "add_dataset", "change_dataset", "delete_dataset"],
    }

    # Base manager returns ALL datasets (no filtering)
    _base_manager = DatasetQuerySet.as_manager()
    # Default manager excludes PRIVATE datasets (privacy-first)
    objects = DatasetManager()

    # Override image field from BaseModel to add aspect ratio guidance
    image = models.ImageField(
        verbose_name=_("image"),
        blank=True,
        null=True,
        upload_to="datasets/",
        help_text=_(
            "Dataset image for card displays and social media previews. "
            "Recommended: 1920x1080px (16:9 aspect ratio). "
            "Minimum: 800x450px. Maximum file size: 5MB."
        ),
    )

    # Override name field from BaseModel to extend max_length
    name = models.CharField(
        _("name"),
        max_length=300,
        help_text=_("Dataset name (required, max 300 characters)"),
    )

    uuid = ShortUUIDField(
        editable=False,
        unique=True,
        prefix="d",
        verbose_name="UUID",
    )

    visibility = models.IntegerField(
        _("visibility"),
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_CHOICES.PRIVATE,
        help_text=_("Visibility within the application."),
    )

    # published = models.BooleanField(
    #     _("published"),
    #     help_text=_("Determines whether data from this dataset can be accessed by the public."),
    #     default=False,
    # )

    # GENERIC RELATIONS
    contributors = GenericRelation("contributors.Contribution", related_query_name="dataset")

    # RELATIONS
    project = models.ForeignKey(
        "project.Project",
        verbose_name=_("project"),
        help_text=_(
            "The project associated with the dataset. "
            "Uses PROTECT to prevent accidental deletion of projects with datasets. "
            "Orphaned datasets (project=null) are permitted but not encouraged."
        ),
        related_name="datasets",
        on_delete=models.PROTECT,
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
    related_literature = models.ManyToManyField(
        "literature.LiteratureItem",
        help_text=_("Any literature that is related to this dataset."),
        through="DatasetLiteratureRelation",
        related_name="related_datasets",
        related_query_name="related_dataset",
        blank=True,
    )
    license = LicenseField(null=True, blank=True)

    _metadata = {
        "title": "name",
        "description": "get_meta_description",
        "type": "research.dataset",
    }

    class Meta:
        verbose_name = _("dataset")
        verbose_name_plural = _("datasets")
        default_related_name = "datasets"
        ordering = ["modified"]
        permissions = [
            *CORE_PERMISSIONS,
            ("import_data", "Can import data into dataset"),
        ]

    @cached_property
    def has_data(self):
        """Check if the dataset has any samples or measurements."""
        return self.samples.exists() or self.measurements.exists()

    @cached_property
    def bbox(self):
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
