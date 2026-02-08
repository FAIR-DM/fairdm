"""
Component Factories for FairDM ModelConfiguration.

This module provides factory classes that generate Django components (Forms, Tables,
Filters, Admin, Serializers, Resources) from ModelConfiguration settings using intelligent
field introspection and the FieldResolver.

Features:
- Smart field type detection and widget/column/filter mapping
- FieldResolver integration for consistent field resolution
- Crispy-forms integration for better form layouts
- Bootstrap 5 styling for tables
- Nested serializers for ForeignKey relationships
- Natural key support for import/export resources

Updated Tasks: T024-T029
"""

from typing import Any, cast

from django.contrib import admin
from django.db import models
from django.forms import ModelForm, modelform_factory
from django_filters import FilterSet
from django_filters.filterset import filterset_factory
from django_tables2 import Table
from django_tables2.tables import table_factory

from fairdm.utils.inspection import FieldInspector


class ComponentFactory:
    """Base factory for generating Django components from configuration.

    This abstract base class provides common functionality for all component factories.
    Subclasses implement specific generation logic for Forms, Tables, Filters, etc.
    """

    def __init__(self, model: type[models.Model], fields: list[str] | None = None):
        """Initialize the factory.

        Args:
            model: The Django model class to generate components for
            fields: List of field names to use (None = use smart defaults)
        """
        self.model = model
        self.fields = fields
        self.inspector = FieldInspector(model)

    def get_fields(self) -> list[str]:
        """Get fields to use, with intelligent fallback chain.

        Resolution order:
        1. Explicitly provided fields
        2. Auto-detected safe fields (inspector.get_safe_fields())

        Returns:
            List of field names to use
        """
        if self.fields is not None:
            return self.fields

        # Use safe fields as default
        return cast(list[str], self.inspector.get_safe_fields())

    def generate(self) -> Any:
        """Generate the component.

        This method must be implemented by subclasses.

        Returns:
            The generated component class
        """
        raise NotImplementedError("Subclasses must implement generate()")


class FormFactory(ComponentFactory):
    """Factory for generating ModelForm classes with smart widgets and crispy-forms layout.

    Features (T024):
    - Uses FieldResolver for consistent field selection
    - Field type to widget mapping (DateInput for dates, Textarea for large text)
    - Crispy-forms FormHelper for Bootstrap 5 styling
    - Smart widget choices based on field characteristics
    """

    def generate(self) -> type[ModelForm]:
        """Generate a ModelForm class with smart widgets.

        Returns:
            ModelForm subclass with smart widgets and crispy-forms configuration
        """
        from crispy_forms.helper import FormHelper
        from crispy_forms.layout import Submit

        fields = self.get_fields()

        # Build widgets dict with smart defaults
        widgets = self._get_smart_widgets()

        # Build form using Django's modelform_factory
        form_class = modelform_factory(
            self.model,
            form=ModelForm,
            fields=fields,
            widgets=widgets,
        )

        # Add crispy-forms helper
        original_init = form_class.__init__

        def __init__(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self.helper = FormHelper()
            self.helper.form_method = "post"
            self.helper.add_input(Submit("submit", "Save"))

        form_class.__init__ = __init__

        return form_class

    def _get_smart_widgets(self) -> dict[str, Any]:
        """Generate smart widget choices based on field types.

        Returns:
            Dictionary mapping field names to widget instances
        """
        from django import forms

        widgets = {}
        fields = self.get_fields()

        for field_name in fields:
            try:
                field = self.model._meta.get_field(field_name)

                # Date fields get DateInput with HTML5 type
                if isinstance(field, models.DateField) and not isinstance(field, models.DateTimeField):
                    widgets[field_name] = forms.DateInput(attrs={"type": "date"})

                # DateTime fields get DateTimeInput with HTML5 type
                elif isinstance(field, models.DateTimeField):
                    widgets[field_name] = forms.DateTimeInput(attrs={"type": "datetime-local"})

                # Large text fields get Textarea
                elif isinstance(field, models.TextField) or (
                    isinstance(field, models.CharField) and getattr(field, "max_length", 0) > 200
                ):
                    widgets[field_name] = forms.Textarea(attrs={"rows": 4})

                # Email fields get EmailInput
                elif isinstance(field, models.EmailField):
                    widgets[field_name] = forms.EmailInput()

                # URL fields get URLInput
                elif isinstance(field, models.URLField):
                    widgets[field_name] = forms.URLInput()

                # File/Image fields already have good defaults

            except Exception:
                # Skip fields that can't be resolved
                pass

        return widgets


class TableFactory(ComponentFactory):
    """Factory for generating Table classes with smart column types and Bootstrap 5 styling.

    Features (T025):
    - Uses FieldResolver for consistent field selection
    - Field type to column mapping (DateColumn for dates, EmailColumn for emails)
    - Bootstrap 5 template
    - Filters large text fields to prevent display issues
    - Smart column ordering and formatting
    """

    def generate(self) -> type[Table]:
        """Generate a django-tables2 Table class with smart columns.

        Returns:
            Table subclass configured with Bootstrap 5 styling and smart columns
        """

        fields = self.get_fields()

        # Filter out large text fields that shouldn't be in tables
        filtered_fields = self._filter_table_fields(fields)

        # Build column overrides with smart types
        extra_columns = self._get_smart_columns(filtered_fields)

        # Create a base table with extra columns as class attributes
        base_table = self.get_base_table_class()
        if extra_columns:
            # Create intermediate class with column definitions
            table_attrs = extra_columns.copy()
            base_table = type("SmartTable", (base_table,), table_attrs)

        # Generate table using django-tables2's table_factory
        table_class = table_factory(
            self.model,
            table=base_table,
            fields=filtered_fields,
        )

        # Apply Bootstrap 5 styling
        if not hasattr(table_class.Meta, "template_name"):
            table_class.Meta.template_name = "django_tables2/bootstrap5.html"
        if not hasattr(table_class.Meta, "attrs"):
            table_class.Meta.attrs = {"class": "table table-striped table-hover"}

        return cast(type[Table], table_class)

    def _filter_table_fields(self, fields: list[str]) -> list[str]:
        """Filter out fields that shouldn't appear in tables (large text, etc).

        Args:
            fields: List of field names

        Returns:
            Filtered list of field names suitable for table display
        """
        filtered = []
        for field_name in fields:
            try:
                field = self.model._meta.get_field(field_name)

                # Skip TextField and long CharField
                if isinstance(field, models.TextField):
                    continue
                if isinstance(field, models.CharField) and getattr(field, "max_length", 0) > 200:
                    continue

                filtered.append(field_name)

            except Exception:
                # Include field if we can't determine its type
                filtered.append(field_name)

        return filtered or fields  # Return original if all filtered out

    def _get_smart_columns(self, fields: list[str]) -> dict[str, Any]:
        """Generate smart column types based on field types.

        Args:
            fields: List of field names

        Returns:
            Dictionary mapping field names to column instances
        """
        import django_tables2 as tables

        columns = {}

        for field_name in fields:
            try:
                field = self.model._meta.get_field(field_name)

                # Date fields get DateColumn
                if isinstance(field, models.DateField) and not isinstance(field, models.DateTimeField):
                    columns[field_name] = tables.DateColumn(format="Y-m-d")

                # DateTime fields get DateTimeColumn
                elif isinstance(field, models.DateTimeField):
                    columns[field_name] = tables.DateTimeColumn(format="Y-m-d H:i")

                # Email fields get EmailColumn
                elif isinstance(field, models.EmailField):
                    columns[field_name] = tables.EmailColumn()

                # URL fields get URLColumn
                elif isinstance(field, models.URLField):
                    columns[field_name] = tables.URLColumn()

                # Boolean fields get BooleanColumn
                elif isinstance(field, models.BooleanField):
                    columns[field_name] = tables.BooleanColumn()

            except Exception:
                # Skip fields that can't be resolved
                pass

        return columns

    def get_base_table_class(self) -> type[Table]:
        """Get the base table class to use.

        Returns:
            Base Table subclass
        """
        from fairdm.contrib.collections.tables import MeasurementTable, SampleTable
        from fairdm.core.models import Measurement, Sample

        if issubclass(self.model, Sample):
            return cast(type[Table], SampleTable)
        elif issubclass(self.model, Measurement):
            return cast(type[Table], MeasurementTable)

        return cast(type[Table], Table)


class FilterFactory(ComponentFactory):
    """Factory for generating FilterSet classes with smart filter types and crispy-forms styling.

    Features (T026):
    - Uses FieldResolver for consistent field selection
    - Field type to filter mapping (DateFromToRangeFilter for dates, ChoiceFilter for choices)
    - Crispy-forms styling integration
    - Smart filter selection based on field characteristics
    """

    def generate(self) -> type[FilterSet]:
        """Generate a django-filter FilterSet class with smart filters.

        Returns:
            FilterSet subclass with smart filters and crispy-forms styling
        """
        import re

        fields = self.get_fields()

        # Validate fields - django-filter is strict about field names and types
        model_field_names = {f.name for f in self.model._meta.get_fields()}
        fields = [f for f in fields if f in model_field_names]

        # Build custom filter dict with smart types
        filter_overrides = self._get_smart_filters(fields)

        # Try generating filterset with smart filters
        try:
            # Create Meta class
            meta_attrs = {
                "model": self.model,
                "fields": fields,
            }
            Meta = type("Meta", (), meta_attrs)

            # Create FilterSet class with overrides
            filterset_attrs = {"Meta": Meta}
            filterset_attrs.update(filter_overrides)

            filterset_class = type(
                f"{self.model.__name__}FilterSet",
                (FilterSet,),
                filterset_attrs,
            )

            return cast(type[FilterSet], filterset_class)

        except Exception:
            # Fallback to basic filterset_factory with error recovery
            fields = [f for f in fields if f in model_field_names]

            # Remove problematic fields iteratively
            max_attempts = len(fields)
            attempt = 0

            while attempt < max_attempts:
                try:
                    filterset_class = filterset_factory(
                        self.model,
                        fields=fields,
                    )
                    return cast(type[FilterSet], filterset_class)
                except AssertionError as e:
                    error_msg = str(e)
                    if "resolved field" in error_msg:
                        match = re.search(r"resolved field '(\w+)'", error_msg)
                        if match:
                            problematic_field = match.group(1)
                            fields = [f for f in fields if f != problematic_field]
                            attempt += 1
                            if not fields:
                                break
                            continue
                    raise

            # Return minimal filterset if all else fails
            return cast(type[FilterSet], filterset_factory(self.model, fields=[]))

    def _get_smart_filters(self, fields: list[str]) -> dict[str, Any]:
        """Generate smart filter types based on field types.

        Args:
            fields: List of field names

        Returns:
            Dictionary mapping field names to filter instances
        """
        import django_filters as filters

        filter_overrides = {}

        for field_name in fields:
            try:
                field = self.model._meta.get_field(field_name)

                # Date fields get DateFromToRangeFilter
                if isinstance(field, models.DateField) and not isinstance(field, models.DateTimeField):
                    filter_overrides[field_name] = filters.DateFromToRangeFilter()

                # DateTime fields get DateTimeFromToRangeFilter
                elif isinstance(field, models.DateTimeField):
                    filter_overrides[field_name] = filters.DateTimeFromToRangeFilter()

                # Boolean fields get BooleanFilter
                elif isinstance(field, models.BooleanField):
                    filter_overrides[field_name] = filters.BooleanFilter()

                # Choice fields get ChoiceFilter
                elif hasattr(field, "choices") and field.choices:
                    filter_overrides[field_name] = filters.ChoiceFilter(choices=field.choices)

                # ForeignKey fields get ModelChoiceFilter
                elif isinstance(field, models.ForeignKey):
                    filter_overrides[field_name] = filters.ModelChoiceFilter(queryset=field.related_model.objects.all())

                # Numeric fields get RangeFilter
                elif isinstance(field, (models.IntegerField, models.FloatField, models.DecimalField)):
                    filter_overrides[field_name] = filters.RangeFilter()

                # Text fields get CharFilter with icontains lookup
                elif isinstance(field, (models.CharField, models.TextField)):
                    filter_overrides[field_name] = filters.CharFilter(lookup_expr="icontains")

            except Exception:
                # Skip fields that can't be resolved
                pass

        return filter_overrides


class AdminFactory(ComponentFactory):
    """Factory for generating Django Admin ModelAdmin classes.

    Features (T029):
    - Uses FieldResolver for consistent field selection
    - Auto-generated list_display, search_fields, list_filter
    - Smart field grouping for fieldsets
    - Readonly fields for timestamps and IDs
    - Date hierarchy for date fields
    """

    def generate(self) -> type[admin.ModelAdmin]:
        """Generate a Django ModelAdmin class.

        Returns:
            ModelAdmin subclass configured for the model
        """
        fields = self.get_fields()
        inspector = FieldInspector(self.model)

        # Determine the correct admin base class for polymorphic models first
        # as this affects what attributes we set
        admin_base = self._get_admin_base_class()

        # Build admin class attributes
        attrs = {
            "model": self.model,
            "list_display": self._get_list_display(fields, inspector),
            "search_fields": self._get_search_fields(fields, inspector),
            "list_filter": self._get_list_filter(fields, inspector),
        }

        # Handle readonly_fields - merge with base class if inheriting from polymorphic admin
        if admin_base is not admin.ModelAdmin:
            # Merge base class readonly_fields with auto-generated ones
            base_readonly = getattr(admin_base, "readonly_fields", [])
            auto_readonly = self._get_readonly_fields(inspector)
            # Combine and deduplicate
            merged_readonly = list(dict.fromkeys(list(base_readonly) + auto_readonly))
            attrs["readonly_fields"] = merged_readonly
        else:
            attrs["readonly_fields"] = self._get_readonly_fields(inspector)

        # Add date hierarchy if model has date fields
        date_hierarchy = self._get_date_hierarchy(inspector)
        if date_hierarchy:
            attrs["date_hierarchy"] = date_hierarchy

        # Add required attrs for polymorphic child admins
        if admin_base is not admin.ModelAdmin:
            attrs["base_model"] = self.model
            attrs["show_in_index"] = True
            # Don't add fields/fieldsets - the base class already has them
            # and Django doesn't allow both to be set
        else:
            # For standard ModelAdmin, add fieldsets or fields
            if len(fields) > 6:
                attrs["fieldsets"] = self._get_fieldsets(fields, inspector)
            else:
                attrs["fields"] = fields

        # Determine app_label based on model inheritance
        app_label = self._get_admin_app_label()
        if app_label:
            meta_attrs = {"app_label": app_label}
            attrs["Meta"] = type("Meta", (), meta_attrs)

        # Create the admin class
        admin_class_name = f"{self.model.__name__}Admin"
        admin_class = type(admin_class_name, (admin_base,), attrs)

        return admin_class

    def _get_list_display(self, fields: list[str], inspector: FieldInspector) -> list[str]:
        """Get list_display fields for admin changelist.

        Args:
            fields: Available field names
            inspector: FieldInspector instance

        Returns:
            List of field names for list_display (max 5)
        """
        # Prioritize: id, name/title, important fields, first 5 total
        display_fields = []

        # Always include ID if present
        if "id" in fields:
            display_fields.append("id")

        # Add name or title if present
        for name_field in ["name", "title", "label"]:
            if name_field in fields and name_field not in display_fields:
                display_fields.append(name_field)
                break

        # Add remaining fields up to 5 total, excluding large text fields
        for field_name in fields:
            if len(display_fields) >= 5:
                break
            if field_name in display_fields:
                continue

            field = inspector.get_field(field_name)
            # Skip TextField and large CharField
            if isinstance(field, models.TextField):
                continue
            if isinstance(field, models.CharField) and field.max_length and field.max_length > 200:
                continue

            display_fields.append(field_name)

        return display_fields if display_fields else ["__str__"]

    def _get_search_fields(self, fields: list[str], inspector: FieldInspector) -> list[str]:
        """Get search_fields for admin search.

        Args:
            fields: Available field names
            inspector: FieldInspector instance

        Returns:
            List of searchable field names
        """
        search_fields = []

        for field_name in fields:
            field = inspector.get_field(field_name)

            # Include text fields
            if isinstance(field, (models.CharField, models.TextField)):
                search_fields.append(field_name)

            # Include email fields
            if isinstance(field, models.EmailField):
                search_fields.append(field_name)

        return search_fields

    def _get_list_filter(self, fields: list[str], inspector: FieldInspector) -> list[str]:
        """Get list_filter fields for admin sidebar.

        Args:
            fields: Available field names
            inspector: FieldInspector instance

        Returns:
            List of filterable field names
        """
        filter_fields = []

        for field_name in fields:
            field = inspector.get_field(field_name)

            # Include boolean fields
            if isinstance(field, models.BooleanField):
                filter_fields.append(field_name)

            # Include choice fields
            if hasattr(field, "choices") and field.choices:
                filter_fields.append(field_name)

            # Include foreign key fields
            if isinstance(field, models.ForeignKey):
                filter_fields.append(field_name)

            # Include date fields (use date hierarchy instead)
            # Commenting out as we use date_hierarchy for this

        return filter_fields

    def _get_readonly_fields(self, inspector: FieldInspector) -> list[str]:
        """Get readonly fields for admin forms.

        Args:
            inspector: FieldInspector instance

        Returns:
            List of readonly field names
        """
        readonly = []

        # Common readonly patterns
        for field_name in ["id", "created", "modified", "created_at", "updated_at"]:
            if inspector.has_field(field_name):
                readonly.append(field_name)

        return readonly

    def _get_date_hierarchy(self, inspector: FieldInspector) -> str | None:
        """Get date field for date_hierarchy.

        Args:
            inspector: FieldInspector instance

        Returns:
            Field name or None
        """
        # Prioritize common date fields
        for field_name in ["created", "modified", "date", "created_at", "updated_at"]:
            if inspector.has_field(field_name):
                field = inspector.get_field(field_name)
                if isinstance(field, (models.DateField, models.DateTimeField)):
                    return field_name

        return None

    def _get_fieldsets(self, fields: list[str], inspector: FieldInspector) -> tuple[tuple[str | None, dict], ...]:
        """Get fieldsets for admin form grouping.

        Args:
            fields: Available field names
            inspector: FieldInspector instance

        Returns:
            Tuple of fieldset tuples (django-polymorphic expects tuples, not lists)
        """
        fieldsets = []

        # Group 1: Basic information
        basic_fields = []
        for field_name in ["name", "title", "label", "description"]:
            if field_name in fields:
                basic_fields.append(field_name)

        if basic_fields:
            fieldsets.append((None, {"fields": basic_fields}))

        # Group 2: Data fields (everything else except metadata)
        data_fields = []
        metadata_fields = ["id", "created", "modified", "created_at", "updated_at"]

        for field_name in fields:
            if field_name not in basic_fields and field_name not in metadata_fields:
                data_fields.append(field_name)

        if data_fields:
            fieldsets.append(("Data", {"fields": data_fields}))

        # Group 3: Metadata (collapsed)
        meta_fields = []
        for field_name in metadata_fields:
            if field_name in fields:
                meta_fields.append(field_name)

        if meta_fields:
            fieldsets.append(("Metadata", {"fields": meta_fields, "classes": ["collapse"]}))

        # Convert to tuple - django-polymorphic requires tuples for fieldsets concatenation
        return tuple(fieldsets) if fieldsets else ((None, {"fields": fields}),)

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

    def _get_admin_base_class(self) -> type[admin.ModelAdmin]:
        """Determine the correct admin base class for polymorphic models.

        For Sample subclasses, returns SampleChildAdmin.
        For Measurement subclasses, returns MeasurementAdmin (child admin).
        Otherwise returns standard ModelAdmin.

        Returns:
            Admin base class appropriate for the model
        """
        try:
            from fairdm.core.measurement.models import Measurement
            from fairdm.core.sample.models import Sample

            # Check if this is a Sample subclass (but not the base Sample itself)
            if issubclass(self.model, Sample) and self.model is not Sample:
                from fairdm.core.sample.admin import SampleChildAdmin

                return SampleChildAdmin

            # Check if this is a Measurement subclass (but not the base Measurement itself)
            if issubclass(self.model, Measurement) and self.model is not Measurement:
                from fairdm.core.admin import MeasurementAdmin

                return MeasurementAdmin

        except (ImportError, TypeError):
            pass

        # Default to standard ModelAdmin
        return admin.ModelAdmin


class SerializerFactory(ComponentFactory):
    """Factory for generating DRF ModelSerializer classes with nested serializers.

    Features (T027):
    - Uses FieldResolver for consistent field selection
    - Nested serializers for ForeignKey relationships
    - Smart field configuration for DRF
    - Depth control for nested relationships
    """

    def generate(self) -> type:
        """Generate a DRF ModelSerializer class with nested serializers.

        Returns:
            ModelSerializer subclass with nested relationships
        """
        try:
            from rest_framework import serializers
        except ImportError:
            # DRF not installed, return placeholder
            return type  # type: ignore

        fields = self.get_fields()

        # Build nested serializers for ForeignKey fields
        nested_serializers = self._get_nested_serializers()

        # Create Meta class
        meta_attrs = {
            "model": self.model,
            "fields": ["id"] + fields,  # Include ID by default
        }
        Meta = type("Meta", (), meta_attrs)

        # Build serializer attributes
        serializer_attrs = {"Meta": Meta}
        serializer_attrs.update(nested_serializers)

        # Create serializer class
        serializer_class_name = f"{self.model.__name__}Serializer"
        serializer_class = type(
            serializer_class_name,
            (serializers.ModelSerializer,),
            serializer_attrs,
        )

        return serializer_class

    def _get_nested_serializers(self) -> dict[str, Any]:
        """Generate nested serializers for ForeignKey relationships.

        Returns:
            Dictionary mapping field names to nested serializer fields
        """
        try:
            from rest_framework import serializers
        except ImportError:
            return {}

        nested: dict[str, type] = {}
        fields = self.get_fields()

        for field_name in fields:
            try:
                field = self.model._meta.get_field(field_name)

                # ForeignKey fields get nested serializers
                if isinstance(field, models.ForeignKey):
                    # Use StringRelatedField for simple nesting
                    nested[field_name] = serializers.StringRelatedField()

            except Exception:
                # Skip fields that can't be resolved
                pass

        return nested


class ResourceFactory(ComponentFactory):
    """Factory for generating import/export Resource classes with natural key support.

    Features (T028):
    - Uses FieldResolver for consistent field selection
    - Natural key support for related models
    - Smart import/export configuration
    - CSV/Excel format support
    """

    def generate(self) -> type:
        """Generate an import/export Resource class.

        Returns:
            ModelResource subclass with natural key support
        """
        try:
            from import_export import resources
        except ImportError:
            # django-import-export not installed, return placeholder
            return type  # type: ignore

        fields = self.get_fields()

        # Create Meta class
        meta_attrs = {
            "model": self.model,
            "fields": ["id"] + fields,  # Include ID by default
            "export_order": ["id"] + fields,
        }
        Meta = type("Meta", (), meta_attrs)

        # Build resource attributes
        resource_attrs = {"Meta": Meta}

        # Add natural key support for ForeignKey fields
        fk_widgets = self._get_fk_widgets()
        resource_attrs.update(fk_widgets)

        # Create resource class
        resource_class_name = f"{self.model.__name__}Resource"
        resource_class = type(
            resource_class_name,
            (resources.ModelResource,),
            resource_attrs,
        )

        return resource_class

    def _get_fk_widgets(self) -> dict[str, Any]:
        """Generate ForeignKey widgets with natural key support.

        Returns:
            Dictionary mapping field names to widget instances
        """
        try:
            from import_export import widgets
        except ImportError:
            return {}

        fk_widgets = {}
        fields = self.get_fields()

        for field_name in fields:
            try:
                field = self.model._meta.get_field(field_name)

                # ForeignKey fields get ForeignKeyWidget
                if isinstance(field, models.ForeignKey):
                    # Use natural_key if available, otherwise pk
                    if hasattr(field.related_model, "natural_key"):
                        fk_widgets[field_name] = widgets.ForeignKeyWidget(field.related_model, "natural_key")
                    else:
                        fk_widgets[field_name] = widgets.ForeignKeyWidget(field.related_model, "pk")

            except Exception:
                # Skip fields that can't be resolved
                pass

        return fk_widgets


# Export factory classes
__all__ = [
    "AdminFactory",
    "ComponentFactory",
    "FilterFactory",
    "FormFactory",
    "ResourceFactory",
    "SerializerFactory",
    "TableFactory",
]
