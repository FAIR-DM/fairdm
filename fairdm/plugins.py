from __future__ import annotations

import re
from dataclasses import dataclass

import flex_menu
from django import urls
from django.db.models.base import Model as Model
from django.forms.widgets import Media
from django.urls import path
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import SingleObjectTemplateResponseMixin

from fairdm.views import FairDMBaseMixin, RelatedObjectMixin

# Plugin category constants
EXPLORE = "explore"
ACTIONS = "actions"
MANAGEMENT = "management"


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


class PluginRegistry:
    """
    Central registry for managing plugins and their associated models.

    Usage:
        from fairdm import plugins

        @plugins.register(Project)
        class MyPlugin(plugins.Explore):
            menu_item = plugins.MenuItem(name="My Plugin", icon="view")
    """

    def __init__(self):
        # Maps models to their PluggableView classes
        self._model_view_registry: dict[type[Model], type[PluggableView]] = {}

    def register(self, *models: type[Model]):
        """
        Register a plugin with one or more models.

        Usage:
            # Single model
            @plugins.register(Project)
            class MyPlugin(FairDMPlugin):
                category = "explore"
                menu_item = PluginMenuItem(name="My Plugin", icon="view")

            # Multiple models
            @plugins.register(Project, Dataset, Sample, Measurement)
            class ContributorsPlugin(FairDMPlugin):
                category = "explore"
                menu_item = PluginMenuItem(name="Contributors", icon="people")

        Args:
            *models: One or more Django Model classes to register the plugin with

        Returns:
            A decorator function that registers the plugin class
        """

        def decorator(plugin_class):
            if not models:
                raise ValueError("plugins.register requires at least one model")

            # Validate all models first
            for model in models:
                if not (isinstance(model, type) and issubclass(model, Model)):
                    raise TypeError(f"plugins.register expects Django Model subclasses, got {type(model)}")

            # Register the plugin with each model
            registered_class = None
            for model in models:
                view_class = self.get_or_create_view_for_model(model)
                registered_class = view_class.register_plugin(plugin_class)

            # Return the last registered class (they should all be equivalent)
            return registered_class

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

    Plugins can be configured using either the new PluginConfig approach or
    the legacy attribute approach:

    New way (preferred):
        class OverviewPlugin(FairDMPlugin, TemplateView):
            config = PluginConfig(
                title=_("Overview"),
                icon="view",
                category=plugins.EXPLORE,
            )

    Legacy way (still supported):
        class OverviewPlugin(FairDMPlugin, TemplateView):
            title = "Overview"
            menu_item = PluginMenuItem(name="Overview", icon="view", category=plugins.EXPLORE)
    """

    config: PluginConfig | None = None
    menu_item: PluginMenuItem | None = None
    title: str = "Unnamed Plugin"

    def get_config(self) -> PluginConfig | None:
        """Get the plugin configuration, checking config first then falling back to attributes."""
        if self.config is not None:
            return self.config
        return None

    def get_title(self) -> str:
        """Get the plugin title from config or fallback to title attribute."""
        if self.config is not None:
            return self.config.title
        return self.title

    def get_menu_item(self) -> PluginMenuItem | None:
        """Get the menu item from config or fallback to menu_item attribute."""
        if self.config is not None:
            return self.config.get_menu_item()
        return self.menu_item

    def get_about(self) -> str | None:
        """Get the about text from config or fallback to about attribute."""
        if self.config is not None:
            return self.config.about
        return getattr(self, "about", None)

    def get_learn_more(self) -> str | None:
        """Get the learn_more link from config or fallback to learn_more attribute."""
        if self.config is not None:
            return self.config.learn_more
        return getattr(self, "learn_more", None)

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

        # Determine the namespace - for polymorphic models, use the base model
        # The base_model attribute is set on the PluggableView subclass
        namespace = model_name
        if hasattr(self, "base_model") and self.base_model:
            namespace = self.base_model._meta.model_name

        # Determine if user is contributor and object is editable
        # user = getattr(self.request, "user", None)
        # is_contributor = user and user.is_authenticated and base_object.is_contributor(user)

        # Check if object is editable (not published/public)
        # For projects, check visibility; for other models, you might check different fields
        # is_editable = True
        # if hasattr(base_object, "visibility"):
        #     from fairdm.utils.choices import Visibility

        #     is_editable = base_object.visibility != Visibility.PUBLIC

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
            {"text": object_str, "href": urls.reverse(f"{namespace}:overview", kwargs={"uuid": base_object.uuid})}
        )

        # Third breadcrumb: Current page title (no href)
        title = self.get_title() if hasattr(self, "get_title") else getattr(self, "title", None)
        if title:
            breadcrumbs.append({"text": str(title)})

        return breadcrumbs

    def get_context_data(self, **kwargs):
        """Add plugin menus to the template context."""
        context = super().get_context_data(**kwargs)
        context["menus"] = self.menus
        context["breadcrumbs"] = self.get_breadcrumbs()
        context["plugin_media"] = self.media
        # Add title to context using get_title() method
        if hasattr(self, "get_title"):
            context["title"] = self.get_title()
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


# Exports
__all__ = [
    "ACTIONS",
    "EXPLORE",
    "MANAGEMENT",
    "FairDMPlugin",
    "PluggableView",
    "PluginConfig",
    "PluginMenuItem",
    "PluginRegistry",
    "check_has_edit_permission",
    "register",
    "registry",
    "reverse",
    "sample_check_has_edit_permission",
]
