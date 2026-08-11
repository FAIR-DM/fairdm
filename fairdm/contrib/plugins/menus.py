"""Menu and tab data structures for plugin system."""

from typing import Any

from django.utils.translation import gettext_lazy as _
from flex_menu import Menu, MenuItem
from flex_menu.renderers import BaseRenderer

overview_context = {"label": _("Overview"), "icon": "overview"}

ProjectMenu = Menu(
    "ProjectMenu",
    children=[MenuItem("Overview", view_name="project-detail", extra_context=overview_context)],
)
DatasetMenu = Menu(
    "DatasetMenu",
    children=[MenuItem("Overview", view_name="dataset-detail", extra_context=overview_context)],
)
SampleMenu = Menu(
    "SampleMenu",
    children=[MenuItem("Overview", view_name="sample-detail", extra_context=overview_context)],
)
PersonMenu = Menu(
    "ContributorMenu",
    children=[MenuItem("Overview", view_name="person-detail", extra_context=overview_context)],
)
OrganizationMenu = Menu(
    "OrganizationMenu",
    children=[MenuItem("Overview", view_name="organization-detail", extra_context=overview_context)],
)


class PluginMenuRenderer(BaseRenderer):
    """Renderer for BS5 nav tabs."""

    templates: dict[Any, Any] = {
        # Depth 0: Container (root menu)
        0: {"default": "menus/tabs.html"},
        # Depth 1+: Nested items (fallback)
        "default": {
            "leaf": "menus/tab.html",
        },
    }
