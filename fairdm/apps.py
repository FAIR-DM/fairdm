from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules

# Registered at module import, not inside ready()'s guarded body, so the
# full check set still participates in `manage.py check --deploy`
# independently of the FR-014 environment guard below (FR-015, FR-016).
from fairdm.conf import checks as conf_checks  # noqa: F401

# The site navigation is declared as an import side effect of `fairdm.menus.menus`,
# and until now the only module importing it was `fairdm.contrib.collections.apps`.
# That made the whole menu tree - Home, Projects, Datasets, Literature and the rest,
# not merely the two headings that app populates - conditional on an optional
# application being installed, which FR-041 forbids. Tying it to the framework's own
# app config instead makes the navigation independent of that application's start-up.
# Module level rather than `ready()`, because `fairdm.menus.menus` imports no models:
# only translation, `flex_menu` and `mvp.menus`.
from fairdm import menus as _menus  # noqa: F401

#: The environments FairDM ships a non-production override module for, and so
#: the only ones the boot refusal below stands down for. Every other resolved
#: name composes the production baseline unchanged — a typo, a case variant and
#: the empty string all do (FR-009, D1) — so every other name is a production
#: deployment and is checked as one (D21).
NON_PRODUCTION_ENVIRONMENTS = frozenset({"development"})


class FairDMConfig(AppConfig):
    name = "fairdm"

    def resolved_environment(self) -> str:
        """
        The environment ``fairdm.setup()`` resolved, recorded as the
        ``DJANGO_ENV`` setting for ``ready()`` to read once ``django.setup()``
        has populated the app registry (research R1). Defaults to
        ``production`` — the safe direction — when unset.
        """
        from django.conf import settings

        return getattr(settings, "DJANGO_ENV", "production")

    def import_models(self) -> None:
        # setup() already applied this rule to the settings it composed, but a
        # portal may narrow LANGUAGES after setup() returns (layer 5, FR-012),
        # which nothing has seen yet. Re-apply it here, on the loaded settings
        # and ahead of fairdm.contrib.identity's models (which import
        # parler.models), so that portal gets FairDM's named error rather than
        # parler's bare traceback. ready() is too late: parler validates during
        # this same model-import phase (T107).
        self._check_parler_languages()

        return super().import_models()

    def _check_parler_languages(self) -> None:
        from django.conf import settings

        from fairdm.conf.checks import raise_on_parler_languages_mismatch

        raise_on_parler_languages_mismatch(
            getattr(settings, "LANGUAGES", []),
            getattr(settings, "PARLER_LANGUAGES", {}),
            getattr(settings, "PARLER_DEFAULT_LANGUAGE_CODE", None),
        )

    def ready(self) -> None:
        # adds a default renderer to all forms to keep a consistent look across the site. This way we don't have to specify it every time
        # patch django-filters to not use crispy forms. should be safe to remove on the
        # next release of fairdm

        autodiscover_modules("config")
        autodiscover_modules("plugins")

        from django_filters import compat

        compat.is_crispy = lambda: False

        self._install_quantity_formatter()

        self._check_production_configuration()

        return super().ready()

    def _install_quantity_formatter(self) -> None:
        """Install the framework's quantity formatter on the shared pint unit
        registry at startup (FR-038).

        Previously this happened as an import side effect of
        ``fairdm/templatetags/fairdm.py``, and Django imports template tag
        modules lazily - only once a template does ``{% load fairdm %}``. A
        value rendered outside a template (a management command, an API view,
        a test) could therefore be formatted with pint's default formatter
        instead of the framework's. ``ready()`` runs once, at application
        startup, regardless of whether any template is ever rendered.
        """
        from fairdm.templatetags.fairdm import MyFormatter, ureg

        ureg.formatter = MyFormatter(registry=ureg)

    def _check_production_configuration(self) -> None:
        """
        Refuse to boot when the settings in force are the production baseline
        and any production-critical check fails, naming every failure in one
        error rather than the first (FR-013, SC-003).

        The gate is the settings that were composed, not an exact match on the
        name ``production``. Layer selection is by file existence, so an
        unrecognised ``DJANGO_ENV`` — ``Production``, ``prod``, the empty
        string — loads no override and runs on the production baseline. Keying
        the refusal on the literal name let exactly those inputs boot with no
        secret key and no database, which is the failure the layering exists to
        prevent (D21). Only an environment FairDM ships a non-production
        override for is exempt, and it runs no checks here at all
        (FR-014, SC-004).
        """
        if self.resolved_environment() in NON_PRODUCTION_ENVIRONMENTS:
            return

        from django.core.checks.registry import registry
        from django.core.management.base import SystemCheckError

        from fairdm.conf.checks import DeployTags

        errors = [
            issue
            for issue in registry.run_checks(
                tags=[DeployTags.production_critical],
                include_deployment_checks=True,
            )
            if issue.is_serious()
        ]
        if errors:
            raise SystemCheckError(
                "FairDM production configuration is invalid:\n\n"
                + "\n\n".join(str(error) for error in errors)
            )
