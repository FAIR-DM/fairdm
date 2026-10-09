"""System checks that validate the configuration and service availability.

Provides fail-fast validation for production and graceful degradation for development.
"""

import logging

from django.conf import settings
from django.core.checks import Error, Tags, register
from django.core.checks import Warning as CheckWarning
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)


class DeployTags(Tags):
    """Custom tags for deployment-related checks."""

    deploy = "deploy"
    #: The subset `FairDMConfig.ready()` aggregates in production. It excludes the Celery
    #: checks, since a portal may run without a worker.
    production_critical = "production_critical"


@register(Tags.database, DeployTags.deploy, DeployTags.production_critical, deploy=True)
def check_database_configured(app_configs, **kwargs):
    """Report fairdm.E100 when DATABASES['default'] is not configured."""
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
    """Report fairdm.E101 when production uses SQLite instead of PostgreSQL."""
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
    """Report fairdm.E102 when DATABASES['default'] has no NAME, as a malformed DATABASE_URL leaves it."""
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


#: Backends shared across processes. Anything else (locmem, dummy, filebased, unset) is
#: per-process or per-filesystem and fails the check.
SHARED_CACHE_BACKENDS = frozenset(
    {
        "django_redis.cache.RedisCache",
        "django.core.cache.backends.memcached.PyMemcacheCache",
        "django.core.cache.backends.memcached.PyLibMCCache",
    }
)

#: The baseline cache is always Redis-shaped, so BACKEND cannot tell a real deployment from
#: an unset REDIS_URL. This unresolvable placeholder LOCATION stands in for the latter.
UNCONFIGURED_REDIS_LOCATION = "redis://unconfigured.invalid:6379/0"


@register(Tags.caches, DeployTags.deploy, DeployTags.production_critical, deploy=True)
def check_cache_backend(app_configs, **kwargs):
    """Report fairdm.E200 when the cache is not a shared backend, or is the baseline's placeholder."""
    errors = []
    caches = getattr(settings, "CACHES", {})
    default_cache = caches.get("default", {})
    backend = default_cache.get("BACKEND", "")
    location = default_cache.get("LOCATION", "")

    if backend not in SHARED_CACHE_BACKENDS or location == UNCONFIGURED_REDIS_LOCATION:
        errors.append(
            Error(
                f"Cache backend '{backend or '(none)'}' is not a shared cache suitable for production.",
                hint="Set REDIS_URL to a Redis instance. Example: redis://localhost:6379/1",
                id="fairdm.E200",
            )
        )

    return errors


#: Django's generated development-key prefix, which FairDM's shipped fallback also carries.
INSECURE_SECRET_KEY_PREFIX = "django-insecure-"  # noqa: S105 — a prefix, not a password

#: The length below which Django's own security.W009 calls a key too easily
#: brute-forced. Reproduced at error severity so it can block a boot.
MINIMUM_SECRET_KEY_LENGTH = 50


@register(Tags.security, DeployTags.deploy, DeployTags.production_critical, deploy=True)
def check_secret_key_exists(app_configs, **kwargs):
    """Report fairdm.E001 when SECRET_KEY is empty, insecure or too short."""
    errors = []
    try:
        secret_key = getattr(settings, "SECRET_KEY", "")
    except ImproperlyConfigured:
        # Django raises this when SECRET_KEY is empty.
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
                hint="Set DJANGO_SECRET_KEY to a private, randomly generated value of 50+ characters.",
                id="fairdm.E001",
            )
        )
    elif len(secret_key) < MINIMUM_SECRET_KEY_LENGTH:
        errors.append(
            Error(
                f"SECRET_KEY is only {len(secret_key)} characters long.",
                hint=(
                    "Set DJANGO_SECRET_KEY to a random string of "
                    f"{MINIMUM_SECRET_KEY_LENGTH}+ characters."
                ),
                id="fairdm.E001",
            )
        )

    return errors


@register(Tags.security, DeployTags.deploy, DeployTags.production_critical, deploy=True)
def check_allowed_hosts_configured(app_configs, **kwargs):
    """Report fairdm.E003 when ALLOWED_HOSTS is empty."""
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
    """Report fairdm.E004 when ALLOWED_HOSTS contains the wildcard '*'."""
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


@register(Tags.security, DeployTags.deploy, DeployTags.production_critical, deploy=True)
def check_debug_false(app_configs, **kwargs):
    """Report fairdm.E005 when DEBUG is True."""
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


#: Cookie-name prefixes a browser silently discards unless the cookie is sent with
#: ``Secure`` (RFC 6265bis, section 4.1.3).
BROWSER_ENFORCED_SECURE_COOKIE_PREFIXES = ("__Secure-", "__Host-")

#: Each cookie-name setting beside the flag that decides whether it is sent with ``Secure``.
PREFIX_CHECKED_COOKIE_SETTINGS = (
    ("CSRF_COOKIE_NAME", "CSRF_COOKIE_SECURE"),
    ("SESSION_COOKIE_NAME", "SESSION_COOKIE_SECURE"),
    ("LANGUAGE_COOKIE_NAME", "LANGUAGE_COOKIE_SECURE"),
)


@register(Tags.security)
def check_secure_cookie_prefixes_match_secure_flag(app_configs, **kwargs):
    """Report fairdm.E006 when a `__Secure-` or `__Host-` cookie name is paired with an insecure flag."""
    errors = []

    for name_setting, secure_setting in PREFIX_CHECKED_COOKIE_SETTINGS:
        name = getattr(settings, name_setting, "") or ""
        if not name.startswith(BROWSER_ENFORCED_SECURE_COOKIE_PREFIXES):
            continue
        if getattr(settings, secure_setting, False):
            continue

        prefix = next(
            candidate
            for candidate in BROWSER_ENFORCED_SECURE_COOKIE_PREFIXES
            if name.startswith(candidate)
        )
        errors.append(
            Error(
                f"{name_setting} is {name!r} while {secure_setting} is False. "
                f"Browsers discard a {prefix} cookie that is not sent with the "
                "Secure attribute, so this cookie is never stored.",
                hint=(
                    f"Either set {secure_setting}=True, or drop the {prefix} "
                    f"prefix from {name_setting} for environments served over "
                    "plain HTTP."
                ),
                id="fairdm.E006",
            )
        )

    return errors


@register(Tags.security, DeployTags.deploy, deploy=True)
def check_api_proxy_count(app_configs, **kwargs):
    """Report fairdm.W601 when REST_FRAMEWORK has no NUM_PROXIES.

    Without it, the API takes a caller's address from the ``X-Forwarded-For`` header, which the
    caller writes, so the request limits can be avoided. Any value an operator sets, ``0`` and
    ``None`` included, is a decision and is left alone.
    """
    if "NUM_PROXIES" in getattr(settings, "REST_FRAMEWORK", {}):
        return []
    return [
        CheckWarning(
            "REST_FRAMEWORK has no NUM_PROXIES, so the API limits count callers by a header "
            "the caller controls.",
            hint=(
                "Set REST_FRAMEWORK['NUM_PROXIES'] to the number of proxies in front of the "
                "portal. See docs/portal-administration/api-limits.md."
            ),
            id="fairdm.W601",
        )
    ]


@register(DeployTags.deploy, deploy=True)
def check_celery_broker(app_configs, **kwargs):
    """Report fairdm.E300 when CELERY_BROKER_URL is not configured."""
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
    """Report fairdm.E301 when CELERY_TASK_ALWAYS_EAGER is True."""
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


#: The command that installs the portal roles. The roles check stands down while it runs:
#: `post_migrate` is the only thing that creates them, and the check fires before it.
MIGRATE_COMMAND_NAME = "migrate"

#: Exceptions that mean the database cannot be read (unmigrated table, no engine to resolve,
#: a test harness refusing database access). A check that queries one treats them as
#: "nothing to report", so an unmigrated database does not look like a misconfigured portal.
UNREADABLE_DATABASE = (
    OperationalError,
    ProgrammingError,
    ImproperlyConfigured,
    RuntimeError,
)


@register(DeployTags.deploy, DeployTags.production_critical, deploy=True)
def check_portal_roles_present(app_configs, **kwargs):
    """Report fairdm.E500 when a shipped portal role is missing from the database."""
    import sys

    from django.contrib.auth.models import Group

    if MIGRATE_COMMAND_NAME in sys.argv:
        return []

    from fairdm.portal_roles import PortalRoles

    try:
        existing = set(
            Group.objects.filter(name__in=PortalRoles.shipped_names()).values_list(
                "name", flat=True
            )
        )
    except UNREADABLE_DATABASE:
        return []

    missing = [name for name in PortalRoles.shipped_names() if name not in existing]
    if not missing:
        return []

    return [
        Error(
            f"FairDM role(s) missing from the database: {', '.join(missing)}.",
            hint="Run `manage.py migrate` to install them.",
            id="fairdm.E500",
        )
    ]


@register(DeployTags.deploy, DeployTags.production_critical, deploy=True)
def check_dev_accounts_absent(app_configs, **kwargs):
    """Report fairdm.E501 when development accounts exist outside development."""
    from django.apps import apps
    from django.contrib.auth import get_user_model

    from fairdm.apps import NON_PRODUCTION_ENVIRONMENTS
    from fairdm.management.commands.create_dev_accounts import (
        DEV_ACCOUNT_EMAILS,
        EXAMPLE_ACCOUNT_EMAILS,
    )

    # `check --deploy` runs every deploy check in any environment, and these accounts
    # belong in development.
    if (
        apps.get_app_config("fairdm").resolved_environment()
        in NON_PRODUCTION_ENVIRONMENTS
    ):
        return []

    Person = get_user_model()

    try:
        found = sorted(
            Person.objects.filter(
                email__in=DEV_ACCOUNT_EMAILS | EXAMPLE_ACCOUNT_EMAILS
            ).values_list("email", flat=True)
        )
    except UNREADABLE_DATABASE:
        return []

    if not found:
        return []

    return [
        Error(
            f"Development account(s) present on a portal outside development: "
            f"{', '.join(found)}.",
            hint=(
                "These accounts share a password published in the "
                "documentation. Remove them, or confirm this portal really "
                "is in development."
            ),
            id="fairdm.E501",
        )
    ]


def _parler_languages_missing_from_languages(
    languages, parler_languages, parler_default_language_code=None
) -> set[str]:
    """Return the PARLER_LANGUAGES codes django-parler would reject.

    A code is rejected when it is neither a LANGUAGES code nor has a LANGUAGES code as its
    base subtag (``fr-ca`` is accepted when LANGUAGES has ``fr``). The ``"default"`` key holds
    fallback configuration rather than a site's choices, but parler validates its ``code`` too,
    falling back to PARLER_DEFAULT_LANGUAGE_CODE, so it is checked as well.

    Args:
        languages: The LANGUAGES setting.
        parler_languages: The PARLER_LANGUAGES setting.
        parler_default_language_code: The PARLER_DEFAULT_LANGUAGE_CODE setting.

    Returns:
        The rejected language codes.
    """
    language_codes = {code for code, _ in languages}

    def rejected(code):
        return (
            bool(code)
            and code not in language_codes
            and code.split("-")[0] not in language_codes
        )

    missing = set()
    defaults = parler_languages.get("default") or {}
    default_code = defaults.get("code", parler_default_language_code)
    if rejected(default_code):
        missing.add(default_code)
    for site_id, choices in parler_languages.items():
        if site_id == "default":
            continue
        for choice in choices:
            if rejected(choice.get("code")):
                missing.add(choice["code"])
    return missing


def parler_languages_errors(
    languages, parler_languages, parler_default_language_code=None
) -> list[Error]:
    """Return fairdm.E400 for the given setting values.

    Takes values rather than reading ``settings`` so the rule can run before settings load,
    as ``raise_on_parler_languages_mismatch`` does.

    Args:
        languages: The LANGUAGES setting.
        parler_languages: The PARLER_LANGUAGES setting.
        parler_default_language_code: The PARLER_DEFAULT_LANGUAGE_CODE setting.

    Returns:
        One error naming the missing codes, or an empty list when the settings agree.
    """
    missing = _parler_languages_missing_from_languages(
        languages or [], parler_languages or {}, parler_default_language_code
    )
    if not missing:
        return []
    return [
        Error(
            "PARLER_LANGUAGES names language code(s) LANGUAGES does not "
            f"include: {', '.join(sorted(missing))}.",
            hint="Add the missing code(s) to LANGUAGES, or remove them from "
            "PARLER_LANGUAGES and PARLER_DEFAULT_LANGUAGE_CODE, so the "
            "settings agree.",
            id="fairdm.E400",
        )
    ]


def raise_on_parler_languages_mismatch(
    languages, parler_languages, parler_default_language_code=None
) -> None:
    """Refuse to continue when PARLER_LANGUAGES and LANGUAGES disagree, naming both.

    Called from ``fairdm.conf.setup()`` on the composed settings, the only point ahead of every
    app's models, and again from ``FairDMConfig.import_models()`` on the loaded settings, which
    sees assignments a portal makes after ``setup()``. A portal that does both still gets
    parler's own error.

    Args:
        languages: The LANGUAGES setting.
        parler_languages: The PARLER_LANGUAGES setting.
        parler_default_language_code: The PARLER_DEFAULT_LANGUAGE_CODE setting.

    Raises:
        SystemCheckError: The two settings disagree.
    """
    from django.core.management.base import SystemCheckError

    errors = parler_languages_errors(
        languages, parler_languages, parler_default_language_code
    )
    if errors:
        raise SystemCheckError(
            "FairDM configuration is invalid:\n\n"
            + "\n\n".join(str(error) for error in errors)
        )


@register(Tags.translation)
def check_parler_languages_subset_of_languages(app_configs, **kwargs):
    """Report fairdm.E400 when PARLER_LANGUAGES names a code LANGUAGES lacks."""
    return parler_languages_errors(
        getattr(settings, "LANGUAGES", []),
        getattr(settings, "PARLER_LANGUAGES", {}),
        getattr(settings, "PARLER_DEFAULT_LANGUAGE_CODE", None),
    )


def validate_addon_module(addon_name: str, module_path: str, env_profile: str) -> bool:
    """Validate that an addon's setup module can be found.

    Only checks that the module can be found, not imported, because addon setup modules are
    executed via ``split_settings.include()``, which supplies the scope they need.

    Args:
        addon_name: The name of the addon package.
        module_path: The path to the addon's setup module.
        env_profile: The resolved environment name (e.g. "production", "development").

    Returns:
        ``True`` if the module is valid, ``False`` otherwise.

    Raises:
        ImproperlyConfigured: The module is invalid and the environment is production.
        ModuleNotFoundError: The module cannot be found. Handled inside this function, so
            callers see ``False``, or ``ImproperlyConfigured`` in production.
    """
    is_production_like = env_profile == "production"

    try:
        import importlib.util

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
            logger.warning(f"⚠️  {error_msg} (skipping in development)")
            return False
    except Exception as e:
        error_msg = (
            f"Addon '{addon_name}' setup module '{module_path}' validation failed: {e}"
        )

        if is_production_like:
            raise ImproperlyConfigured(error_msg) from e
        else:
            logger.warning(f"❌ {error_msg} (skipping in development)")
            return False
