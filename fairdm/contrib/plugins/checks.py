"""Registration-time validation that refuses a plugin registration that cannot work.

Validation runs in the decorator rather than in Django's check framework, because checks only run
from management commands and would never fire on a production boot.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.urls import path

if TYPE_CHECKING:
    from .base import Plugin
    from .registration import Mount


class PluginRegistrationError(ImproperlyConfigured):
    """A plugin registration that cannot work."""


def _fail(plugin: Any, model: Any, problem: str) -> None:
    """Raise a registration error naming the plugin, the record type and the problem.

    Args:
        plugin: The plugin class being registered.
        model: The record type it is registered against.
        problem: What is wrong.

    Raises:
        PluginRegistrationError: Always.
    """
    plugin_name = getattr(plugin, "__name__", repr(plugin))
    model_name = getattr(model, "__name__", repr(model))
    msg = f"{plugin_name} registered against {model_name}: {problem}"
    raise PluginRegistrationError(msg)


def validate_models(plugin_class: type[Plugin], models: tuple[Any, ...]) -> None:
    """Require at least one model and that each is a Django model class.

    Refusal raises ``PluginRegistrationError``.

    Args:
        plugin_class: The plugin being registered.
        models: The values given to the decorator.
    """
    if not models:
        _fail(plugin_class, "nothing", "no model was given to register against")
    for model in models:
        if not (isinstance(model, type) and issubclass(model, Model)):
            _fail(
                plugin_class,
                model,
                f"expected a Django model, got {type(model).__name__}",
            )


def validate_options(
    plugin_class: type[Plugin], model: Any, options: dict[str, Any]
) -> None:
    """Require the place and column a registration names to exist and to go together.

    A column is only for a card, and a card can only be a card: it has no entry to decline and
    no page to be registered as. A refused option raises ``PluginRegistrationError``.

    Args:
        plugin_class: The plugin being registered.
        model: The record type it is registered against.
        options: The keyword arguments given to ``register``.
    """
    from .cards import Card
    from .places import Column, Place

    place = options.get("place")
    column = options.get("column")
    if place is not None and place not in Place.values:
        _fail(
            plugin_class,
            model,
            f"place {place!r} does not exist; use one of {', '.join(Place.values)}",
        )
    if place != Place.CARD:
        if column is not None:
            _fail(
                plugin_class,
                model,
                "a column can only be given for an overview card, and this registration is "
                f"{'a ' + str(place) if place else 'a navigation entry'}",
            )
        if issubclass(plugin_class, Card):
            _fail(
                plugin_class,
                model,
                "is a card, which has no page of its own; register it with place='card'",
            )
        return
    if column is not None and column not in Column.values:
        _fail(
            plugin_class,
            model,
            f"column {column!r} does not exist; use one of {', '.join(Column.values)}",
        )
    if options.get("menu") is False:
        _fail(
            plugin_class,
            model,
            "a card has no navigation entry, so menu=False means nothing for it",
        )
    if not issubclass(plugin_class, Card):
        _fail(
            plugin_class,
            model,
            "cannot be drawn as a card because it is not built on Card",
        )
    if not plugin_class.template_name and plugin_class.render_card is Card.render_card:
        _fail(
            plugin_class,
            model,
            "cannot be drawn as a card because it has no template_name and does not "
            "draw itself with render_card",
        )


def validate_check(plugin_class: type[Plugin], model: Any) -> None:
    """Require ``check`` to be a bool or a callable the access decision can evaluate.

    A ``classmethod`` is refused because it is truthy but not callable, so it would permit every request.

    A failing check raises ``PluginRegistrationError``.

    Args:
        plugin_class: The plugin being registered.
        model: The record type it is registered against.
    """
    from .access import check_is_valid, resolve_check

    check = resolve_check(plugin_class)
    if not check_is_valid(check):
        _fail(
            plugin_class,
            model,
            f"check is a {type(check).__name__}, which cannot be called. Use a plain function, a "
            f"staticmethod or a bool — a classmethod is truthy but not callable, so it would "
            f"permit every request",
        )


def validate_segment(plugin_class: type[Plugin], model: Any, segment: str) -> None:
    """Require a path segment to be usable in a route.

    A segment Django rejects raises ``PluginRegistrationError``.

    Args:
        plugin_class: The plugin being registered.
        model: The record type it is registered against.
        segment: The URL path segment.
    """
    # Built with `path()` so Django reports unknown converters and `<int:pk>/edit` stays valid.
    try:
        path(f"{segment}/", lambda request: None)
    except Exception as exc:
        _fail(plugin_class, model, f"url_path {segment!r} is not a valid route ({exc})")


def validate_extra_views(plugin_class: type[Plugin], model: Any) -> None:
    """Require additional views to be plugins that do not collide, nest or claim the plugin's own address.

    A violation raises ``PluginRegistrationError``.

    Args:
        plugin_class: The plugin being registered.
        model: The record type it is registered against.
    """
    from .base import Plugin as PluginBase

    extras = plugin_class.get_extra_views()
    seen: dict[str, str] = {}
    for extra in extras:
        if not (isinstance(extra, type) and issubclass(extra, PluginBase)):
            _fail(
                plugin_class,
                model,
                f"extra_views contains {extra!r}, which is not a Plugin subclass",
            )
        if extra is plugin_class:
            _fail(plugin_class, model, "extra_views contains the plugin itself")
        if extra.get_extra_views():
            _fail(
                plugin_class,
                model,
                f"extra_views contains {extra.__name__}, which declares extra_views of its own; "
                f"nesting is not supported",
            )
        segment = extra.get_url_path() or ""
        validate_segment(extra, model, segment)
        if not segment:
            _fail(
                plugin_class,
                model,
                f"{extra.__name__} has no url_path, so it would collide with the plugin's own "
                f"address",
            )
        if segment in seen:
            _fail(
                plugin_class,
                model,
                f"{extra.__name__} and {seen[segment]} both claim the segment {segment!r}",
            )
        seen[segment] = extra.__name__


def url_names_for(plugin_class: type[Plugin]) -> list[str]:
    """List every URL name the plugin will generate.

    Args:
        plugin_class: The plugin.

    Returns:
        The plugin's own name followed by one name per additional view.
    """
    base = plugin_class.get_name()
    return [base, *(f"{base}-{e.get_name()}" for e in plugin_class.get_extra_views())]


def validate_against_existing(
    plugin_class: type[Plugin],
    model: Any,
    existing: list[tuple[type[Plugin], dict]],
) -> None:
    """Require names, segments and generated URL names to be unique for one record type.

    A clash raises ``PluginRegistrationError``.

    Args:
        plugin_class: The plugin being registered.
        model: The record type it is registered against.
        existing: The ``(plugin class, options)`` entries already registered for it.
    """
    # Names alone are not enough: plugin `a` with child `b` and plugin `a-b` reverse to the same name.
    name = plugin_class.get_name()
    segment = plugin_class.get_url_path()
    new_url_names = set(url_names_for(plugin_class))

    for other, _ in existing:
        if other is plugin_class:
            continue
        if other.get_name() == name:
            _fail(plugin_class, model, f"another plugin already uses the name {name!r}")
        if segment is not None and other.get_url_path() == segment:
            _fail(
                plugin_class,
                model,
                f"{other.__name__} already serves the segment {segment!r}",
            )
        clashes = new_url_names & set(url_names_for(other))
        if clashes:
            _fail(
                plugin_class,
                model,
                f"would generate the address name {sorted(clashes)[0]!r}, which "
                f"{other.__name__} already generates",
            )


def validate_registration(
    plugin_class: type[Plugin],
    model: Any,
    existing: list[tuple[type[Plugin], dict]],
) -> None:
    """Run every check possible when a plugin is registered against one record type.

    A registration that cannot work raises ``PluginRegistrationError``.

    Args:
        plugin_class: The plugin being registered.
        model: The record type it is registered against.
        existing: The ``(plugin class, options)`` entries already registered for it.
    """
    validate_check(plugin_class, model)
    segment = plugin_class.get_url_path()
    if segment is not None:
        validate_segment(plugin_class, model, segment)
    validate_extra_views(plugin_class, model)
    validate_against_existing(plugin_class, model, existing)


def validate_mounts(model: Any, mounts: list[Mount]) -> None:
    """Require the names, segments and generated URL names of what a record type serves to be unique.

    Applies the rules of :func:`validate_against_existing` to the whole set.

    A clash raises ``PluginRegistrationError``.

    Args:
        model: The record type.
        mounts: What it serves, in registration order.
    """
    served: list[tuple[type[Plugin], dict]] = []
    for mount in mounts:
        validate_against_existing(mount.plugin_class, model, served)
        served.append((mount.plugin_class, {}))


def validate_places_offered(model: Any, mounts: list[Mount]) -> None:
    """Require the record type's overview to draw every place a plugin asks for beyond the navigation.

    A record type draws page actions and cards when one of its plugins is built on
    ``OverviewPlaces``.

    A refused place raises ``PluginRegistrationError``.

    Args:
        model: The record type.
        mounts: What it serves.
    """
    from .places import OverviewPlaces, Place

    if any(issubclass(mount.plugin_class, OverviewPlaces) for mount in mounts):
        return
    for mount in mounts:
        if mount.place is not Place.NAVIGATION:
            _fail(
                mount.plugin_class,
                model,
                f"is registered as a {mount.place.value}, but no plugin registered for "
                f"{model.__name__} is built on OverviewPlaces, so no page of this record type "
                f"would draw it",
            )
