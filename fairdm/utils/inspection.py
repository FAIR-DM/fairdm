"""Field inspection and smart defaults for FairDM models.

Provides the FieldInspector class that introspects Django models to detect field types,
suggest widgets and filters, and provide smart defaults for configuration.
"""

import difflib
from typing import Any

from django.db import models
from django.db.models import Field
from django.db.models.constants import LOOKUP_SEP


class FieldInspector:
    """Introspects Django models to provide smart field detection and configuration.

    The FieldInspector analyzes a model's fields and provides intelligent defaults for forms,
    tables, filters, and admin interfaces based on field types and patterns.

    Args:
        model: The Django model class to inspect.

    Attributes:
        ALWAYS_EXCLUDE: Field names always left out of auto-detection.
        EXCLUDE_SUFFIXES: Name suffixes left out of auto-detection.
        NEVER_DEFAULT: Names never included by default, whatever their type.
        DATE_PATTERNS: Name fragments that mark a date field for grouping.
        STATUS_PATTERNS: Name fragments that mark a status field for grouping.
        RELATION_TYPES: The field classes that count as relations.

    Example:
        >>> inspector = FieldInspector(MySampleModel)
        >>> safe_fields = inspector.get_safe_fields()
        >>> date_fields = inspector.get_date_fields()
        >>> widget = inspector.suggest_widget("collected_at")
    """

    ALWAYS_EXCLUDE = [
        "id",
        "polymorphic_ctype",
        "polymorphic_ctype_id",
    ]

    # Matched as suffixes, not substrings: a field named `sample_ptr_note` is a real field.
    EXCLUDE_SUFFIXES = (
        "_ptr",
        "_ptr_id",
    )

    # Named rather than inferred from a substring, so `password_hint` is not caught by accident.
    NEVER_DEFAULT = ("password",)

    DATE_PATTERNS = ["_at", "_date", "date_", "created", "modified", "updated"]
    STATUS_PATTERNS = ["status", "state", "published", "active", "enabled"]
    RELATION_TYPES = (models.ForeignKey, models.OneToOneField, models.ManyToManyField)

    def __init__(self, model: type[models.Model]):
        self.model = model
        self._fields_cache: list[Field[Any, Any]] | None = None
        self._field_map_cache: dict[str, Field[Any, Any]] | None = None

    def _get_all_fields(self) -> list[Field]:
        """Get all fields from the model including inherited ones.

        Returns:
            The model's Django field instances.
        """
        if self._fields_cache is None:
            self._fields_cache = [
                f for f in self.model._meta.get_fields() if isinstance(f, Field)
            ]
        return self._fields_cache

    def _get_field_map(self) -> dict[str, Field]:
        """Get a mapping of field names to field instances.

        Returns:
            A dictionary mapping field names to Field instances.
        """
        if self._field_map_cache is None:
            self._field_map_cache = {f.name: f for f in self._get_all_fields()}
        return self._field_map_cache

    def get_field(self, field_name: str) -> Field | None:
        """Get a specific field by name.

        Args:
            field_name: Name of the field.

        Returns:
            The field instance, or ``None`` if not found.
        """
        return self._get_field_map().get(field_name)

    def has_field(self, field_name: str) -> bool:
        """Check if the model has a field with the given name.

        Args:
            field_name: Name of the field.

        Returns:
            ``True`` if the field exists, ``False`` otherwise.
        """
        return field_name in self._get_field_map()

    def should_exclude_field(self, field_name: str) -> bool:
        """Return whether a field stays out of the framework's own choice of fields.

        This is the one implementation of that rule: the primary key, polymorphic type columns,
        inheritance pointers, automatic timestamps, anything non-editable, reverse relations,
        many-to-many fields with an explicit through model, and the names in NEVER_DEFAULT.

        A portal that wants an excluded field says so in its own field list. This decides only
        what happens when it says nothing.

        Args:
            field_name: Name of the field.

        Returns:
            ``True`` when the field is left out by default.
        """
        if field_name in self.ALWAYS_EXCLUDE or field_name in self.NEVER_DEFAULT:
            return True

        if field_name.endswith(self.EXCLUDE_SUFFIXES):
            return True

        field = self.get_field(field_name)
        if field is None:
            return True

        if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
            return True

        # Django's admin rejects a many-to-many field with an explicit through model
        # (admin.E013), so a generated admin carrying one fails to load.
        if isinstance(field, models.ManyToManyField):
            through = getattr(field.remote_field, "through", None)
            if isinstance(through, str):
                return True
            if through is not None and not through._meta.auto_created:
                return True

        return not field.editable

    def get_default_fields(self, exclude: list[str] | None = None) -> list[str]:
        """Return the framework's own choice of fields for this model.

        This is what a component is built from when a portal declares no field list of its own.
        There is one implementation of it, here, because two copies disagreeing meant the API and
        the admin could show different default fields for the same model.

        Args:
            exclude: Field names to leave out as well.

        Returns:
            The default field names.
        """
        exclude = exclude or []
        safe_fields = []

        for field in self._get_all_fields():
            if field.name in exclude:
                continue
            if not self.should_exclude_field(field.name):
                safe_fields.append(field.name)

        return safe_fields

    def get_safe_fields(self, exclude: list[str] | None = None) -> list[str]:
        """Deprecated name for :meth:`get_default_fields`."""
        return self.get_default_fields(exclude=exclude)

    def resolve_path(self, path: str) -> tuple[bool, str | None]:
        """Walk a field path, one segment at a time.

        Used by registration to refuse a path before it becomes a broken page.

        Args:
            path: A field path using double underscores, such as ``"dataset__name"``.

        Returns:
            Whether the whole path resolves and, when it does not, the reason: either the prefix that
            is not a relation, or ``None`` when a segment does not exist.
        """
        model: Any = self.model
        segments = path.split(LOOKUP_SEP)

        for index, segment in enumerate(segments):
            if model is None:
                prefix = LOOKUP_SEP.join(segments[:index])
                return False, (
                    f"{prefix!r} is not a relation, so the rest of the path cannot "
                    f"resolve"
                )

            if segment not in {f.name for f in model._meta.get_fields()}:
                return False, None

            if index < len(segments) - 1:
                model = model._meta.get_field(segment).related_model

        return True, None

    def close_matches(self, name: str, limit: int = 3) -> list[str]:
        """Return field names close enough to ``name`` to be worth suggesting.

        Args:
            name: The misspelled name.
            limit: The most matches to return.

        Returns:
            Up to ``limit`` similar field names.
        """
        return difflib.get_close_matches(
            name, [f.name for f in self._get_all_fields()], n=limit, cutoff=0.6
        )

    def get_all_field_names(self) -> list[str]:
        """Get all field names on the model.

        Returns:
            All field names.
        """
        return [f.name for f in self._get_all_fields()]

    def get_date_fields(self) -> list[str]:
        """Get fields that represent dates or datetimes.

        Returns:
            The date, datetime and time field names.
        """
        date_fields = []
        for field in self._get_all_fields():
            if isinstance(
                field, (models.DateField, models.DateTimeField, models.TimeField)
            ):
                date_fields.append(field.name)
        return date_fields

    def get_choice_fields(self) -> list[str]:
        """Get fields that have choices defined.

        Returns:
            The names of fields with choices.
        """
        choice_fields = []
        for field in self._get_all_fields():
            if hasattr(field, "choices") and field.choices:
                choice_fields.append(field.name)
        return choice_fields

    def get_relation_fields(self) -> list[str]:
        """Get foreign key and many-to-many relationship fields.

        Returns:
            The relationship field names.
        """
        relation_fields = []
        for field in self._get_all_fields():
            if isinstance(field, tuple(self.RELATION_TYPES)):
                relation_fields.append(field.name)
        return relation_fields

    def get_text_fields(self) -> list[str]:
        """Get text fields (CharField, TextField).

        Returns:
            The text field names.
        """
        text_fields = []
        for field in self._get_all_fields():
            if isinstance(field, (models.CharField, models.TextField)):
                text_fields.append(field.name)
        return text_fields

    def get_boolean_fields(self) -> list[str]:
        """Get boolean fields.

        Returns:
            The boolean field names.
        """
        boolean_fields = []
        for field in self._get_all_fields():
            if isinstance(field, models.BooleanField):
                boolean_fields.append(field.name)
        return boolean_fields

    def get_numeric_fields(self) -> list[str]:
        """Get numeric fields (Integer, Float, Decimal).

        Returns:
            The numeric field names.
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
            The file field names.
        """
        file_fields = []
        for field in self._get_all_fields():
            if isinstance(field, (models.FileField, models.ImageField)):
                file_fields.append(field.name)
        return file_fields

    def suggest_widget(self, field_name: str) -> str | None:
        """Suggest an appropriate widget for a field.

        Args:
            field_name: Name of the field.

        Returns:
            The widget class name, or ``None`` for the default.
        """
        field = self.get_field(field_name)
        if field is None:
            return None

        # DateTimeField subclasses DateField, so it is checked first.
        if isinstance(field, models.DateTimeField):
            return "SplitDateTimeWidget"
        if isinstance(field, models.TimeField):
            return "TimeInput"
        if isinstance(field, models.DateField):
            return "DateInput"

        if isinstance(field, models.ImageField):
            return "ImageWidget"
        if isinstance(field, models.FileField):
            return "FileInput"

        if isinstance(field, models.ForeignKey):
            return "Select2Widget"
        if isinstance(field, models.ManyToManyField):
            return "Select2MultipleWidget"

        if isinstance(field, models.TextField):
            return "Textarea"
        if isinstance(field, models.URLField):
            return "URLInput"
        if isinstance(field, models.EmailField):
            return "EmailInput"

        if hasattr(field, "choices") and field.choices:
            choice_count = len(field.choices)
            if choice_count <= 5:
                return "RadioSelect"
            return "Select"

        if isinstance(field, models.BooleanField):
            return "CheckboxInput"

        return None

    def suggest_filter_type(self, field_name: str) -> str | None:
        """Suggest an appropriate filter type for a field.

        Args:
            field_name: Name of the field.

        Returns:
            The filter class name, or ``None`` for the default.
        """
        field = self.get_field(field_name)
        if field is None:
            return None

        if isinstance(field, (models.DateField, models.DateTimeField)):
            return "DateFromToRangeFilter"

        if isinstance(field, models.BooleanField):
            return "BooleanFilter"

        if hasattr(field, "choices") and field.choices:
            return "MultipleChoiceFilter"

        if isinstance(field, models.ForeignKey):
            return "ModelChoiceFilter"
        if isinstance(field, models.ManyToManyField):
            return "ModelMultipleChoiceFilter"

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

        if isinstance(field, (models.CharField, models.TextField)):
            return "CharFilter"

        return None

    def get_default_list_fields(self) -> list[str]:
        """Get default fields suitable for list and table display.

        Includes the name field if present, plus a few other key fields, excluding long text fields
        and relations.

        Returns:
            The field names suitable for tables.
        """
        candidates = self.get_safe_fields()
        list_fields = []

        priority_fields = ["name", "title", "status", "created", "modified"]

        for field_name in priority_fields:
            if field_name in candidates:
                list_fields.append(field_name)

        for field_name in candidates:
            if field_name in list_fields:
                continue

            field = self.get_field(field_name)
            if isinstance(field, models.TextField):
                continue
            if isinstance(field, models.ManyToManyField):
                continue

            list_fields.append(field_name)

            if len(list_fields) >= 5:
                break

        return list_fields

    def get_default_filter_fields(self) -> list[str]:
        """Get default fields suitable for filtering.

        Includes date fields, choice fields, boolean fields, and foreign keys.

        Returns:
            The field names suitable for filters.
        """
        filter_fields = []

        filter_fields.extend(self.get_date_fields())

        filter_fields.extend(self.get_choice_fields())

        filter_fields.extend(self.get_boolean_fields())

        for field in self._get_all_fields():
            if isinstance(field, models.ForeignKey) and not self.should_exclude_field(
                field.name
            ):
                filter_fields.append(field.name)

        return list(set(filter_fields))

    def group_fields_for_admin(self) -> dict[str, list[str]]:
        """Group fields into logical sections for admin fieldsets.

        Returns:
            A dictionary mapping non-empty section names to field lists.
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

        return {k: v for k, v in groups.items() if v}

    def get_field_info(self, field_name: str) -> dict[str, Any]:
        """Get comprehensive information about a field.

        Args:
            field_name: Name of the field.

        Returns:
            A dictionary with field information, or ``{"exists": False}`` when there is no such field.
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
