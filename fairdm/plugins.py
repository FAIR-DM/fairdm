from __future__ import annotations

import re

import flex_menu
from django import urls
from django.db.models.base import Model as Model
from django.urls import path
from django.utils.text import slugify
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from flex_menu import MenuItem

from fairdm.views import FairDMBaseMixin, RelatedObjectMixin

# Plugin category constants
EXPLORE = "explore"
ACTIONS = "actions"
MANAGEMENT = "management"


class PluginMenuItem(MenuItem):
    icon: str = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_context.update({"icon": self.icon})


def class_to_slug(name: str | object | type) -> str:
    if not isinstance(name, str):
        name = name.__name__

    # Split CamelCase / PascalCase into words with spaces
    split = re.sub(r"(?<!^)(?=[A-Z])", " ", name)
    # Use Django's slugify
    return slugify(split)


def check_has_edit_permission(request, instance, **kwargs):
    """Check if the user has permission to edit the object."""
    if request.user.is_superuser:
        return True

    if request.user == instance:
        return True

    if request.user.groups.filter(name="Data Administrators").exists():
        return True

    if instance:
        perm = f"change_{instance._meta.model_name}"
        has_perm = request.user.has_perm(perm, instance)
        return has_perm


def sample_check_has_edit_permission(request, instance, **kwargs):
    """Check if the user has permission to edit the sample object."""
    return True


def reverse(model, view_name, *args, **kwargs):
    namespace = model._meta.model_name.lower()
    kwargs.update({"uuid": model.uuid})
    return urls.reverse(f"{namespace}:{view_name}", args=args, kwargs=kwargs)


def register_plugin(view_class):
    """
    Register a plugin with a specific view class.

    Usage:
        @register_plugin(ProjectDetailPage)
        class MyPlugin(Plugin):
            category = "explore"
            menu_item = PluginMenuItem(name="My Plugin", icon="eye")
    """

    def decorator(plugin_class):
        return view_class.register_plugin(plugin_class)

    return decorator


class FairDMPlugin:
    """
    Base mixin for FairDM plugins.

    All plugin classes must inherit from this mixin to access the parent view's
    menus and other functionality.

    Usage:
        class OverviewPlugin(FairDMPlugin, FieldsetsMixin, TemplateView):
            category = "explore"
            menu_item = PluginMenuItem(name="Overview", icon="eye")
            title = "Overview"
    """

    menu_item: PluginMenuItem | None = None
    title = "Unnamed Plugin"

    def get_context_data(self, **kwargs):
        """Add plugin menus to the template context."""
        context = super().get_context_data(**kwargs)
        context["menus"] = self.menus
        return context


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

        Template resolution order:
        1. {model_name}/plugins/{plugin_class_name}.html
        2. plugins/{plugin_class_name}.html
        3. fairdm/detail_view.html (fallback)
        """
        if self.template_name is not None:
            return [self.template_name]

        templates = []
        plugin_class_name = class_to_slug(self.__class__.__name__)

        # First option: model-specific plugin template
        if self.base_model:
            opts = self.base_model._meta
            templates.append(f"{opts.model_name}/plugins/{plugin_class_name}.html")

        # Second option: generic plugin template
        templates.append(f"plugins/{plugin_class_name}.html")

        # Fallback: default detail view template
        templates.append("fairdm/detail_view.html")

        return templates

    # def get_context_data(self, **kwargs):
    #     """Add plugin menus to the template context."""
    #     context = super().get_context_data(**kwargs)
    #     context["menus"] = self.menus
    #     return context

    @classmethod
    def register_plugin(cls, plugin_class):
        """Register a plugin for this view."""
        if plugin_class.category not in ["explore", "actions", "management"]:
            raise ValueError(
                f"Invalid category '{plugin_class.category}'. Must be one of: explore, actions, management"
            )

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

            # Generate URL path based on category
            url_path = f"{plugin_name}/" if plugin.category == "explore" else f"{plugin.category}/{plugin_name}/"

            plugin_url = path(url_path, plugin.as_view(), name=plugin_name)
            urls.append(plugin_url)

            # Add plugin to appropriate menu using .append method if menu_item is defined
            if plugin.menu_item is not None:
                # Set the view_name on the menu item
                plugin.menu_item.view_name = f"{model_name}:{plugin_name}"
                cls.menus[plugin.category].append(plugin.menu_item)

        return urls


# Exports
__all__ = [
    "ACTIONS",
    "EXPLORE",
    "MANAGEMENT",
    "FairDMPlugin",
    "PluggableView",
    "PluginMenuItem",
    "check_has_edit_permission",
    "register_plugin",
    "reverse",
    "sample_check_has_edit_permission",
]
