import flex_menu
from django import urls
from django.apps import apps
from django.db.models.base import Model as Model
from django.urls import path
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import SingleObjectTemplateResponseMixin

from fairdm.utils.view_mixins import FairDMBaseMixin, FairDMModelFormMixin, RelatedObjectMixin


def check_has_edit_permission(request, instance, **kwargs):
    """
    Check if the user has permission to edit the object.
    This is a placeholder function and should be replaced with actual permission logic.
    """
    if request.user.is_superuser:
        return True

    if request.user == instance:
        return True

    if request.user.groups.filter(name="Data Administrators").exists():
        return True

    if instance:
        perm = f"change_{instance._meta.model_name}"
        return request.user.has_perm(perm, instance)


def sample_check_has_edit_permission(request, instance, **kwargs):
    """
    Check if the user has permission to edit the sample object.
    This is a placeholder function and should be replaced with actual permission logic.
    """
    return True


def reverse(model, view_name, *args, **kwargs):
    namespace = model._meta.model_name.lower()
    kwargs.update({"uuid": model.uuid})  # Ensure the UUID is included in the kwargs
    return urls.reverse(f"{namespace}:{view_name}", args=args, kwargs=kwargs)


class Menu(flex_menu.Menu):
    root_template = "fairdm/menus/detail.html"


class SubMenu(flex_menu.Menu):
    root_template = "fairdm/menus/menu_list.html"


class MenuItem(flex_menu.MenuItem):
    template = "fairdm/menus/detail/menu.html"


class BasePlugin(FairDMBaseMixin, RelatedObjectMixin, SingleObjectTemplateResponseMixin):
    """
    BasePlugin is an abstract base class for creating plugin components within the FairDM framework.
    Attributes:
        base_model (type): The base model associated with the plugin.
        type (str): The type identifier for the plugin.
        sidebar_primary (dict): Configuration for the primary sidebar component.
        sidebar_secondary (bool): Flag to show/hide the secondary sidebar (default: False).
        menu_item (dict): Configuration for the menu item.
        menu (Any): The menu associated with the plugin.
        name (str): The display name of the plugin.
        path (str): The URL path for the plugin.
        icon (str): The icon associated with the plugin.
        check (bool): Flag to enable/disable plugin checks (default: True).
        learn_more (str): Additional information or help text for the plugin.
    """

    base_model = None
    type = None
    sections = {
        "sidebar_primary": "layouts.plugin.sidebar",
        "sidebar_secondary": False,
        "header": "layouts.plugin.header",
        "title": "text.title",
    }
    sidebar_primary_config = {
        "header": {},
    }
    header_config = {
        "actions": [
            "layouts.plugin.components.share",
            # "components.actions.contact",
        ],
    }

    # sidebar_secondary_component = False  # hide the seconday sidebar by default
    menu_item = {}
    menu = None
    name = None
    path = None
    icon = None
    check = True
    learn_more = ""

    @classmethod
    def get_name(cls):
        return cls.name or slugify(cls.__name__)

    @classmethod
    def get_path(cls):
        if cls.path == "":
            return cls.path
        elif cls.path is None:
            return cls.get_name() + "/"
        return cls.path.rstrip("/") + "/"

    @classmethod
    def get_urls(cls, **kwargs):
        url_path = cls.get_path()
        name = cls.get_name()
        return [path(url_path, cls.as_view(**kwargs), name=name)], name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["menu"] = self.menu
        context["learn_more"] = self.learn_more
        return context

    def get_meta_title(self, context):
        context["title"] = self.title
        return f"{self.title} - {self.base_object}"


class BaseFormPlugin(BasePlugin, FairDMModelFormMixin):
    menu = None
    template_name = "fairdm/form_view.html"
    sections = {
        "sidebar_secondary": "sections.sidebar.empty",
    }

    @property
    def model(self):
        return self.base_object.__class__

    def get_template_names(self):
        if self.template_name is not None:
            return [self.template_name]
        cname = self.__class__.__name__.lower()
        if self.model is not None:
            return [
                f"{self.model._meta.app_label}/{self.model._meta.object_name.lower()}{cname}.html",
                # "fairdm_core/sample{self.template_name_suffix}.html",
                "fairdm/form_view.html",
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
    sections = {
        "sidebar_primary": "layouts.plugin.management-sidebar",
    }
    form_config = {
        "submit_button": {
            "text": _("Update"),
        },
    }
    check = check_has_edit_permission

    def get_success_url(self):
        return self.request.path  # Redirect to the same page after saving changes


class PluginRegistry:
    def __init__(self, model: Model | str, management_check=None, **kwargs):
        if isinstance(model, str):
            self.model = apps.get_model(model)
        else:
            self.model = model

        self.name = self.model._meta.model_name
        self.verbose_name = self.model._meta.verbose_name
        self.management_check = management_check or check_has_edit_permission
        self.kwargs = kwargs
        self.menu = Menu(name=self.name)
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
                            name=_(f"Manage {self.verbose_name}"),
                            icon="gear",
                            check=self.management_check,
                            view_name=f"{self.name}:configure",
                        )
                    ],
                ),
                # SubMenu(name=_("Manage Object")),
            ],
        )
        self.manage_menu = SubMenu("Manage")
        self.menu.extend([self.public_menu, self.manage_menu])

    def register(self, *views) -> None:
        # If used as a decorator: @register(category="explore")
        if not views:

            def decorator(view_class):
                self.plugins[view_class.type].append(view_class)
                return view_class

            return decorator

        # Used directly: register(View1, View2, category="explore")
        for view_class in views:
            self.plugins[view_class.type].append(view_class)

    def unregister(self, view):
        """Unregisters a plugin from the registry."""
        for category in self.plugins:
            if view in self.plugins[category]:
                self.plugins[category].remove(view)

    def attach_menu(self, plugin, view_name):
        menu_item = MenuItem(
            **plugin.menu_item,
            view_name=f"{self.name.lower()}:{view_name}",
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
        urls = []
        plugin_list = self.plugins[category]
        for plugin in plugin_list:
            plugin_urls, main_view_name = plugin.get_urls(base_model=self.model, menu=menu, **self.kwargs)
            self.attach_menu(plugin, main_view_name)
            urls.extend(plugin_urls)
        return urls


dataset = PluginRegistry(model="dataset.Dataset")
project = PluginRegistry(model="project.Project")
sample = PluginRegistry(model="sample.Sample", management_check=sample_check_has_edit_permission)
location = PluginRegistry(model="fairdm_location.Point")
contributor = PluginRegistry(
    model="contributors.Contributor",
    sections={
        "header": "contributor.plugin.header",
    },
)
measurement = PluginRegistry(model="measurement.Measurement")


def register(to, **kwargs):
    """Decorator to register a page view and add it as an item to the page menu."""

    def decorator(view_class):
        # for registry in to:
        # if registry not in plugins:
        # raise ValueError(f"Invalid registry name: {registry}. Valid names are: {list(plugins.keys())}")
        # plugins[registry].register(view_class, **kwargs)

        return view_class

    return decorator
