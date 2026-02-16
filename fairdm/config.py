"""
Re-export registry configuration classes for convenient imports.

This module provides a convenient single import point for configuration classes.
Instead of importing from fairdm.registry.config, users can import from fairdm.config.

Note: Imports are deferred to avoid circular dependencies during Django setup.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fairdm.registry.config import (
        Authority,
        Citation,
        ModelConfiguration,
        ModelMetadata,
    )
    from fairdm.registry.registry import register
else:

    def __getattr__(name):
        """Lazy import to avoid circular dependencies."""
        if name in ("Authority", "Citation", "ModelConfiguration", "ModelMetadata"):
            from fairdm.registry.config import (
                Authority,
                Citation,
                ModelConfiguration,
                ModelMetadata,
            )

            globals().update(
                {
                    "Authority": Authority,
                    "Citation": Citation,
                    "ModelConfiguration": ModelConfiguration,
                    "ModelMetadata": ModelMetadata,
                }
            )
            return globals()[name]
        elif name == "register":
            from fairdm.registry.registry import register

            globals()["register"] = register
            return register
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Authority",
    "Citation",
    "ModelConfiguration",
    "ModelMetadata",
    "register",
]
