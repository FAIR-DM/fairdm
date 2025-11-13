"""
FairDM Configuration classes for Sample and Measurement registration.

This module provides the base configuration classes and decorators for the
consistent @fairdm.register API pattern.
"""

from typing import Any

from django.forms import ModelForm
from django_filters import FilterSet
from django_tables2 import Table
from import_export.resources import ModelResource


class BaseModelConfig:
    """
    Base configuration class for FairDM model registration.

    This class defines the standard configuration pattern that users should follow
    when registering Sample and Measurement subclasses.

    Usage:
        @fairdm.register
        class MySampleConfig(BaseModelConfig):
            model = MySample
            display_name = "Water Sample"
            list_fields = ["name", "location", "collected_at"]
            detail_fields = ["name", "description", "metadata"]
            filter_fields = ["collected_at", "contributor"]
    """

    # Required attribute - must be set by subclasses
    model: type | None = None

    # Display configuration
    display_name: str | None = None
    description: str | None = None

    # Field configuration
    list_fields: list[str] = []
    """Fields to display in list views and tables"""

    detail_fields: list[str] = []
    """Fields to display in detail forms and views"""

    filter_fields: list[str] = []
    """Fields to include in FilterSet for searching/filtering"""

    private_fields: list[str] = []
    """Fields to exclude from all auto-generated forms and displays"""

    # Override classes - if provided, auto-generation is skipped
    form_class: type[ModelForm] | None = None
    filterset_class: type[FilterSet] | None = None
    table_class: type[Table] | None = None
    resource_class: type[ModelResource] | None = None
    serializer_class: type | None = None

    # Options for auto-generation
    form_options: dict[str, Any] = {}
    filterset_options: dict[str, Any] = {}
    table_options: dict[str, Any] = {}
    resource_options: dict[str, Any] = {}
    serializer_options: dict[str, Any] = {}

    def __init__(self, model_class: type | None = None):
        """Initialize configuration with model class."""
        if model_class:
            self.model = model_class

        if not self.model:
            raise ValueError("Configuration must specify a model class")

        # Set display_name from model if not provided
        if not self.display_name:
            self.display_name = self.model._meta.verbose_name.title()

    def get_display_name(self) -> str:
        """Get the display name for this model."""
        if not self.model:
            return "Unknown Model"
        return self.display_name or self.model._meta.verbose_name.title()

    def get_description(self) -> str:
        """Get the description for this model."""
        if not self.model:
            return "No model specified"
        return self.description or f"Configuration for {self.model.__name__}"

    def get_list_fields(self) -> list[str]:
        """Get fields for list display."""
        if not self.model:
            return []

        if self.list_fields:
            return self.list_fields

        # Default list fields
        default_fields = ["name", "created", "modified"]
        return [
            f.name for f in self.model._meta.fields if f.name in default_fields and f.name not in self.private_fields
        ]

    def get_detail_fields(self) -> list[str]:
        """Get fields for detail forms."""
        if self.detail_fields:
            return self.detail_fields

        # Use list_fields if detail_fields not specified
        return self.get_list_fields()

    def get_filter_fields(self) -> list[str]:
        """Get fields for filtering."""
        if not self.model:
            return []

        if self.filter_fields:
            return self.filter_fields

        # Default filter fields
        default_fields = ["created", "modified"]
        return [
            f.name for f in self.model._meta.fields if f.name in default_fields and f.name not in self.private_fields
        ]

    def has_custom_form(self) -> bool:
        """Check if custom form class is provided."""
        return self.form_class is not None

    def has_custom_filterset(self) -> bool:
        """Check if custom filterset class is provided."""
        return self.filterset_class is not None

    def has_custom_table(self) -> bool:
        """Check if custom table class is provided."""
        return self.table_class is not None

    def has_custom_resource(self) -> bool:
        """Check if custom resource class is provided."""
        return self.resource_class is not None

    def has_custom_serializer(self) -> bool:
        """Check if custom serializer class is provided."""
        return self.serializer_class is not None


class SampleConfig(BaseModelConfig):
    """Base configuration class for Sample subclasses."""

    pass


class MeasurementConfig(BaseModelConfig):
    """Base configuration class for Measurement subclasses."""

    pass
