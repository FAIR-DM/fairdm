from __future__ import annotations

import re

from django import urls
from django.db.models.base import Model as Model
from django.utils.text import slugify


def class_to_slug(name: str | object | type) -> str:
    name_str: str
    if not isinstance(name, str):
        if hasattr(name, "__name__"):
            name_str = name.__name__  # type: ignore[attr-defined,unused-ignore]
        else:
            name_str = str(name)
    else:
        name_str = name

    # Split CamelCase / PascalCase into words with spaces
    split = re.sub(r"(?<!^)(?=[A-Z])", " ", name_str)
    # Use Django's slugify
    return slugify(split)


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
