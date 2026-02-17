"""Template tags for plugin system."""

from django import template

from fairdm.contrib.plugins.registry import registry
from fairdm.contrib.plugins.utils import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def get_plugin_tabs(context, model=None, obj=None):
    """Get list of Tab objects for a model.

    Usage in templates:
        {% get_plugin_tabs model=object|model obj=object as tabs %}

    Args:
        context: Template context
        model: Model class or instance (required, can be passed via object|model filter)
        obj: Model instance (optional, for instance-level checks)

    Returns:
        List of Tab objects sorted by order, then label
    """
    from django.db.models import Model

    request = context.get("request")

    if not model:
        # Try to get model from object
        if obj:
            model = obj.__class__
        else:
            return []

    # If model is an instance, get its class
    if isinstance(model, Model):
        model = model.__class__

    if not request:
        return []

    return registry.get_tabs_for_model(model, request, obj)


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
