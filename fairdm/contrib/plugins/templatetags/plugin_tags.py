"""Template tags for plugin system."""

from django import template

from fairdm.contrib.plugins.utils import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def plugin_url(context, view_name, *args, **kwargs):
    """Generate URL for a plugin view within the current object's namespace.

    Usage in templates:
        {% plugin_url 'view-name' %}
        {% plugin_url 'view-name' pk=123 %}

    Args:
        context: Template context
        view_name: Name of the plugin view
        *args: Positional arguments for URL reversal
        **kwargs: Keyword arguments for URL reversal

    Returns:
        Resolved URL string for the plugin view

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
