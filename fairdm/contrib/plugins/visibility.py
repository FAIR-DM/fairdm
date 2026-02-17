"""Visibility check helpers for plugin system."""

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import Model
    from django.http import HttpRequest


def is_instance_of(*model_classes: type["Model"]) -> Callable[["HttpRequest", "Model | None"], bool]:
    """Returns a check function that passes if obj is an instance of any model_class.

    Args:
        *model_classes: One or more Django Model classes to check against

    Returns:
        A check function suitable for use as Plugin.check or PluginGroup.check

    Example:
        >>> from myapp.models import RockSample, SoilSample
        >>> check = is_instance_of(RockSample)
        >>> # Or multiple types:
        >>> check = is_instance_of(RockSample, SoilSample)
    """

    def check(request: "HttpRequest", obj: "Model | None") -> bool:
        """Check if obj is an instance of any of the specified model classes.

        Args:
            request: The HTTP request
            obj: Model instance to check (or None for model-level access)

        Returns:
            True if obj is None (allow model-level access) or obj is an instance
            of any of the specified model classes
        """
        if obj is None:
            return True  # Allow model-level access
        return isinstance(obj, model_classes)

    return check
