"""
Configuration validation and service availability checks.

Provides fail-fast validation for production/staging and graceful degradation for development.
"""

import logging
from typing import Any

from django.conf import settings
from django.core.checks import Error, Tags, Warning, register
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class DeployTags(Tags):
    """Custom tags for deployment-related checks."""

    deploy = "deploy"


# =============================================================================
# DATABASE CHECKS
# =============================================================================


@register(Tags.database, DeployTags.deploy, deploy=True)
def check_database_configured(app_configs, **kwargs):
    """
    Check that DATABASES['default'] is configured.

    Error ID: fairdm.E100
    """
    errors = []
    databases = getattr(settings, "DATABASES", {})
    default_db = databases.get("default", {})

    if not default_db:
        errors.append(
            Error(
                "DATABASES['default'] is not configured.",
                hint="Set DATABASE_URL environment variable.",
                id="fairdm.E100",
            )
        )

    return errors


@register(Tags.database, DeployTags.deploy, deploy=True)
def check_database_production_ready(app_configs, **kwargs):
    """
    Check that production uses PostgreSQL, not SQLite.

    Error ID: fairdm.E101
    """
    errors = []
    databases = getattr(settings, "DATABASES", {})
    default_db = databases.get("default", {})

    if default_db.get("ENGINE") == "django.db.backends.sqlite3":
        errors.append(
            Error(
                "SQLite is not recommended for production.",
                hint="Set DATABASE_URL to a PostgreSQL connection string.",
                id="fairdm.E101",
            )
        )

    return errors


# =============================================================================
# CACHE CHECKS
# =============================================================================


@register(Tags.caches, DeployTags.deploy, deploy=True)
def check_cache_backend(app_configs, **kwargs):
    """
    Check that production uses persistent cache, not locmem or dummy.

    Error ID: fairdm.E200
    """
    errors = []
    caches = getattr(settings, "CACHES", {})
    default_cache = caches.get("default", {})
    backend = default_cache.get("BACKEND", "")

    development_backends = [
        "django.core.cache.backends.locmem.LocMemCache",
        "django.core.cache.backends.dummy.DummyCache",
    ]

    if backend in development_backends:
        errors.append(
            Error(
                f"Cache backend '{backend}' is not suitable for production.",
                hint="Set CACHE_URL to Redis or Memcached. Example: redis://localhost:6379/1",
                id="fairdm.E200",
            )
        )

    return errors


# =============================================================================
# SECRET KEY CHECKS
# =============================================================================


@register(Tags.security, DeployTags.deploy, deploy=True)
def check_secret_key_exists(app_configs, **kwargs):
    """
    Check that SECRET_KEY is set and not empty.

    Error ID: fairdm.E001
    """
    errors = []
    try:
        secret_key = getattr(settings, "SECRET_KEY", "")
    except ImproperlyConfigured:
        # Django raises ImproperlyConfigured when SECRET_KEY is empty
        secret_key = ""

    if not secret_key:
        errors.append(
            Error(
                "SECRET_KEY is not set or is empty.",
                hint="Set SECRET_KEY environment variable to a random string (50+ characters recommended).",
                id="fairdm.E001",
            )
        )

    return errors


# =============================================================================
# ALLOWED_HOSTS CHECKS
# =============================================================================


@register(Tags.security, DeployTags.deploy, deploy=True)
def check_allowed_hosts_configured(app_configs, **kwargs):
    """
    Check that ALLOWED_HOSTS is not empty.

    Error ID: fairdm.E003
    """
    errors = []
    allowed_hosts = getattr(settings, "ALLOWED_HOSTS", [])

    if not allowed_hosts:
        errors.append(
            Error(
                "ALLOWED_HOSTS is empty.",
                hint="Set DJANGO_ALLOWED_HOSTS environment variable with comma-separated domain names.",
                id="fairdm.E003",
            )
        )

    return errors


@register(Tags.security, DeployTags.deploy, deploy=True)
def check_allowed_hosts_secure(app_configs, **kwargs):
    """
    Check that ALLOWED_HOSTS doesn't contain wildcard '*'.

    Error ID: fairdm.E004
    """
    errors = []
    allowed_hosts = getattr(settings, "ALLOWED_HOSTS", [])

    if "*" in allowed_hosts:
        errors.append(
            Error(
                "ALLOWED_HOSTS contains wildcard '*' - this is insecure for production.",
                hint="Specify explicit domain names instead of '*'.",
                id="fairdm.E004",
            )
        )

    return errors


# =============================================================================
# DEBUG CHECKS
# =============================================================================


@register(Tags.security, DeployTags.deploy, deploy=True)
def check_debug_false(app_configs, **kwargs):
    """
    Check that DEBUG is False in production.

    Error ID: fairdm.E005
    """
    errors = []
    debug = getattr(settings, "DEBUG", False)

    if debug:
        errors.append(
            Error(
                "DEBUG is True - this must be False in production.",
                hint="Set DJANGO_DEBUG=False in production environment.",
                id="fairdm.E005",
            )
        )

    return errors


# =============================================================================
# CELERY CHECKS
# =============================================================================


@register(DeployTags.deploy, deploy=True)
def check_celery_broker(app_configs, **kwargs):
    """
    Check that CELERY_BROKER_URL is configured.

    Error ID: fairdm.E300
    """
    errors = []
    broker_url = getattr(settings, "CELERY_BROKER_URL", "")

    if not broker_url:
        errors.append(
            Error(
                "CELERY_BROKER_URL is not configured.",
                hint="Set CELERY_BROKER_URL environment variable. Example: redis://localhost:6379/0",
                id="fairdm.E300",
            )
        )

    return errors


@register(DeployTags.deploy, deploy=True)
def check_celery_async(app_configs, **kwargs):
    """
    Check that CELERY_TASK_ALWAYS_EAGER is False (tasks run async).

    Error ID: fairdm.E301
    """
    errors = []
    always_eager = getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False)

    if always_eager:
        errors.append(
            Error(
                "CELERY_TASK_ALWAYS_EAGER is True - tasks will run synchronously.",
                hint="Set CELERY_TASK_ALWAYS_EAGER=False in production to enable asynchronous task processing.",
                id="fairdm.E301",
            )
        )

    return errors


# =============================================================================
# LEGACY VALIDATION FUNCTIONS (TO BE DEPRECATED)
# =============================================================================


def validate_services(env_profile: str, settings_dict: dict[str, Any]) -> None:
    """
    DEPRECATED: Use Django's check framework instead.

    Validate that required services are configured correctly.

    This function is deprecated and will be removed in a future version.
    Use `python manage.py check --deploy` to validate production readiness.

    Args:
        env_profile: The environment profile (production, staging, development)
        settings_dict: The settings dictionary to validate

    Raises:
        ImproperlyConfigured: In production/staging if required services are missing
    """
    import warnings

    warnings.warn(
        "validate_services() is deprecated. Use 'python manage.py check --deploy' instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    is_production_like = env_profile in ("production", "staging")
    errors = []
    warnings_list = []

    # =============================================================================
    # DATABASE VALIDATION
    # =============================================================================

    databases = settings_dict.get("DATABASES", {})
    default_db = databases.get("default", {})

    if not default_db:
        msg = "DATABASES['default'] is not configured. Set DATABASE_URL environment variable."
        if is_production_like:
            errors.append(msg)
        else:
            warnings_list.append(msg)
    elif default_db.get("ENGINE") == "django.db.backends.sqlite3" and is_production_like:
        errors.append("SQLite is not recommended for production. Set DATABASE_URL to a PostgreSQL connection string.")

    # =============================================================================
    # CACHE VALIDATION
    # =============================================================================

    caches = settings_dict.get("CACHES", {})
    default_cache = caches.get("default", {})
    cache_backend = default_cache.get("BACKEND", "")

    if "locmem" in cache_backend.lower() or "dummy" in cache_backend.lower():
        msg = (
            f"Cache backend '{cache_backend}' is not suitable for production. "
            "Set REDIS_URL environment variable for Redis cache."
        )
        if is_production_like:
            errors.append(msg)
        else:
            warnings_list.append(msg)

    # =============================================================================
    # SECRET KEY VALIDATION
    # =============================================================================

    secret_key = settings_dict.get("SECRET_KEY", "")

    if not secret_key:
        errors.append("SECRET_KEY is not set. Set DJANGO_SECRET_KEY environment variable.")
    elif "insecure" in secret_key.lower() and is_production_like:
        errors.append(
            "SECRET_KEY contains 'insecure' - this appears to be a development key. "
            "Set a proper DJANGO_SECRET_KEY for production."
        )
    elif len(secret_key) < 50:
        msg = f"SECRET_KEY is too short ({len(secret_key)} characters). Recommended: 50+ characters."
        if is_production_like:
            errors.append(msg)
        else:
            warnings_list.append(msg)

    # =============================================================================
    # ALLOWED_HOSTS VALIDATION
    # =============================================================================

    allowed_hosts = settings_dict.get("ALLOWED_HOSTS", [])

    if is_production_like:
        if not allowed_hosts:
            errors.append("ALLOWED_HOSTS is empty. Set DJANGO_ALLOWED_HOSTS environment variable.")
        elif "*" in allowed_hosts:
            errors.append(
                "ALLOWED_HOSTS contains '*' (wildcard). This is insecure for production. "
                "Set specific domains in DJANGO_ALLOWED_HOSTS."
            )

    # =============================================================================
    # DEBUG MODE VALIDATION
    # =============================================================================

    debug = settings_dict.get("DEBUG", False)

    if debug and is_production_like:
        errors.append(
            "DEBUG is True in production/staging. This is a security risk. Ensure DJANGO_DEBUG is set to False."
        )

    # =============================================================================
    # HTTPS/SSL VALIDATION
    # =============================================================================

    if is_production_like:
        if not settings_dict.get("SECURE_SSL_REDIRECT", False):
            warnings_list.append("SECURE_SSL_REDIRECT is False. Consider enabling HTTPS redirect in production.")

        if settings_dict.get("SESSION_COOKIE_SECURE", True) is False:
            errors.append("SESSION_COOKIE_SECURE must be True in production.")

        if settings_dict.get("CSRF_COOKIE_SECURE", True) is False:
            errors.append("CSRF_COOKIE_SECURE must be True in production.")

    # =============================================================================
    # CELERY BROKER VALIDATION
    # =============================================================================

    celery_broker = settings_dict.get("CELERY_BROKER_URL", "")
    celery_eager = settings_dict.get("CELERY_TASK_ALWAYS_EAGER", False)

    if celery_eager and is_production_like:
        errors.append(
            "CELERY_TASK_ALWAYS_EAGER is True. Async tasks will run synchronously. "
            "Set REDIS_URL to enable proper task queue."
        )

    if not celery_broker and is_production_like:
        errors.append(
            "CELERY_BROKER_URL is not set. Background tasks require Redis. Set REDIS_URL environment variable."
        )

    # =============================================================================
    # REPORT FINDINGS
    # =============================================================================

    # Log warnings
    for warning in warnings_list:
        logger.warning(f"Configuration Warning: {warning}")

    # Fail fast in production/staging if errors exist
    if errors:
        error_message = "\n\n".join(
            [
                "❌ Configuration Validation Failed",
                f"Environment: {env_profile}",
                "",
                "The following configuration errors were detected:",
                "",
                *[f"  • {error}" for error in errors],
                "",
                "Please fix these issues before starting the application.",
            ]
        )

        if is_production_like:
            raise ImproperlyConfigured(error_message)
        else:
            logger.error(error_message)
            logger.warning(
                "⚠️  Continuing in development mode despite configuration errors. "
                "These would prevent startup in production."
            )


def validate_addon_module(addon_name: str, module_path: str, env_profile: str) -> bool:
    """
    Validate that an addon's setup module can be imported.

    Args:
        addon_name: The name of the addon package
        module_path: The path to the addon's setup module
        env_profile: The environment profile (production, staging, development)

    Returns:
        bool: True if the module is valid, False otherwise

    Raises:
        ImproperlyConfigured: In production/staging if addon module is invalid
    """
    is_production_like = env_profile in ("production", "staging")

    try:
        from importlib import import_module

        import_module(module_path)
        return True
    except ImportError as e:
        error_msg = f"Addon '{addon_name}' setup module '{module_path}' could not be imported: {e}"

        if is_production_like:
            raise ImproperlyConfigured(error_msg) from e
        else:
            logger.debug(f"⚠️  {error_msg} (skipping in development)")
            return False
    except Exception as e:
        error_msg = f"Addon '{addon_name}' setup module '{module_path}' raised an error: {e}"

        if is_production_like:
            raise ImproperlyConfigured(error_msg) from e
        else:
            logger.debug(f"❌ {error_msg} (skipping in development)")
            return False
