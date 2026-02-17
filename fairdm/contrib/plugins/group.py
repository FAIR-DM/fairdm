"""PluginGroup composition class for wrapping multiple plugins."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from django.urls import include, path

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.db.models import Model
    from django.http import HttpRequest
    from django.urls import URLPattern

    from .base import Plugin


class PluginGroup:
    """Composition class that wraps multiple Plugin classes into a single feature.

    PluginGroup provides:
    - Shared URL namespace (all plugins under common prefix)
    - Single tab entry (links to default plugin)
    - Group-level permission checking
    - Coordinated plugin registration

    Attributes:
        plugins: Ordered list of wrapped Plugin classes
        url_prefix: Common URL prefix for all wrapped plugins
        permission: Group-level permission (checked before individual plugin perms)
        name: Group identifier (auto-derived from class name if not set)
        menu: Tab configuration dict (same format as Plugin.menu)
        check: Visibility check callable (request, obj) -> bool
        model: Set by registry during registration

    Example:
        @register_plugin(Sample)
        class MetadataGroup(PluginGroup):
            plugins = [MetadataView, MetadataEdit, MetadataDelete]
            url_prefix = "metadata"
            check = is_instance_of(RockSample)
            menu = {
                "label": "Metadata",
                "icon": "database",
                "order": 20,
            }
    """

    # Class attributes
    plugins: ClassVar[list[type[Plugin]]] = []
    url_prefix: ClassVar[str | None] = None
    permission: ClassVar[str | None] = None
    name: ClassVar[str | None] = None
    menu: ClassVar[dict[str, Any] | None] = None
    check: ClassVar[Callable[[HttpRequest, Model | None], bool] | None] = None
    model: ClassVar[type[Model] | None] = None

    @classmethod
    def get_name(cls) -> str:
        """Get the group name (slugified class name if not set).

        Returns:
            Group name used for identification
        """
        if cls.name:
            return cls.name
        from .utils import slugify

        return slugify(cls.__name__)

    @classmethod
    def get_url_prefix(cls) -> str:
        """Get the URL prefix for all wrapped plugins.

        Returns:
            URL prefix (e.g., "metadata" or "actions")
        """
        if cls.url_prefix:
            return cls.url_prefix
        return cls.get_name()

    @classmethod
    def get_urls(cls) -> list[URLPattern]:
        """Generate URL patterns for all wrapped plugins.

        Each plugin's URL patterns are prefixed with the group's url_prefix.

        Returns:
            List of URL patterns with group prefix
        """
        # Collect all plugin URL patterns
        plugin_patterns = []
        for plugin_class in cls.plugins:
            plugin_patterns.extend(plugin_class.get_urls())

        # Wrap them under the group's prefix
        return [
            path(f"{cls.get_url_prefix()}/", include(plugin_patterns)),
        ]

    @classmethod
    def get_default_plugin(cls) -> type[Plugin]:
        """Get the default plugin (first in the list).

        Used for tab linking - clicking the group's tab takes you to the default plugin.

        Returns:
            First Plugin class in the plugins list

        Raises:
            IndexError: If plugins list is empty
        """
        if not cls.plugins:
            msg = f"PluginGroup {cls.__name__} has no plugins"
            raise IndexError(msg)
        return cls.plugins[0]

    @classmethod
    def get_default_url_name(cls) -> str:
        """Get the URL name of the default plugin.

        Returns:
            URL name of the first plugin (for reversal in templates)
        """
        return cls.get_default_plugin().get_name()

    def has_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        """Group-level permission check.

        Checks group-level permission first, then checks if ANY wrapped plugin
        would grant access.

        Args:
            request: HTTP request
            obj: Model instance (optional, for object-level checks)

        Returns:
            True if user has permission to access the group
        """
        # Check group-level permission
        if self.permission and not request.user.has_perm(self.permission):
            return False

        # Check if any wrapped plugin grants access
        for plugin_class in self.plugins:
            plugin_instance = plugin_class()  # type: ignore[call-arg]
            if plugin_instance.has_permission(request, obj):
                return True

        return False
