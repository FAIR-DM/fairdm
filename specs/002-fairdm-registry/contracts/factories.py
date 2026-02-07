"""Component Factory Protocols - Factory Interface Contracts.

This module defines the Protocol for ComponentFactory and FieldResolver,
specifying the exact interface for component generation factories.
"""

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from django.db import models

    from .config import ModelConfigurationProtocol


class FieldResolverProtocol(Protocol):
    """Protocol for field resolution and filtering.

    FieldResolvers determine which fields should be used for a specific
    component type, applying the three-tier precedence:
    1. Component-specific fields (highest)
    2. Parent fields (middle)
    3. Smart defaults (lowest)

    Then filters fields based on component capabilities.
    """

    def resolve_fields(
        self,
        config: "ModelConfigurationProtocol",
        component_type: str,
    ) -> list[str] | None:
        """Resolve field list for a component type.

        Args:
            config: ModelConfiguration instance
            component_type: One of 'table', 'form', 'filterset', 'serializer', 'resource', 'admin'

        Returns:
            List of field names to use for component generation.
            Returns None if custom class is provided (class handles its own fields).

        Example:
            resolver = FieldResolver()
            fields = resolver.resolve_fields(config, 'table')
            # Returns: ['name', 'location', 'contributor']
        """
        ...

    def filter_for_component(
        self,
        fields: list[str],
        component_type: str,
        model: type["models.Model"],
    ) -> list[str]:
        """Filter field list based on component capabilities.

        Different components have different constraints:
        - Forms: Cannot include related field paths (e.g., 'project__title')
        - Tables: Can include related paths, exclude large text fields
        - Filters: Can include related paths, focus on searchable types

        Args:
            fields: Base field list to filter
            component_type: Component being generated
            model: Model class for field introspection

        Returns:
            Filtered field list appropriate for component type

        Example:
            resolver = FieldResolver()
            filtered = resolver.filter_for_component(
                ['name', 'project__title', 'notes'],  # Input
                'form',
                RockSample
            )
            # Returns: ['name', 'notes']  # Excludes project__title (related field)
        """
        ...


class ComponentFactoryProtocol(Protocol):
    """Protocol for component class factories.

    ComponentFactories generate Django component classes (Forms, Tables, etc.)
    from ModelConfiguration specifications. Each factory type implements
    this protocol with component-specific generation logic.

    Available factories:
    - FormFactory (ModelForm)
    - TableFactory (django-tables2 Table)
    - FilterFactory (django-filter FilterSet)
    - SerializerFactory (DRF ModelSerializer)
    - ResourceFactory (import_export Resource)
    - AdminFactory (Django Admin ModelAdmin)
    """

    model: type["models.Model"]
    """Django model class being configured."""

    config: "ModelConfigurationProtocol"
    """ModelConfiguration instance with field specifications."""

    def generate(self) -> type[Any]:
        """Generate component class from configuration.

        This method:
        1. Resolves field list using FieldResolver
        2. Maps Django field types to component-specific types
        3. Creates dynamic class with appropriate Meta configuration
        4. Returns cached class on subsequent calls

        Returns:
            Component class ready for instantiation

        Raises:
            FieldValidationError: If field names are invalid
            ComponentGenerationError: If class creation fails

        Example:
            factory = FormFactory(RockSample, config)
            FormClass = factory.generate()
            form = FormClass(instance=sample)
        """
        ...

    def validate_fields(self, fields: list[str]):
        """Validate that fields exist and are suitable for component.

        Args:
            fields: Field names to validate

        Raises:
            FieldValidationError: If fields are invalid with suggestions

        Example:
            factory.validate_fields(['name', 'location'])
            # Passes validation

            factory.validate_fields(['nonexistent'])
            # Raises: FieldValidationError("Field 'nonexistent' does not exist...")
        """
        ...

    def get_field_mapping(self, field_name: str) -> dict[str, Any]:
        """Get component-specific configuration for a Django field.

        Maps Django field types to component-specific types. For example:
        - Forms: CharField → TextInput widget
        - Tables: DateField → DateColumn
        - Filters: CharField → CharFilter with icontains lookup

        Args:
            field_name: Django model field name

        Returns:
            Dictionary of component-specific configuration

        Example (FormFactory):
            mapping = factory.get_field_mapping('date_collected')
            # Returns: {'widget': DateInput(attrs={'type': 'date'})}

        Example (TableFactory):
            mapping = factory.get_field_mapping('date_collected')
            # Returns: {'column_class': DateColumn, 'format': 'Y-m-d'}
        """
        ...


class FormFactoryProtocol(ComponentFactoryProtocol, Protocol):
    """Protocol for ModelForm generation.

    Generates Django ModelForm classes with:
    - Resolved field list in Meta.fields
    - Appropriate widgets for field types
    - crispy-forms Bootstrap 5 styling
    """

    def generate(self) -> type["models.Model"]:
        """Generate ModelForm class.

        Returns:
            ModelForm subclass with configured fields and widgets
        """
        ...


class TableFactoryProtocol(ComponentFactoryProtocol, Protocol):
    """Protocol for django-tables2 Table generation.

    Generates Table classes with:
    - Resolved field list as columns
    - Appropriate column types for field types
    - Detail link column
    - Pagination support
    """

    def generate(self) -> type["models.Model"]:
        """Generate Table class.

        Returns:
            Table subclass with configured columns
        """
        ...


class FilterFactoryProtocol(ComponentFactoryProtocol, Protocol):
    """Protocol for django-filter FilterSet generation.

    Generates FilterSet classes with:
    - Resolved field list as filters
    - Appropriate filter types for field types
    - Range filters for date/numeric fields
    - Autocomplete for foreign keys
    """

    def generate(self) -> type["models.Model"]:
        """Generate FilterSet class.

        Returns:
            FilterSet subclass with configured filters
        """
        ...


class SerializerFactoryProtocol(ComponentFactoryProtocol, Protocol):
    """Protocol for DRF ModelSerializer generation.

    Generates ModelSerializer classes with:
    - Resolved field list in Meta.fields
    - Appropriate serializer fields for model field types
    - Nested serializers for foreign keys (when appropriate)
    """

    def generate(self) -> type["models.Model"]:
        """Generate ModelSerializer class.

        Returns:
            ModelSerializer subclass with configured fields
        """
        ...


class ResourceFactoryProtocol(ComponentFactoryProtocol, Protocol):
    """Protocol for import_export Resource generation.

    Generates Resource classes with:
    - Resolved field list for import/export
    - Natural key handling for foreign keys
    - CSV/Excel format support
    """

    def generate(self) -> type["models.Model"]:
        """Generate Resource class.

        Returns:
            ModelResource subclass with configured fields
        """
        ...


class AdminFactoryProtocol(ComponentFactoryProtocol, Protocol):
    """Protocol for Django Admin ModelAdmin generation.

    Generates ModelAdmin classes with:
    - Resolved field list in list_display
    - Search fields
    - Filters
    - Inline editing support
    """

    def generate(self) -> type["models.Model"]:
        """Generate ModelAdmin class.

        Returns:
            ModelAdmin subclass with configured admin options
        """
        ...
