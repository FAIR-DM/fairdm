"""
Configuration validation and service availability checks.

Provides fail-fast validation for production and graceful degradation for development.
"""

import logging

from django.conf import settings
from django.core.checks import Error, Tags, register
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class DeployTags(Tags):
    """Custom tags for deployment-related checks."""

    deploy = "deploy"
    #: The subset FairDMConfig.ready() runs and aggregates in production
    #: (research R5) — withheld from the Celery checks, since a portal may
    #: legitimately run without a worker (FR-013, FR-016).
    production_critical = "production_critical"


# =============================================================================
# DATABASE CHECKS
# =============================================================================


@register(Tags.database, DeployTags.deploy, DeployTags.production_critical, deploy=True)
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


@register(Tags.database, DeployTags.deploy, DeployTags.production_critical, deploy=True)
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


@register(Tags.database, DeployTags.deploy, DeployTags.production_critical, deploy=True)
def check_database_usable(app_configs, **kwargs):
    """
    Check that DATABASES['default'] carries a usable database name — distinct
    from being absent outright (fairdm.E100), this catches a syntactically
    malformed DATABASE_URL that parses to a present dict with no NAME (e.g.
    ``postgresql://`` with nothing after the scheme) (edge case, FR-017).

    Error ID: fairdm.E102
    """
    errors = []
    databases = getattr(settings, "DATABASES", {})
    default_db = databases.get("default", {})

    if default_db and not default_db.get("NAME"):
        errors.append(
            Error(
                "DATABASES['default'] is configured but has no NAME — "
                "DATABASE_URL is likely malformed.",
                hint="Set DATABASE_URL to a complete PostgreSQL connection string.",
                id="fairdm.E102",
            )
        )

    return errors


# =============================================================================
# CACHE CHECKS
# =============================================================================


#: Backends shared across processes, suitable for production (FR-016, FR-017).
#: Anything else — absent, empty, locmem, dummy, filebased, or unrecognised —
#: is per-process or per-filesystem and fails the check.
SHARED_CACHE_BACKENDS = frozenset(
    {
        "django_redis.cache.RedisCache",
        "django.core.cache.backends.memcached.PyMemcacheCache",
        "django.core.cache.backends.memcached.PyLibMCCache",
    }
)


@register(Tags.caches, DeployTags.deploy, DeployTags.production_critical, deploy=True)
def check_cache_backend(app_configs, **kwargs):
    """
    Check that production uses a shared cache backend (e.g. Redis or
    Memcached), not an absent, empty, or per-process backend such as locmem,
    dummy or filebased.

    Error ID: fairdm.E200
    """
    errors = []
    caches = getattr(settings, "CACHES", {})
    default_cache = caches.get("default", {})
    backend = default_cache.get("BACKEND", "")

    if backend not in SHARED_CACHE_BACKENDS:
        errors.append(
            Error(
                f"Cache backend '{backend or '(none)'}' is not a shared cache suitable for production.",
                hint="Set CACHE_URL to Redis or Memcached. Example: redis://localhost:6379/1",
                id="fairdm.E200",
            )
        )

    return errors


# =============================================================================
# SECRET KEY CHECKS
# =============================================================================


#: Django's own generated-development-key prefix. FairDM's shipped fallback
#: (fairdm/conf/environment.py) carries it too, so this also catches a
#: portal that boots on FairDM's own published default (SC-006).
INSECURE_SECRET_KEY_PREFIX = "django-insecure-"  # noqa: S105 — a prefix, not a password


@register(Tags.security, DeployTags.deploy, DeployTags.production_critical, deploy=True)
def check_secret_key_exists(app_configs, **kwargs):
    """
    Check that SECRET_KEY is set, non-empty, and not a published or
    otherwise insecure value — FairDM's own error-severity check, kept
    alongside Django's warning-severity security.W009 so this one can
    actually block a boot (research R5).

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
    elif secret_key.startswith(INSECURE_SECRET_KEY_PREFIX):
        errors.append(
            Error(
                "SECRET_KEY carries an insecure, published value.",
                hint="Set DJANGO_SECRET_KEY to a private, randomly generated value.",
                id="fairdm.E001",
            )
        )

    return errors


# =============================================================================
# ALLOWED_HOSTS CHECKS
# =============================================================================


@register(Tags.security, DeployTags.deploy, DeployTags.production_critical, deploy=True)
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


@register(Tags.security, DeployTags.deploy, DeployTags.production_critical, deploy=True)
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


@register(Tags.security, DeployTags.deploy, DeployTags.production_critical, deploy=True)
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
# ADDON VALIDATION
# =============================================================================


def validate_addon_module(addon_name: str, module_path: str, env_profile: str) -> bool:
    """
    Validate that an addon's setup module can be found.

    Note: We only check if the module can be found, not imported, because
    addon setup modules are designed to be executed via split_settings.include()
    which provides them with the necessary scope (INSTALLED_APPS, etc.).

    Args:
        addon_name: The name of the addon package
        module_path: The path to the addon's setup module
        env_profile: The resolved environment name (e.g. "production", "development")

    Returns:
        bool: True if the module is valid, False otherwise

    Raises:
        ImproperlyConfigured: In production if addon module is invalid
    """
    is_production_like = env_profile == "production"

    try:
        import importlib.util

        # Only check if the module spec can be found, don't actually import it
        spec = importlib.util.find_spec(module_path)
        if spec is None or spec.origin is None:
            raise ModuleNotFoundError(f"No module named '{module_path}'")

        return True
    except (ImportError, ModuleNotFoundError) as e:
        error_msg = (
            f"Addon '{addon_name}' setup module '{module_path}' could not be found: {e}"
        )

        if is_production_like:
            raise ImproperlyConfigured(error_msg) from e
        else:
            logger.debug(f"⚠️  {error_msg} (skipping in development)")
            return False
    except Exception as e:
        error_msg = (
            f"Addon '{addon_name}' setup module '{module_path}' validation failed: {e}"
        )

        if is_production_like:
            raise ImproperlyConfigured(error_msg) from e
        else:
            logger.debug(f"❌ {error_msg} (skipping in development)")
            return False
