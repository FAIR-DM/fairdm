"""Public API for the FairDM plugin system.

- ``Plugin`` — base class for a view attached to a core record
- ``register`` — the registration decorator, used as ``@plugins.register(Model, ...)``
- ``registry`` — the registry itself
- ``can_open`` / ``has_perm`` — the access decision and its memoised permission check
- ``is_instance_of`` — narrows a plugin to one subtype of a polymorphic record
- ``reverse`` — resolves a plugin address for a record

Attributes are resolved on first access because Django imports this package during
``apps.populate()``, before ``Plugin``'s auth imports are safe.
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
    """Resolve a public name on first access.

    Args:
        name: The attribute being looked up.

    Returns:
        The named object from its submodule.

    Raises:
        AttributeError: The name is not part of the public API.
    """
    # The registry lives in `registration.py` because a submodule named `registry` would shadow the instance.
    from importlib import import_module

    if name == "register":
        return import_module(".registration", __name__).registry.register
    if name in _LAZY:
        module, attr = _LAZY[name]
        return getattr(import_module(module, __name__), attr)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


def __dir__() -> list[str]:
    """List the public names."""
    return sorted(__all__)
