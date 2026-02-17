"""Public API for the FairDM plugin system.

This module exports the main classes and functions for working with plugins:

- Plugin: Mixin base class for creating plugins
- PluginGroup: Composition class for grouping plugins
- register: Decorator for registering plugins (use as @plugins.register(...))
- registry: Global plugin registry instance
- is_instance_of: Visibility helper for type filtering
- Tab: Data class for tab rendering
- slugify: Utility for converting names to URL-safe slugs
"""

# Core plugin system
from .base import Plugin
from .group import PluginGroup
from .menu import Tab
from .registry import registry

# Utility functions
from .utils import slugify
from .visibility import is_instance_of

# Convenience: allow @plugins.register(...) syntax
register = registry.register

__all__ = [
    # Core API
    "Plugin",
    "PluginGroup",
    "Tab",
    "register",
    "registry",
    "is_instance_of",
    "slugify",
]
