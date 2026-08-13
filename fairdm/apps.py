from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules

# Registered at module import, not inside ready()'s guarded body, so the
# full check set still participates in `manage.py check --deploy`
# independently of the FR-014 environment guard below (FR-015, FR-016).
from fairdm.conf import checks as conf_checks  # noqa: F401


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

        # Import registry checks to register them with Django check framework
        from django_filters import compat

        from fairdm.registry import checks  # noqa: F401

        compat.is_crispy = lambda: False

        self._check_production_configuration()

        return super().ready()

    def _check_production_configuration(self) -> None:
        """
        Refuse to boot when the resolved environment is production and any
        production-critical check fails, naming every failure in one error
        rather than the first (FR-013, FR-014, SC-003). Every other
        environment runs no checks here at all (FR-014, SC-004).
        """
        if self.resolved_environment() != "production":
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
