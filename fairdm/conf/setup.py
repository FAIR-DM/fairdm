"""
FairDM configuration setup entry point.

This module provides the main `setup()` function that portals call to initialize
their configuration. It handles profile selection, environment loading, and addon integration.
"""

import inspect
import logging
import os
from pathlib import Path

import environ
from split_settings.tools import include

from .addons import load_addons

logger = logging.getLogger(__name__)


def setup(
    apps: list[str] | None = None,
    addons: list[str] | None = None,
    base_dir: Path | None = None,
    env_file: str | None = None,
) -> None:
    """
    Initialize FairDM configuration with environment-specific settings.

    This is the main entry point for portal configuration. It:
    1. Determines the resolved environment (FR-007)
    2. Loads environment variables
    3. Composes settings into the caller's global namespace in five layers (FR-008)
    4. Loads addon configurations
    5. Runs configuration checks (see ``FairDMConfig.ready()``)

    A portal overrides a setting FairDM owns by assigning to it after this
    call returns — the only supported mechanism (FR-012).

    Args:
        apps: List of portal-specific Django apps to include in INSTALLED_APPS
        addons: List of FairDM addon packages to enable
        base_dir: Project base directory (auto-detected if not provided)
        env_file: Optional path to .env file to load

    Example:
        >>> import fairdm
        >>> fairdm.setup(
        ...     apps=["my_portal_app"],
        ...     addons=["fairdm_discussions"],
        ... )
    """
    apps = apps or []
    addons = addons or []

    # Determine the resolved environment: taken literally from DJANGO_ENV, with
    # no normalisation and no allowlist (FR-007, FR-010).
    env_profile = os.environ.get("DJANGO_ENV", "production")

    logger.info(f"🚀 FairDM Configuration: {env_profile} environment")

    # Get caller's global namespace (where settings will be injected)
    caller_globals = inspect.stack()[1][0].f_globals

    # Capture the portal's settings-module directory now, before __file__ is
    # overwritten below for split_settings' relative-include resolution
    # (research R4). The portal's override module, if any, lives beside it —
    # anchored to the settings module rather than a hardcoded directory name
    # (FR-011). A settings module with no usable __file__ (generated, or
    # imported from an archive) cannot be anchored; the lookup is skipped.
    portal_settings_dir: Path | None = None
    caller_file = caller_globals.get("__file__")
    if caller_file:
        try:
            portal_settings_dir = Path(caller_file).resolve(strict=True).parent
        except OSError:
            portal_settings_dir = None
    if portal_settings_dir is None:
        logger.warning(
            "Could not determine the portal's settings module directory; "
            "its environment override module (if any) will not be looked up."
        )

    # Determine base directory
    if not base_dir:
        base_dir = Path(caller_globals["__file__"]).resolve(strict=True).parent.parent

    # Load environment variables
    from .environment import env

    # Load environment files in order of precedence (later files override earlier)
    env_files_to_load = []

    # 1. Base environment file (if exists)
    if (base_dir / "stack.env").exists():
        env_files_to_load.append(str(base_dir / "stack.env"))

    # 2. Environment-specific file (if exists)
    env_specific_file = base_dir / f"stack.{env_profile}.env"
    if env_specific_file.exists():
        env_files_to_load.append(str(env_specific_file))

    # 3. Custom env file (if provided)
    if env_file and Path(env_file).exists():
        env_files_to_load.append(env_file)

    # Load all env files
    for env_path in env_files_to_load:
        # Use overwrite=True for custom env files to allow explicit overrides
        # Base files (stack.env, stack.{profile}.env) respect existing env vars
        is_custom_file = env_path == env_file
        environ.Env.read_env(env_path, overwrite=is_custom_file)
        logger.debug(
            f"Loaded environment file: {env_path} (overwrite={is_custom_file})"
        )

    # Inject essential variables into caller's namespace
    caller_globals.update(
        {
            "env": env,
            "BASE_DIR": base_dir,
            "FAIRDM_APPS": apps,
            "DJANGO_ENV": env_profile,
            "__file__": os.path.realpath(__file__),
        }
    )

    # Load all settings modules from settings/ directory (production baseline)
    logger.info("Loading production baseline settings...")

    # Define explicit order for settings modules to ensure dependencies are met
    settings_modules = [
        "settings/apps.py",  # INSTALLED_APPS, MIDDLEWARE, TEMPLATES (needs env, BASE_DIR)
        "settings/security.py",  # SECRET_KEY, ALLOWED_HOSTS, DEBUG, security headers
        "settings/database.py",  # Database configuration
        "settings/cache.py",  # Cache backends
        "settings/static_media.py",  # Static/media file handling
        "settings/celery.py",  # Background task processing
        "settings/auth.py",  # Authentication backends
        "settings/logging.py",  # Logging configuration
        "settings/email.py",  # Email backend
        "settings/addons.py",  # Third-party add-on configurations
        "settings/api.py",  # REST API (DRF, drf-spectacular, CORS) — Feature 011
    ]

    include(*settings_modules, scope=caller_globals)

    # Layer 2 — FairDM's own override module for the resolved environment.
    # Selected by existence, not from a fixed list of permitted names: FairDM
    # ships only development.py, but any name is looked up the same way
    # (FR-009, FR-010).
    fairdm_override = Path(__file__).parent / f"{env_profile}.py"
    if fairdm_override.exists():
        logger.info(f"Applying FairDM {env_profile} overrides from {fairdm_override.name}")
        include(fairdm_override.name, scope=caller_globals)

    # Layer 3 — settings contributed by addons.
    if addons:
        addon_setup_modules = load_addons(addons, env_profile)
        if addon_setup_modules:
            include(*addon_setup_modules, scope=caller_globals)

    # Layer 4 — the portal's own override module for the resolved environment,
    # resolved beside its settings module rather than a hardcoded directory
    # (FR-011). Also selected by existence; skipped without error if absent.
    if portal_settings_dir is not None:
        portal_override = portal_settings_dir / f"{env_profile}.py"
        if portal_override.exists():
            logger.info(f"Applying portal {env_profile} overrides from {portal_override}")
            include(str(portal_override), scope=caller_globals)

    # Layer 5 — assignment after this call returns, in the portal's own
    # settings module. Nothing to do here; that is the portal's own code.

    # Finalize SPECTACULAR_SETTINGS: allow portal developers to override
    # FAIRDM_API_TITLE and FAIRDM_API_DESCRIPTION without touching the dict directly.
    # This must run AFTER all settings files and overrides are applied so that
    # portal-level values shadow the FairDM defaults.
    if "SPECTACULAR_SETTINGS" in caller_globals:
        from fairdm.api.settings import FAIRDM_API_DESCRIPTION as _default_desc
        from fairdm.api.settings import FAIRDM_API_TITLE as _default_title

        spectacular = caller_globals["SPECTACULAR_SETTINGS"]
        title_override = caller_globals.get("FAIRDM_API_TITLE", _default_title)
        desc_override = caller_globals.get("FAIRDM_API_DESCRIPTION", _default_desc)
        spectacular["TITLE"] = title_override
        spectacular["DESCRIPTION"] = desc_override

    # Note: Configuration validation is now handled by Django's check framework.
    # Run `python manage.py check --deploy` to validate production readiness.
    # The old validate_services() function is deprecated.

    logger.info("✅ Configuration complete")


# Export addon_urls for backward compatibility
from .addons import addon_urls  # noqa: F401
