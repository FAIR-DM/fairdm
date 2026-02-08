"""
Field Inspection and Smart Detection for FairDM Models.

This module provides the FieldInspector class that introspects Django models
to automatically detect field types, suggest appropriate widgets, filters,
and provide smart defaults for configuration.
"""

from typing import Any

from django.db import models
from django.db.models import Field


class FieldInspector:
    """Introspects Django models to provide smart field detection and configuration.

    The FieldInspector analyzes a model's fields and provides intelligent defaults
    for forms, tables, filters, and admin interfaces based on field types and patterns.

    Usage:
        inspector = FieldInspector(MySampleModel)
        safe_fields = inspector.get_safe_fields()
        date_fields = inspector.get_date_fields()
        widget = inspector.suggest_widget('collected_at')
    """

    # Fields to always exclude from auto-detection
    ALWAYS_EXCLUDE = [
        "id",
        "polymorphic_ctype",
        "polymorphic_ctype_id",
    ]

    # Field name patterns to exclude
    EXCLUDE_PATTERNS = [
        "_ptr",  # Polymorphic pointer fields
        "_ptr_id",
        "password",  # Security sensitive
    ]

    # Common field name patterns for smart grouping
    DATE_PATTERNS = ["_at", "_date", "date_", "created", "modified", "updated"]
    STATUS_PATTERNS = ["status", "state", "published", "active", "enabled"]
    RELATION_TYPES = (models.ForeignKey, models.OneToOneField, models.ManyToManyField)

    def __init__(self, model: type[models.Model]):
        """Initialize inspector with a Django model.

        Args:
            model: The Django model class to inspect
        """
        self.model = model
        self._fields_cache: list[Field[Any, Any]] | None = None
        self._field_map_cache: dict[str, Field[Any, Any]] | None = None

    def _get_all_fields(self) -> list[Field]:
        """Get all fields from the model including inherited ones.

        Returns:
            List of Django field instances
        """
        if self._fields_cache is None:
            self._fields_cache = [f for f in self.model._meta.get_fields() if isinstance(f, Field)]
        return self._fields_cache

    def _get_field_map(self) -> dict[str, Field]:
        """Get a mapping of field names to field instances.

        Returns:
            Dictionary mapping field names to Field instances
        """
        if self._field_map_cache is None:
            self._field_map_cache = {f.name: f for f in self._get_all_fields()}
        return self._field_map_cache

    def get_field(self, field_name: str) -> Field | None:
        """Get a specific field by name.

        Args:
            field_name: Name of the field

        Returns:
            Field instance or None if not found
        """
        return self._get_field_map().get(field_name)

    def has_field(self, field_name: str) -> bool:
        """Check if the model has a field with the given name.

        Args:
            field_name: Name of the field

        Returns:
            True if field exists, False otherwise
        """
        return field_name in self._get_field_map()

    def should_exclude_field(self, field_name: str) -> bool:
        """Determine if a field should be excluded from auto-detection.

        Fields are excluded if they:
        - Are in ALWAYS_EXCLUDE list
        - Match EXCLUDE_PATTERNS
        - Are auto-generated (auto_now, auto_now_add)
        - Are not editable

        Args:
            field_name: Name of the field to check

        Returns:
            True if field should be excluded
        """
        # Check always exclude list
        if field_name in self.ALWAYS_EXCLUDE:
            return True

        # Check patterns
        if any(pattern in field_name for pattern in self.EXCLUDE_PATTERNS):
            return True

        # Check field properties
        field = self.get_field(field_name)
        if field is None:
            return True

        # Exclude auto-generated fields
        if hasattr(field, "auto_now") and field.auto_now:
            return True
        if hasattr(field, "auto_now_add") and field.auto_now_add:
            return True

        # Exclude ManyToManyFields with custom through models
        # (can't be in forms/fieldsets - Django admin error E013)
        if isinstance(field, models.ManyToManyField):
            try:
                # Check if through model exists and is not auto-created
                if hasattr(field, "remote_field") and hasattr(field.remote_field, "through"):
                    through = field.remote_field.through
                    if through is not None:
                        # String reference means it's explicitly set (not auto-created)
                        if isinstance(through, str):
                            return True
                        # Model class - check if auto_created
                        if hasattr(through, "_meta") and not through._meta.auto_created:
                            return True
            except (AttributeError, TypeError):
                # If we can't determine, be safe and exclude it
                pass

        # Exclude non-editable fields (except ForeignKey which might be editable=False for admin)
        return not field.editable and not isinstance(field, self.RELATION_TYPES)

    def get_safe_fields(self, exclude: list[str] | None = None) -> list[str]:
        """Get list of safe fields suitable for forms, tables, etc.

        Safe fields exclude:
        - Auto-generated fields (id, created, modified)
        - Internal Django fields (polymorphic_ctype, *_ptr)
        - Security-sensitive fields (password)
        - Non-editable fields

        Args:
            exclude: Additional field names to exclude

        Returns:
            List of safe field names
        """
        exclude = exclude or []
        safe_fields = []

        for field in self._get_all_fields():
            if field.name in exclude:
                continue
            if not self.should_exclude_field(field.name):
                safe_fields.append(field.name)

        return safe_fields

    def get_all_field_names(self) -> list[str]:
        """Get all field names on the model.

        Returns:
            List of all field names
        """
        return [f.name for f in self._get_all_fields()]

    def get_date_fields(self) -> list[str]:
        """Get fields that represent dates or datetimes.

        Returns:
            List of date/datetime field names
        """
        date_fields = []
        for field in self._get_all_fields():
            if isinstance(field, (models.DateField, models.DateTimeField, models.TimeField)):
                date_fields.append(field.name)
        return date_fields

    def get_choice_fields(self) -> list[str]:
        """Get fields that have choices defined.

        Returns:
            List of field names with choices
        """
        choice_fields = []
        for field in self._get_all_fields():
            if hasattr(field, "choices") and field.choices:
                choice_fields.append(field.name)
        return choice_fields

    def get_relation_fields(self) -> list[str]:
        """Get foreign key and many-to-many relationship fields.

        Returns:
            List of relationship field names
        """
        relation_fields = []
        for field in self._get_all_fields():
            if isinstance(field, tuple(self.RELATION_TYPES)):
                relation_fields.append(field.name)
        return relation_fields

    def get_text_fields(self) -> list[str]:
        """Get text fields (CharField, TextField).

        Returns:
            List of text field names
        """
        text_fields = []
        for field in self._get_all_fields():
            if isinstance(field, (models.CharField, models.TextField)):
                text_fields.append(field.name)
        return text_fields

    def get_boolean_fields(self) -> list[str]:
        """Get boolean fields.

        Returns:
            List of boolean field names
        """
        boolean_fields = []
        for field in self._get_all_fields():
            if isinstance(field, models.BooleanField):
                boolean_fields.append(field.name)
        return boolean_fields

    def get_numeric_fields(self) -> list[str]:
        """Get numeric fields (Integer, Float, Decimal).

        Returns:
            List of numeric field names
        """
        numeric_fields = []
        for field in self._get_all_fields():
            if isinstance(
                field,
                (
                    models.IntegerField,
                    models.BigIntegerField,
                    models.SmallIntegerField,
                    models.PositiveIntegerField,
                    models.PositiveSmallIntegerField,
                    models.FloatField,
                    models.DecimalField,
                ),
            ):
                numeric_fields.append(field.name)
        return numeric_fields

    def get_file_fields(self) -> list[str]:
        """Get file and image fields.

        Returns:
            List of file field names
        """
        file_fields = []
        for field in self._get_all_fields():
            if isinstance(field, (models.FileField, models.ImageField)):
                file_fields.append(field.name)
        return file_fields

    def suggest_widget(self, field_name: str) -> str | None:
        """Suggest an appropriate widget for a field.

        Args:
            field_name: Name of the field

        Returns:
            Widget class name or None for default
        """
        field = self.get_field(field_name)
        if field is None:
            return None

        # Date/time fields (check DateTime before Date since DateTime is subclass of Date)
        if isinstance(field, models.DateTimeField):
            return "SplitDateTimeWidget"
        if isinstance(field, models.TimeField):
            return "TimeInput"
        if isinstance(field, models.DateField):
            return "DateInput"

        # File fields
        if isinstance(field, models.ImageField):
            return "ImageWidget"
        if isinstance(field, models.FileField):
            return "FileInput"

        # Relationship fields
        if isinstance(field, models.ForeignKey):
            return "Select2Widget"
        if isinstance(field, models.ManyToManyField):
            return "Select2MultipleWidget"

        # Text fields
        if isinstance(field, models.TextField):
            return "Textarea"
        if isinstance(field, models.URLField):
            return "URLInput"
        if isinstance(field, models.EmailField):
            return "EmailInput"

        # Choice fields
        if hasattr(field, "choices") and field.choices:
            choice_count = len(field.choices)
            # Use radio buttons for few choices, select for many
            if choice_count <= 5:
                return "RadioSelect"
            return "Select"

        # Boolean
        if isinstance(field, models.BooleanField):
            return "CheckboxInput"

        return None

    def suggest_filter_type(self, field_name: str) -> str | None:
        """Suggest an appropriate filter type for a field.

        Args:
            field_name: Name of the field

        Returns:
            Filter class name or None for default
        """
        field = self.get_field(field_name)
        if field is None:
            return None

        # Date fields get range filters
        if isinstance(field, (models.DateField, models.DateTimeField)):
            return "DateFromToRangeFilter"

        # Boolean fields
        if isinstance(field, models.BooleanField):
            return "BooleanFilter"

        # Choice fields
        if hasattr(field, "choices") and field.choices:
            return "MultipleChoiceFilter"

        # Foreign keys
        if isinstance(field, models.ForeignKey):
            return "ModelChoiceFilter"
        if isinstance(field, models.ManyToManyField):
            return "ModelMultipleChoiceFilter"

        # Numeric fields
        if isinstance(
            field,
            (
                models.IntegerField,
                models.BigIntegerField,
                models.FloatField,
                models.DecimalField,
            ),
        ):
            return "RangeFilter"

        # Text fields
        if isinstance(field, (models.CharField, models.TextField)):
            return "CharFilter"  # Will use icontains

        return None

    def get_default_list_fields(self) -> list[str]:
        """Get default fields suitable for list/table display.

        Includes name field if present, plus a few other key fields,
        excluding long text fields and relations.

        Returns:
            List of field names suitable for tables
        """
        candidates = self.get_safe_fields()
        list_fields = []

        # Prioritize common fields
        priority_fields = ["name", "title", "status", "created", "modified"]

        for field_name in priority_fields:
            if field_name in candidates:
                list_fields.append(field_name)

        # Add other safe fields up to a reasonable limit
        for field_name in candidates:
            if field_name in list_fields:
                continue

            # Skip text fields and relations for list view
            field = self.get_field(field_name)
            if isinstance(field, models.TextField):
                continue
            if isinstance(field, models.ManyToManyField):
                continue

            list_fields.append(field_name)

            # Limit to ~5 fields for list view
            if len(list_fields) >= 5:
                break

        return list_fields

    def get_default_filter_fields(self) -> list[str]:
        """Get default fields suitable for filtering.

        Includes date fields, choice fields, boolean fields, and foreign keys.

        Returns:
            List of field names suitable for filters
        """
        filter_fields = []

        # Date fields are good for filtering
        filter_fields.extend(self.get_date_fields())

        # Choice fields
        filter_fields.extend(self.get_choice_fields())

        # Boolean fields
        filter_fields.extend(self.get_boolean_fields())

        # Foreign keys (but not M2M to avoid complexity)
        for field in self._get_all_fields():
            if isinstance(field, models.ForeignKey) and not self.should_exclude_field(field.name):
                filter_fields.append(field.name)

        return list(set(filter_fields))  # Remove duplicates

    def group_fields_for_admin(self) -> dict[str, list[str]]:
        """Group fields into logical sections for admin fieldsets.

        Returns:
            Dictionary mapping section names to field lists
        """
        groups: dict[str, list[str]] = {
            "Basic Information": [],
            "Dates": [],
            "Relations": [],
            "Status & Settings": [],
            "Advanced": [],
        }

        safe_fields = self.get_safe_fields()

        for field_name in safe_fields:
            field = self.get_field(field_name)
            if field is None:
                continue

            # Check field patterns
            if any(pattern in field_name for pattern in self.DATE_PATTERNS):
                groups["Dates"].append(field_name)
            elif any(pattern in field_name for pattern in self.STATUS_PATTERNS):
                groups["Status & Settings"].append(field_name)
            elif isinstance(field, tuple(self.RELATION_TYPES)):
                groups["Relations"].append(field_name)
            elif field_name in ["name", "title", "description"]:
                groups["Basic Information"].append(field_name)
            else:
                groups["Advanced"].append(field_name)

        # Remove empty groups
        return {k: v for k, v in groups.items() if v}

    def get_field_info(self, field_name: str) -> dict[str, Any]:
        """Get comprehensive information about a field.

        Args:
            field_name: Name of the field

        Returns:
            Dictionary with field information
        """
        field = self.get_field(field_name)
        if field is None:
            return {"exists": False}

        return {
            "exists": True,
            "name": field.name,
            "type": field.__class__.__name__,
            "verbose_name": str(field.verbose_name),
            "help_text": field.help_text or "",
            "required": not field.blank,
            "editable": field.editable,
            "has_choices": bool(hasattr(field, "choices") and field.choices),
            "is_relation": isinstance(field, tuple(self.RELATION_TYPES)),
            "suggested_widget": self.suggest_widget(field_name),
            "suggested_filter": self.suggest_filter_type(field_name),
        }
