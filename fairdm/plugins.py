import flex_menu
from django.db.models.base import Model as Model
from django.urls import path
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import SingleObjectTemplateResponseMixin

from fairdm.utils.view_mixins import FairDMBaseMixin, FairDMModelFormMixin, RelatedObjectMixin


class Menu(flex_menu.Menu):
    root_template = "fairdm/menus/detail.html"


class SubMenu(flex_menu.Menu):
    root_template = "fairdm/menus/menu_list.html"


class MenuItem(flex_menu.MenuItem):
    template = "fairdm/menus/detail/menu.html"


class BasePlugin(FairDMBaseMixin, RelatedObjectMixin, SingleObjectTemplateResponseMixin):
    """
    A generic plugin base class providing menu integration and context data enrichment.
    Attributes:
        menu (str): The default menu category for the plugin. (e.g., "Explore", "Actions")
        menu_item (dict): A dictionary defining the menu item properties.
        check (bool): Flag indicating if the menu should be checked/active.
        learn_more (str): Optional additional information or help text.
    Methods:
        get_context_data(**kwargs):
            Extends the context data with menu name and 'learn more' information.
    """

    type = None
    sidebar_primary = {
        "component": "layouts.plugin.sidebar",
        "collapsible": False,
    }
    sidebar_secondary = False  # hide the seconday sidebar by default
    menu_item = {}
    menu = None
    slug = None  # slug for the URL, if not set, it will be derived from the class name
    icon = None
    check = True
    learn_more = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context["menu_name"] = self.related_class.__name__ + "Menu"
        context["menu"] = self.menu
        context["learn_more"] = self.learn_more
        return context

    def get_meta_title(self, context):
        context["title"] = self.title
        return f"{self.title} - {self.base_object}"


class BaseFormPlugin(FairDMModelFormMixin, BasePlugin):
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


class Explore(BasePlugin):
    type = _("Explore")


class Action(BaseFormPlugin):
    type = _("Actions")


class Management(BaseFormPlugin):
    type = _("Management")
    sidebar_primary = {
        "component": "layouts.plugin.management-sidebar",
        "collapsible": False,
    }


def check_has_edit_permission(request, instance, **kwargs):
    """
    Check if the user has permission to edit the object.
    This is a placeholder function and should be replaced with actual permission logic.
    """
    return request.user.is_superuser
    # return request.user.is_authenticated and request.user.has_perm("change_object", obj=instance)


class PluginRegistry:
    def __init__(self, name=""):
        self.name = name
        self.menu = Menu(name=name)
        self.plugins = {
            Explore.type: [],
            Action.type: [],
            Management.type: [],
        }

        self.public_menu = Menu(
            "Public",
            children=[
                SubMenu(Explore.type),
                SubMenu(
                    Action.type,
                    children=[
                        MenuItem(
                            name=_(f"Manage {name}"),
                            icon="gear",
                            check=check_has_edit_permission,
                            view_name=f"{name.lower()}-configure",
                        )
                    ],
                ),
                # SubMenu(name=_("Manage Object")),
            ],
        )
        self.manage_menu = SubMenu("Manage")
        self.menu.extend([self.public_menu, self.manage_menu])

    def register(self, *views):
        # If used as a decorator: @register(category="explore")
        if not views:

            def decorator(view_class):
                self.plugins[view_class.type].append(view_class)
                return view_class

            return decorator

        # Used directly: register(View1, View2, category="explore")
        for view_class in views:
            self.plugins[view_class.type].append(view_class)

    def attach_menu(self, plugin, view_name):
        menu_item = MenuItem(
            **plugin.menu_item,
            view_name=view_name,
            check=plugin.check,
        )

        if plugin.type == Management.type:
            self.manage_menu.append(menu_item)
        else:
            self.public_menu.get(plugin.type).append(menu_item)

    def get_urls(self):
        """Returns all URL patterns for explore, actions, and manage plugins."""
        urls = []
        urls.extend(self._get_urls(Explore.type, menu=self.public_menu))
        urls.extend(self._get_urls(Action.type, menu=self.public_menu))
        urls.extend(self._get_urls(Management.type, menu=self.manage_menu))
        return urls

    def _get_urls(self, category, menu):
        """Returns all URL patterns for a given plugin list."""
        urls = []
        plugin_list = self.plugins[category]
        for plugin in plugin_list:
            plugin_name = plugin.menu_item.get("name", False) or plugin.__class__.__name__.lower()
            plugin_slug = slugify(plugin_name)  # e.g. "overview" for class Overview(BasePlugin):
            registry_name = slugify(self.name)
            slug = plugin_slug if plugin.slug is None else plugin.slug
            url_base = f"{slug}/" if slug else ""
            view_name = f"{registry_name}-{plugin_slug}"  # e.g. dataset-overview
            self.attach_menu(plugin, view_name)
            urls.append(path(url_base, plugin.as_view(menu=menu), name=view_name))
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
