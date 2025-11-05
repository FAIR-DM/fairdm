from __future__ import annotations

import re

import flex_menu
from django import urls
from django.db.models.base import Model as Model
from django.urls import path
from django.utils.text import slugify
from django.views.generic.detail import SingleObjectTemplateResponseMixin

from fairdm.views import FairDMBaseMixin, RelatedObjectMixin

# Plugin category constants
EXPLORE = "explore"
ACTIONS = "actions"
MANAGEMENT = "management"


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
            menu_item = {"name": "My Plugin", "icon": "eye"}
    """

    def decorator(plugin_class):
        return view_class.register_plugin(plugin_class)

    return decorator


class Menu(flex_menu.MenuGroup):
    root_template = "fairdm/menus/detail.html"


class SubMenu(flex_menu.MenuGroup):
    root_template = "fairdm/menus/menu_list.html"


class PluginMixin(FairDMBaseMixin, RelatedObjectMixin, SingleObjectTemplateResponseMixin):
    """Mixin that adds plugin registration and URL generation capabilities to views."""

    menu_item = {}
    title = "Unnamed Plugin"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Each view class gets its own plugin list
        cls.plugins = []
        cls.menus = {
            "explore": SubMenu(name="Explore"),
            "actions": SubMenu(name="Actions"),
            "management": SubMenu(name="Management"),
        }

    @classmethod
    def register_plugin(cls, plugin_class):
        """Register a plugin for this view."""
        if plugin_class.category not in ["explore", "actions", "management"]:
            raise ValueError(
                f"Invalid category '{plugin_class.category}'. Must be one of: explore, actions, management"
            )

        # auto mixin PluginMixin with the plugin_class
        if not issubclass(plugin_class, PluginMixin):
            plugin_class = type(
                plugin_class.__name__,
                (PluginMixin, plugin_class),
                dict(plugin_class.__dict__),
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

        # Main detail view URL
        # urls.append(path("", cls.as_view(), name="detail"))
        print(cls.plugins)
        # Plugin URLs
        for plugin in cls.plugins:
            plugin_name = class_to_slug(plugin.__name__)

            # Generate URL path based on category
            if plugin.category == "explore":
                url_path = f"{plugin_name}/"
            else:
                url_path = f"{plugin.category}/{plugin_name}/"

            plugin_url = path(url_path, plugin.as_view(), name=plugin_name)
            urls.append(plugin_url)

            # Add plugin to appropriate submenu if menu_item is defined
            if plugin.menu_item is not None:
                # Find the submenu by category name (capitalize first letter to match SubMenu names)
                submenu = cls.menus.get(plugin.category)
                submenu.append(
                    flex_menu.MenuLink(
                        **{
                            "view_name": plugin_name,
                            "name": plugin.title,
                            **plugin.menu_item,
                        }
                    )
                )

        return urls


# Exports
__all__ = [
    "ACTIONS",
    "EXPLORE",
    "MANAGEMENT",
    "PluginMixin",
    "check_has_edit_permission",
    "register_plugin",
    "reverse",
    "sample_check_has_edit_permission",
]
