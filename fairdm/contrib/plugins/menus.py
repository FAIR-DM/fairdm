"""Menu and tab data structures for plugin system."""

from typing import Any

from django.utils.translation import gettext_lazy as _
from flex_menu import Menu, MenuItem
from flex_menu.renderers import BaseRenderer


class PluginMenu(Menu):
    """Custom menu class for plugin integration.

    For the moment, it provides no additional functionality beyond the base Menu class, but it serves as a clear marker for plugin-specific menus. In the future, we can easily extend this class to include plugin-specific behavior or attributes without affecting the core menu system.
    """


class PluginTab(MenuItem):
    """Custom menu item class for plugin tabs.

    This class represents a single tab in the plugin menu. It includes
    attributes for label, icon, URL, order, and active state. It can be used
    to define the tabs that appear in the plugin interface.
    """


# ========= START CONCRETE MENU TYPES FOR PLUGINS BELOW THIS LINE =========


overview_context = {"label": _("Overview"), "icon": "overview"}

ProjectMenu = PluginMenu(
    "ProjectMenu",
    children=[PluginTab("Overview", view_name="project-detail", extra_context=overview_context)],
)
DatasetMenu = PluginMenu(
    "DatasetMenu",
    children=[PluginTab("Overview", view_name="dataset-detail", extra_context=overview_context)],
)
SampleMenu = PluginMenu(
    "SampleMenu",
    children=[PluginTab("Overview", view_name="sample-detail", extra_context=overview_context)],
)
PersonMenu = PluginMenu(
    "PersonMenu",
    children=[PluginTab("Overview", view_name="person-detail", extra_context=overview_context)],
)
OrganizationMenu = PluginMenu(
    "OrganizationMenu",
    children=[PluginTab("Overview", view_name="organization-detail", extra_context=overview_context)],
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
