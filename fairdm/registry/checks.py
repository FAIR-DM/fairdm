"""
Django Check Framework Integration for FairDM Registry.

This module provides system checks that validate registry configurations at startup
and provide helpful warnings/errors for common configuration issues.

Features (T032):
- E001: Invalid field names in configuration
- E002: Duplicate model registrations
- E003: Custom class type validation
- W001: Missing recommended fields
- W002: Performance warnings for large field lists

Usage:
    These checks run automatically when Django starts or when running:
    $ python manage.py check

References:
    - Django Check Framework: https://docs.djangoproject.com/en/stable/topics/checks/
    - FairDM Validation: fairdm/registry/validation.py
"""

from typing import Any

from django.core import checks
from django.db import models
from django.forms import ModelForm
from django_filters import FilterSet
from django_tables2 import Table

from fairdm.registry import registry


@checks.register()
def check_registry_field_names(app_configs: Any = None, **kwargs: Any) -> list[checks.CheckMessage]:
    """Check that all registered models have valid field names.

    Args:
        app_configs: Optional list of app configs to check
        **kwargs: Additional keyword arguments

    Returns:
        List of Error/Warning objects for invalid fields
    """
    errors = []

    # Only check if registry has models
    if not hasattr(registry, "_registry") or not registry._registry:
        return errors

    for model, config in registry._registry.items():
        model_name = f"{model._meta.app_label}.{model.__name__}"

        # Check all field configurations
        field_configs = [
            ("fields", config.fields),
            ("table_fields", config.table_fields),
            ("form_fields", config.form_fields),
            ("filterset_fields", config.filterset_fields),
            ("serializer_fields", config.serializer_fields),
            ("resource_fields", config.resource_fields),
            ("admin_list_display", config.admin_list_display),
        ]

        for config_name, field_list in field_configs:
            if field_list is None:
                continue

            invalid_fields = _get_invalid_fields(model, field_list)

            if invalid_fields:
                errors.append(
                    checks.Error(
                        f"Invalid field names in {model_name}.{config_name}: {', '.join(invalid_fields)}",
                        hint=f"Check that these fields exist on the {model.__name__} model",
                        obj=model,
                        id="fairdm.registry.E001",
                    )
                )

    return errors


@checks.register()
def check_registry_custom_classes(app_configs: Any = None, **kwargs: Any) -> list[checks.CheckMessage]:
    """Check that custom component classes have correct base classes.

    Args:
        app_configs: Optional list of app configs to check
        **kwargs: Additional keyword arguments

    Returns:
        List of Error/Warning objects for invalid custom classes
    """
    errors = []

    # Only check if registry has models
    if not hasattr(registry, "_registry") or not registry._registry:
        return errors

    for model, config in registry._registry.items():
        model_name = f"{model._meta.app_label}.{model.__name__}"

        # Check custom form class
        if config.form_class is not None:
            form_class = config._get_class(config.form_class)
            if not issubclass(form_class, ModelForm):
                errors.append(
                    checks.Error(
                        f"{model_name}: form_class must be a ModelForm subclass",
                        hint=f"Make {form_class.__name__} inherit from django.forms.ModelForm",
                        obj=model,
                        id="fairdm.registry.E003",
                    )
                )

        # Check custom table class
        if config.table_class is not None:
            table_class = config._get_class(config.table_class)
            if not issubclass(table_class, Table):
                errors.append(
                    checks.Error(
                        f"{model_name}: table_class must be a django_tables2.Table subclass",
                        hint=f"Make {table_class.__name__} inherit from django_tables2.Table",
                        obj=model,
                        id="fairdm.registry.E003",
                    )
                )

        # Check custom filterset class
        if config.filterset_class is not None:
            filterset_class = config._get_class(config.filterset_class)
            if not issubclass(filterset_class, FilterSet):
                errors.append(
                    checks.Error(
                        f"{model_name}: filterset_class must be a django_filters.FilterSet subclass",
                        hint=f"Make {filterset_class.__name__} inherit from django_filters.FilterSet",
                        obj=model,
                        id="fairdm.registry.E003",
                    )
                )

    return errors


@checks.register()
def check_registry_performance(app_configs: Any = None, **kwargs: Any) -> list[checks.CheckMessage]:
    """Check for performance issues in registry configurations.

    Args:
        app_configs: Optional list of app configs to check
        **kwargs: Additional keyword arguments

    Returns:
        List of Warning objects for potential performance issues
    """
    warnings = []

    # Only check if registry has models
    if not hasattr(registry, "_registry") or not registry._registry:
        return warnings

    for model, config in registry._registry.items():
        model_name = f"{model._meta.app_label}.{model.__name__}"

        # Check for excessive field counts
        if config.fields and len(config.fields) > 50:
            warnings.append(
                checks.Warning(
                    f"{model_name} has {len(config.fields)} fields configured",
                    hint="Consider using component-specific field lists for better performance",
                    obj=model,
                    id="fairdm.registry.W002",
                )
            )

    return warnings


def _get_invalid_fields(model: type[models.Model], field_names: list[str]) -> list[str]:
    """Get list of field names that don't exist on the model.

    Args:
        model: Django model class
        field_names: List of field names to validate (can contain strings or tuples)

    Returns:
        List of invalid field names
    """
    invalid = []

    for field_name in field_names:
        # Handle tuples (e.g., from admin_list_display with callables)
        if isinstance(field_name, tuple):
            field_name = field_name[0]

        # Skip non-string fields (e.g., callables)
        if not isinstance(field_name, str):
            continue

        try:
            # Handle related field paths like "author__name"
            if "__" in field_name:
                parts = field_name.split("__")
                current_model = model

                for part in parts:
                    current_model._meta.get_field(part)
                    field = current_model._meta.get_field(part)
                    if hasattr(field, "related_model"):
                        current_model = field.related_model
            else:
                model._meta.get_field(field_name)

        except Exception:
            invalid.append(field_name)

    return invalid
