from __future__ import annotations

import re

from django import urls
from django.db.models.base import Model as Model


def slugify(text: str) -> str:
    """Convert text to URL-safe slug format.

    Converts CamelCase class names and regular text to lowercase hyphenated slugs.

    Args:
        text: Text to slugify (e.g., "MyPluginName" or "My Plugin Name")

    Returns:
        Lowercase slug with hyphens (e.g., "my-plugin-name")

    Example:
        >>> slugify("MyPluginName")
        'my-plugin-name'
        >>> slugify("Analysis Plugin")
        'analysis-plugin'
    """
    # Convert CamelCase to hyphenated (e.g., "MyPlugin" → "my-plugin")
    text = re.sub(r"(?<!^)(?=[A-Z])", "-", text).lower()
    # Replace spaces and underscores with hyphens
    text = re.sub(r"[\s_]+", "-", text)
    # Remove non-alphanumeric characters except hyphens
    text = re.sub(r"[^a-z0-9-]+", "", text)
    # Remove duplicate hyphens and strip leading/trailing hyphens
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def class_to_slug(name: str | object | type) -> str:
    """Legacy function for backward compatibility.

    Converts class names to slugs. Use slugify() for new code.
    """
    name_str = (name.__name__ if hasattr(name, "__name__") else str(name)) if not isinstance(name, str) else name  # type: ignore[attr-defined,unused-ignore]
    return slugify(name_str)


def check_has_edit_permission(request, instance, **kwargs):
    """Check if the user has permission to edit the object."""
    if request.user.is_superuser:
        return True

    if request.user == instance:
        return True

    if request.user.groups.filter(name="Data Administrators").exists():
        return True

    if instance:
        perm = f"{instance._meta.app_label}.change_{instance._meta.model_name}"
        has_perm = request.user.has_perm(perm, instance)
        return has_perm


def sample_check_has_edit_permission(request, instance, **kwargs):
    """Check if the user has permission to edit the sample object."""
    return True


def reverse(model, view_name, *args, **kwargs):
    namespace = model._meta.model_name.lower()
    kwargs.update({"uuid": model.uuid})
    return urls.reverse(f"{namespace}:{view_name}", args=args, kwargs=kwargs)
