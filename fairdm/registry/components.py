"""
Component Configuration Classes for FairDM ModelConfiguration.

This module defines the nested configuration dataclasses used within ModelConfiguration
to specify component-specific settings for tables, forms, filters, admin, API, etc.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TableConfig:
    """Configuration for django-tables2 Table generation.

    Attributes:
        fields: Field names to include in table. None = use parent config.fields
        exclude: Field names to exclude from table
        orderable: Which columns are sortable. True = all, False = none, list = specific
        table_class: Full custom Table class (overrides all auto-generation)
    """

    fields: list[str] | None = None
    exclude: list[str] | None = None
    orderable: list[str] | bool = True
    table_class: type | str | None = None


@dataclass
class FormConfig:
    """Configuration for ModelForm generation.

    Attributes:
        fields: Field names to include. None = parent config, "__all__" = all fields
        exclude: Field names to exclude
        widgets: Custom widgets per field {field_name: widget}
        labels: Custom labels per field {field_name: label}
        help_texts: Custom help texts per field
        error_messages: Custom error messages per field
        field_classes: Custom field classes per field
        form_class: Full custom Form class (overrides all auto-generation)
        layout: Crispy forms layout object
    """

    fields: list[str] | str | None = None
    exclude: list[str] | None = None
    widgets: dict[str, Any] | None = None
    labels: dict[str, str] | None = None
    help_texts: dict[str, str] | None = None
    error_messages: dict[str, dict[str, str]] | None = None
    field_classes: dict[str, type] | None = None
    form_class: type | str | None = None
    layout: Any | None = None


@dataclass
class FiltersConfig:
    """Configuration for django-filter FilterSet generation.

    Attributes:
        fields: Field names to create filters for. None = use parent config
        exclude: Field names to exclude from filters
        exact_fields: Fields that use exact match filtering
        range_fields: Fields that use range filtering (dates, numbers)
        search_fields: Fields that use icontains search
        filterset_class: Full custom FilterSet class (overrides all auto-generation)
        filter_overrides: Custom filter types per field {field_name: filter_class}
    """

    fields: list[str] | None = None
    exclude: list[str] | None = None
    exact_fields: list[str] | None = None
    range_fields: list[str] | None = None
    search_fields: list[str] | None = None
    filterset_class: type | str | None = None
    filter_overrides: dict[str, type | str] | None = None


@dataclass
class AdminConfig:
    """Configuration for Django Admin ModelAdmin generation.

    Attributes:
        list_display: Fields to show in admin list view
        list_filter: Fields to filter by in sidebar
        search_fields: Fields to search in admin
        fieldsets: Field grouping. Dict format: {group_name: [fields]} or Django tuple format
        inlines: Inline model admin classes
        readonly_fields: Fields that are read-only in admin
        prepopulated_fields: Fields to auto-populate {target: (source_fields,)}
        list_per_page: Number of items per page in list view
        list_editable: Fields editable directly in list view
        ordering: Default ordering for list view
        date_hierarchy: Field to use for date drill-down
        admin_class: Full custom ModelAdmin class (overrides all auto-generation)
    """

    list_display: list[str] | None = None
    list_filter: list[str] | None = None
    search_fields: list[str] | None = None
    fieldsets: dict[str, list[str]] | list[tuple] | None = None
    inlines: list[Any] | None = None
    readonly_fields: list[str] | None = None
    prepopulated_fields: dict[str, tuple] | None = None
    list_per_page: int = 25
    list_editable: list[str] | None = None
    ordering: list[str] | None = None
    date_hierarchy: str | None = None
    admin_class: type | str | None = None


@dataclass
class APIConfig:
    """Configuration for DRF Serializer generation (when DRF is installed).

    Attributes:
        fields: Fields to include. None = parent config, "__all__" = all
        exclude: Fields to exclude
        read_only: Fields that are read-only
        write_only: Fields that are write-only
        depth: Nested serialization depth (0 = no nesting)
        serializer_class: Full custom Serializer class (overrides all auto-generation)
        extra_kwargs: Additional kwargs for serializer fields
    """

    fields: list[str] | str | None = None
    exclude: list[str] | None = None
    read_only: list[str] | None = None
    write_only: list[str] | None = None
    depth: int = 0
    serializer_class: type | str | None = None
    extra_kwargs: dict[str, dict[str, Any]] | None = None


@dataclass
class ImportConfig:
    """Configuration for import functionality (django-import-export).

    Attributes:
        fields: Fields to allow for import. None = use parent config
        skip_fields: Fields to skip during import
        id_fields: Fields that form a natural key for matching existing records
        resource_class: Full custom Resource class (overrides all auto-generation)
    """

    fields: list[str] | None = None
    skip_fields: list[str] | None = None
    id_fields: list[str] | None = None
    resource_class: type | str | None = None


@dataclass
class ExportConfig:
    """Configuration for export functionality (django-import-export).

    Attributes:
        fields: Fields to include in export. None = parent config, "__all__" = all
        exclude: Fields to exclude from export
        formats: Export formats to enable (e.g., ["csv", "xlsx", "json"])
        resource_class: Full custom Resource class (overrides all auto-generation)
    """

    fields: list[str] | str | None = None
    exclude: list[str] | None = None
    formats: list[str] = field(default_factory=lambda: ["csv", "xlsx"])
    resource_class: type | str | None = None


# Export all config classes
__all__ = [
    "APIConfig",
    "AdminConfig",
    "ExportConfig",
    "FiltersConfig",
    "FormConfig",
    "ImportConfig",
    "TableConfig",
]
