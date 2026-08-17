"""Public API for the FairDM plugin system.

- ``Plugin`` — base class for a view attached to a core record
- ``register`` — the registration decorator, used as ``@plugins.register(Model, ...)``
- ``registry`` — the registry itself
- ``can_open`` / ``has_perm`` — the access decision and its memoised permission check
- ``is_instance_of`` — narrows a plugin to one subtype of a polymorphic record
- ``reverse`` — resolves a plugin address for a record

Attributes are resolved on first access rather than at import. This package is listed in
``INSTALLED_APPS``, so Django imports it during ``apps.populate()`` — before the app registry is
ready. ``Plugin`` inherits from ``PermissionRequiredMixin``, whose module pulls in
``django.contrib.auth.models``, and importing that during ``populate()`` raises
``AppRegistryNotReady``. Deferring keeps ``from fairdm.contrib.plugins import Plugin`` working for
callers while giving Django an empty module at startup.

The registry lives in ``registration.py`` rather than ``registry.py`` because a submodule binds its
own name onto the package once imported, and a submodule binding wins over ``__getattr__`` — so a
module named ``registry`` would shadow the ``registry`` instance exported here, silently and only
after something happened to import it.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import-time surface for type checkers only
    from .access import can_open, has_perm, is_instance_of
    from .base import Plugin
    from .registration import registry
    from .utils import reverse, slugify

__all__ = [
    "Plugin",
    "can_open",
    "has_perm",
    "is_instance_of",
    "register",
    "registry",
    "reverse",
    "slugify",
]

_LAZY = {
    "Plugin": (".base", "Plugin"),
    "can_open": (".access", "can_open"),
    "has_perm": (".access", "has_perm"),
    "is_instance_of": (".access", "is_instance_of"),
    "registry": (".registration", "registry"),
    "reverse": (".utils", "reverse"),
    "slugify": (".utils", "slugify"),
}


def __getattr__(name: str):
    from importlib import import_module

    if name == "register":
        return import_module(".registration", __name__).registry.register
    if name in _LAZY:
        module, attr = _LAZY[name]
        return getattr(import_module(module, __name__), attr)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


def __dir__() -> list[str]:
    return sorted(__all__)
