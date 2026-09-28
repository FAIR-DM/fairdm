"""FairDM configuration setup entry point.

This module provides ``setup()``, the single call a portal's settings module
makes to obtain a complete Django configuration.

**Resolved environment.** Taken literally from the ``DJANGO_ENV`` environment
variable, defaulting to ``production`` when unset. Not validated against an
allowlist: any name is valid, including one nothing ships an override for.

**Environment files**, read in this order, later files not overriding a
variable already set in the process environment except where noted:

1. ``stack.env``, beside the portal's ``base_dir``, if present.
2. ``stack.<environment>.env``, beside ``base_dir``, if present.
3. The explicit ``env_file=`` argument, if given — this one *does* overwrite
   variables already set, including by the two files above.

**Layers**, applied in this order, each later layer overriding the same
setting in an earlier one:

1. The production baseline — every module under ``fairdm/conf/settings/``.
2. FairDM's own override module for the resolved environment, if it ships
   one. Only ``development.py`` today.
3. Settings contributed by addons named in the ``addons=`` argument.
4. The portal's own override module for the resolved environment, resolved
   beside its settings module regardless of directory name.
5. Assignments the portal's settings module makes after ``setup()`` returns —
   the only supported way to override a FairDM-owned setting.

Layers 2 and 4 are both selected by existence, not from a fixed list of
permitted names: if no module named after the resolved environment exists,
that layer is skipped without error.
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
    """Return every uppercase key in ``scope`` and its current value.

    Uppercase is Django's settings convention, also used for the bookkeeping keys
    ``setup()`` injects itself.

    Args:
        scope: The namespace to read.

    Returns:
        The uppercase entries of ``scope``.
    """
    return {key: value for key, value in scope.items() if key.isupper()}


def _snapshot_scope(scope: dict) -> dict:
    """Return ``_uppercase_scope`` with mutable containers copied out of harm's way.

    A layer does not have to rebind a name to change a setting: ``development.py`` writes
    ``INSTALLED_APPS += [...]``, which mutates the baseline's own list in place. A snapshot
    holding a reference to that list sees the mutation on both sides of the diff and credits
    the baseline with a value it did not produce.

    Args:
        scope: The namespace to snapshot.

    Returns:
        The uppercase entries of ``scope``, with lists, dicts and sets deep-copied.
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
    """Return a private copy of ``scope`` an addon's setup module can execute against.

    ``include()`` execs a module directly against whatever dict it is given, so a shallow copy
    would still share the object a ``+=`` mutates in place. A discarded scratch copy that shared
    the baseline's ``INSTALLED_APPS`` would corrupt the real scope before raising.

    Only settings are copied. Django reads uppercase names and nothing else, so lowercase names
    (the portal's imports and helpers, and ``__builtins__``) stay in the scratch scope by
    reference. Copying those too would rebind a container the portal shares with another module
    when the copies merge back.

    Args:
        scope: The namespace to copy.

    Returns:
        A scope whose uppercase mutable containers are deep-copied.
    """
    scratch = {}
    for key, value in scope.items():
        if key.isupper() and isinstance(value, _MUTABLE_CONTAINERS):
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
    """Return whether a layer changed a container, comparing by value.

    Args:
        before_value: The container before the layer ran.
        after_value: The container after the layer ran.

    Returns:
        ``True`` when the values differ, or when they cannot be compared and are not identical.
    """
    try:
        return bool(before_value != after_value)
    except Exception:  # pragma: no cover — defensive
        return before_value is not after_value


def _written_keys(before: dict, after: dict) -> list[str]:
    """Return the uppercase keys a layer wrote.

    That is the names it introduced, the names it rebound, and the containers it mutated in place.

    Args:
        before: The snapshot taken before the layer ran.
        after: The scope after the layer ran.

    Returns:
        The written setting names, sorted.
    """
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
    """Initialize FairDM configuration with environment-specific settings.

    The main entry point for portal configuration. See the module docstring for the resolved
    environment, the environment files and the five layers this composes into the caller's
    global namespace.

    Args:
        apps: List of portal-specific Django apps to include in INSTALLED_APPS.
        addons: List of FairDM addon packages to enable.
        base_dir: Project base directory (auto-detected if not provided).
        env_file: Optional path to .env file to load.

    Raises:
        ImproperlyConfigured: An addon's setup module fails while applying in production.

    Example:
        >>> import fairdm
        >>> fairdm.setup(
        ...     apps=["my_portal_app"],
        ...     addons=["fairdm_discussions"],
        ... )
    """
    apps = apps or []
    addons = addons or []

    env_profile = os.environ.get("DJANGO_ENV", "production")

    logger.info(f"🚀 FairDM Configuration: {env_profile} environment")

    caller_globals = inspect.stack()[1][0].f_globals

    # Captured before `__file__` is overwritten below for split_settings. A settings module
    # with no usable `__file__` (generated, or imported from an archive) cannot be anchored,
    # so the portal override lookup is skipped.
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

    if not base_dir:
        base_dir = Path(caller_globals["__file__"]).resolve(strict=True).parent.parent

    from .environment import env

    env_files_to_load = []

    if (base_dir / "stack.env").exists():
        env_files_to_load.append(str(base_dir / "stack.env"))

    env_specific_file = base_dir / f"stack.{env_profile}.env"
    if env_specific_file.exists():
        env_files_to_load.append(str(env_specific_file))

    if env_file and Path(env_file).exists():
        env_files_to_load.append(env_file)

    for env_path in env_files_to_load:
        # Only the explicit file overwrites variables already set.
        is_custom_file = env_path == env_file
        environ.Env.read_env(env_path, overwrite=is_custom_file)
        logger.debug(
            f"Loaded environment file: {env_path} (overwrite={is_custom_file})"
        )

    caller_globals.update(
        {
            "env": env,
            "BASE_DIR": base_dir,
            "FAIRDM_APPS": apps,
            "DJANGO_ENV": env_profile,
            "__file__": os.path.realpath(__file__),
        }
    )

    # Each layer's contribution is the delta of the scope's uppercase keys around its
    # `include()` call.
    record.reset()

    logger.info("Loading production baseline settings...")

    # Order matters: later modules read names the earlier ones define.
    settings_modules = [
        "settings/apps.py",
        "settings/security.py",
        "settings/database.py",
        "settings/cache.py",
        "settings/static_media.py",
        "settings/celery.py",
        "settings/auth.py",
        "settings/logging.py",
        "settings/email.py",
        "settings/addons.py",
        "settings/api.py",
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

    # Layer 2. Selected by existence: any environment name is looked up the same way.
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

    # Layer 3. Each addon applies to a scratch scope and merges only on success, so a
    # module that raises partway leaves no partial writes. A failure fails fast in
    # production and warns and skips elsewhere, like an addon that cannot be found.
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

    # Layer 4. Selected by existence, and skipped without error if absent.
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

    # Validation belongs to Django's check framework (`fairdm/conf/checks.py`), except this
    # rule: django-parler enforces it when any parler-model app imports, before checks run,
    # and this is the only point ahead of every such app.
    from django.conf import global_settings

    from fairdm.conf.checks import raise_on_parler_languages_mismatch

    raise_on_parler_languages_mismatch(
        caller_globals.get("LANGUAGES", global_settings.LANGUAGES),
        caller_globals.get("PARLER_LANGUAGES", {}),
        caller_globals.get("PARLER_DEFAULT_LANGUAGE_CODE"),
    )

    logger.info("✅ Configuration complete")


from .addons import addon_urls  # noqa: F401
