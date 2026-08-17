"""Registration-time validation.

A registration that cannot work is refused when it is made, naming what is wrong. The alternative
is what this replaces: two plugins claiming one address and the framework serving whichever
imported first, and five plugins registered against a record that has no page, inert for months
with nothing to say so.

Validation runs in the decorator rather than through Django's check framework because checks only
run from management commands, so one never fires on a production boot. Registration happens at
import, so it fails on every start. That is the same reasoning already settled for the model
registry.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.urls import path

if TYPE_CHECKING:
    from .base import Plugin


class PluginRegistrationError(ImproperlyConfigured):
    """A plugin registration that cannot work."""


def _fail(plugin: Any, model: Any, problem: str) -> None:
    """Every refusal names the plugin, the record type and the problem."""
    plugin_name = getattr(plugin, "__name__", repr(plugin))
    model_name = getattr(model, "__name__", repr(model))
    msg = f"{plugin_name} registered against {model_name}: {problem}"
    raise PluginRegistrationError(msg)


def validate_models(plugin_class: type[Plugin], models: tuple[Any, ...]) -> None:
    """The decorator must name at least one record type, and they must be models."""
    if not models:
        _fail(plugin_class, "nothing", "no model was given to register against")
    for model in models:
        if not (isinstance(model, type) and issubclass(model, Model)):
            _fail(
                plugin_class,
                model,
                f"expected a Django model, got {type(model).__name__}",
            )


def validate_check(plugin_class: type[Plugin], model: Any) -> None:
    """A predicate must be something the access decision can evaluate.

    A ``classmethod`` is the case worth refusing: it survives attribute lookup unchanged, it is not
    callable, and it is truthy — so a guard of the shape ``if callable(check)`` falls through to
    ``bool(check)`` and publishes the page its author wrote it to hide.
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
    """A path segment must be usable in a route.

    Built with ``path()`` rather than parsed, so an unknown converter is reported by Django itself
    and the route syntax an additional view needs — ``<int:pk>/edit`` — keeps working.
    """
    try:
        path(f"{segment}/", lambda request: None)
    except Exception as exc:
        _fail(plugin_class, model, f"url_path {segment!r} is not a valid route ({exc})")


def validate_extra_views(plugin_class: type[Plugin], model: Any) -> None:
    """Additional views must be plugins, must not collide, and must not nest."""
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
    """Every URL name this plugin will generate."""
    base = plugin_class.get_name()
    return [base, *(f"{base}-{e.get_name()}" for e in plugin_class.get_extra_views())]


def validate_against_existing(
    plugin_class: type[Plugin],
    model: Any,
    existing: list[tuple[type[Plugin], dict]],
) -> None:
    """Names, segments and generated URL names must all be unique for one record type.

    Names and segments are not enough on their own: a plugin ``a`` owning a child ``b`` and a
    separate plugin ``a-b`` produce the same reverse name from different paths, and Django keeps
    the last one silently.
    """
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
    """Everything checkable at the moment a plugin is registered against one record type."""
    validate_check(plugin_class, model)
    segment = plugin_class.get_url_path()
    if segment is not None:
        validate_segment(plugin_class, model, segment)
    validate_extra_views(plugin_class, model)
    validate_against_existing(plugin_class, model, existing)
