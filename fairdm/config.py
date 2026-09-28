"""Re-export the registry configuration classes from a single import point.

Instead of importing from ``fairdm.registry.config``, users can import from
``fairdm.config``. Imports are deferred to avoid circular dependencies during Django setup.
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
        """Import the requested configuration class on first access.

        Args:
            name: The attribute being looked up on this module.

        Returns:
            The registry class or the ``register`` decorator of that name.

        Raises:
            AttributeError: ``name`` is not one of the re-exported names.
        """
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
