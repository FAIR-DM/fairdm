"""Template tags for plugin system."""

from django import template

from fairdm.contrib.plugins.registry import registry

register = template.Library()


@register.simple_tag(takes_context=True)
def get_plugin_tabs(context, model=None, obj=None):
    """Get list of Tab objects for a model.

    Usage in templates:
        {% get_plugin_tabs model=object|model obj=object as tabs %}

    Args:
        context: Template context
        model: Model class (required, can be passed via object|model filter)
        obj: Model instance (optional, for instance-level checks)

    Returns:
        List of Tab objects sorted by order, then label
    """
    request = context.get("request")

    if not model:
        # Try to get model from object
        if obj:
            model = obj.__class__
        else:
            return []

    if not request:
        return []

    return registry.get_tabs_for_model(model, request, obj)
