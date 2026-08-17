"""One access decision, consulted by navigation and by dispatch.

A plugin surface that is not shown must not be reachable, and one that is not reachable must not be
shown. Splitting those into two mechanisms is what lets an author hide a page, forget the
permission, and publish it — so both callers go through :func:`can_open`.
"""

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

    Narrowing a plugin to one subtype of a polymorphic record is the common case::

        class RockAnalysis(Plugin, FairDMTemplateView):
            check = staticmethod(is_instance_of(RockSample))

    A record of ``None`` passes, so the plugin is admitted where no record is in hand.
    """

    def check(request: HttpRequest, obj: Model | None) -> bool:
        if obj is None:
            return True
        return isinstance(obj, model_classes)

    return check


def has_perm(request: HttpRequest, permission: str, obj: Model | None = None) -> bool:
    """Resolve ``permission`` for this user, memoised for the life of the request.

    Two calls, not one. ``ModelBackend`` contributes nothing once an object is passed
    (``django/contrib/auth/backends.py``), so ``user.has_perm(p, obj)`` alone consults only the
    object-level backends and refuses a user who holds the permission globally. This is the shape
    ``guardian.utils.get_40x_or_None`` uses for the same reason.

    Exported because the memo is only worth having if plugin predicates use it too — a record page
    evaluates every registered plugin, and an unmemoised object-level check costs several queries
    each time.
    """
    cache: dict[tuple[Any, ...], bool] = getattr(request, _MEMO_ATTR, None)
    if cache is None:
        cache = {}
        setattr(request, _MEMO_ATTR, cache)

    # Keyed by identity of the record, never by id(), which CPython reuses after collection —
    # and this is reachable from template loops over short-lived objects.
    if obj is None:
        key: tuple[Any, ...] = (permission, None)
    else:
        key = (permission, obj._meta.label, obj.pk)

    if key not in cache:
        user = request.user
        granted = user.has_perm(permission)
        if not granted and obj is not None:
            granted = user.has_perm(permission, obj)
        cache[key] = granted
    return cache[key]


def resolve_check(view_class: type) -> Callable[..., bool] | bool:
    """Read a view's predicate without invoking the descriptor protocol.

    ``getattr`` on a class attribute that happens to be a function returns a bound or unbound
    callable depending on how it is reached, which is what made the same predicate uncallable from
    one caller and wrongly-argumented from the other. ``getattr_static`` returns the object as
    declared, so a plain function, a lambda, a ``staticmethod`` and an inherited attribute all
    behave identically.
    """
    return inspect.getattr_static(view_class, "check", True)


def check_is_valid(check: Any) -> bool:
    """Is ``check`` something :func:`can_open` can evaluate?

    A ``classmethod`` object is the trap: ``getattr_static`` returns it unchanged, it is **not**
    callable, and it **is** truthy — so a ``callable()`` guard falls through to ``bool(check)`` and
    publishes the page the author meant to hide. Registration refuses anything that is neither a
    plain bool nor callable.
    """
    return isinstance(check, bool) or callable(check)


def can_open(
    view_class: type,
    request: HttpRequest,
    obj: Model | None = None,
) -> bool:
    """Decide whether this view may be opened by this user for this record.

    Both the navigation entry and the view's own dispatch call this, so they cannot disagree.

    The predicate is read from the **owning plugin**, not from ``view_class``. An additional view is
    an ordinary :class:`~fairdm.contrib.plugins.base.Plugin` subclass and inherits the permissive
    default, so reading it off the view would leave a child of a restricted plugin reachable while
    its parent is refused and unlisted.
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
    """Adapt :func:`can_open` to the signature the navigation package calls.

    ``flex_menu`` invokes ``check(request, **kwargs)`` and catches nothing, so an author's predicate
    raising there takes down the whole page during template rendering. The adapter is what the menu
    holds; the author's function is never handed over directly.
    """

    def check(request: HttpRequest, **kwargs: Any) -> bool:
        try:
            return can_open(view_class, request, kwargs.get("object"))
        except Exception:
            # Hiding is the fail-safe direction for a visibility decision, and the alternative is a
            # 500 from inside template rendering.
            logger.exception(
                "Plugin visibility check failed for %s; hiding the entry",
                view_class.__name__,
            )
            return False

    return check
