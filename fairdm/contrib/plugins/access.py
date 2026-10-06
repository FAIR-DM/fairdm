"""One access decision, consulted by both navigation and dispatch through :func:`can_open`."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.db.models import Model
    from django.http import HttpRequest

logger = logging.getLogger(__name__)

_MEMO_ATTR = "_fairdm_plugin_perm_cache"


def is_instance_of(*model_classes: type[Model]) -> Callable[..., bool]:
    """Return a predicate that passes when the record is one of ``model_classes``.

    A record of ``None`` passes, so the plugin is admitted where no record is in hand.

    Args:
        *model_classes: The accepted model classes.

    Returns:
        A ``check(request, obj)`` predicate.

    Example:
        Narrow a plugin to one subtype of a polymorphic record::

            class RockAnalysis(Plugin, FairDMTemplateView):
                check = staticmethod(is_instance_of(RockSample))
    """

    def check(request: HttpRequest, obj: Model | None) -> bool:
        """Pass when there is no record or it is one of the model classes."""
        if obj is None:
            return True
        return isinstance(obj, model_classes)

    return check


def has_perm(request: HttpRequest, permission: str, obj: Model | None = None) -> bool:
    """Resolve ``permission`` for the request's user, memoised for the life of the request.

    Args:
        request: The current request.
        permission: The permission codename, with app label.
        obj: The record to check against, if any.

    Returns:
        True when the user holds the permission globally or on the record.
    """
    cache: dict[tuple[Any, ...], bool] = getattr(request, _MEMO_ATTR, None)
    if cache is None:
        cache = {}
        setattr(request, _MEMO_ATTR, cache)

    # Keyed by label and pk, never `id()`, which CPython reuses for short-lived objects.
    if obj is None:
        key: tuple[Any, ...] = (permission, None)
    else:
        key = (permission, obj._meta.label, obj.pk)

    if key not in cache:
        user = request.user
        # With an object, ModelBackend contributes nothing, so a global grant needs its own check.
        granted = user.has_perm(permission)
        if not granted and obj is not None:
            granted = user.has_perm(permission, obj)
        cache[key] = granted
    return cache[key]


def resolve_check(view_class: type) -> Callable[..., bool] | bool:
    """Read a view's predicate as declared, without invoking the descriptor protocol.

    Args:
        view_class: The view class.

    Returns:
        The ``check`` attribute, or True when the view declares none.
    """
    return inspect.getattr_static(view_class, "check", True)


def check_is_valid(check: Any) -> bool:
    """Report whether ``check`` is a bool or a callable that :func:`can_open` can evaluate.

    A ``classmethod`` object is neither but is truthy, so it would publish a page meant to be hidden.

    Args:
        check: The value read from a view's ``check`` attribute.

    Returns:
        True when the value is a bool or callable.
    """
    return isinstance(check, bool) or callable(check)


def can_open(
    view_class: type,
    request: HttpRequest,
    obj: Model | None = None,
) -> bool:
    """Decide whether the user may open this view for this record.

    The predicate is read from the class's ``plugin_class`` when that names an owner, and from
    the class itself otherwise. Dispatch passes the view's own class, whose ``plugin_class``
    is None, so a further view of a page is decided by its own ``check`` and ``permission``,
    not its parent's. A further view of a card must also pass ``Card.admits``.

    Args:
        view_class: The plugin or additional view class.
        request: The current request.
        obj: The record the page belongs to, if any.

    Returns:
        True when the predicate and every required permission pass.
    """
    owner = getattr(view_class, "plugin_class", None) or view_class
    check = resolve_check(owner)

    if callable(check):
        if not check(request, obj):
            return False
    elif not check:
        return False

    permission = getattr(view_class, "permission", None)
    if permission:
        permissions = [permission] if isinstance(permission, str) else list(permission)
        return all(has_perm(request, perm, obj) for perm in permissions)

    return True


def menu_check(view_class: type) -> Callable[..., bool]:
    """Adapt :func:`can_open` to the ``check(request, **kwargs)`` signature ``flex_menu`` calls.

    Args:
        view_class: The plugin or additional view class.

    Returns:
        A predicate that hides the entry when the check raises.
    """

    def check(request: HttpRequest, **kwargs: Any) -> bool:
        """Evaluate :func:`can_open`, hiding the entry on any error."""
        try:
            return can_open(view_class, request, kwargs.get("object"))
        except Exception:
            # flex_menu catches nothing, so raising would fail the whole page render.
            logger.exception(
                "Plugin visibility check failed for %s; hiding the entry",
                view_class.__name__,
            )
            return False

    return check
