from django.urls import reverse

from fairdm import plugins
from fairdm.registry import registry

from .menus import DropdownLink


def resolve_collection_view(view_name):
    """
    Resolve the collection view for the given instance.
    This function is used to determine the view name for the collection of a specific type.
    """

    def func(request, instance=None, **kwargs):
        if not instance:
            return reverse(view_name)
        return plugins.reverse(instance, view_name)

    return func


def generate_menu_items(items):
    return [
        DropdownLink(
            item["verbose_name_plural"],
            url=resolve_collection_view(f"{item['slug']}-collection"),
        )
        for item in items
    ]


def get_sample_menu_items():
    """Get sample menu items based on the sample type."""
    return generate_menu_items(registry.samples)


def get_measurement_menu_items():
    """Get measurement menu items based on the measurement type."""
    return generate_menu_items(registry.measurements)
