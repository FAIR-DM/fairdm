"""
ModelConfiguration class using property-based API with @cached_property.

This implements the FairDM Registry System specification with:
- Parent `fields` attribute + optional component-specific field overrides
- Custom class overrides for full control
- Lazy component generation via @cached_property
- Three-tier field resolution algorithm
"""

from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING, cast

from django.forms import ModelForm
from django.utils.module_loading import import_string
from django_filters import FilterSet
from django_tables2 import Table
from import_export.resources import ModelResource

from fairdm.registry.exceptions import ConfigurationError

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin
    from django.db import models
    from rest_framework.serializers import ModelSerializer


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


@dataclass
class ModelConfiguration:
    """Configuration for auto-generating components from Sample/Measurement models.

    This class follows a three-tier configuration pattern:
    1. Parent fields (simplest): `fields = ['name', 'location']`
    2. Component-specific fields: `table_fields = ['name', 'location']`
    3. Custom classes (full control): `table_class = MyCustomTable`

    Examples:
        Basic registration with shared fields::

            @register
            class RockSampleConfig(ModelConfiguration):
                model = RockSample
                fields = ["name", "location", "date_collected"]
                # All components auto-generate from these fields

        Component-specific field lists::

            @register
            class RockSampleConfig(ModelConfiguration):
                model = RockSample
                fields = ["name", "location"]  # Default for all
                table_fields = ["name", "location", "contributor"]  # Table extra column
                form_fields = ["name", "description", "location"]  # Form includes description

        Custom class overrides::

            @register
            class RockSampleConfig(ModelConfiguration):
                model = RockSample
                table_class = RockSampleTable  # Custom table with special columns
                form_class = RockSampleForm  # Custom form with validation logic
    """

    # Required Attributes
    model: type["models.Model"] | None = None
    """Django model class (Sample or Measurement subclass). Required."""

    metadata: "ModelMetadata | None" = None
    """Structured FAIR-compliant metadata about the model."""

    # Parent Field Configuration (Level 1)
    fields: list[str] = field(default_factory=list)
    """Parent field list inherited by all components when component-specific fields not specified.

    Supports:
    - Simple field names: ['name', 'location']
    - Related field paths: ['project__title', 'contributor__name']
    - Empty list = use smart defaults (all user-defined fields, excluding auto-generated)
    """

    exclude: list[str] = field(default_factory=list)
    """Fields to exclude from all components.

    Always excluded by default:
    - 'id', 'polymorphic_ctype', 'polymorphic_ctype_id'
    - Fields ending with '_ptr' or '_ptr_id' (multi-table inheritance)
    - Fields with auto_now=True or auto_now_add=True
    - Fields with editable=False
    """

    # Component-Specific Field Lists (Level 2)
    table_fields: list[str] | None = None
    """Fields for django-tables2 Table columns. Overrides parent `fields` for tables only."""

    form_fields: list[str] | None = None
    """Fields for Django ModelForm inputs. Overrides parent `fields` for forms only."""

    filterset_fields: list[str] | None = None
    """Fields for django-filter FilterSet filters. Overrides parent `fields` for filters only."""

    serializer_fields: list[str] | None = None
    """Fields for DRF ModelSerializer. Overrides parent `fields` for serializers only."""

    resource_fields: list[str] | None = None
    """Fields for import_export Resource. Overrides parent `fields` for import/export only."""

    admin_list_display: list[str] | None = None
    """Fields for Django Admin list_display. Overrides parent `fields` for admin list only."""

    # Custom Class Overrides (Level 3)
    form_class: type[ModelForm] | None = None
    """Custom ModelForm class. Completely replaces auto-generation (ignores all field lists)."""

    table_class: type[Table] | None = None
    """Custom django-tables2 Table class. Completely replaces auto-generation."""

    filterset_class: type[FilterSet] | None = None
    """Custom django-filter FilterSet class. Completely replaces auto-generation."""

    serializer_class: type["ModelSerializer"] | None = None
    """Custom DRF ModelSerializer class. Completely replaces auto-generation."""

    resource_class: type[ModelResource] | None = None
    """Custom import_export Resource class. Completely replaces auto-generation."""

    admin_class: type["ModelAdmin"] | str | None = None
    """Custom Django Admin ModelAdmin class or dotted import path. Completely replaces auto-generation."""

    # Metadata
    display_name: str = ""
    """Human-readable name for this model (e.g., 'Rock Sample'). Used in UI labels."""

    description: str = ""
    """Detailed description of this model type. Used in documentation and help text."""

    def __post_init__(self):
        """Validate configuration after initialization (T009, T030)."""
        # Copy class attributes to instance if not provided as arguments
        # This allows subclass definitions like:
        #   class MyConfig(ModelConfiguration):
        #       model = MyModel
        #       table_class = MyTable

        # List of attributes that should be copied from class to instance
        class_attrs = [
            "model",
            "metadata",
            "fields",
            "exclude",
            "table_fields",
            "form_fields",
            "filterset_fields",
            "serializer_fields",
            "resource_fields",
            "admin_list_display",
            "form_class",
            "table_class",
            "filterset_class",
            "serializer_class",
            "resource_class",
            "admin_class",
            "display_name",
            "description",
        ]

        for attr_name in class_attrs:
            # Get instance value
            instance_value = getattr(self, attr_name)

            # Check if there's a class-level value that differs from the default
            if hasattr(self.__class__, attr_name):
                class_value = getattr(self.__class__, attr_name)

                # Determine if we should use the class value:
                # - For model: if instance is None
                # - For strings: if instance is empty string
                # - For lists: if instance is empty list (default_factory creates new empty list)
                # - For None-defaulting attrs: if instance is None
                should_use_class_value = False

                if attr_name == "model":
                    should_use_class_value = instance_value is None and class_value is not None
                elif attr_name in ("display_name", "description"):
                    should_use_class_value = not instance_value and class_value
                elif attr_name in ("fields", "exclude"):
                    # These have default_factory, so instance is always a new list
                    # Use class value if it's not the default (empty list) and instance hasn't been modified
                    should_use_class_value = class_value and instance_value == []
                elif attr_name == "metadata":
                    should_use_class_value = instance_value is None and class_value is not None
                else:
                    # For component-specific fields and custom classes (all default to None)
                    should_use_class_value = instance_value is None and class_value is not None

                if should_use_class_value:
                    object.__setattr__(self, attr_name, class_value)

        if self.model is None:
            raise ConfigurationError("ModelConfiguration.model is required")

        # Set display_name from model if not provided
        if not self.display_name:
            self.display_name = str(self.model._meta.verbose_name).title()

        # Initialize metadata if not provided
        if self.metadata is None:
            self.metadata = ModelMetadata()

        # Validate field names (T030)
        self._validate_fields()

        # Validate admin class inheritance for polymorphic models
        self._validate_admin_inheritance()

    def _validate_fields(self):
        """Validate that all field names exist on the model (T030).

        Raises:
            FieldValidationError: If any field name doesn't exist on the model
        """
        from fairdm.registry.exceptions import FieldValidationError

        # Collect all field lists to validate
        field_lists = [
            ("fields", self.fields),
            ("table_fields", self.table_fields),
            ("form_fields", self.form_fields),
            ("filterset_fields", self.filterset_fields),
            ("serializer_fields", self.serializer_fields),
            ("resource_fields", self.resource_fields),
            ("admin_list_display", self.admin_list_display),
        ]

        # Get valid field names from model
        assert self.model is not None  # Validated in __post_init__
        valid_fields = {f.name for f in self.model._meta.get_fields()}

        # Validate each field list
        for field_list_name, field_list in field_lists:
            if field_list is None:
                continue

            # Flatten field list (handles tuples for grouping)
            flat_field_list = []
            for item in field_list:
                if isinstance(item, (tuple, list)):
                    flat_field_list.extend(item)
                else:
                    flat_field_list.append(item)

            for field_name in flat_field_list:
                # Handle related field paths (e.g., 'project__title')
                base_field = field_name.split("__")[0]

                if base_field not in valid_fields:
                    # Try to find similar field names for helpful error message
                    import difflib

                    suggestions = difflib.get_close_matches(base_field, valid_fields, n=3, cutoff=0.6)

                    error_msg = f"Invalid field: {field_name} in {field_list_name}"
                    if suggestions:
                        error_msg += f". Did you mean: {', '.join(suggestions)}?"

                    raise FieldValidationError(error_msg, model=self.model)

    def _validate_admin_inheritance(self):
        """Validate that polymorphic models use correct admin base classes.

        For Sample subclasses, admin_class must inherit from SampleChildAdmin.
        For Measurement subclasses, admin_class must inherit from MeasurementAdmin (child).

        Raises:
            ConfigurationError: If admin_class doesn't inherit from required base
        """
        # Only validate if admin_class is explicitly provided
        if self.admin_class is None:
            return

        assert self.model is not None  # Validated in __post_init__

        # Get the admin class (may be string reference)
        admin_cls = self._get_class(self.admin_class)

        # Import base model classes to check inheritance
        try:
            from fairdm.core.admin import MeasurementAdmin as MeasurementChildAdmin
            from fairdm.core.models import Measurement, Sample
            from fairdm.core.sample.admin import SampleChildAdmin
        except ImportError:
            # Core models not available (testing scenario), skip validation
            return

        # Check Sample subclass
        if issubclass(self.model, Sample) and self.model is not Sample:
            if not issubclass(admin_cls, SampleChildAdmin):
                raise ConfigurationError(
                    f"Admin class for Sample subclass {self.model.__name__} must inherit from "
                    f"SampleChildAdmin. Got {admin_cls.__name__} instead. "
                    f"Change your admin class to: class {admin_cls.__name__}(SampleChildAdmin): ..."
                )

        # Check Measurement subclass
        if issubclass(self.model, Measurement) and self.model is not Measurement:
            if not issubclass(admin_cls, MeasurementChildAdmin):
                raise ConfigurationError(
                    f"Admin class for Measurement subclass {self.model.__name__} must inherit from "
                    f"MeasurementAdmin (the child admin base class). Got {admin_cls.__name__} instead. "
                    f"Change your admin class to: class {admin_cls.__name__}(MeasurementAdmin): ..."
                )

    @classmethod
    def get_default_fields(cls, model: type["models.Model"]) -> list[str]:
        """Get smart default field list for a model (T010).

        Excludes:
        - 'id', 'polymorphic_ctype', 'polymorphic_ctype_id'
        - Fields ending with '_ptr' or '_ptr_id' (multi-table inheritance)
        - Fields with auto_now=True or auto_now_add=True
        - Fields with editable=False

        Args:
            model: Django model class

        Returns:
            List of field names suitable for auto-generation
        """
        from django.db import models

        excluded_names = {"id", "polymorphic_ctype", "polymorphic_ctype_id"}
        fields = []

        for field in model._meta.get_fields():
            # Skip excluded field names
            if field.name in excluded_names:
                continue

            # Skip multi-table inheritance pointer fields
            if field.name.endswith("_ptr") or field.name.endswith("_ptr_id"):
                continue

            # Skip auto-generated timestamp fields
            if hasattr(field, "auto_now") and field.auto_now:
                continue
            if hasattr(field, "auto_now_add") and field.auto_now_add:
                continue

            # Skip non-editable fields
            if hasattr(field, "editable") and not field.editable:
                continue

            # Skip reverse relations (ManyToOneRel, ManyToManyRel)
            if hasattr(field, "related_name") and not hasattr(field, "column"):
                continue

            # Skip ManyToMany fields with custom through models (admin.E013)
            if isinstance(field, models.ManyToManyField):
                try:
                    if hasattr(field, "remote_field") and hasattr(field.remote_field, "through"):
                        through = field.remote_field.through
                        if through is not None:
                            # String reference means explicitly set (not auto-created)
                            if isinstance(through, str):
                                continue
                            # Model class - check if auto_created
                            if hasattr(through, "_meta") and not through._meta.auto_created:
                                continue
                except (AttributeError, TypeError):
                    # If we can't determine, be safe and exclude it
                    continue

            fields.append(field.name)

        return fields

    def _get_class(self, class_or_path: str | type) -> type:
        """Import a class from a string path or return the class directly."""
        if isinstance(class_or_path, str):
            return cast(type, import_string(class_or_path))
        return cast(type, class_or_path)

    # Display & Metadata Methods

    def get_display_name(self) -> str:
        """Get the display name for this model."""
        if self.display_name:
            return self.display_name
        if not self.model:
            return "Unknown Model"
        return str(self.model._meta.verbose_name).title()

    def get_description(self) -> str:
        """Get the description for this model."""
        if self.metadata and self.metadata.description:
            return self.metadata.description
        if not self.model:
            return "No model specified"
        return f"Configuration for {self.model.__name__}"

    def get_slug(self) -> str:
        """Get the URL-safe slug for this model.

        Returns the model's lowercase model name, used in URLs and view names.

        Returns:
            str: The model's slug (e.g., 'customsample', 'watermeasurement')
        """
        if not self.model:
            return "unknown"
        assert self.model is not None  # This should not happen after __post_init__
        return self.model._meta.model_name or ""

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
            str: The model's plural verbose name (e.g., 'custom samples')
        """
        if not self.model:
            return "Unknown Models"
        return str(self.model._meta.verbose_name_plural)

    def _flatten_fields(self, field_list: list[str | tuple[str, ...]] | None) -> list[str]:
        """Flatten a field list that may contain tuples for grouping.

        Args:
            field_list: List that may contain strings or tuples of strings

        Returns:
            Flattened list containing only strings
        """
        if not field_list:
            return []

        flat_list = []
        for item in field_list:
            if isinstance(item, (tuple, list)):
                flat_list.extend(item)
            else:
                flat_list.append(item)
        return flat_list

    # Component Generation Properties (using @cached_property for lazy evaluation)

    @cached_property
    def form(self) -> type[ModelForm]:
        """Get or auto-generate the ModelForm class using FormFactory (T016)."""
        if self.form_class is not None:
            return self._get_class(self.form_class)

        from fairdm.registry.factories import FormFactory

        assert self.model is not None  # Validated in __post_init__

        # Determine which fields to use (component-specific > parent > defaults)
        resolved_fields = self.form_fields or self.fields or self.get_default_fields(self.model)
        # Flatten any tuples in field list (used for UI grouping)
        resolved_fields = self._flatten_fields(resolved_fields)

        factory = FormFactory(
            model=self.model,
            fields=resolved_fields,
        )
        return factory.generate()

    @cached_property
    def table(self) -> type[Table]:
        """Get or auto-generate the Table class using TableFactory (T017)."""
        if self.table_class is not None:
            return self._get_class(self.table_class)

        from fairdm.registry.factories import TableFactory

        assert self.model is not None  # Validated in __post_init__
        # Determine which fields to use
        resolved_fields = self.table_fields or self.fields or self.get_default_fields(self.model)
        # Flatten any tuples in field list
        resolved_fields = self._flatten_fields(resolved_fields)

        factory = TableFactory(
            model=self.model,
            fields=resolved_fields,
        )
        return factory.generate()

    @cached_property
    def filterset(self) -> type[FilterSet]:
        """Get or auto-generate the FilterSet class using FilterFactory (T018)."""
        if self.filterset_class is not None:
            return self._get_class(self.filterset_class)

        from fairdm.registry.factories import FilterFactory

        assert self.model is not None  # Validated in __post_init__

        # Determine which fields to use
        resolved_fields = self.filterset_fields or self.fields or self.get_default_fields(self.model)
        # Flatten any tuples in field list
        resolved_fields = self._flatten_fields(resolved_fields)

        factory = FilterFactory(
            model=self.model,
            fields=resolved_fields,
        )
        return factory.generate()

    @cached_property
    def serializer(self) -> type["ModelSerializer"]:
        """Get or auto-generate the DRF ModelSerializer class (T019, T027)."""
        if self.serializer_class is not None:
            return self._get_class(self.serializer_class)

        # Use SerializerFactory for auto-generation
        from fairdm.registry.factories import SerializerFactory

        assert self.model is not None  # Validated in __post_init__

        # Determine which fields to use
        resolved_fields = self.serializer_fields or self.fields or self.get_default_fields(self.model)
        # Flatten any tuples in field list
        resolved_fields = self._flatten_fields(resolved_fields)

        factory = SerializerFactory(
            model=self.model,
            fields=resolved_fields,
        )
        return factory.generate()

    @cached_property
    def resource(self) -> type[ModelResource]:
        """Get or auto-generate the import/export Resource class (T020, T028)."""
        if self.resource_class is not None:
            return self._get_class(self.resource_class)

        # Use ResourceFactory for auto-generation
        from fairdm.registry.factories import ResourceFactory

        assert self.model is not None  # Validated in __post_init__

        # Determine which fields to use
        resolved_fields = self.resource_fields or self.fields or self.get_default_fields(self.model)
        # Flatten any tuples in field list
        resolved_fields = self._flatten_fields(resolved_fields)

        factory = ResourceFactory(
            model=self.model,
            fields=resolved_fields,
        )
        return factory.generate()

    @cached_property
    def admin(self) -> type["ModelAdmin"]:
        """Get or auto-generate the ModelAdmin class using AdminFactory (T021)."""
        if self.admin_class is not None:
            return self._get_class(self.admin_class)

        from fairdm.registry.factories import AdminFactory

        assert self.model is not None  # Validated in __post_init__

        # Determine which fields to use
        resolved_fields = self.admin_list_display or self.fields or self.get_default_fields(self.model)
        # Flatten any tuples in field list
        resolved_fields = self._flatten_fields(resolved_fields)

        factory = AdminFactory(
            model=self.model,
            fields=resolved_fields,
        )
        return factory.generate()

    def clear_cache(self) -> None:
        """Clear all cached component properties (T022).

        Call this method to invalidate cached components and force regeneration
        on next access. Useful for testing or when model schema changes dynamically.
        """
        cached_props = ["form", "table", "filterset", "serializer", "resource", "admin"]

        for prop_name in cached_props:
            try:
                delattr(self, prop_name)
            except AttributeError:
                # Property not yet accessed/cached
                pass

    # Backward compatibility methods (deprecated - use properties instead)

    def get_form_class(self) -> type[ModelForm]:
        """Get or auto-generate the ModelForm class.

        .. deprecated:: Use the ``form`` property instead.
        """
        return self.form

    def get_table_class(self) -> type[Table]:
        """Get or auto-generate the Table class.

        .. deprecated:: Use the ``table`` property instead.
        """
        return self.table

    def get_filterset_class(self) -> type[FilterSet]:
        """Get or auto-generate the FilterSet class.

        .. deprecated:: Use the ``filterset`` property instead.
        """
        return self.filterset

    def get_admin_class(self) -> type["ModelAdmin"]:
        """Get or auto-generate the ModelAdmin class.

        .. deprecated:: Use the ``admin`` property instead.
        """
        return self.admin

    def get_resource_class(self) -> type[ModelResource]:
        """Get or auto-generate the import/export Resource class.

        .. deprecated:: Use the ``resource`` property instead.
        """
        return self.resource

    def get_serializer_class(self) -> type["ModelSerializer"] | None:
        """Get the serializer class for the model, if DRF is available.

        .. deprecated:: Use the ``serializer`` property instead.
        """
        return self.serializer

        # DRF support is future work
        return None

    # Convenience Methods

    def has_custom_form(self) -> bool:
        """Check if a custom form class is provided."""
        return self.form_class is not None

    def has_custom_filterset(self) -> bool:
        """Check if a custom filterset class is provided."""
        return self.filterset_class is not None

    def has_custom_table(self) -> bool:
        """Check if a custom table class is provided."""
        return self.table_class is not None

    def has_custom_admin(self) -> bool:
        """Check if a custom admin class is provided."""
        return self.admin_class is not None

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
