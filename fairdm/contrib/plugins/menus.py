"""Renderer for a record's local navigation."""

from typing import Any

from flex_menu import MenuItem
from flex_menu.renderers import BaseRenderer


class PluginTabItem(MenuItem):
    """A record's tab, marked as current on every address its plugin mounts.

    The names of the views the plugin mounts are kept in ``extra_context["view_names"]``,
    because flex_menu builds each request's copy of an item from only a few of its
    attributes and copies that dictionary across.
    """

    def match_url(self) -> bool:
        """Mark the tab when the request resolved to any view of the plugin.

        Returns:
            True when the tab is marked as current.
        """
        view_names = self.extra_context.get("view_names")
        match = getattr(self.request, "resolver_match", None)
        if not view_names or match is None:
            return super().match_url()
        self.selected = match.view_name in view_names
        return self.selected


class PluginMenuRenderer(BaseRenderer):
    """Renderer for the horizontal tab navigation on a record's pages."""

    templates: dict[Any, Any] = {
        0: {"default": "menus/tabs.html"},
        "default": {
            "leaf": "menus/tab.html",
        },
    }
