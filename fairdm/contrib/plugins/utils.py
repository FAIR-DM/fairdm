"""Helpers for plugin slugs, edit permission checks and address resolution."""

from __future__ import annotations

from django import urls
from django.db.models.base import Model as Model
from django.utils.text import camel_case_to_spaces
from django.utils.text import slugify as django_slugify


def slugify(text: str) -> str:
    """Convert a class name or phrase to a URL-safe slug.

    Args:
        text: The class name or phrase.

    Returns:
        The slug.

    Example:
        >>> slugify("URLTestPlugin")
        'url-test-plugin'
        >>> slugify("My Plugin_Name")
        'my-plugin-name'
    """
    return django_slugify(camel_case_to_spaces(text).replace("_", " "))


def class_to_slug(name: str | object | type) -> str:
    """Convert a class, an instance or a string to a slug. Prefer ``slugify`` in new code.

    Args:
        name: A string, or an object whose ``__name__`` is used.

    Returns:
        The slug.
    """
    name_str = (
        (name.__name__ if hasattr(name, "__name__") else str(name))
        if not isinstance(name, str)
        else name
    )  # type: ignore[attr-defined,unused-ignore]
    return slugify(name_str)


def check_has_edit_permission(request, instance, **kwargs):
    """Check whether the user may edit the object.

    Args:
        request: The current request.
        instance: The object being edited.
        **kwargs: Unused.

    Returns:
        True for a superuser or the object itself, otherwise the user's change permission
        on the object. None when there is no object.
    """
    if request.user.is_superuser:
        return True

    if request.user == instance:
        return True

    if instance:
        perm = f"{instance._meta.app_label}.change_{instance._meta.model_name}"
        has_perm = request.user.has_perm(perm, instance)
        return has_perm


def sample_check_has_edit_permission(request, instance, **kwargs):
    """Allow editing a sample.

    Args:
        request: The current request.
        instance: The sample.
        **kwargs: Unused.

    Returns:
        Always True.
    """
    return True


NO_DEFAULT = object()


def reverse(instance, view_name, *args, default=NO_DEFAULT, **kwargs):
    """Resolve a plugin address for a record.

    A plugin another portal removed from the record type has no address, so a link to a plugin
    that is not yours should ask with ``default=""`` and be left out when it comes back empty.

    Args:
        instance: The record.
        view_name: The plugin's URL name.
        *args: Positional URL arguments.
        default: What to return when the name does not resolve. Without it the lookup raises.
        **kwargs: Keyword URL arguments. Those in the record's declared addressing are filled in.

    Returns:
        The URL, or ``default`` when the name does not resolve and a default was given.

    Raises:
        NoReverseMatch: The name does not resolve and no default was given.
    """
    from .registration import registry

    # A subtype such as `RockSample` shares its base's namespace ("sample"), so use `type_of` when set.
    model = getattr(instance, "type_of", type(instance))
    namespace = model._meta.model_name.lower()
    for kwarg, field in registry.lookup_for(type(instance)).items():
        kwargs.setdefault(kwarg, getattr(instance, field))
    try:
        return urls.reverse(f"{namespace}:{view_name}", args=args, kwargs=kwargs)
    except urls.NoReverseMatch:
        if default is NO_DEFAULT:
            raise
        return default
