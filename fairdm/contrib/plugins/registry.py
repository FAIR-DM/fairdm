"""Plugin registry for managing plugin/model associations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import URLPattern

if TYPE_CHECKING:
    from django.db.models import Model
    from django.http import HttpRequest

    from .base import Plugin
    from .group import PluginGroup
    from .menu import Tab


class PluginRegistry:
    """Central registry tracking model → plugin/group associations.

    This singleton maintains a mapping of Django models to their registered
    plugins and plugin groups. It provides methods for:
    - Registering plugins/groups via decorator
    - Retrieving plugins for a model
    - Aggregating URL patterns
    - Collecting tabs with permission filtering

    Usage:
        from fairdm.contrib.plugins import register_plugin

        @register_plugin(Sample)
        class MyPlugin(Plugin, TemplateView):
            menu = {"label": "My Plugin", "icon": "star", "order": 10}
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        # Maps base models to lists of Plugin/PluginGroup classes
        self._registry: dict[type[Model], list[type[Plugin | PluginGroup]]] = {}

    def register(self, *models: type[Model]):
        """Decorator to register a Plugin or PluginGroup with one or more models.

        Args:
            *models: One or more Django Model classes (base models only)

        Returns:
            Decorator function that adds the plugin/group to the registry

        Raises:
            TypeError: If any model is not a Django Model class
            ValueError: If no models are provided

        Example:
            @register_plugin(Sample)
            class AnalysisPlugin(Plugin, TemplateView):
                check = is_instance_of(RockSample)
                menu = {"label": "Analysis", "order": 10}
        """

        def decorator(plugin_class: type[Plugin | PluginGroup]) -> type[Plugin | PluginGroup]:
            if not models:
                msg = "register_plugin requires at least one model"
                raise ValueError(msg)

            # Validate all models first
            from django.db.models import Model

            for model in models:
                if not (isinstance(model, type) and issubclass(model, Model)):
                    msg = f"register_plugin expects Django Model subclasses, got {type(model)}"
                    raise TypeError(msg)

            # Register the plugin with each model
            for model in models:
                if model not in self._registry:
                    self._registry[model] = []
                self._registry[model].append(plugin_class)

            # Set model attribute for single-model registration
            if len(models) == 1:
                plugin_class.model = models[0]  # type: ignore[attr-defined]
            else:
                plugin_class.model = None  # type: ignore[attr-defined]

            return plugin_class

        return decorator

    def get_plugins_for_model(self, model: type[Model]) -> list[type[Plugin | PluginGroup]]:
        """Get all plugins/groups registered for a model.

        Args:
            model: Django Model class

        Returns:
            List of Plugin and PluginGroup classes registered for the model.
            Returns empty list if no plugins are registered.
        """
        return self._registry.get(model, [])

    def is_registered(self, plugin: type[Plugin | PluginGroup], model: type[Model]) -> bool:
        """Check if a plugin/group is registered for a model.

        Args:
            plugin: Plugin or PluginGroup class
            model: Django Model class

        Returns:
            True if the plugin is registered for the model
        """
        return plugin in self._registry.get(model, [])

    def get_urls_for_model(self, model: type[Model]) -> list[URLPattern]:
        """Get aggregated URL patterns from all plugins/groups for a model.

        Calls get_urls() on each registered plugin/group and concatenates results.

        Args:
            model: Django Model class

        Returns:
            List of URL patterns suitable for include() in Django URL configuration
        """
        url_patterns: list[URLPattern] = []
        for plugin_class in self.get_plugins_for_model(model):
            url_patterns.extend(plugin_class.get_urls())
        return url_patterns

    def get_tabs_for_model(self, model: type[Model], request: HttpRequest, obj: Model | None = None) -> list[Tab]:
        """Collect tabs from all registered plugins/groups with permission filtering.

        Only plugins/groups with a truthy `menu` attribute appear as tabs.
        Tabs are filtered by:
        1. Visibility check (plugin.check callable if present)
        2. Permission check (plugin.has_permission)

        Args:
            model: Django Model class
            request: HTTP request for permission checking
            obj: Model instance (optional, for instance-level checks)

        Returns:
            Sorted list of Tab objects (sorted by order, then label)
        """
        from .menu import Tab

        tabs: list[Tab] = []

        for plugin_class in self.get_plugins_for_model(model):
            # Skip if no menu configuration
            menu = getattr(plugin_class, "menu", None)
            if not menu:
                continue

            # Check visibility filter
            check = getattr(plugin_class, "check", None)
            if check and not check(request, obj):
                continue

            # Check permissions
            # Note: We create a minimal instance just for permission checking
            # The actual view instance will be created later during request handling
            plugin_instance = plugin_class()  # type: ignore[call-arg]
            if not plugin_instance.has_permission(request, obj):  # type: ignore[attr-defined]
                continue

            # Build tab
            label = menu.get("label", plugin_class.__name__)
            icon = menu.get("icon", "")
            order = menu.get("order", 0)

            # Get URL for the tab
            # URL will be resolved in template with obj.pk
            url = ""  # Template will resolve this using {% url %} tag

            # Check if this tab is active (based on current URL path)
            # This will be set in the template context
            is_active = False

            tabs.append(Tab(label=label, icon=icon, url=url, order=order, is_active=is_active))

        # Sort by order, then label
        tabs.sort(key=lambda t: (t.order, t.label))
        return tabs


# Global plugin registry instance
registry = PluginRegistry()
