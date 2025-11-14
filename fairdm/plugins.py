from __future__ import annotations

import re

import flex_menu
from django import urls
from django.db.models.base import Model as Model
from django.forms.widgets import Media
from django.urls import path
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from flex_menu import MenuItem

from fairdm.views import FairDMBaseMixin, RelatedObjectMixin

# Plugin category constants
EXPLORE = "explore"
ACTIONS = "actions"
MANAGEMENT = "management"


class PluginRegistry:
    """
    Central registry for managing plugins and their associated models.

    Usage:
        from fairdm import plugins

        @plugins.register(Project)
        class MyPlugin(plugins.Explore):
            menu_item = plugins.MenuItem(name="My Plugin", icon="eye")
    """

    def __init__(self):
        # Maps models to their PluggableView classes
        self._model_view_registry: dict[type[Model], type[PluggableView]] = {}

    def register(self, model: type[Model]):
        """
        Register a plugin with a specific model.

        Usage:
            @plugins.register(Project)
            class MyPlugin(FairDMPlugin):
                category = "explore"
                menu_item = PluginMenuItem(name="My Plugin", icon="eye")

        Args:
            model: The Django Model class to register the plugin with

        Returns:
            A decorator function that registers the plugin class
        """

        def decorator(plugin_class):
            if not (isinstance(model, type) and issubclass(model, Model)):
                raise TypeError(f"plugins.register expects a Django Model subclass, got {type(model)}")

            view_class = self.get_or_create_view_for_model(model)
            return view_class.register_plugin(plugin_class)

        return decorator

    def get_or_create_view_for_model(self, model: type[Model]) -> type[PluggableView]:
        """
        Get or create a PluggableView subclass for the given model.

        This function maintains a registry of dynamically created view classes,
        one per model. If a view doesn't exist for the model yet, it creates one.

        Args:
            model: The Django model class to create/retrieve a view for

        Returns:
            A PluggableView subclass configured for the given model
        """
        if model not in self._model_view_registry:
            # Create a new PluggableView subclass for this model
            view_class = type(
                f"{model.__name__}DetailView",
                (PluggableView,),
                {
                    "base_model": model,
                    "model": model,
                },
            )
            self._model_view_registry[model] = view_class

        return self._model_view_registry[model]

    def get_view_for_model(self, model: type[Model]) -> type[PluggableView] | None:
        """
        Get the PluggableView for a model if it exists.

        Args:
            model: The Django model class

        Returns:
            The PluggableView subclass for the model, or None if not found
        """
        return self._model_view_registry.get(model)


# Global plugin registry instance
registry = PluginRegistry()

# Convenience alias for cleaner syntax: plugins.register(Model) instead of plugins.registry.register(Model)
register = registry.register


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

            class Media:
                css = {
                    'all': ('css/my-plugin.css',)
                }
                js = ('js/my-plugin.js',)
    """

    menu_item: PluginMenuItem | None = None
    title = "Unnamed Plugin"

    @property
    def media(self):
        """
        Return the Media object for this plugin if defined.

        Plugins can define a Media inner class with custom CSS and JS files.
        This property checks for the Media class and returns it if available.
        """
        if hasattr(self.__class__, "Media"):
            return Media(self.__class__.Media)
        return Media()

    def get_breadcrumbs(self) -> list[dict[str, str]]:
        """
        Return a list of breadcrumb items for navigation.

        Each breadcrumb is a dictionary with:
        - 'text': The display text for the breadcrumb (required)
        - 'href': The URL for the breadcrumb (optional)

        Breadcrumb logic:
        1. First item: Points to user's base_model list view if user is a contributor
           and object is editable (not published), otherwise points to public list view
        2. Second item: Truncated object.__str__ representation pointing to overview plugin
        3. Additional items: Page title with no href

        Example:
            [
                {'text': 'My Projects', 'href': '/user/projects/'},
                {'text': 'My Research Project', 'href': '/project/abc123/overview/'},
                {'text': 'Datasets'}  # Current page title
            ]

        Returns:
            list[dict[str, str]]: List of breadcrumb dictionaries
        """
        breadcrumbs = []

        # Only generate breadcrumbs if we have a base_object
        if not hasattr(self, "base_object") or not self.base_object:
            return breadcrumbs

        base_object = self.base_object
        model_name = base_object._meta.model_name
        model_verbose_name_plural = base_object._meta.verbose_name_plural

        # Determine if user is contributor and object is editable
        user = getattr(self.request, "user", None)
        is_contributor = user and user.is_authenticated and base_object.is_contributor(user)

        # Check if object is editable (not published/public)
        # For projects, check visibility; for other models, you might check different fields
        is_editable = True
        if hasattr(base_object, "visibility"):
            from fairdm.utils.choices import Visibility

            is_editable = base_object.visibility != Visibility.PUBLIC

        # First breadcrumb: List view
        if is_contributor and is_editable:
            # Point to user's personal list view (fake for now)
            breadcrumbs.append(
                {
                    "text": _(f"My {model_verbose_name_plural.title()}"),
                    "href": f"/user/{model_name}s/",  # Fake URL for now
                }
            )
        else:
            # Point to public list view
            breadcrumbs.append(
                {"text": _(f"All {model_verbose_name_plural.title()}"), "href": urls.reverse(f"{model_name}-list")}
            )

        # Second breadcrumb: Object overview with truncated name
        object_str = str(base_object)
        # Truncate to 50 characters
        if len(object_str) > 30:
            object_str = object_str[:27] + "..."

        breadcrumbs.append(
            {"text": object_str, "href": urls.reverse(f"{model_name}:overview", kwargs={"uuid": base_object.uuid})}
        )

        # Third breadcrumb: Current page title (no href)
        if hasattr(self, "title") and self.title:
            breadcrumbs.append({"text": str(self.title)})

        return breadcrumbs

    def get_context_data(self, **kwargs):
        """Add plugin menus to the template context."""
        context = super().get_context_data(**kwargs)
        context["menus"] = self.menus
        context["breadcrumbs"] = self.get_breadcrumbs()
        context["plugin_media"] = self.media
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
        3. fairdm/plugin.html (fallback)
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
        templates.append("fairdm/plugin.html")

        return templates

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
    "PluginRegistry",
    "check_has_edit_permission",
    "register",
    "registry",
    "reverse",
    "sample_check_has_edit_permission",
]
