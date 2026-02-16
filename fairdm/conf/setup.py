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
from .checks import validate_services

logger = logging.getLogger(__name__)


def setup(
    apps: list[str] | None = None,
    addons: list[str] | None = None,
    base_dir: Path | None = None,
    env_file: str | None = None,
    **overrides,
) -> None:
    """
    Initialize FairDM configuration with environment-specific settings.

    This is the main entry point for portal configuration. It:
    1. Determines the environment profile (production, staging, development)
    2. Loads environment variables
    3. Injects base settings into the caller's global namespace
    4. Loads addon configurations
    5. Validates the configuration
    6. Applies any user overrides

    Args:
        apps: List of portal-specific Django apps to include in INSTALLED_APPS
        addons: List of FairDM addon packages to enable
        base_dir: Project base directory (auto-detected if not provided)
        env_file: Optional path to .env file to load
        **overrides: Additional settings to override after profile loading

    Example:
        >>> import fairdm
        >>> fairdm.setup(
        ...     apps=["my_portal_app"],
        ...     addons=["fairdm_discussions"],
        ... )
    """
    apps = apps or []
    addons = addons or []

    # Determine environment profile
    env_profile = os.environ.get("DJANGO_ENV", "production")
    if env_profile not in ("production", "staging", "development"):
        logger.warning(
            f"Unknown DJANGO_ENV='{env_profile}'. Defaulting to 'production'. "
            "Valid options: production, staging, development"
        )
        env_profile = "production"

    logger.info(f"🚀 FairDM Configuration: {env_profile} profile")

    # Get caller's global namespace (where settings will be injected)
    caller_globals = inspect.stack()[1][0].f_globals

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
        logger.debug(f"Loaded environment file: {env_path} (overwrite={is_custom_file})")

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
    settings_dir = Path(__file__).parent / "settings"

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
    ]

    include(*settings_modules, scope=caller_globals)

    # Load environment-specific overrides
    env_override_files = {
        "development": "development.py",
        "staging": "staging.py",
    }

    if env_profile in env_override_files:
        override_file = env_override_files[env_profile]
        override_path = Path(__file__).parent / override_file
        if override_path.exists():
            logger.info(f"Applying {env_profile} overrides from {override_file}")
            include(override_file, scope=caller_globals)

    # Load addon configurations
    if addons:
        addon_setup_modules = load_addons(addons, env_profile)
        if addon_setup_modules:
            include(*addon_setup_modules, scope=caller_globals)

    # Apply user overrides
    if overrides:
        logger.info(f"Applying {len(overrides)} custom override(s)")
        caller_globals.update(overrides)

    # Note: Configuration validation is now handled by Django's check framework.
    # Run `python manage.py check --deploy` to validate production readiness.
    # The old validate_services() function is deprecated.

    logger.info("✅ Configuration complete")


# Export addon_urls for backward compatibility
from .addons import addon_urls  # noqa: E402, F401
