"""Plugin registry for managing plugin/model associations."""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, ClassVar

from django.db.models import Model
from django.urls import URLPattern
from flex_menu import Menu, MenuItem, root

from .access import menu_check

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

    #: How a record is found in an address, when a model declares nothing else. Every core record
    #: but one uses this; the exception is the location record, which has no ``uuid`` field at all.
    DEFAULT_ROUTE = "<str:uuid>"
    DEFAULT_LOOKUP: ClassVar[dict[str, str]] = {"uuid": "uuid"}

    def __init__(self) -> None:
        """Initialize empty registry."""
        # model -> (route fragment, {url kwarg: model field})
        self._addressing: dict[type[Model], tuple[str, dict[str, str]]] = {}
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
            from .checks import validate_models, validate_registration

            validate_models(plugin_class, models)
            for model in models:
                existing = self._registry.setdefault(model, [])
                validate_registration(plugin_class, model, existing)
                existing.append((plugin_class, kwargs))

            return plugin_class

        return decorator

    def declare_addressing(
        self,
        model: type[Model],
        route: str,
        lookup: dict[str, str],
    ) -> None:
        """Declare how a record of ``model`` appears in an address.

        Addressing belongs to the model, not to a registration: two plugins on one record cannot
        disagree about how their shared record is found.

        Args:
            model: the record type
            route: the route fragment, e.g. ``"<str:lon>/<str:lat>"``
            lookup: url kwarg to model field, e.g. ``{"lon": "x", "lat": "y"}``. Explicit in both
                directions, because reverse has to go back the other way.
        """
        missing = [kwarg for kwarg in lookup if f":{kwarg}>" not in route]
        if missing:
            msg = (
                f"declare_addressing({model.__name__}): lookup names {missing} which the route "
                f"{route!r} does not capture"
            )
            raise ValueError(msg)
        self._addressing[model] = (route, dict(lookup))

    def get_addressing(self, model: type[Model]) -> tuple[str, dict[str, str]]:
        """The route fragment and lookup map for a record type."""
        return self._addressing.get(
            model, (self.DEFAULT_ROUTE, dict(self.DEFAULT_LOOKUP))
        )

    def route_for(self, model: type[Model]) -> str:
        """The route fragment a URL configuration mounts this record's plugins beneath."""
        return self.get_addressing(model)[0]

    def lookup_for(self, model: type[Model]) -> dict[str, str]:
        """Url kwarg to model field, for resolving a record and for reversing to it."""
        return self.get_addressing(model)[1]

    def get_plugins_for_model(self, model: type[Model]) -> list[type[Plugin]]:
        """Get all plugins/groups registered for a model.

        Args:
            model: Django Model class

        Returns:
            List of Plugin and PluginGroup classes registered for the model.
            Returns empty list if no plugins are registered.
        """
        return self._registry.get(model, [])

    def get_plugin_menu_for_model(self, model: type[Model]) -> Menu:
        """The navigation object for a record type, created on first use.

        Five of these used to be hand-written in ``menus.py`` and found by the string
        ``f"{model.__name__}Menu"``. A record with none — the location record — made this return
        ``None``, and the caller appended to it unguarded. Owning them here means registering a
        plugin against any record type is enough.
        """
        menu_name = f"{model.__name__}Menu"
        menu = root.get(menu_name)
        if menu is None:
            menu = Menu(menu_name)
            root.append(menu)
        return menu

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
            # The model is passed into get_urls() and bound per mount by as_view(). Assigning it
            # onto the class made the last URL configuration imported win for every mount, so a
            # plugin registered against two records served the wrong one on all but the last.
            url_patterns.extend(
                plugin_class.get_urls(menu_class=plugin_menu, model=model)
            )
            if kwargs.get("menu") is not False:
                plugin_menu.append(self.configure_tab(plugin_class, model, **kwargs))
        self.sort_menu(plugin_menu)
        return url_patterns

    def configure_tab(
        self, plugin_class: type[Plugin], model: type[Model], **kwargs
    ) -> MenuItem:
        """Build the navigation entry for a registration.

        Label, icon and position come from the decorator and nowhere else. The ``menu`` class
        attribute they used to compete with belonged to a navigation system that no longer exists;
        ten plugins declared one that nothing read, and eight registrations passed a position that
        was silently discarded.
        """
        label = kwargs.get("label") or plugin_class.get_name().replace("-", " ").title()
        name = plugin_class.get_name()
        view_name = f"{model._meta.model_name.lower()}:{name}"
        item = MenuItem(
            label,
            view_name=view_name,
            # Never the author's own predicate. The navigation package calls
            # check(request, **kwargs) and catches nothing, so a predicate written to any other
            # signature takes the page down during template rendering. The adapter also routes the
            # decision through can_open(), so an entry is shown only when its destination opens.
            check=menu_check(plugin_class),
            extra_context={
                "label": label,
                "icon": kwargs.get("icon", "circle"),
            },
        )
        # flex_menu appends in call order and has no ordering of its own, so position is carried
        # here and applied once every entry for the record is known.
        item.plugin_order = kwargs.get("order", 0)
        return item

    def sort_menu(self, menu: Menu) -> None:
        """Order a record's entries by declared position rather than registration order."""
        ordered = sorted(
            menu.children, key=lambda child: getattr(child, "plugin_order", 0)
        )
        menu.children = type(menu.children)(ordered)


registry = PluginRegistry()
