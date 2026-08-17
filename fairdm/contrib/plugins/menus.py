"""Rendering for a record's local navigation.

The per-record navigation objects used to be declared here and found by the string
``f"{model.__name__}Menu"``. The registry owns them now and creates one on first registration, so
a record type gains navigation by having a plugin registered against it rather than by someone
remembering to add a menu here. A record with no hand-written entry — the location record — used to
make the lookup return ``None`` and the caller append to it.
"""

from typing import Any

from flex_menu.renderers import BaseRenderer


class PluginMenuRenderer(BaseRenderer):
    """Renderer for the horizontal tab navigation on a record's pages."""

    templates: dict[Any, Any] = {
        # Depth 0: Container (root menu)
        0: {"default": "menus/tabs.html"},
        # Depth 1+: Nested items (fallback)
        "default": {
            "leaf": "menus/tab.html",
        },
    }
