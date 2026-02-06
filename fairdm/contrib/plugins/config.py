from __future__ import annotations

import re
from dataclasses import dataclass

from django.db.models.base import Model as Model


@dataclass
class PluginConfig:
    """
    Configuration for a plugin.

    Centralizes all plugin configuration in one place, reducing duplication
    and providing a clear structure for plugin metadata.

    Example:
        config = PluginConfig(
            title=_("Contributors"),
            icon="people",
            category=plugins.EXPLORE,
            url_path="people/",  # Custom URL path
        )
    """

    # Display
    title: str
    icon: str | None = None

    # Menu configuration
    menu: str | None = None  # Menu text (defaults to title if category is set)
    category: str | None = None  # EXPLORE, ACTIONS, MANAGEMENT, or None for no menu

    # URL configuration
    url_path: str | None = None  # Custom URL path (supports Django path patterns like <int:pk>)
    url_name: str | None = None  # Custom URL name (auto-generated if not provided)

    # Permissions
    check: callable | None = None  # Permission check function

    # Documentation
    about: str | None = None  # Description shown on the page
    learn_more: str | None = None  # Link to documentation

    def get_menu_item(self) -> PluginMenuItem | None:
        """
        Generate PluginMenuItem from config.

        Returns None if category is not set (no menu entry desired).
        """
        if self.category is None:
            return None
        return PluginMenuItem(
            name=self.menu or self.title,
            category=self.category,
            icon=self.icon,
        )

    def get_url_name_from_path(self, plugin_name: str) -> str:
        """
        Extract URL name from custom path or use plugin name.

        For paths like "actions/contribution/<int:pk>/edit/",
        generates a sensible name like "contribution-edit".
        """
        if self.url_name:
            return self.url_name

        # If custom path is provided, try to extract meaningful name
        if self.url_path:
            # Remove parameter patterns and clean up
            path_parts = re.sub(r"<[^>]+>", "", self.url_path).strip("/")
            name_parts = [p for p in path_parts.split("/") if p]
            if name_parts:
                return "-".join(name_parts)

        # Fallback to plugin name
        return plugin_name


@dataclass
class PluginMenuItem:
    """
    Configuration for a plugin menu item.

    This dataclass holds the configuration that will be used to create
    a MenuItem instance during plugin registration, avoiding shared state issues.

    Attributes:
        name: Display name for the menu item
        icon: Icon identifier for the menu item
        category: Plugin category (EXPLORE, ACTIONS, or MANAGEMENT)
    """

    name: str
    category: str
    icon: str = ""
