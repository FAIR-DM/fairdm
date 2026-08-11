"""Plugin registry for managing plugin/model associations."""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

from django.db.models import Model
from django.urls import URLPattern
from flex_menu import Menu, MenuItem, root

if TYPE_CHECKING:
    from .base import Plugin


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
        # Maps base models to lists of Plugin classes
        # Registry format looks like:
        # {
        #     Project: [
        #         (PluginClass, kwargs),
        #         (PluginClass, kwargs),
        #         ...
        #     ],
        #     Dataset: [
        #         (PluginClass, kwargs),
        #         ...
        #     ],
        # }
        # kwargs are passed to the register decorator and can include menu configuration, icons, etc.
        self._registry: dict[type[Model], list[type[Plugin]]] = {}

    def register(self, *models: type[Model], **kwargs):
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
        """

        def decorator(plugin_class: type[Plugin]) -> type[Plugin]:
            if not models:
                msg = "register_plugin requires at least one model"
                raise ValueError(msg)

            for model in models:
                if not (isinstance(model, type) and issubclass(model, Model)):
                    msg = f"register_plugin expects Django Model subclasses, got {type(model)}"
                    raise TypeError(msg)

            # Register the plugin with each model
            for model in models:
                if model not in self._registry:
                    self._registry[model] = []
                self._registry[model].append((plugin_class, kwargs))

            return plugin_class

        return decorator

    def get_plugins_for_model(self, model: type[Model]) -> list[type[Plugin]]:
        """Get all plugins/groups registered for a model.

        Args:
            model: Django Model class

        Returns:
            List of Plugin and PluginGroup classes registered for the model.
            Returns empty list if no plugins are registered.
        """
        return self._registry.get(model, [])

    def get_plugin_menu_for_model(self, model: type[Model]) -> Menu | None:
        """Get the menu configuration for a plugin, if it exists.

        Args:
            model: Django Model class
        Returns:
            Menu object with menu configuration, or None if no menu defined
        """
        menu_name = f"{model.__name__}Menu"
        return root.get(menu_name)

    def get_urls_for_model(self, model: type[Model]) -> list[URLPattern]:
        """Get aggregated URL patterns from all plugins/groups for a model.

        Calls get_urls() on each registered plugin/group and concatenates results.

        Args:
            model: Django Model class

        Returns:
            List of URL patterns suitable for include() in Django URL configuration
        """
        plugin_menu = self.get_plugin_menu_for_model(model)
        url_patterns: list[URLPattern] = []

        for plugin_class, kwargs in itertools.chain(self.get_plugins_for_model(model)):
            plugin_class.registered_model = model  # type: ignore[attr-defined]
            url_patterns.extend(plugin_class.get_urls(menu_class=plugin_menu))
            if tab := self.configure_tab(plugin_class, model, **kwargs):
                plugin_menu.append(tab)
        return url_patterns

    def configure_tab(self, plugin_class: type[Plugin], model: type[Model], **kwargs) -> None:
        """Configure the tab for a plugin based on its menu definition.

        This method resolves the URL for the plugin's tab using the registered
        base model's namespace and updates the tab's view_name accordingly.

        Args:
            plugin_class: The Plugin class to configure
            model: The Django Model class associated with the plugin
        Returns:
            None
        """
        label = kwargs.get("label") or getattr(plugin_class, "page_title", plugin_class.__name__)
        name = plugin_class.get_name()
        view_name = f"{model._meta.model_name.lower()}:{name}"
        return MenuItem(
            label,
            view_name=view_name,
            check=plugin_class.check,
            extra_context={
                "label": label,
                "icon": kwargs.get("icon") or getattr(plugin_class, "page_icon", "circle"),
            },
        )


registry = PluginRegistry()
