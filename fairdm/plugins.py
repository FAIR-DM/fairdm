from django.db.models.base import Model as Model
from django.urls import path
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from flex_menu import Menu, MenuItem

from fairdm.utils.view_mixins import FairDMBaseMixin, FairDMModelFormMixin, RelatedObjectMixin

EXPLORE = _("Explore")
ACTIONS = _("Actions")
MANAGE = _("Manage")


class PluginMenu(Menu):
    root_template = "fairdm/menus/detail.html"


class PluginSubMenu(Menu):
    root_template = "fairdm/menus/menu_list.html"


class PluginMenuItem(MenuItem):
    template = "fairdm/menus/detail/menu.html"


class GenericPlugin(FairDMBaseMixin, RelatedObjectMixin, SingleObjectTemplateResponseMixin):
    """
    A generic plugin base class providing menu integration and context data enrichment.
    Attributes:
        menu (str): The default menu category for the plugin. (e.g., "Explore", "Actions")
        name (str or None): The name identifier for the plugin.
        icon (str or None): The icon associated with the plugin.
        check (bool): Flag indicating if the menu should be checked/active.
        learn_more (str): Optional additional information or help text.
    Methods:
        get_context_data(**kwargs):
            Extends the context data with menu name and 'learn more' information.
    """

    sidebar_primary = {
        "component": "layouts.plugin.sidebar",
        "collapsible": False,
    }
    sidebar_secondary = False  # hide the seconday sidebar by default
    # sidebar_primary = {"visible": True}
    # sidebar_secondary = {"visible": True}
    menu = None
    name = None
    slug = None
    icon = None
    check = True
    learn_more = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["menu_name"] = self.related_class.__name__ + "Menu"
        context["menu"] = self.menu
        context["learn_more"] = self.learn_more
        return context

    def get_meta_title(self, context):
        context["title"] = self.title
        return f"{self.title} - {self.base_object}"


class ModelFormPlugin(FairDMModelFormMixin, GenericPlugin):
    menu = None

    @property
    def model(self):
        return self.base_object.__class__

    def get_template_names(self):
        if self.template_name is not None:
            return [self.template_name]

        if self.model is not None and self.template_name_suffix is not None:
            return [
                f"{self.model._meta.app_label}/{self.model._meta.object_name.lower()}{self.template_name_suffix}.html",
                # "fairdm_core/sample{self.template_name_suffix}.html",
                "cotton/layouts/plugin/form.html",
            ]
        return super().get_template_names()

    def get_object(self, queryset=None):
        return self.base_object

    def get_success_url(self):
        return self.object.get_absolute_url()


class PluginRegistry:
    def __init__(self, name=""):
        self.name = name
        self.menu = Menu(name=name)
        self.plugins = {
            EXPLORE: [],
            ACTIONS: [],
            MANAGE: [],
        }
        self.public_menu = PluginMenu(
            "Public",
            children=[
                PluginSubMenu(EXPLORE),
                PluginSubMenu(ACTIONS),
            ],
        )
        self.manage_menu = PluginSubMenu("Manage")
        self.menu.extend([self.public_menu, self.manage_menu])

    def register(self, *views, category=EXPLORE):
        if category not in self.plugins:
            raise ValueError(f"Unknown plugin category: {category}")

        # If used as a decorator: @register(category="explore")
        if not views:

            def decorator(view_class):
                self.plugins[category].append(view_class)
                return view_class

            return decorator

        # Used directly: register(View1, View2, category="explore")
        for view in views:
            self.plugins[category].append(view)

    def explore(self, *views):
        """Decorator to register a plugin in the explore category."""
        return self.register(*views, category=EXPLORE)

    def actions(self, *views):
        """Decorator to register a plugin in the actions category."""
        return self.register(*views, category=ACTIONS)

    def manage(self, *views):
        """Decorator to register a plugin in the manage category."""
        return self.register(*views, category=MANAGE)

    def attach_menu(self, plugin, view_name, category):
        menu_item = PluginMenuItem(
            name=plugin.name,
            view_name=view_name,
            icon=plugin.icon,
            check=plugin.check,
        )

        if category == MANAGE:
            self.manage_menu.append(menu_item)
        else:
            self.public_menu.get(category).append(menu_item)

    def get_urls(self):
        """Returns all URL patterns for explore, actions, and manage plugins."""
        urls = []
        urls.extend(self._get_urls(EXPLORE))
        urls.extend(self._get_urls(ACTIONS))
        urls.extend(self._get_urls(MANAGE))
        return urls

    def _get_urls(self, category):
        """Returns all URL patterns for a given plugin list."""
        urls = []
        plugin_list = self.plugins[category]
        for plugin in plugin_list:
            plugin_name = slugify(plugin.name)  # e.g. "overview" for class Overview(GenericPlugin):
            registry_name = slugify(self.name)
            slug = plugin_name if plugin.slug is None else plugin.slug
            url_base = f"{slug}/" if slug else ""
            view_name = f"{registry_name}-{plugin_name}"  # e.g. dataset-overview
            self.attach_menu(plugin, view_name, category=category)
            urls.append(path(url_base, plugin.as_view(menu=self.public_menu), name=view_name))
        return urls


dataset = PluginRegistry(name="Dataset")
project = PluginRegistry(name="Project")
sample = PluginRegistry(name="Sample")
location = PluginRegistry(name="Location")
contributor = PluginRegistry(name="Contributor")
measurement = PluginRegistry(name="Measurement")


def register(to, **kwargs):
    """Decorator to register a page view and add it as an item to the page menu."""

    def decorator(view_class):
        # for registry in to:
        # if registry not in plugins:
        # raise ValueError(f"Invalid registry name: {registry}. Valid names are: {list(plugins.keys())}")
        # plugins[registry].register(view_class, **kwargs)

        return view_class

    return decorator
