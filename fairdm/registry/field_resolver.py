"""Field resolution utilities for FairDM Registry System.

This module implements the three-tier field resolution algorithm:
1. Custom class provided → use custom class (bypass field resolution)
2. Component-specific fields (e.g., table_fields) → use those
3. Parent fields (e.g., list_fields) → use as fallback
4. Smart defaults (ModelConfiguration.get_default_fields()) → final fallback

See specs/002-fairdm-registry/data-model.md Section 4 for algorithm specification.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fairdm.config import ModelConfiguration


class FieldResolver:
    """Resolves field lists for component generation using 3-tier algorithm."""

    def __init__(self, config: "ModelConfiguration"):
        """Initialize FieldResolver with a ModelConfiguration.

        Args:
            config: The ModelConfiguration instance to resolve fields for
        """
        self.config = config
        self.model = config.model

    def resolve_fields_for_component(self, component_type: str) -> list[str]:
        """Resolve field list for a specific component type.

        Implements 3-tier resolution:
        1. Component-specific fields (e.g., table_fields for component_type="table")
        2. Parent fields (config.list_fields or config.detail_fields depending on component)
        3. Smart defaults (ModelConfiguration.get_default_fields())

        Args:
            component_type: The component type ("form", "table", "filterset", "serializer",
                           "resource", "admin")

        Returns:
            List of field names for the component

        Examples:
            >>> resolver = FieldResolver(config)
            >>> resolver.resolve_fields_for_component("table")
            ['name', 'location', 'collection_date']
        """
        # Map component types to their specific field attributes
        component_field_map = {
            "form": self.config.form_fields,
            "table": self.config.table_fields,
            "filterset": self.config.filterset_fields,
            "serializer": self.config.serializer_fields,
            "resource": self.config.resource_fields,
            "admin": self.config.admin_list_display,
        }

        # Map component types to their parent field attributes
        # All components now use the common 'fields' attribute as parent fallback
        parent_fields = self.config.fields

        # Tier 1: Component-specific fields
        component_fields = component_field_map.get(component_type)
        if component_fields is not None:
            return list(component_fields)  # Ensure it's a list[str]

        # Tier 2: Parent fields
        if parent_fields:  # Check if parent_fields is not None and not empty list
            return list(parent_fields)  # Ensure it's a list[str]

        # Tier 3: Smart defaults
        from fairdm.config import ModelConfiguration

        return list(ModelConfiguration.get_default_fields(self.model))  # Ensure it's a list[str]

    def filter_for_component(
        self,
        component_type: str,
        field_predicate: Callable | None = None,
    ) -> list[str]:
        """Resolve and optionally filter field list for a component.

        Args:
            component_type: The component type ("form", "table", etc.)
            field_predicate: Optional callable that takes (field_name, field) and returns bool

        Returns:
            Filtered list of field names

        Examples:
            >>> # Get only CharField fields for form
            >>> def is_char_field(field_name, field):
            ...     return isinstance(field, models.CharField)
            >>> resolver.filter_for_component("form", is_char_field)
            ['name', 'location']
        """
        fields = self.resolve_fields_for_component(component_type)

        if field_predicate is None:
            return fields

        # Filter fields using predicate
        filtered_fields = []
        for field_name in fields:
            try:
                field = self.model._meta.get_field(field_name)
                if field_predicate(field_name, field):
                    filtered_fields.append(field_name)
            except Exception:
                # If field doesn't exist or predicate fails, skip it
                continue

        return filtered_fields

    def get_field_type(self, field_name: str) -> type | None:
        """Get the Django field type for a field name.

        Args:
            field_name: Name of the field

        Returns:
            Field class type or None if field doesn't exist

        Examples:
            >>> resolver.get_field_type("name")
            <class 'django.db.models.fields.CharField'>
        """
        try:
            field = self.model._meta.get_field(field_name)
            return type(field)
        except Exception:
            return None

    def validate_field_exists(self, field_name: str) -> bool:
        """Check if a field exists on the model.

        Args:
            field_name: Name of the field to check

        Returns:
            True if field exists, False otherwise

        Examples:
            >>> resolver.validate_field_exists("name")
            True
            >>> resolver.validate_field_exists("nonexistent")
            False
        """
        try:
            self.model._meta.get_field(field_name)
            return True
        except Exception:
            return False

    def validate_field_path(self, field_path: str) -> bool:
        """Check if a related field path is valid.

        Validates paths like "related__field" by checking each part.

        Args:
            field_path: Field path with __ separators

        Returns:
            True if path is valid, False otherwise

        Examples:
            >>> resolver.validate_field_path("related__name")
            True
            >>> resolver.validate_field_path("related__nonexistent")
            False
        """
        if "__" not in field_path:
            return self.validate_field_exists(field_path)

        # Validate related field path
        parts = field_path.split("__")
        current_model = self.model

        for i, part in enumerate(parts):
            try:
                field = current_model._meta.get_field(part)

                # If not the last part, get the related model
                if i < len(parts) - 1:
                    if hasattr(field, "related_model"):
                        current_model = field.related_model
                    else:
                        # Not a relation field in the middle of path
                        return False
            except Exception:
                return False

        return True
