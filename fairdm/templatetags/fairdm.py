import re

from django import template
from django.core.exceptions import FieldDoesNotExist
from django.db import models

# import flatattrs
from django.template.loader import render_to_string
from quantityfield import settings as qsettings

from fairdm import plugins

register = template.Library()
ureg = qsettings.DJANGO_PINT_UNIT_REGISTER
ureg.default_format = ".2f~P"


@register.simple_tag(takes_context=True)
def is_active(context, url):
    if context["request"].path.startswith(url):
        return "active"
    return ""


@register.filter
def unit(unit):
    """Renders HTML of the specified unit"""
    if isinstance(unit, str):
        # if a string is passed, create a unit from it (e.g. "m" or "m/s")
        u = ureg.Unit(unit)
    elif isinstance(unit, ureg.Unit):
        # if a unit is passed, use it directly (e.g. calling the value directly on an instance instance.value.units)
        u = unit

    return f"{u:~H}"


@register.simple_tag
def get_registry_info(model_or_qs):
    if isinstance(model_or_qs, models.QuerySet):  # QuerySet
        return model_or_qs.model.config

    return model_or_qs.config


@register.simple_tag
def display_url(url):
    return url.replace("https://", "").replace("http://", "").replace("www.", "")


@register.simple_tag
def get_field(obj, fname):
    try:
        return obj._meta.get_field(fname)
    except FieldDoesNotExist:
        return None


@register.simple_tag
def get_field_and_value(obj, fname):
    return {
        "field": obj._meta.get_field(fname),
        "value": getattr(obj, fname),
    }


@register.simple_tag
def get_fields(obj, fields):
    return [(obj._meta.get_field(f), getattr(obj, f)) for f in fields]


@register.simple_tag
def edit_url(obj, fields=None):
    url = reverse(f"{obj._meta.model_name}-update", kwargs={"uuid": obj.uuid})  # Adjust the URL name as needed
    if fields:
        return f"{url}?fields={','.join(fields)}"
    return url


@register.simple_tag
def avatar_url(contributor, **kwargs):
    """Renders a default img tag for the given profile. If the profile.image is None, renders a default icon if no image is set."""

    if not contributor:
        # for anonymous users
        return render_to_string("icons/user.svg")

    if contributor.image:
        return contributor.image.url
    else:
        return render_to_string("icons/user.svg")


@register.simple_tag(takes_context=True)
def plugin_url(context, view_name, *args, **kwargs):
    """
    Returns a URL for a plugin view, using the base_object's model name as the namespace.
    """
    return plugins.reverse(context.get("non_polymorphic_object"), view_name, *args, **kwargs)


@register.filter
def normalize_doi(doi):
    """
    Normalize any DOI input to a full https://doi.org/ URL.

    Examples:
        - "10.1000/xyz123" → "https://doi.org/10.1000/xyz123"
        - "doi:10.1000/xyz123" → "https://doi.org/10.1000/xyz123"
        - "https://doi.org/10.1000/xyz123" → "https://doi.org/10.1000/xyz123"

    Returns None if input does not look like a valid DOI.
    """
    if not doi:
        return None

    # Strip whitespace and lowercase DOI scheme
    doi = doi.strip()

    # Remove common prefixes
    doi = re.sub(r"^(doi:|DOI:|https?://(dx\.)?doi\.org/)", "", doi, flags=re.IGNORECASE)

    # Check for valid DOI pattern
    if not re.match(r"^10\.\d{4,9}/\S+$", doi):
        return None

    return f"https://doi.org/{doi}"


@register.filter
def has_perms(permission_obj, perms):
    """
    Check if the user has the provided object permission or is a privileged user.

    """
    return any(perm in permission_obj for perm in perms.split(","))
    # is_privileged = (
    #     permission_obj.user.is_superuser or permission_obj.user.groups.filter(name="Data Administrators").exists()
    # )
    # return has_obj_perms or is_privileged


@register.simple_tag(takes_context=True)
def has_permission(context, perms):
    """
    Check if the user has the specified permission on the given object.
    """
    permission_obj = context.get("user_permissions", [])
    if any(perm in permission_obj for perm in perms.split(",")):
        return True
    user = context.get("user", None)
    if not user:
        return False
    if user.is_superuser:
        return True
    if user.groups.filter(name="Data Administrators").exists():
        return True
