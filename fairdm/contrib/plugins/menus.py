"""Renderer for a record's local navigation."""

from typing import Any

from flex_menu.renderers import BaseRenderer


class PluginMenuRenderer(BaseRenderer):
    """Renderer for the horizontal tab navigation on a record's pages."""

    templates: dict[Any, Any] = {
        0: {"default": "menus/tabs.html"},
        "default": {
            "leaf": "menus/tab.html",
        },
    }
