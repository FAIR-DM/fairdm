from __future__ import annotations

import flex_menu
from django.db.models.base import Model as Model
from django.urls import path
from django.views.generic.detail import SingleObjectTemplateResponseMixin

from fairdm.views import FairDMBaseMixin, RelatedObjectMixin

from .config import PluginMenuItem
from .utils import class_to_slug


class PluggableView(FairDMBaseMixin, RelatedObjectMixin, SingleObjectTemplateResponseMixin):
    """Mixin that adds plugin registration and URL generation capabilities to views."""

    menu_item: PluginMenuItem | None = None
    title = "Unnamed Plugin"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Each view class gets its own plugin list
        cls.plugins = []
        # Initialize the three menu types as flex_menu.Menu objects
        cls.menus = {
            "explore": flex_menu.Menu(name="Explore"),
            "actions": flex_menu.Menu(name="Actions"),
            "management": flex_menu.Menu(name="Management"),
        }

    def get_template_names(self):
        """
        Return a list of template names to be used for the plugin view.

        Template resolution order (for polymorphic models):
        1. {actual_model_name}/plugins/{plugin_class_name}.html (e.g., person/plugins/overview.html)
        2. {base_model_name}/plugins/{plugin_class_name}.html (e.g., contributor/plugins/overview.html)
        3. plugins/{plugin_class_name}.html
        4. fairdm/plugin.html (fallback)

        For non-polymorphic models:
        1. {model_name}/plugins/{plugin_class_name}.html
        2. plugins/{plugin_class_name}.html
        3. fairdm/plugin.html (fallback)
        """
        if self.template_name is not None:
            return [self.template_name]

        templates = []
        plugin_class_name = class_to_slug(self.__class__.__name__)

        # Check if we have a base_object and if it's polymorphic
        if hasattr(self, "base_object") and self.base_object:
            actual_model = type(self.base_object)

            # If the actual model is different from base_model, it's polymorphic
            if self.base_model and actual_model != self.base_model:
                # First priority: template for the actual/child model (e.g., person/plugins/overview.html)
                templates.append(f"{actual_model._meta.model_name}/plugins/{plugin_class_name}.html")

                # Second priority: template for the base model (e.g., contributor/plugins/overview.html)
                templates.append(f"{self.base_model._meta.model_name}/plugins/{plugin_class_name}.html")
            elif self.base_model:
                # Non-polymorphic case: just use the base_model
                templates.append(f"{self.base_model._meta.model_name}/plugins/{plugin_class_name}.html")
        elif self.base_model:
            # Fallback if no base_object yet
            templates.append(f"{self.base_model._meta.model_name}/plugins/{plugin_class_name}.html")

        # Generic plugin template
        templates.append(f"plugins/{plugin_class_name}.html")

        # Fallback: default detail view template
        templates.append("fairdm/plugin.html")

        return templates

    @classmethod
    def register_plugin(cls, plugin_class):
        """Register a plugin for this view."""
        # Plugins with a menu_item must have a category
        if hasattr(plugin_class, "menu_item") and plugin_class.menu_item is not None:
            category = plugin_class.menu_item.category
            if category not in ["explore", "actions", "management"]:
                raise ValueError(f"Invalid category '{category}'. Must be one of: explore, actions, management")

        # auto mixin the parent view class with the plugin_class
        if not issubclass(plugin_class, PluggableView):
            plugin_class = type(
                plugin_class.__name__,
                (plugin_class, cls),
                {},
            )

            # Restore the parent's plugins and menus to the new plugin class
            plugin_class.plugins = cls.plugins
            plugin_class.menus = cls.menus

        # Register the plugin
        cls.plugins.append(plugin_class)
        return plugin_class

    @classmethod
    def get_urls(cls):
        """Generate URL patterns for the main view and all its plugins."""
        urls = []

        # Plugin URLs
        for plugin in cls.plugins:
            plugin_name = class_to_slug(plugin.__name__)
            model_name = plugin.base_model._meta.model_name

            # Check if plugin uses new PluginConfig
            config = getattr(plugin, "config", None)
            menu_item = plugin.menu_item if not config else config.get_menu_item()

            # Determine URL path and name
            if config and config.url_path:
                # Custom URL path from config
                url_path = config.url_path
                url_name = config.get_url_name_from_path(plugin_name)
            elif menu_item is None:
                # No menu item - use management category
                url_path = f"management/{plugin_name}/"
                url_name = plugin_name
            else:
                # Standard plugin with menu item
                category = menu_item.category
                url_path = f"{plugin_name}/" if category == "explore" else f"{category}/{plugin_name}/"
                url_name = plugin_name

            # Create URL pattern
            plugin_url = path(url_path, plugin.as_view(), name=url_name)
            urls.append(plugin_url)

            # Check for extra URLs from this plugin
            if hasattr(plugin, "get_extra_urls") and callable(plugin.get_extra_urls):
                extra_urls = plugin.get_extra_urls()
                if extra_urls:
                    urls.extend(extra_urls)

            # Add to menu if menu_item exists
            if menu_item is not None:
                menu_item_instance = flex_menu.MenuItem(
                    name=menu_item.name,
                    view_name=f"{model_name}:{url_name}",
                    extra_context={"icon": menu_item.icon},
                )
                cls.menus[menu_item.category].append(menu_item_instance)

        return urls
