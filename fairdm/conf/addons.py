"""Addon discovery and configuration loading.

Handles integration of FairDM addons that provide additional settings, apps, and middleware.
"""

import importlib
import importlib.util
import logging
import os
from importlib import import_module

from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

addon_urls: list[str] = []


def get_module_path(module_name: str) -> str:
    """Get the file system path to a Python module.

    Args:
        module_name: Fully qualified module name (e.g., 'myapp.conf').

    Returns:
        Absolute path to the module file.

    Raises:
        ModuleNotFoundError: The module cannot be found.
        ValueError: The module is a package, not a single file.
    """
    spec = importlib.util.find_spec(module_name)
    if spec is None or spec.origin is None:
        raise ModuleNotFoundError(f"Module '{module_name}' not found")

    if spec.submodule_search_locations:
        raise ValueError(f"'{module_name}' is a package, not a module")

    return os.path.abspath(spec.origin)


def discover_addon_setup_modules(
    addons: list[str], env_profile: str
) -> list[tuple[str, str]]:
    """Discover setup modules for the given addon packages.

    Args:
        addons: List of addon package names.
        env_profile: Environment profile, used for validation.

    Returns:
        ``(addon_name, absolute path to its setup module file)`` pairs, one per addon
        whose setup module was found and passed validation. The name travels with its
        path so a later failure applying that file can still name the addon.

    Raises:
        ImproperlyConfigured: An addon's configuration is invalid, so production fails fast.
    """
    from .checks import validate_addon_module

    setup_modules = []

    for addon_name in addons:
        try:
            addon_module = import_module(addon_name)

            setup_module_path = getattr(addon_module, "__fdm_setup_module__", None)

            if setup_module_path is None:
                logger.warning(
                    f"⚠️  Addon '{addon_name}' does not define '__fdm_setup_module__'. "
                    "No settings will be loaded from this addon."
                )
                continue

            if not validate_addon_module(addon_name, setup_module_path, env_profile):
                continue

            try:
                module_file_path = get_module_path(setup_module_path)
                setup_modules.append((addon_name, module_file_path))
                logger.info(
                    f"✓ Loaded addon setup module: {addon_name} → {setup_module_path}"
                )
            except (ModuleNotFoundError, ValueError) as e:
                logger.error(
                    f"❌ Could not locate setup module '{setup_module_path}' for addon '{addon_name}': {e}"
                )

        except ImproperlyConfigured:
            raise
        except ImportError as e:
            logger.error(f"❌ Could not import addon '{addon_name}': {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error loading addon '{addon_name}': {e}")

    return setup_modules


def discover_addon_urls(addons: list[str]) -> list[str]:
    """Discover URL configurations from addons.

    Args:
        addons: List of addon package names.

    Returns:
        Addon URL module paths (e.g., ['addon1.urls', 'addon2.urls']).
    """
    global addon_urls
    addon_urls = []

    for addon_name in addons:
        try:
            spec = importlib.util.find_spec(f"{addon_name}.urls")
            if spec is not None and spec.origin is not None:
                addon_urls.append(f"{addon_name}.urls")
                logger.info(f"✓ Registered URL config from addon: {addon_name}.urls")
        except Exception as e:
            logger.debug(f"Addon '{addon_name}' has no urls.py: {e}")

    return addon_urls


def load_addons(addons: list[str], env_profile: str) -> list[tuple[str, str]]:
    """Load addon configurations and discover their URLs.

    This is the main entry point for addon integration. It discovers addon setup
    modules (for settings) and addon URL configurations.

    Args:
        addons: List of addon package names.
        env_profile: The resolved environment name (e.g. "production", "development").

    Returns:
        ``(addon_name, absolute path to its setup module file)`` pairs, as returned by
        ``discover_addon_setup_modules``.
    """
    logger.info(
        f"Loading {len(addons)} addon(s): {', '.join(addons) if addons else '(none)'}"
    )

    setup_modules = discover_addon_setup_modules(addons, env_profile)

    discover_addon_urls(addons)

    return setup_modules
