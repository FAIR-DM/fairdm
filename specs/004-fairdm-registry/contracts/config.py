"""ModelConfiguration Protocol - Component Configuration API Contract.

This module defines the Protocol for ModelConfiguration, specifying the
exact interface for configuration classes and component access methods.
"""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin
    from django.db import models
    from django.forms import ModelForm
    from django_filters import FilterSet
    from django_tables2 import Table
    from import_export.resources import ModelResource
    from rest_framework.serializers import ModelSerializer


class ModelConfigurationProtocol(Protocol):
    """Protocol defining the ModelConfiguration public API.

    ModelConfiguration is the central class for configuring auto-generation
    of components (forms, tables, filters, serializers, etc.) for Sample
    and Measurement models.

    It supports three configuration levels:
    1. Simple: Parent `fields` attribute (all components inherit)
    2. Intermediate: Component-specific fields (table_fields, form_fields, etc.)
    3. Advanced: Custom classes (table_class, form_class, etc.)

    Example:
        Simple configuration::

            @register
            class RockSampleConfig(ModelConfiguration):
                model = RockSample
                fields = ["name", "location", "date_collected"]

        Component-specific fields::

            @register
            class RockSampleConfig(ModelConfiguration):
                model = RockSample
                fields = ["name", "location"]  # Default
                table_fields = ["name", "location", "contributor"]  # Extra column
                form_fields = ["name", "description", "location"]  # Include description

        Custom classes::

            @register
            class RockSampleConfig(ModelConfiguration):
                model = RockSample
                table_class = RockSampleTable  # Full control
                form_class = RockSampleForm  # Custom validation
    """

    # Required Attributes
    model: type["models.Model"]
    """Django model class (Sample or Measurement subclass). Required."""

    # Parent Field Configuration
    fields: list[str]
    """Parent field list inherited by all components.

    Empty list = use smart defaults (all user-defined fields).
    """

    exclude: list[str]
    """Fields to exclude from all components."""

    # Component-Specific Field Lists
    table_fields: list[str] | None
    """Fields for django-tables2 Table columns. Overrides parent `fields`."""

    form_fields: list[str] | None
    """Fields for Django ModelForm inputs. Overrides parent `fields`."""

    filterset_fields: list[str] | None
    """Fields for django-filter FilterSet filters. Overrides parent `fields`."""

    serializer_fields: list[str] | None
    """Fields for DRF ModelSerializer. Overrides parent `fields`."""

    resource_fields: list[str] | None
    """Fields for import_export Resource. Overrides parent `fields`."""

    admin_list_display: list[str] | None
    """Fields for Django Admin list_display. Overrides parent `fields`."""

    # Custom Class Overrides
    form_class: type["ModelForm"] | None
    """Custom ModelForm class. Replaces auto-generation."""

    table_class: type["Table"] | None
    """Custom django-tables2 Table class. Replaces auto-generation."""

    filterset_class: type["FilterSet"] | None
    """Custom django-filter FilterSet class. Replaces auto-generation."""

    serializer_class: type["ModelSerializer"] | None
    """Custom DRF ModelSerializer class. Replaces auto-generation."""

    resource_class: type["ModelResource"] | None
    """Custom import_export Resource class. Replaces auto-generation."""

    admin_class: type["ModelAdmin"] | None
    """Custom Django Admin ModelAdmin class. Replaces auto-generation."""

    # Metadata
    display_name: str
    """Human-readable name for this model (e.g., 'Rock Sample')."""

    description: str
    """Detailed description of this model type."""

    # Component Access Methods

    def get_form_class(self) -> type["ModelForm"]:
        """Get or generate ModelForm class.

        Returns custom form_class if provided, otherwise generates form from
        form_fields (or parent fields if form_fields not specified).

        Result is cached after first generation for performance.

        Returns:
            ModelForm subclass ready for instantiation

        Raises:
            FieldValidationError: If field names are invalid
            ConfigurationError: If custom form_class doesn't inherit from ModelForm

        Example:
            config = registry.get_for_model(RockSample)
            FormClass = config.get_form_class()
            form = FormClass(instance=sample)
        """
        ...

    @property
    def table(self) -> type["Table"]:
        """Get or generate django-tables2 Table class.

        Returns custom table_class if provided, otherwise generates table from
        table_fields (or parent fields if table_fields not specified).

        Result is cached automatically via @cached_property.

        Returns:
            Table subclass ready for instantiation with queryset

        Example:
            config = registry.get_for_model(RockSample)
            TableClass = config.table
            table = TableClass(RockSample.objects.all())
        """
        ...

    @property
    def filterset(self) -> type["FilterSet"]:
        """Get or generate django-filter FilterSet class.

        Returns custom filterset_class if provided, otherwise generates filterset from
        filterset_fields (or parent fields if filterset_fields not specified).

        Result is cached automatically via @cached_property.

        Returns:
            FilterSet subclass ready for instantiation with queryset

        Example:
            config = registry.get_for_model(RockSample)
            FilterSetClass = config.filterset
            filterset = FilterSetClass(request.GET, queryset=qs)
        """
        ...

    @property
    def serializer(self) -> type["ModelSerializer"]:
        """Get or generate DRF ModelSerializer class.

        Returns custom serializer_class if provided, otherwise generates serializer from
        serializer_fields (or parent fields if serializer_fields not specified).

        Result is cached automatically via @cached_property.

        Returns:
            ModelSerializer subclass for REST API endpoints

        Example:
            config = registry.get_for_model(RockSample)
            SerializerClass = config.serializer
            serializer = SerializerClass(data=request.data)
        """
        ...

    @property
    def resource(self) -> type["ModelResource"]:
        """Get or generate import_export Resource class.

        Returns custom resource_class if provided, otherwise generates resource from
        resource_fields (or parent fields if resource_fields not specified).

        Result is cached automatically via @cached_property.

        Returns:
            ModelResource subclass for CSV/Excel import/export

        Example:
            config = registry.get_for_model(RockSample)
            ResourceClass = config.resource
            resource = ResourceClass()
            dataset = resource.export(RockSample.objects.all())
        """
        ...

    @property
    def admin(self) -> type["ModelAdmin"]:
        """Get or generate Django Admin ModelAdmin class.

        Returns custom admin_class if provided, otherwise generates admin configuration
        from admin_list_display (or parent fields if admin_list_display not specified).

        Result is cached automatically via @cached_property.

        Returns:
            ModelAdmin subclass for Django admin site

        Example:
            config = registry.get_for_model(RockSample)
            AdminClass = config.admin
            admin.site.register(RockSample, AdminClass)
        """
        ...

    def clear_cache(self):
        """Clear all cached component classes.

        Used primarily in testing to force regeneration of components.
        Should not be needed in production code.

        Uses delattr() to remove @cached_property values.

        Example (pytest):
            def test_field_changes():
                config.clear_cache()  # Force regeneration
                config.table_fields = ['name', 'new_field']
                table_class = config.table
                assert 'new_field' in table_class.base_columns
        """
        ...

    @classmethod
    def get_default_fields(cls, model: type["models.Model"]) -> list[str]:
        """Generate smart default field list for a model.

        Includes all user-defined fields while excluding:
        - Technical fields (id, polymorphic_ctype, *_ptr)
        - Auto-generated timestamp fields (auto_now, auto_now_add)
        - Non-editable fields

        Args:
            model: Django model class

        Returns:
            List of field names safe for component generation

        Example:
            fields = ModelConfiguration.get_default_fields(RockSample)
            # Returns: ['name', 'description', 'location', 'date_collected']
            # Excludes: 'id', 'created', 'modified', 'sample_ptr'
        """
        ...
