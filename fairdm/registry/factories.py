"""
Component Factories for FairDM ModelConfiguration.

This module provides factory classes that generate Django components (Forms, Tables,
Filters, Admin) from ModelConfiguration settings using intelligent field introspection.
"""

from typing import Any

from django.contrib import admin
from django.db import models
from django.forms import ModelForm, modelform_factory
from django_filters import FilterSet
from django_filters.filterset import filterset_factory
from django_tables2 import Table
from django_tables2.tables import table_factory

from fairdm.registry.components import AdminConfig, FiltersConfig, FormConfig, TableConfig
from fairdm.utils.inspection import FieldInspector


class ComponentFactory:
    """Base factory for generating Django components from configuration.

    This abstract base class provides common functionality for all component factories.
    Subclasses implement specific generation logic for Forms, Tables, Filters, etc.
    """

    def __init__(self, model: type[models.Model], config: Any):
        """Initialize the factory.

        Args:
            model: The Django model class to generate components for
            config: The component-specific configuration (e.g., TableConfig, FormConfig)
        """
        self.model = model
        self.config = config
        self.inspector = FieldInspector(model)

    def get_fields(self) -> list[str]:
        """Get fields to use, with intelligent fallback chain.

        Resolution order:
        1. Component-specific fields (e.g., config.Table.fields)
        2. Global fields (config.fields)
        3. Auto-detected safe fields (inspector.get_safe_fields())

        Returns:
            List of field names to use
        """
        # If config specifies fields, use them
        if hasattr(self.config, "fields") and self.config.fields is not None:
            if self.config.fields == "__all__":
                return self.inspector.get_all_field_names()
            return self.config.fields

        # Otherwise, use safe fields
        return self.inspector.get_safe_fields()

    def apply_exclusions(self, fields: list[str]) -> list[str]:
        """Apply exclusions to field list.

        Args:
            fields: Initial field list

        Returns:
            Field list with exclusions removed
        """
        if hasattr(self.config, "exclude") and self.config.exclude:
            return [f for f in fields if f not in self.config.exclude]
        return fields

    def generate(self) -> Any:
        """Generate the component.

        This method must be implemented by subclasses.

        Returns:
            The generated component class
        """
        raise NotImplementedError("Subclasses must implement generate()")


class FormFactory(ComponentFactory):
    """Factory for generating ModelForm classes with smart widgets."""

    def __init__(self, model: type[models.Model], config: FormConfig, parent_fields: list[str] | None = None):
        """Initialize FormFactory.

        Args:
            model: The Django model class
            config: FormConfig with form-specific settings
            parent_fields: Fields from parent ModelConfiguration (fallback)
        """
        super().__init__(model, config)
        self.parent_fields = parent_fields

    def get_fields(self) -> list[str] | str:
        """Get fields for the form.

        Returns:
            List of field names or "__all__"
        """
        # Check if config specifies fields
        if self.config.fields is not None:
            fields = self.config.fields
        # Fall back to parent fields
        elif self.parent_fields:
            fields = self.parent_fields
        else:
            # Default to safe fields
            return self.inspector.get_safe_fields()

        # Flatten nested tuples (e.g., from fieldsets format)
        if isinstance(fields, (list, tuple)):
            flattened = []
            for item in fields:
                if isinstance(item, (list, tuple)):
                    flattened.extend(item)
                else:
                    flattened.append(item)

            # Filter out non-editable fields (auto_now, auto_now_add, etc.)
            safe_fields = self.inspector.get_safe_fields()
            return [f for f in flattened if f in safe_fields or f == "__all__"]

        return fields

    def get_widgets(self) -> dict[str, Any]:
        """Generate smart widgets for fields.

        Returns:
            Dictionary mapping field names to widget instances
        """
        # Start with user-provided widgets
        widgets = dict(self.config.widgets) if self.config.widgets else {}

        # Get fields that need widgets
        fields = self.get_fields()
        if fields == "__all__":
            fields = self.inspector.get_safe_fields()

        # Add smart widgets for fields that don't have custom ones
        for field_name in fields:
            if field_name in widgets:
                continue  # User provided custom widget

            # Get widget suggestion from inspector
            suggested_widget = self.inspector.suggest_widget(field_name)
            if suggested_widget:
                # Note: We return widget names, the actual widget classes
                # will be resolved by the form generation
                widgets[field_name] = suggested_widget

        return widgets

    def generate(self) -> type[ModelForm]:
        """Generate a ModelForm class.

        Returns:
            ModelForm subclass with smart widgets and configuration
        """
        # If user provided a custom form class, use it
        if self.config.form_class is not None:
            if isinstance(self.config.form_class, str):
                from django.utils.module_loading import import_string

                return import_string(self.config.form_class)
            return self.config.form_class

        # Prepare form factory kwargs
        fields = self.get_fields()
        exclude = self.config.exclude

        # Build form using Django's modelform_factory
        # Django requires either fields or exclude to be specified
        if fields == "__all__":
            # Pass __all__ as string, not None
            kwargs = {"fields": "__all__"}
        elif fields:
            kwargs = {"fields": fields}
        else:
            # If no fields specified, use safe fields
            kwargs = {"fields": self.inspector.get_safe_fields()}

        if exclude:
            kwargs["exclude"] = exclude

        # Note: Widget mapping will be handled by a separate method
        # that converts widget names to actual widget instances
        form_class = modelform_factory(
            self.model,
            form=ModelForm,
            **kwargs,
        )

        # TODO: Apply custom widgets, labels, help_texts, etc.
        # This will require creating a custom Meta class or modifying the form

        return form_class


class TableFactory(ComponentFactory):
    """Factory for generating Table classes with smart defaults."""

    def __init__(self, model: type[models.Model], config: TableConfig, parent_fields: list[str] | None = None):
        """Initialize TableFactory.

        Args:
            model: The Django model class
            config: TableConfig with table-specific settings
            parent_fields: Fields from parent ModelConfiguration (fallback)
        """
        super().__init__(model, config)
        self.parent_fields = self._flatten_fields(parent_fields) if parent_fields else None

    def _flatten_fields(self, fields: list | tuple | None) -> list[str] | None:
        """Flatten nested tuples/lists in field definitions.

        Args:
            fields: Field list that may contain nested tuples

        Returns:
            Flattened list of field names or None
        """
        if not fields:
            return None

        flattened = []
        for item in fields:
            if isinstance(item, (list, tuple)):
                flattened.extend(item)
            else:
                flattened.append(item)
        return flattened

    def get_fields(self) -> list[str]:
        """Get fields for the table.

        Returns:
            List of field names for table columns
        """
        # Check if config specifies fields
        if self.config.fields is not None:
            fields = self.config.fields
        # Fall back to parent fields
        elif self.parent_fields:
            fields = self.parent_fields
        # Use inspector's smart defaults
        else:
            fields = self.inspector.get_default_list_fields()

        # Apply exclusions
        return self.apply_exclusions(fields)

    def generate(self) -> type[Table]:
        """Generate a django-tables2 Table class.

        Returns:
            Table subclass configured for the model
        """
        # If user provided a custom table class, use it
        if self.config.table_class is not None:
            if isinstance(self.config.table_class, str):
                from django.utils.module_loading import import_string

                return import_string(self.config.table_class)
            return self.config.table_class

        # Get fields for the table
        fields = self.get_fields()

        # Generate table using django-tables2's table_factory
        # Note: django-tables2's table_factory doesn't have an orderable parameter
        # We'll need to set orderable on the Meta class after generation
        table_class = table_factory(
            self.model,
            fields=fields,
        )

        # Apply orderable configuration to the Meta class
        if self.config.orderable is not None:
            if isinstance(self.config.orderable, bool):
                # Set orderable for all columns
                table_class._meta.orderable = self.config.orderable
            else:
                # Set orderable to specific list of columns
                table_class._meta.orderable = self.config.orderable

        return table_class


class FilterFactory(ComponentFactory):
    """Factory for generating FilterSet classes with smart filters."""

    def __init__(self, model: type[models.Model], config: FiltersConfig, parent_fields: list[str] | None = None):
        """Initialize FilterFactory.

        Args:
            model: The Django model class
            config: FiltersConfig with filter-specific settings
            parent_fields: Fields from parent ModelConfiguration (fallback)
        """
        super().__init__(model, config)
        self.parent_fields = self._flatten_fields(parent_fields) if parent_fields else None

    def _flatten_fields(self, fields: list | tuple | None) -> list[str] | None:
        """Flatten nested tuples/lists in field definitions.

        Args:
            fields: Field list that may contain nested tuples

        Returns:
            Flattened list of field names or None
        """
        if not fields:
            return None

        flattened = []
        for item in fields:
            if isinstance(item, (list, tuple)):
                flattened.extend(item)
            else:
                flattened.append(item)
        return flattened

    def get_fields(self) -> list[str]:
        """Get fields for filters.

        Returns:
            List of field names to create filters for
        """
        # Check if config specifies fields
        if self.config.fields is not None:
            fields = self.config.fields
        # Fall back to parent fields
        elif self.parent_fields:
            fields = self.parent_fields
        # Use inspector's smart defaults for filters
        else:
            fields = self.inspector.get_default_filter_fields()

        # Validate fields - django-filter is strict about field names
        # Only include fields that actually exist in the model and are valid for filtering
        model_field_names = {f.name for f in self.model._meta.get_fields()}
        fields = [f for f in fields if f in model_field_names]

        # Apply exclusions
        return self.apply_exclusions(fields)

    def get_filter_overrides(self) -> dict[str, str]:
        """Get filter type overrides based on configuration and smart detection.

        Returns:
            Dictionary mapping field names to filter type names
        """
        overrides = {}

        # Start with user-provided overrides
        if self.config.filter_overrides:
            overrides.update(self.config.filter_overrides)

        # Get fields
        fields = self.get_fields()

        # Apply smart filter detection for fields without custom overrides
        for field_name in fields:
            if field_name in overrides:
                continue  # User provided custom filter

            # Check if field is in exact_fields list
            if self.config.exact_fields and field_name in self.config.exact_fields:
                overrides[field_name] = "exact"
                continue

            # Check if field is in range_fields list
            if self.config.range_fields and field_name in self.config.range_fields:
                suggested_filter = self.inspector.suggest_filter_type(field_name)
                if suggested_filter and "Range" in suggested_filter:
                    overrides[field_name] = suggested_filter
                continue

            # Check if field is in search_fields list
            if self.config.search_fields and field_name in self.config.search_fields:
                overrides[field_name] = "CharFilter"  # icontains
                continue

            # Otherwise, use smart detection
            suggested_filter = self.inspector.suggest_filter_type(field_name)
            if suggested_filter:
                overrides[field_name] = suggested_filter

        return overrides

    def generate(self) -> type[FilterSet]:
        """Generate a django-filter FilterSet class.

        Returns:
            FilterSet subclass with smart filters
        """
        # If user provided a custom filterset class, use it
        if self.config.filterset_class is not None:
            if isinstance(self.config.filterset_class, str):
                from django.utils.module_loading import import_string

                return import_string(self.config.filterset_class)
            return self.config.filterset_class

        # Get fields for filters
        fields = self.get_fields()

        # Generate filterset using django-filter's filterset_factory
        # Note: Filter type overrides will need to be applied separately
        # as filterset_factory doesn't directly support custom filter types per field
        filterset_class = filterset_factory(
            self.model,
            fields=fields,
        )

        # TODO: Apply filter overrides to the generated filterset
        # This may require creating a custom Meta class or modifying the filterset

        return filterset_class


class AdminFactory(ComponentFactory):
    """Factory for generating Django Admin ModelAdmin classes."""

    def __init__(self, model: type[models.Model], config: AdminConfig, parent_fields: list[str] | None = None):
        """Initialize AdminFactory.

        Args:
            model: The Django model class
            config: AdminConfig with admin-specific settings
            parent_fields: Fields from parent ModelConfiguration (fallback)
        """
        super().__init__(model, config)
        self.parent_fields = self._flatten_fields(parent_fields) if parent_fields else None

    def _flatten_fields(self, fields: list | tuple | None) -> list[str] | None:
        """Flatten nested tuples/lists in field definitions.

        Args:
            fields: Field list that may contain nested tuples

        Returns:
            Flattened list of field names or None
        """
        if not fields:
            return None

        flattened = []
        for item in fields:
            if isinstance(item, (list, tuple)):
                flattened.extend(item)
            else:
                flattened.append(item)
        return flattened

    def get_list_display(self) -> list[str]:
        """Get fields for admin list display.

        Returns:
            List of field names for list display
        """
        if self.config.list_display is not None:
            return self.config.list_display

        # Use parent fields if available
        if self.parent_fields:
            fields = self.parent_fields[:5]  # Limit to first 5 for list view
        else:
            # Use inspector's default list fields
            fields = self.inspector.get_default_list_fields()

        # Validate fields - ensure they actually exist in the model
        model_field_names = {f.name for f in self.model._meta.get_fields()}
        return [f for f in fields if f in model_field_names]

    def get_list_filter(self) -> list[str]:
        """Get fields for admin list filter sidebar.

        Returns:
            List of field names for filtering
        """
        if self.config.list_filter is not None:
            return self.config.list_filter

        # Smart defaults: date, choice, and boolean fields
        filters = []
        for field_name in self.inspector.get_date_fields():
            filters.append(field_name)
        for field_name in self.inspector.get_choice_fields():
            filters.append(field_name)
        for field_name in self.inspector.get_boolean_fields():
            filters.append(field_name)

        return filters[:5]  # Limit to 5 filters

    def get_search_fields(self) -> list[str]:
        """Get fields for admin search.

        Returns:
            List of field names for search
        """
        if self.config.search_fields is not None:
            return self.config.search_fields

        # Smart defaults: text fields that make sense for search
        search_fields = []
        text_fields = self.inspector.get_text_fields()

        # Prioritize common search fields
        priority = ["name", "title", "description"]
        for field_name in priority:
            if field_name in text_fields:
                search_fields.append(field_name)

        # Add other text fields
        for field_name in text_fields:
            if field_name not in search_fields and field_name not in ["id", "uuid"]:
                search_fields.append(field_name)

        return search_fields[:3]  # Limit to 3 search fields

    def get_fieldsets(self) -> list[tuple[str | None, dict[str, Any]]] | None:
        """Get fieldsets for admin form organization.

        Returns:
            List of fieldsets in Django admin format or None
        """
        if self.config.fieldsets is not None:
            # Check if it's a dict (our simplified format)
            if isinstance(self.config.fieldsets, dict):
                # Convert dict to Django admin format
                return [
                    (section_name, {"fields": field_list}) for section_name, field_list in self.config.fieldsets.items()
                ]
            # Already in Django format
            return self.config.fieldsets

        # Auto-generate fieldsets using inspector
        groups = self.inspector.group_fields_for_admin()

        # Convert to Django admin format
        fieldsets = []
        for section_name, field_list in groups.items():
            if field_list:  # Only include non-empty sections
                fieldsets.append((section_name, {"fields": field_list}))

        return fieldsets if fieldsets else None

    def generate(self) -> type[admin.ModelAdmin]:
        """Generate a Django ModelAdmin class.

        Returns:
            ModelAdmin subclass configured for the model
        """
        # If user provided a custom admin class, use it
        if self.config.admin_class is not None:
            if isinstance(self.config.admin_class, str):
                from django.utils.module_loading import import_string

                return import_string(self.config.admin_class)
            return self.config.admin_class

        # Build admin class attributes
        attrs = {
            "model": self.model,
            "list_display": self.get_list_display(),
            "list_filter": self.get_list_filter(),
            "search_fields": self.get_search_fields(),
        }

        # Add optional attributes if configured
        if self.config.list_per_page:
            attrs["list_per_page"] = self.config.list_per_page

        if self.config.list_editable:
            attrs["list_editable"] = self.config.list_editable

        if self.config.ordering:
            attrs["ordering"] = self.config.ordering

        if self.config.date_hierarchy:
            attrs["date_hierarchy"] = self.config.date_hierarchy

        if self.config.readonly_fields:
            attrs["readonly_fields"] = self.config.readonly_fields

        if self.config.prepopulated_fields:
            attrs["prepopulated_fields"] = self.config.prepopulated_fields

        if self.config.inlines:
            attrs["inlines"] = self.config.inlines

        # Add fieldsets
        fieldsets = self.get_fieldsets()
        if fieldsets:
            attrs["fieldsets"] = fieldsets

        # Determine app_label based on model inheritance
        # Group Sample subtypes under 'sample' app and Measurement subtypes under 'measurement' app
        app_label = self._get_admin_app_label()
        if app_label:
            # Create Meta class with app_label override
            meta_attrs = {"app_label": app_label}
            attrs["Meta"] = type("Meta", (), meta_attrs)

        # Create the admin class
        admin_class_name = f"{self.model.__name__}Admin"
        admin_class = type(admin_class_name, (admin.ModelAdmin,), attrs)

        return admin_class

    def _get_admin_app_label(self) -> str | None:
        """Determine the app_label for admin grouping based on model inheritance.

        Returns:
            App label string for Sample/Measurement subtypes, None otherwise
        """
        try:
            from fairdm.core.measurement.models import Measurement
            from fairdm.core.sample.models import Sample

            if issubclass(self.model, Sample):
                return "sample"
            elif issubclass(self.model, Measurement):
                return "measurement"
        except (ImportError, TypeError):
            pass
        return None


# Export factory classes
__all__ = [
    "AdminFactory",
    "ComponentFactory",
    "FilterFactory",
    "FormFactory",
    "TableFactory",
]
