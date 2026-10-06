"""Registration-time validation that refuses a plugin registration that cannot work.

Validation runs in the decorator rather than in Django's check framework, because checks only run
from management commands and would never fire on a production boot.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.urls import path

if TYPE_CHECKING:
    from .base import Plugin
    from .registration import Candidate, Mount


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


def _fail_removal(name: str, model: Any, problem: str) -> None:
    """Raise a registration error naming the removal, the record type and the problem.

    Args:
        name: The name of the plugin the removal declares.
        model: The record type it is removed from.
        problem: What is wrong.

    Raises:
        PluginRegistrationError: Always.
    """
    model_name = getattr(model, "__name__", repr(model))
    msg = f"removal of {name!r} from {model_name}: {problem}"
    raise PluginRegistrationError(msg)


def _fail_between(plugins: list[Any], model: Any, problem: str) -> None:
    """Raise a registration error naming several plugins, the record type and the problem.

    Args:
        plugins: The plugin classes the problem is between.
        model: The record type they are registered against.
        problem: What is wrong.

    Raises:
        PluginRegistrationError: Always.
    """
    names = " and ".join(
        getattr(plugin, "__name__", repr(plugin)) for plugin in plugins
    )
    model_name = getattr(model, "__name__", repr(model))
    msg = f"{names} registered against {model_name}: {problem}"
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
    """Require the place, column and replacement target a registration names to be usable.

    A column is only for a card, and a card can only be a card: it has no entry to decline and
    no page to be registered as. A refused option raises ``PluginRegistrationError``.

    Args:
        plugin_class: The plugin being registered.
        model: The record type it is registered against.
        options: The keyword arguments given to ``register``.
    """
    from .base import Plugin as PluginBase
    from .cards import Card
    from .places import Column, Place

    replaces = options.get("replaces")
    if replaces is not None and not (
        (isinstance(replaces, str) and replaces)
        or (isinstance(replaces, type) and issubclass(replaces, PluginBase))
    ):
        _fail(
            plugin_class,
            model,
            f"replaces {replaces!r}, which is neither a plugin class nor the name of one",
        )
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


@dataclass(frozen=True)
class Claim:
    """What one plugin takes of a record type's addresses: its name, its segment and its URL names.

    Attributes:
        plugin_class: The plugin making the claim.
        name: The name it is served under.
        url_path: The segment it is served at, None when it has none to claim.
    """

    plugin_class: type[Plugin]
    name: str
    url_path: str | None

    @classmethod
    def of_plugin(cls, plugin_class: type[Plugin]) -> Claim:
        """Build the claim a plugin makes under its own name and segment.

        Args:
            plugin_class: The plugin.

        Returns:
            The claim.
        """
        return cls(plugin_class, plugin_class.get_name(), plugin_class.get_url_path())

    @classmethod
    def of_mount(cls, mount: Mount) -> Claim:
        """Build the claim a mount makes, under the name and segment it is served at.

        Args:
            mount: What the record type serves.

        Returns:
            The claim.
        """
        return cls(mount.plugin_class, mount.name, mount.url_path)

    @property
    def url_names(self) -> list[str]:
        """Every URL name the claim generates: its own, then one per view the plugin owns."""
        extras = self.plugin_class.get_extra_views()
        return [self.name, *(f"{self.name}-{extra.get_name()}" for extra in extras)]

    def problem_with(self, other: Claim, *, addresses: bool = True) -> str | None:
        """Say how this claim clashes with another, if it does.

        Names alone are not enough: plugin ``a`` with child ``b`` and plugin ``a-b`` reverse to the
        same name.

        Args:
            other: A claim already made on the record type.
            addresses: False to compare names only, for a claim that is not served under its own
                segment or URL names.

        Returns:
            The problem, or None when the two can be served together.
        """
        if other.name == self.name:
            return f"another plugin already uses the name {self.name!r}"
        if not addresses:
            return None
        if self.url_path is not None and other.url_path == self.url_path:
            return (
                f"{other.plugin_class.__name__} already serves the segment "
                f"{self.url_path!r}"
            )
        clashes = set(self.url_names) & set(other.url_names)
        if clashes:
            return (
                f"would generate the address name {sorted(clashes)[0]!r}, which "
                f"{other.plugin_class.__name__} already generates"
            )
        return None


def validate_against_existing(
    plugin_class: type[Plugin],
    model: Any,
    existing: list[tuple[type[Plugin], dict]],
    options: dict[str, Any],
) -> None:
    """Require names, segments and generated URL names to be unique for one record type.

    A registration that states ``replaces`` is served under its target's segment and names, so
    it is left out of the segment and URL name comparison, whether it is the one arriving or
    one already there. Its own name must still be unique.

    A clash raises ``PluginRegistrationError``.

    Args:
        plugin_class: The plugin being registered.
        model: The record type it is registered against.
        existing: The ``(plugin class, options)`` entries already registered for it.
        options: The keyword arguments the plugin is being registered with.
    """
    claim = Claim.of_plugin(plugin_class)
    for other, other_options in existing:
        if other is plugin_class:
            continue
        compare = not (options.get("replaces") or other_options.get("replaces"))
        problem = claim.problem_with(Claim.of_plugin(other), addresses=compare)
        if problem:
            _fail(plugin_class, model, problem)


def validate_registration(
    plugin_class: type[Plugin],
    model: Any,
    existing: list[tuple[type[Plugin], dict]],
    options: dict[str, Any],
) -> None:
    """Run every check possible when a plugin is registered against one record type.

    A registration that cannot work raises ``PluginRegistrationError``.

    Args:
        plugin_class: The plugin being registered.
        model: The record type it is registered against.
        existing: The ``(plugin class, options)`` entries already registered for it.
        options: The keyword arguments the plugin is being registered with.
    """
    validate_check(plugin_class, model)
    segment = plugin_class.get_url_path()
    if segment is not None:
        validate_segment(plugin_class, model, segment)
    validate_extra_views(plugin_class, model)
    validate_against_existing(plugin_class, model, existing, options)


def validate_mounts(model: Any, mounts: list[Mount]) -> None:
    """Require the names, segments and generated URL names of what a record type serves to be unique.

    Applies the rules of :func:`validate_against_existing` to the whole set, under the names and
    segments the mounts are served at.

    A clash raises ``PluginRegistrationError``.

    Args:
        model: The record type.
        mounts: What it serves, in registration order.
    """
    claims: list[Claim] = []
    for mount in mounts:
        claim = Claim.of_mount(mount)
        for other in claims:
            problem = claim.problem_with(other)
            if problem:
                _fail(mount.plugin_class, model, problem)
        claims.append(claim)


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


def is_overview(mount: Mount) -> bool:
    """Say whether a mount is its record type's overview.

    The overview is built on ``OverviewPlaces`` or served at the record's own address. The address
    alone does not decide it, because a sample's overview is served beneath the sample.

    Args:
        mount: One of a record type's mounts.

    Returns:
        True for the overview.
    """
    from .places import OverviewPlaces

    return issubclass(mount.plugin_class, OverviewPlaces) or mount.url_path is None


def validate_removals(
    model: Any, candidates: list[Candidate], removals: list[str]
) -> None:
    """Require each removal to name a registration that can be removed.

    A removal that names nothing registered for the record type, or its overview, raises
    ``PluginRegistrationError``. A replacement of the overview is not the overview, so it can be
    removed and the plugin it replaced is served again.

    Args:
        model: The record type.
        candidates: What its registrations declare, before any removal.
        removals: The names declared with ``remove``.
    """
    named = {candidate.mount.name: candidate for candidate in candidates}
    for name in removals:
        candidate = named.get(name)
        if candidate is None:
            _fail_removal(
                name,
                model,
                f"no plugin of that name is registered against {model.__name__}",
            )
        elif candidate.replaces is None and is_overview(candidate.mount):
            _fail_removal(
                name,
                model,
                "this is the overview of the record type, which can be replaced but not removed",
            )


def validate_replacements(
    model: Any, candidates: list[Candidate], removals: list[str]
) -> None:
    """Require each replacement to name a plugin that is served, once, with no circle.

    A replacement whose target is not registered against the record type or is removed from it,
    two replacements for one target and a circle of replacements raise
    ``PluginRegistrationError``.

    Args:
        model: The record type.
        candidates: What remains of its registrations after the removals.
        removals: The names declared with ``remove``.
    """
    named = {candidate.mount.name: candidate for candidate in candidates}
    replacers: dict[str, Candidate] = {}
    for candidate in candidates:
        target = candidate.replaces
        if target is None:
            continue
        plugin = candidate.mount.plugin_class
        if target in removals:
            _fail(
                plugin,
                model,
                f"replaces {target!r}, which the removal of {target!r} takes away from "
                f"{model.__name__}; leave out the removal or the replacement",
            )
        if target not in named:
            _fail(
                plugin,
                model,
                f"replaces {target!r}, but no plugin of that name is registered against "
                f"{model.__name__}",
            )
        if target in replacers:
            _fail_between(
                [replacers[target].mount.plugin_class, plugin],
                model,
                f"both replace {target!r}; remove one of them",
            )
        replacers[target] = candidate
    for candidate in candidates:
        path = [candidate.mount.name]
        target = candidate.replaces
        while target is not None:
            if target in path:
                circle = [
                    named[name].mount.plugin_class
                    for name in path[path.index(target) :]
                ]
                _fail_between(
                    circle,
                    model,
                    "replace one another in a circle, so none of them is served"
                    if len(circle) > 1
                    else f"replaces itself, {target!r}",
                )
            path.append(target)
            target = named[target].replaces


def validate_place_kept(
    model: Any, replacement: Candidate, replaced: Candidate, place: Any
) -> None:
    """Require a replacement to appear in the place of the plugin it replaces.

    A replacement that states a different place raises ``PluginRegistrationError``. One that
    states none takes its target's, and must be able to appear there.

    Args:
        model: The record type.
        replacement: The replacement.
        replaced: What it replaces, or the replacement before it in a chain.
        place: The place the plugin it replaces appears in.
    """
    from .places import Place

    stated = replacement.options.get("place")
    plugin = replacement.mount.plugin_class
    if stated is not None and Place(stated) is not place:
        _fail_between(
            [plugin, replaced.mount.plugin_class],
            model,
            f"{plugin.__name__} is registered as a {Place(stated).value}, but it replaces "
            f"{replaced.mount.name!r}, which is a {place.value}; a replacement appears in the "
            f"place of the plugin it replaces",
        )
    validate_options(plugin, model, {**replacement.options, "place": place.value})
