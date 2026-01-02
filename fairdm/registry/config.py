"""
NEW ModelConfiguration class using nested config structure and factory system.

This is the Day 3 redesign that replaces the old ModelConfiguration.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from django.forms import ModelForm
from django.utils.module_loading import import_string
from django_filters import FilterSet
from django_tables2 import Table
from import_export.resources import ModelResource

from fairdm.registry.components import AdminConfig, FiltersConfig, FormConfig, TableConfig
from fairdm.registry.factories import AdminFactory, FilterFactory, FormFactory, TableFactory

if TYPE_CHECKING:
    pass


@dataclass(frozen=True, kw_only=True)
class Authority:
    """Represents the authority that created or maintains a data model.

    Attributes:
        name: The full name of the authority (required)
        short_name: An abbreviated name for the authority
        website: The authority's website URL
    """

    name: str
    """The name of the authority that created this metadata. This is required."""

    short_name: str = ""
    """The short name of the authority that created this metadata."""

    website: str = ""
    """The website of the authority that created this metadata."""


@dataclass(frozen=True, kw_only=True)
class Citation:
    """Represents a citation for a data model.

    Attributes:
        text: The full citation text
        doi: The DOI for the citation
    """

    text: str = ""
    """The citation for the data model."""

    doi: str = ""
    """The DOI for the citation."""


@dataclass
class ModelMetadata:
    """Structured metadata describing a registered model.

    This class contains FAIR-compliant metadata about a Sample or Measurement model,
    including its description, authority, keywords, and citation information.

    Attributes:
        description: A detailed description of the model
        authority: The organization or person responsible for the model
        keywords: List of keywords for discoverability
        repository_url: URL to the source code repository
        citation: How to cite this model
        maintainer: Name of the current maintainer
        maintainer_email: Contact email for the maintainer
    """

    description: str = ""
    authority: Authority | None = None
    keywords: list[str] = field(default_factory=list)
    repository_url: str = ""
    citation: Citation | None = None
    maintainer: str = ""
    maintainer_email: str = ""


class ModelConfiguration:
    """NEW configuration system for Sample/Measurement models using nested config structure.

    This redesigned class uses:
    - Nested config objects (Form, Table, Filters, Admin) for better organization
    - Factory pattern for auto-generation with smart defaults
    - Progressive disclosure (simple fields → detailed config → custom classes)
    - Consistent API across all components

    Usage - Simple (fields only):
        @fairdm.register
        class MySampleConfig(ModelConfiguration):
            model = MySample
            fields = ["name", "location", "collected_at"]
            # Everything auto-generated with smart defaults

    Usage - Intermediate (component configs):
        @fairdm.register
        class MySampleConfig(ModelConfiguration):
            model = MySample
            fields = ["name", "location", "collected_at"]

            # Fine-tune table display
            table = TableConfig(
                fields=["name", "collected_at"],
                orderable=True
            )

            # Configure filters
            filters = FiltersConfig(
                fields=["collected_at", "status"],
                range_fields=["collected_at"]
            )

    Usage - Advanced (custom classes):
        @fairdm.register
        class MySampleConfig(ModelConfiguration):
            model = MySample

            # Full custom control
            form = FormConfig(form_class=MyCustomForm)
            table = TableConfig(table_class=MyCustomTable)
    """

    # Required attributes
    model = None
    metadata: ModelMetadata | None = None

    # Primary field configuration - fallback for all components
    fields: list[str] = []
    exclude: list[str] = []

    # Nested component configurations
    form: FormConfig | None = None
    table: TableConfig | None = None
    filters: FiltersConfig | None = None
    admin: AdminConfig | None = None

    # Legacy component classes (for backwards compatibility)
    form_class = None
    table_class = None
    filterset_class = None
    resource_class = None
    serializer_class = None

    def __init__(self, model=None):
        """Initialize configuration."""
        if model is not None:
            self.model = model

        if self.metadata is None:
            self.metadata = ModelMetadata()

        # Initialize nested configs if not provided
        if self.form is None:
            self.form = FormConfig()
        if self.table is None:
            self.table = TableConfig()
        if self.filters is None:
            self.filters = FiltersConfig()
        if self.admin is None:
            self.admin = AdminConfig()

        # Handle legacy form_class/table_class/filterset_class
        if self.form_class is not None and self.form.form_class is None:
            self.form.form_class = self.form_class
        if self.table_class is not None and self.table.table_class is None:
            self.table.table_class = self.table_class
        if self.filterset_class is not None and self.filters.filterset_class is None:
            self.filters.filterset_class = self.filterset_class

    def _get_class(self, class_or_path: str | type) -> type:
        """Import a class from a string path or return the class directly."""
        if isinstance(class_or_path, str):
            return import_string(class_or_path)
        return class_or_path

    # Display & Metadata Methods

    def get_display_name(self) -> str:
        """Get the display name for this model."""
        if hasattr(self, "display_name") and self.display_name:
            return self.display_name
        if not self.model:
            return "Unknown Model"
        return self.model._meta.verbose_name.title()

    def get_description(self) -> str:
        """Get the description for this model."""
        if self.metadata and self.metadata.description:
            return self.metadata.description
        if not self.model:
            return "No model specified"
        return f"Configuration for {self.model.__name__}"

    def get_slug(self) -> str:
        """Get the URL-safe slug for this model.

        Returns the model's lowercase model name, which is used in URLs and view names.

        Returns:
            str: The model's slug (e.g., 'customsample', 'watermeasurement')
        """
        if not self.model:
            return "unknown"
        return self.model._meta.model_name

    def get_verbose_name(self) -> str:
        """Get the singular verbose name for this model.

        Returns:
            str: The model's verbose name (e.g., 'custom sample', 'water measurement')
        """
        if not self.model:
            return "Unknown Model"
        return str(self.model._meta.verbose_name)

    def get_verbose_name_plural(self) -> str:
        """Get the plural verbose name for this model.

        Returns:
            str: The model's plural verbose name (e.g., 'custom samples', 'water measurements')
        """
        if not self.model:
            return "Unknown Models"
        return str(self.model._meta.verbose_name_plural)

    # Component Generation Methods

    def get_form_class(self) -> type[ModelForm]:
        """Get or auto-generate the ModelForm class using FormFactory."""
        if not self.form:
            self.form = FormConfig()

        factory = FormFactory(
            model=self.model,
            config=self.form,
            parent_fields=self.fields,
        )
        return factory.generate()

    def get_table_class(self) -> type[Table]:
        """Get or auto-generate the Table class using TableFactory."""
        if not self.table:
            self.table = TableConfig()

        factory = TableFactory(
            model=self.model,
            config=self.table,
            parent_fields=self.fields,
        )
        return factory.generate()

    def get_filterset_class(self) -> type[FilterSet]:
        """Get or auto-generate the FilterSet class using FilterFactory."""
        if not self.filters:
            self.filters = FiltersConfig()

        factory = FilterFactory(
            model=self.model,
            config=self.filters,
            parent_fields=self.fields,
        )
        return factory.generate()

    def get_admin_class(self):
        """Get or auto-generate the ModelAdmin class using AdminFactory."""

        if not self.admin:
            self.admin = AdminConfig()

        factory = AdminFactory(
            model=self.model,
            config=self.admin,
            parent_fields=self.fields,
        )
        admin_class = factory.generate()
        return admin_class

    def get_resource_class(self) -> type[ModelResource]:
        """Get or auto-generate the import/export Resource class.

        NOTE: This still uses old factory system - will be updated in future sprint.
        """
        if self.resource_class is not None:
            return self._get_class(self.resource_class)

        # Use old factory for now - Resource factory is not in Day 3 scope
        from fairdm.utils import factories

        if self.fields:
            return factories.modelresource_factory(self.model, fields=self.fields)
        else:
            exclude = [
                "polymorphic_ctype",
                "sample_ptr",
                "image",
                "keywords",
                "created",
                "modified",
                "options",
                "keywords",
            ]
            return factories.modelresource_factory(self.model, exclude=exclude)

    def get_serializer_class(self) -> type | None:
        """Get the serializer class for the model, if DRF is available.

        NOTE: This still uses old system - DRF factory is future work.
        """
        if self.serializer_class is not None:
            return self._get_class(self.serializer_class)

        # DRF support is future work
        return None

    # Convenience/Backwards Compatibility Methods

    def has_custom_form(self) -> bool:
        """Check if a custom form class is provided."""
        return self.form is not None and self.form.form_class is not None

    def has_custom_filterset(self) -> bool:
        """Check if a custom filterset class is provided."""
        return self.filters is not None and self.filters.filterset_class is not None

    def has_custom_table(self) -> bool:
        """Check if a custom table class is provided."""
        return self.table is not None and self.table.table_class is not None

    def has_custom_admin(self) -> bool:
        """Check if a custom admin class is provided."""
        return self.admin is not None and self.admin.admin_class is not None

    def has_custom_resource(self) -> bool:
        """Check if a custom resource class is provided."""
        return self.resource_class is not None

    def has_custom_serializer(self) -> bool:
        """Check if a custom serializer class is provided."""
        return self.serializer_class is not None


class SampleConfig(ModelConfiguration):
    """Base configuration class for Sample subclasses.

    Inherits all functionality from ModelConfiguration. Use this when registering
    Sample models for semantic clarity.
    """

    pass


class MeasurementConfig(ModelConfiguration):
    """Base configuration class for Measurement subclasses.

    Inherits all functionality from ModelConfiguration. Use this when registering
    Measurement models for semantic clarity.
    """

    pass


# Export the main classes
__all__ = [
    "Authority",
    "Citation",
    "MeasurementConfig",
    "ModelConfiguration",
    "ModelMetadata",
    "SampleConfig",
]
