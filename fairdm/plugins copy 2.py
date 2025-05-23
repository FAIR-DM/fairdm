from django.db.models.base import Model as Model
from django.urls import path
from django.utils.text import slugify
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from flex_menu import Menu, MenuItem
from meta.views import MetadataMixin

from fairdm.utils.view_mixins import RelatedObjectMixin


class PluginMenus:
    EXPLORE = "Explore"
    ACTIONS = "Actions"
    MANAGE = "Manage"


class PluginMenuItem(MenuItem):
    template = "fairdm/menus/detail/menu.html"


class GenericPlugin(RelatedObjectMixin, MetadataMixin, SingleObjectTemplateResponseMixin):
    """
    A generic plugin base class providing menu integration and context data enrichment.
    Attributes:
        menu (str): The default menu category for the plugin. (e.g., "Explore", "Actions")
        name (str or None): The name identifier for the plugin.
        icon (str or None): The icon associated with the plugin.
        menu_check (bool): Flag indicating if the menu should be checked/active.
        learn_more (str): Optional additional information or help text.
    Methods:
        get_context_data(**kwargs):
            Extends the context data with menu name and 'learn more' information.
    """

    menu = "Explore"
    name = None
    icon = None
    menu_check = True
    learn_more = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["menu_name"] = self.related_class.__name__ + "Menu"
        context["learn_more"] = self.learn_more
        return context


class ModelFormPlugin(GenericPlugin):
    menu = PluginMenus.MANAGE
    form_class = None

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

    def get_form_class(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        if self.form_class:
            return self.form_class
        elif getattr(self.base_object, "config", None):
            return self.base_object.config.get_form_class()
        return super().get_form_class(form_class)

    def get_object(self, queryset=None):
        return self.base_object

    def get_success_url(self):
        return self.object.get_absolute_url()


class PluginRegistry:
    """PluginRegistry is used to manage a registry of plugins for the detail view of a core obejct within the FairDM database. A plugin, in this context, is represented by a view class, which is a class that defines how a certain type of page or action should be displayed or handled in a web application."""

    def __init__(self, name=None):
        self.plugins = []
        self.name = name
        self.menu_name = name.capitalize() + "Menu"
        self.menu = self._build_initial_menu()

    def _build_initial_menu(self):
        return Menu(
            self.menu_name,
            root_template="fairdm/menus/detail.html",
            children=[
                Menu(PluginMenus.EXPLORE),
                Menu(PluginMenus.ACTIONS),
            ],
        )

    def register(self, view_class, **kwargs):
        """Register a page view and add it as an item to the page menu."""
        # view_class = type(f"{view_class.__name__}", (view_class,), kwargs)
        menu_category = getattr(view_class, "menu", PluginMenus.EXPLORE)

        # if an unknown menu is declared, add it to the menu
        # NOTE: This may not be a good idea in the long run, as it may lead to a lot of menu categories
        if menu_category and not self.menu.get(menu_category):
            self.menu.append(Menu(menu_category))

        self.plugins.append(view_class)

    def attach_menu(self, plugin, view_name, **kwargs):
        """Creates a menu item from the view class."""

        if plugin.menu:
            # get the correct menu declared in the plugin class using the django-flex-menu API
            submenu = self.menu.get(plugin.menu)

            # create the menu item for the plugin and add it to the submenu
            submenu.append(
                PluginMenuItem(
                    name=plugin.name,
                    view_name=view_name,
                    icon=plugin.icon,
                    check=plugin.menu_check,
                )
            )

    def get_urls(self):
        """Returns a list of URL patterns for the registered plugins.

        Note:
            - This method is called in urls.py AFTER all plugins have been registered.
            - The order of the plugins in the registry is preserved in the URL patterns.
        """
        urls = []
        for i, plugin in enumerate(self.plugins):
            name = slugify(plugin.name)
            url_base = f"{name}/" if i > 0 else ""
            view_name = f"{self.name}-{name}"
            self.attach_menu(plugin, view_name)
            urls.append(path(f"{url_base}", plugin.as_view(menu=self.menu), name=view_name))
        return urls

    def get_management_urls(self):
        """Returns a list of URL patterns for the registered plugins.

        Note:
            - This method is called in urls.py AFTER all plugins have been registered.
            - The order of the plugins in the registry is preserved in the URL patterns.
        """
        urls = []
        for i, plugin in enumerate(self.plugins):
            name = slugify(plugin.name)
            url_base = f"{name}/" if i > 0 else ""
            view_name = f"{self.name}-{name}-manage"
            self.attach_menu(plugin, view_name)
            urls.append(path(f"{url_base}manage/", plugin.as_view(menu=self.menu), name=view_name))
        return urls


plugins = {
    "project": PluginRegistry(name="project"),
    "dataset": PluginRegistry(name="dataset"),
    "sample": PluginRegistry(name="sample"),
    "contributor": PluginRegistry(name="contributor"),
    "location": PluginRegistry(name="location"),
}


def register(to, **kwargs):
    """Decorator to register a page view and add it as an item to the page menu."""

    def decorator(view_class):
        for registry in to:
            if registry not in plugins:
                raise ValueError(f"Invalid registry name: {registry}. Valid names are: {list(plugins.keys())}")
            plugins[registry].register(view_class, **kwargs)

        return view_class

    return decorator
