from .config import PluginConfig, PluginMenuItem
from .plugin import ACTIONS, EXPLORE, MANAGEMENT, FairDMPlugin
from .registry import PluginRegistry, register, registry
from .utils import (
    check_has_edit_permission,
    class_to_slug,
    reverse,
    sample_check_has_edit_permission,
)
from .views import PluggableView

__all__ = [
    "ACTIONS",
    "EXPLORE",
    "MANAGEMENT",
    "FairDMPlugin",
    "PluggableView",
    "PluginConfig",
    "PluginMenuItem",
    "PluginRegistry",
    "check_has_edit_permission",
    "class_to_slug",
    "register",
    "registry",
    "reverse",
    "sample_check_has_edit_permission",
]
