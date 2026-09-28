"""Template tags for plugin system."""

from django import template

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
