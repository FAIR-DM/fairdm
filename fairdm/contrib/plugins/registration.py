"""Plugin registry for managing plugin/model associations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from django.db.models import Model
from django.urls import URLPattern
from flex_menu import Menu, MenuItem, root

from .access import menu_check
from .places import Column, Place

if TYPE_CHECKING:
    from .base import Plugin


@dataclass(frozen=True)
class Mount:
    """One plugin as a record type serves it, worked out from the registrations.

    Attributes:
        plugin_class: The class that is served.
        name: The name it is served under, which URL names and lookups use.
        url_path: The segment it is served at, or None for the record's own address.
        place: Where it appears on the record's page.
        label: The text of its entry.
        icon: The icon of its entry.
        order: Its position among the entries of its place.
        listed: False when the registration declined its entry.
        column: The overview column a card is drawn in, None for anything that is not a card.
    """

    plugin_class: type[Plugin]
    name: str
    url_path: str | None
    place: Place
    label: str
    icon: str
    order: int
    listed: bool
    column: Column | None = None

    @classmethod
    def from_registration(
        cls, plugin_class: type[Plugin], options: dict[str, Any]
    ) -> Mount:
        """Build the mount a registration declares.

        Args:
            plugin_class: The registered plugin.
            options: The keyword arguments given to ``register``.

        Returns:
            The mount, with the defaults a navigation entry has.
        """
        name = plugin_class.get_name()
        place = Place(options.get("place") or Place.NAVIGATION)
        column = (
            Column(options.get("column") or Column.SIDE)
            if place is Place.CARD
            else None
        )
        return cls(
            plugin_class=plugin_class,
            name=name,
            url_path=plugin_class.get_url_path(),
            place=place,
            label=options.get("label") or name.replace("-", " ").title(),
            icon=options.get("icon", "circle"),
            order=options.get("order", 0),
            listed=options.get("menu") is not False,
            column=column,
        )


class PluginRegistry:
    """Track which plugins are registered for each model and how records are addressed.

    The registry keeps every registration as it was made and works out from them what a record
    type serves. It builds each model's URL patterns and navigation menu from that.

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
            **kwargs: Registration options such as ``label``, ``icon``, ``order``, ``menu``
                ``place`` and ``column``, kept with the plugin for building its entry. ``place`` is
                a :class:`~fairdm.contrib.plugins.places.Place` or its value, and defaults to the
                navigation. ``column`` is a :class:`~fairdm.contrib.plugins.places.Column` or its
                value, and only a card takes one.

        Returns:
            A decorator that adds the plugin class to the registry and returns it.

        Example:
            Restrict a plugin to one subtype::

                @plugins.register(Sample)
                class AnalysisPlugin(Plugin, TemplateView):
                    check = is_instance_of(RockSample)
        """

        def decorator(plugin_class: type[Plugin]) -> type[Plugin]:
            from .checks import validate_models, validate_options, validate_registration

            validate_models(plugin_class, models)
            for model in models:
                validate_options(plugin_class, model, kwargs)
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

    def resolve(self, model: type[Model]) -> list[Mount]:
        """Work out what a record type serves from its registrations.

        Nothing is stored: every call reads the registrations again, so the registry's list is
        never edited to produce the answer.

        Args:
            model: The record type.

        Returns:
            One mount per registration, in the order they were registered.

        Raises:
            PluginRegistrationError: The mounts clash with each other, or one asks for a place
                the record type's overview does not draw.
        """
        from .checks import validate_mounts, validate_places_offered

        mounts = [
            Mount.from_registration(plugin_class, options)
            for plugin_class, options in self.get_plugins_for_model(model)
        ]
        validate_mounts(model, mounts)
        validate_places_offered(model, mounts)
        return mounts

    def validate_all(self) -> None:
        """Resolve every record type that has a registration, refusing what cannot work.

        Raises:
            PluginRegistrationError: A record type's registrations cannot be served.
        """
        for model in list(self._registry):
            self.resolve(model)

    def get_page_actions(self, model: type[Model]) -> list[Mount]:
        """Return the page actions a record type offers, before any visitor is considered.

        Args:
            model: The record type.

        Returns:
            The listed action mounts, by position and then name, so the order is the same
            whichever order the plugins were registered in.
        """
        actions = [
            mount
            for mount in self.resolve(model)
            if mount.place is Place.ACTION and mount.listed
        ]
        return sorted(actions, key=lambda mount: (mount.order, mount.name))

    def get_cards(self, model: type[Model]) -> list[Mount]:
        """Return the cards a record type offers, before any visitor is considered.

        Args:
            model: The record type.

        Returns:
            The card mounts, by position and then name, so the order is the same whichever
            order the plugins were registered in.
        """
        cards = [mount for mount in self.resolve(model) if mount.place is Place.CARD]
        return sorted(cards, key=lambda mount: (mount.order, mount.name))

    def get_urls_for_model(self, model: type[Model]) -> list[URLPattern]:
        """Collect the URL patterns of every plugin a model serves and build its menu.

        Args:
            model: The model class.

        Returns:
            URL patterns suitable for ``include()``.
        """
        plugin_menu = self.get_plugin_menu_for_model(model)
        # Rebuilt, not appended to, so calling this twice does not duplicate menu entries.
        plugin_menu.children = type(plugin_menu.children)()
        url_patterns: list[URLPattern] = []

        for mount in self.resolve(model):
            url_patterns.extend(
                mount.plugin_class.get_urls(
                    menu_class=plugin_menu,
                    model=model,
                    name=mount.name,
                    url_path=mount.url_path,
                )
            )
            if mount.place is Place.NAVIGATION and mount.listed:
                plugin_menu.append(self.configure_tab(mount, model))
        self.sort_menu(plugin_menu)
        return url_patterns

    def configure_tab(self, mount: Mount, model: type[Model]) -> MenuItem:
        """Build the navigation entry for a mount.

        Args:
            mount: The mount the entry is for.
            model: The model it is served for.

        Returns:
            The menu item, visible only when the plugin's page opens.
        """
        view_name = f"{model._meta.model_name.lower()}:{mount.name}"
        item = MenuItem(
            mount.label,
            view_name=view_name,
            # Never the author's predicate: flex_menu calls check(request, **kwargs) and catches nothing.
            check=menu_check(mount.plugin_class),
            extra_context={
                "label": mount.label,
                "icon": mount.icon,
            },
        )
        # flex_menu has no ordering of its own, so `sort_menu` applies this once all entries exist.
        item.plugin_order = mount.order
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
