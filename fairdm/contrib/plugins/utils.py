from __future__ import annotations

from django import urls
from django.db.models.base import Model as Model
from django.utils.text import camel_case_to_spaces
from django.utils.text import slugify as django_slugify


def slugify(text: str) -> str:
    """Convert a class name or phrase to a URL-safe slug.

    Django's own two helpers, rather than hand-rolled rules. The bespoke version inserted a hyphen
    before every capital, so ``URLTestPlugin`` became ``u-r-l-test-plugin`` — and a test asserted
    that as correct.

    Example:
        >>> slugify("URLTestPlugin")
        'url-test-plugin'
        >>> slugify("My Plugin_Name")
        'my-plugin-name'
    """
    return django_slugify(camel_case_to_spaces(text).replace("_", " "))


def class_to_slug(name: str | object | type) -> str:
    """Legacy function for backward compatibility.

    Converts class names to slugs. Use slugify() for new code.
    """
    name_str = (
        (name.__name__ if hasattr(name, "__name__") else str(name))
        if not isinstance(name, str)
        else name
    )  # type: ignore[attr-defined,unused-ignore]
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


def reverse(instance, view_name, *args, **kwargs):
    """Resolve a plugin address for a record.

    The kwargs come from the record's declared addressing. Hardcoding ``uuid`` here is what made a
    record without one unreachable — and invisibly so, because the navigation package filters
    kwargs and then swallows the failure, rendering an empty menu rather than raising.
    """
    from .registration import registry

    namespace = instance._meta.model_name.lower()
    for kwarg, field in registry.lookup_for(type(instance)).items():
        kwargs.setdefault(kwarg, getattr(instance, field))
    return urls.reverse(f"{namespace}:{view_name}", args=args, kwargs=kwargs)
