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
    """Track which plugins are registered for each model and how records are addressed.

    The registry builds each model's URL patterns and navigation menu.

    Attributes:
        DEFAULT_ROUTE: The route fragment for a record when its model declares none.
        DEFAULT_LOOKUP: The URL kwarg to model field map used when its model declares none.

    Example:
        Register a plugin for a model::

            from fairdm import plugins


            @plugins.register(Sample, label="My Plugin", icon="star", order=10)
            class MyPlugin(Plugin, TemplateView): ...
    """

    DEFAULT_ROUTE = "<str:uuid>"
    DEFAULT_LOOKUP: ClassVar[dict[str, str]] = {"uuid": "uuid"}

    def __init__(self) -> None:
        self._addressing: dict[type[Model], tuple[str, dict[str, str]]] = {}
        # Each entry pairs a plugin class with the keyword arguments given to `register`.
        self._registry: dict[type[Model], list[type[Plugin]]] = {}

    def register(self, *models: type[Model], **kwargs):
        """Return a decorator that registers a plugin with one or more models.

        Args:
            *models: The base model classes to register the plugin against.
            **kwargs: Registration options such as ``label``, ``icon``, ``order`` and
                ``menu``, kept with the plugin for building its navigation entry.

        Returns:
            A decorator that adds the plugin class to the registry and returns it.

        Example:
            Restrict a plugin to one subtype::

                @plugins.register(Sample)
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

        Args:
            model: The record type.
            route: The route fragment, such as ``"<str:lon>/<str:lat>"``.
            lookup: URL kwarg to model field, such as ``{"lon": "x", "lat": "y"}``.

        Raises:
            ValueError: A lookup name is not captured by the route.
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
        """Return the route fragment and lookup map for a record type.

        Args:
            model: The record type.

        Returns:
            The declared ``(route, lookup)`` pair, or the defaults.
        """
        return self._addressing.get(
            model, (self.DEFAULT_ROUTE, dict(self.DEFAULT_LOOKUP))
        )

    def route_for(self, model: type[Model]) -> str:
        """Return the route fragment a URL configuration mounts this record's plugins beneath.

        Args:
            model: The record type.

        Returns:
            The route fragment.
        """
        return self.get_addressing(model)[0]

    def lookup_for(self, model: type[Model]) -> dict[str, str]:
        """Return the URL kwarg to model field map for resolving and reversing a record.

        Args:
            model: The record type.

        Returns:
            The lookup map.
        """
        return self.get_addressing(model)[1]

    def get_plugins_for_model(self, model: type[Model]) -> list[type[Plugin]]:
        """Return the plugins registered for a model.

        Args:
            model: The model class.

        Returns:
            The registered ``(plugin class, options)`` entries, empty when there are none.
        """
        return self._registry.get(model, [])

    def get_plugin_menu_for_model(self, model: type[Model]) -> Menu:
        """Return the navigation menu for a record type, creating it on first use.

        Args:
            model: The record type.

        Returns:
            The menu named ``<Model>Menu``.
        """
        menu_name = f"{model.__name__}Menu"
        menu = root.get(menu_name)
        if menu is None:
            menu = Menu(menu_name)
            root.append(menu)
        return menu

    def get_urls_for_model(self, model: type[Model]) -> list[URLPattern]:
        """Collect the URL patterns of every plugin registered for a model and build its menu.

        Args:
            model: The model class.

        Returns:
            URL patterns suitable for ``include()``.
        """
        plugin_menu = self.get_plugin_menu_for_model(model)
        # Rebuilt, not appended to, so calling this twice does not duplicate menu entries.
        plugin_menu.children = type(plugin_menu.children)()
        url_patterns: list[URLPattern] = []

        for plugin_class, kwargs in itertools.chain(self.get_plugins_for_model(model)):
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

        Args:
            plugin_class: The registered plugin.
            model: The model it is registered against.
            **kwargs: The registration options: ``label``, ``icon`` and ``order``.

        Returns:
            The menu item, visible only when the plugin's page opens.
        """
        label = kwargs.get("label") or plugin_class.get_name().replace("-", " ").title()
        name = plugin_class.get_name()
        view_name = f"{model._meta.model_name.lower()}:{name}"
        item = MenuItem(
            label,
            view_name=view_name,
            # Never the author's predicate: flex_menu calls check(request, **kwargs) and catches nothing.
            check=menu_check(plugin_class),
            extra_context={
                "label": label,
                "icon": kwargs.get("icon", "circle"),
            },
        )
        # flex_menu has no ordering of its own, so `sort_menu` applies this once all entries exist.
        item.plugin_order = kwargs.get("order", 0)
        return item

    def sort_menu(self, menu: Menu) -> None:
        """Order a record's entries by declared position rather than registration order.

        Args:
            menu: The menu to sort in place.
        """
        ordered = sorted(
            menu.children, key=lambda child: getattr(child, "plugin_order", 0)
        )
        menu.children = type(menu.children)(ordered)


registry = PluginRegistry()
