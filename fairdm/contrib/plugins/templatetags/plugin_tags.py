"""Template tags for plugin system."""

from django import template

from fairdm.contrib.plugins import access
from fairdm.contrib.plugins.utils import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def plugin_url(context, view_name, *args, **kwargs):
    """Generate the URL for a plugin view of the current object.

    Args:
        context: The template context.
        view_name: The plugin's URL name.
        *args: Positional arguments for URL reversal.
        **kwargs: Keyword arguments for URL reversal.

    Returns:
        The resolved URL, or an empty string when the context has no object.

    Example:
        {% plugin_url 'contributors' %}
        {% plugin_url 'edit-details' pk=object.pk %}
    """
    obj = context.get("non_polymorphic_object")
    if not obj:
        obj = context.get("object")

    if not obj:
        return ""

    return reverse(obj, view_name, *args, **kwargs)


@register.simple_tag(takes_context=True)
def holds_level(context, level, record):
    """Say whether the viewer holds a level on a project, dataset, sample or measurement.

    Decided by :func:`~fairdm.contrib.plugins.access.holds_level`, the decision the record's
    own pages are opened with.

    Args:
        context: The template context, which holds ``request`` on any page a view renders.
        level: ``"view"``, ``"edit"`` or ``"manage"``.
        record: The record asked about.

    Returns:
        True when the viewer holds the level or a higher one. False for a visitor, and where
        the context has no request.

    Example:
        {% holds_level "edit" object as can_edit %}
        {% if can_edit %}...{% endif %}
    """
    request = context.get("request")
    if request is None:
        return False
    return access.holds_level(request, level, record)
