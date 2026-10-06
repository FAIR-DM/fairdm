"""Template tags and filters used across FairDM templates."""

from django import template
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import mark_safe
from literature import utils
from pint.delegates.formatter.plain import PrettyFormatter
from quantityfield import settings as qsettings

from fairdm.utils.markdown import markdownify

register = template.Library()
ureg = qsettings.DJANGO_PINT_UNIT_REGISTER


class MyFormatter(PrettyFormatter):
    """A pint formatter that prints quantities with two decimals and unit symbols."""

    default_format = ".2f~P"

    def format_uncertainty(
        self,
        uncertainty,
        unc_spec: str = "",
        sort_func=None,
        **babel_kwds,
    ) -> str:
        """Format an uncertainty with spaces around the ``±`` sign."""
        unc_spec = unc_spec.replace("~", "")
        return format(uncertainty, unc_spec).replace("±", " ± ")

    def format_measurement(
        self,
        measurement,
        meas_spec="",
        sort_func=None,
        **babel_kwds,
    ) -> str:
        """Format a measurement without the surrounding parentheses."""
        result = super().format_measurement(
            measurement, meas_spec, sort_func, **babel_kwds
        )
        result = result.replace("(", "").replace(")", "")
        return result


@register.simple_tag(takes_context=True)
def is_active(context, url):
    """Return ``"active"`` when the current request path starts with ``url``.

    Args:
        context: The template context, which must hold ``request``.
        url: The path prefix to compare against.

    Returns:
        ``"active"`` or an empty string.
    """
    if context["request"].path.startswith(url):
        return "active"
    return ""


@register.filter
def unit(unit):
    """Render the HTML of a unit.

    Args:
        unit: A unit, or a unit string such as ``"m"`` or ``"m/s"``.

    Returns:
        The unit formatted as HTML with symbols.
    """
    if isinstance(unit, str):
        u = ureg.Unit(unit)
    elif isinstance(unit, ureg.Unit):
        u = unit

    return f"{u:~H}"


@register.simple_tag
def get_registry_info(model_or_qs):
    """Return the registry configuration for a model, an instance or a queryset.

    Returns ``None`` when the model is not registered, because a template asking what the
    registry knows about something is asking, not asserting. Python callers use
    `registry.get_for_model()`, which raises.

    Args:
        model_or_qs: A model class, a model instance or a queryset.

    Returns:
        The model's registry configuration, or ``None`` when it is not registered.
    """
    from fairdm.registry import registry
    from fairdm.registry.exceptions import NotRegisteredError

    if isinstance(model_or_qs, models.QuerySet):
        model = model_or_qs.model
    elif isinstance(model_or_qs, type):
        model = model_or_qs
    else:
        model = type(model_or_qs)

    try:
        return registry.get_for_model(model)
    except NotRegisteredError:
        return None


@register.simple_tag
def display_url(url):
    """Return a URL without its scheme and ``www.`` prefix, for display.

    Args:
        url: The URL to shorten.

    Returns:
        The shortened URL.
    """
    return url.replace("https://", "").replace("http://", "").replace("www.", "")


@register.simple_tag
def get_field(obj, fname):
    """Return a model field by name.

    Args:
        obj: A model instance or class.
        fname: The field name.

    Returns:
        The field, or ``None`` when the model has no such field.
    """
    try:
        return obj._meta.get_field(fname)
    except FieldDoesNotExist:
        return None


@register.simple_tag
def get_field_and_value(obj, fname):
    """Return a model field together with its value on an instance.

    Args:
        obj: The model instance.
        fname: The field name.

    Returns:
        A dict with the ``field`` and its ``value``.
    """
    return {
        "field": obj._meta.get_field(fname),
        "value": getattr(obj, fname),
    }


@register.simple_tag
def get_fields(obj, fields):
    """Return the fields named, each paired with its value on an instance.

    Args:
        obj: The model instance.
        fields: The field names.

    Returns:
        A list of ``(field, value)`` tuples in the order of ``fields``.
    """
    return [(obj._meta.get_field(f), getattr(obj, f)) for f in fields]


@register.simple_tag
def edit_url(obj, fields=None):
    """Return the update URL for an instance.

    Args:
        obj: The model instance, which needs a ``uuid``.
        fields: Field names to restrict the form to, sent as a ``fields`` query parameter.

    Returns:
        The update URL, with the ``fields`` query parameter when ``fields`` is given.
    """
    url = reverse(f"{obj._meta.model_name}-update", kwargs={"uuid": obj.uuid})
    if fields:
        return f"{url}?fields={','.join(fields)}"
    return url


@register.simple_tag
def avatar_url(contributor, **kwargs):
    """Return the contributor's image URL, or the default user icon markup when there is none.

    Args:
        contributor: The contributor, or a falsy value for an anonymous user.
        **kwargs: Ignored.

    Returns:
        The image URL, or the rendered default icon.
    """
    if not contributor:
        return render_to_string("icons/user.svg")

    if contributor.image:
        return contributor.image.url
    else:
        return render_to_string("icons/user.svg")


@register.simple_tag(takes_context=True)
def plugin_url(context, view_name, *args, **kwargs):
    """Return the URL of a plugin view for the current object.

    Deprecated: use ``{% plugin_url %}`` from ``fairdm.contrib.plugins.templatetags.plugin_tags``,
    which replaces this tag.

    Args:
        context: The template context, which supplies the object.
        view_name: The plugin view name.
        *args: Positional arguments for the URL.
        **kwargs: Keyword arguments for the URL.

    Returns:
        The URL, or an empty string when the context holds no object or the plugin is not
        served for it.
    """
    from fairdm.contrib.plugins.utils import reverse

    obj = context.get("non_polymorphic_object")
    if not obj:
        obj = context.get("object")

    if not obj:
        return ""

    try:
        return reverse(obj, view_name, *args, **kwargs)
    except NoReverseMatch:
        return ""


@register.filter
def normalize_doi(doi):
    """Normalize any DOI input to a full https://doi.org/ URL.

    Examples:
        - "10.1000/xyz123" → "https://doi.org/10.1000/xyz123"
        - "doi:10.1000/xyz123" → "https://doi.org/10.1000/xyz123"
        - "https://doi.org/10.1000/xyz123" → "https://doi.org/10.1000/xyz123"

    Args:
        doi: The DOI in any accepted form.

    Returns:
        The DOI URL, or ``None`` if the input does not look like a valid DOI.
    """
    if not doi:
        return None
    return utils.generic.normalize_doi(doi)


@register.filter
def safe_markdown(content):
    """Render markdown to sanitised HTML, safe to output without further escaping.

    Args:
        content: The markdown source.

    Returns:
        The sanitised HTML, marked safe.
    """
    return mark_safe(markdownify(content))


@register.filter
def has_perms(permission_obj, perms):
    """Check whether any of the comma-separated permissions is in the permission object.

    Args:
        permission_obj: A collection of permission names.
        perms: Comma-separated permission names.

    Returns:
        ``True`` when at least one of them is present.
    """
    return any(perm in permission_obj for perm in perms.split(","))


@register.simple_tag(takes_context=True)
def has_permission(context, perms):
    """Check whether the user holds any of the comma-separated permissions.

    Checks the context's ``user_permissions`` first, then falls back to the user's own permissions.

    Args:
        context: The template context.
        perms: Comma-separated permission names.

    Returns:
        ``True`` when at least one permission is held.
    """
    permission_obj = context.get("user_permissions", [])
    if any(perm in permission_obj for perm in perms.split(",")):
        return True
    user = context.get("user", None)
    if not user:
        return False
    return any(user.has_perm(perm) for perm in perms.split(","))


@register.simple_tag
def get_related_field(obj, field_name):
    """Drill down an object's attributes using Django-style double-underscore notation.

    Args:
        obj: The root model instance.
        field_name: A path such as ``"reference__publisher__name"``, of any depth.

    Returns:
        A tuple ``(final_obj, final_attr)``: the object holding the last attribute and that
        attribute's name. ``(None, None)`` when an intermediate object is ``None``.

    An attribute missing from the path before the last part raises ``AttributeError``.
    """
    parts = field_name.split("__")
    current = obj

    for part in parts[:-1]:
        current = getattr(current, part)
        if current is None:
            return None, None

    final_attr = parts[-1]
    final_obj = current

    return final_obj, final_attr
