"""
FairDM configuration setup entry point.

This module provides ``setup()``, the single call a portal's settings module
makes to obtain a complete Django configuration (FR-001).

**Resolved environment.** Taken literally from the ``DJANGO_ENV`` environment
variable, defaulting to ``production`` when unset. Not validated against an
allowlist — any name is valid, including one nothing ships an override for
(FR-007, FR-010).

**Environment files**, read in this order, later files not overriding a
variable already set in the process environment except where noted:

1. ``stack.env``, beside the portal's ``base_dir``, if present.
2. ``stack.<environment>.env``, beside ``base_dir``, if present.
3. The explicit ``env_file=`` argument, if given — this one *does* overwrite
   variables already set, including by the two files above (FR-006).

**Layers**, applied in this order, each later layer overriding the same
setting in an earlier one (FR-008):

1. The production baseline — every module under ``fairdm/conf/settings/``.
2. FairDM's own override module for the resolved environment, if it ships
   one — only ``development.py`` today (FR-009).
3. Settings contributed by addons named in the ``addons=`` argument.
4. The portal's own override module for the resolved environment, resolved
   beside its settings module regardless of directory name (FR-011).
5. Assignments the portal's settings module makes after ``setup()`` returns —
   the only supported way to override a FairDM-owned setting (FR-012).

Layers 2 and 4 are both selected by existence, not from a fixed list of
permitted names: if no module named after the resolved environment exists,
that layer is skipped without error (FR-010).
"""

import copy
import inspect
import logging
import os
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured
from split_settings.tools import include

from . import record
from .addons import load_addons

logger = logging.getLogger(__name__)


#: Value types a layer can alter without rebinding the name. Deep-copied when
#: a snapshot is taken, so the change is still visible afterwards.
_MUTABLE_CONTAINERS = (list, dict, set)


def _uppercase_scope(scope: dict) -> dict:
    """Every uppercase key in ``scope`` and its current value — Django's
    settings convention, also used for the bookkeeping keys ``setup()``
    injects itself (research R2)."""
    return {key: value for key, value in scope.items() if key.isupper()}


def _snapshot_scope(scope: dict) -> dict:
    """``_uppercase_scope`` with mutable containers copied out of harm's way.

    A layer does not have to rebind a name to change a setting: FairDM's own
    ``development.py`` writes ``INSTALLED_APPS += [...]``, and ``+=`` on a
    list calls ``__iadd__``, mutating the baseline's own object in place. A
    snapshot that holds a reference to that object sees the mutation on both
    sides of the diff and concludes nothing was written, which credits the
    baseline with a value it did not produce.
    """
    snapshot = {}
    for key, value in scope.items():
        if not key.isupper():
            continue
        if isinstance(value, _MUTABLE_CONTAINERS):
            try:
                value = copy.deepcopy(value)
            except Exception:  # pragma: no cover — defensive
                logger.debug(
                    f"Could not snapshot {key} for provenance; "
                    "falling back to identity comparison"
                )
        snapshot[key] = value
    return snapshot


def _scratch_scope(scope: dict) -> dict:
    """A private copy of ``scope`` an addon's setup module can execute
    against without a change reaching ``scope`` unless deliberately merged
    in afterwards.

    ``include()`` execs a module directly against whatever dict it is
    given, so a shallow copy would still share the object a ``+=`` mutates
    in place — the same hazard ``_snapshot_scope`` guards against, but here
    it matters even when the module never returns: a discarded scratch copy
    that shared the baseline's own ``INSTALLED_APPS`` list would have
    mutated it before raising, corrupting the real scope regardless (T101,
    T102).
    """
    scratch = {}
    for key, value in scope.items():
        if isinstance(value, _MUTABLE_CONTAINERS):
            try:
                value = copy.deepcopy(value)
            except Exception:  # pragma: no cover — defensive
                logger.debug(
                    f"Could not snapshot {key} for an addon's scratch scope; "
                    "falling back to a shared reference"
                )
        scratch[key] = value
    return scratch


def _differs(before_value, after_value) -> bool:
    """Whether a layer changed this container, comparing by value."""
    try:
        return bool(before_value != after_value)
    except Exception:  # pragma: no cover — defensive
        return before_value is not after_value


def _written_keys(before: dict, after: dict) -> list[str]:
    """The uppercase keys a layer wrote: names it introduced, names it
    rebound, and containers it mutated in place."""
    written = []
    for key, value in after.items():
        if key not in before:
            written.append(key)
        elif isinstance(value, _MUTABLE_CONTAINERS):
            if _differs(before[key], value):
                written.append(key)
        elif before[key] is not value:
            written.append(key)
    return sorted(written)


def setup(
    apps: list[str] | None = None,
    addons: list[str] | None = None,
    base_dir: Path | None = None,
    env_file: str | None = None,
) -> None:
    """
    Initialize FairDM configuration with environment-specific settings.

    The main entry point for portal configuration — see the module docstring
    for the resolved environment, the environment files, and the five layers
    this composes into the caller's global namespace.

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

    # The provenance record (FR-019, FR-020, research R2): setup() snapshots
    # the scope's uppercase keys before and after each layer's include() call
    # and records the delta as that layer's contribution. A settings module
    # executes once per process, so a fresh setup() call replaces the record
    # rather than appending to it.
    record.reset()

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

    before = _snapshot_scope(caller_globals)
    include(*settings_modules, scope=caller_globals)
    after = _uppercase_scope(caller_globals)
    record.add_layer(
        "baseline",
        str(Path(__file__).parent / "settings"),
        True,
        _written_keys(before, after),
    )

    # Layer 2 — FairDM's own override module for the resolved environment.
    # Selected by existence, not from a fixed list of permitted names: FairDM
    # ships only development.py, but any name is looked up the same way
    # (FR-009, FR-010).
    fairdm_override = Path(__file__).parent / f"{env_profile}.py"
    fairdm_override_found = fairdm_override.exists()
    before = _snapshot_scope(caller_globals)
    if fairdm_override_found:
        logger.info(
            f"Applying FairDM {env_profile} overrides from {fairdm_override.name}"
        )
        include(fairdm_override.name, scope=caller_globals)
    after = _uppercase_scope(caller_globals)
    record.add_layer(
        "fairdm override",
        str(fairdm_override),
        fairdm_override_found,
        _written_keys(before, after),
    )

    # Layer 3 — settings contributed by addons. Each addon's setup module is
    # applied to a private scratch scope first and merged into the caller's
    # scope only on success, so a module that raises partway through does
    # not leave the composed scope holding its own partial writes (edge
    # case, FR-022) — an isolation include()'s shared-scope contract does
    # not give an addon on its own. A failure is routed through the same
    # unloadable-addon path as one that could not be found at all: fail
    # fast in production, warn and skip elsewhere.
    applied_addon_modules: list[str] = []
    before = _snapshot_scope(caller_globals)
    if addons:
        for addon_name, module_path in load_addons(addons, env_profile):
            scratch = _scratch_scope(caller_globals)
            try:
                include(module_path, scope=scratch)
            except Exception as exc:
                message = (
                    f"Addon '{addon_name}' setup module raised while applying "
                    f"its settings: {exc}"
                )
                if env_profile == "production":
                    raise ImproperlyConfigured(message) from exc
                logger.warning(message)
                continue
            caller_globals.update(scratch)
            applied_addon_modules.append(module_path)
    after = _uppercase_scope(caller_globals)
    record.add_layer(
        "addons",
        ", ".join(applied_addon_modules) if applied_addon_modules else None,
        bool(applied_addon_modules),
        _written_keys(before, after),
    )

    # Layer 4 — the portal's own override module for the resolved environment,
    # resolved beside its settings module rather than a hardcoded directory
    # (FR-011). Also selected by existence; skipped without error if absent.
    portal_override: Path | None = None
    portal_override_found = False
    before = _snapshot_scope(caller_globals)
    if portal_settings_dir is not None:
        portal_override = portal_settings_dir / f"{env_profile}.py"
        portal_override_found = portal_override.exists()
        if portal_override_found:
            logger.info(
                f"Applying portal {env_profile} overrides from {portal_override}"
            )
            include(str(portal_override), scope=caller_globals)
    after = _uppercase_scope(caller_globals)
    record.add_layer(
        "portal override",
        str(portal_override) if portal_override else None,
        portal_override_found,
        _written_keys(before, after),
    )

    # Layer 5 — assignment after this call returns, in the portal's own
    # settings module. Nothing to do here; that is the portal's own code.
    #
    # No FairDM-owned setting requires special-case handling here (D10): the
    # REST API schema's title and description are finalised entirely within
    # settings/api.py, the module that owns them. A portal overrides that
    # module's dict directly after this call, the same ordinary mechanism as
    # any other FairDM-owned setting.

    # Configuration validation is handled entirely by Django's check
    # framework (FR-018) — see fairdm/conf/checks.py and FairDMConfig.ready().
    # Run `python manage.py check --deploy` to validate production readiness.
    #
    # One exception, and only because the check framework cannot reach it:
    # django-parler validates PARLER_LANGUAGES against LANGUAGES on import of
    # any parler-model app, which happens before any check runs. This is the
    # only point ahead of every such app, a portal's own included (D11).
    from django.conf import global_settings

    from fairdm.conf.checks import raise_on_parler_languages_mismatch

    raise_on_parler_languages_mismatch(
        caller_globals.get("LANGUAGES", global_settings.LANGUAGES),
        caller_globals.get("PARLER_LANGUAGES", {}),
        caller_globals.get("PARLER_DEFAULT_LANGUAGE_CODE"),
    )

    logger.info("✅ Configuration complete")


# Export addon_urls for backward compatibility
from .addons import addon_urls  # noqa: F401
