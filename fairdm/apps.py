"""Application config for the FairDM framework app."""

from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules

# Imported at module level, not in `ready()`, so the navigation exists regardless of
# which optional apps are installed. `fairdm.menus.menus` imports no models.
from fairdm import menus as _menus  # noqa: F401

# Imported at module level so the checks also run under `manage.py check --deploy`
# when the production-configuration guard in `ready()` is skipped.
from fairdm.conf import checks as conf_checks  # noqa: F401

#: Environments that ship a non-production override module. Every other name,
#: including typos and the empty string, composes the production baseline and is
#: checked as production.
NON_PRODUCTION_ENVIRONMENTS = frozenset({"development"})


class FairDMConfig(AppConfig):
    """Wire the FairDM framework into Django's startup."""

    name = "fairdm"

    def resolved_environment(self) -> str:
        """Return the environment ``fairdm.setup()`` resolved, defaulting to ``production``.

        Returns:
            The value of the ``DJANGO_ENV`` setting.
        """
        from django.conf import settings

        return getattr(settings, "DJANGO_ENV", "production")

    def import_models(self) -> None:
        """Re-check the parler language settings before any model imports parler."""
        # A portal may narrow LANGUAGES after setup() returns. parler validates during
        # this model-import phase, so `ready()` is too late to give FairDM's named error.
        self._check_parler_languages()

        return super().import_models()

    def _check_parler_languages(self) -> None:
        """Raise when ``PARLER_LANGUAGES`` disagrees with ``LANGUAGES``."""
        from django.conf import settings

        from fairdm.conf.checks import raise_on_parler_languages_mismatch

        raise_on_parler_languages_mismatch(
            getattr(settings, "LANGUAGES", []),
            getattr(settings, "PARLER_LANGUAGES", {}),
            getattr(settings, "PARLER_DEFAULT_LANGUAGE_CODE", None),
        )

    def ready(self) -> None:
        """Discover portal config and plugin modules and install FairDM's startup hooks."""
        autodiscover_modules("config")
        autodiscover_modules("plugins")

        from django_filters import compat

        # Stops django-filter rendering through crispy forms.
        compat.is_crispy = lambda: False

        self._install_quantity_formatter()

        self._connect_portal_roles_reconciliation()

        self._check_production_configuration()

        return super().ready()

    def _install_quantity_formatter(self) -> None:
        """Install the framework's quantity formatter on the shared pint unit registry."""
        # Done here rather than in the template tag module, which Django imports only
        # once a template loads it, so values formatted elsewhere would miss it.
        from fairdm.templatetags.fairdm import MyFormatter, ureg

        ureg.formatter = MyFormatter(registry=ureg)

    def _connect_portal_roles_reconciliation(self) -> None:
        """Reconcile the four portal roles after every ``migrate`` run."""
        # Connected with no sender: `fairdm` precedes the apps whose permissions the
        # roles need, so its own `post_migrate` would fire before those exist.
        from django.db.models.signals import post_migrate

        post_migrate.connect(
            self._reconcile_portal_roles,
            dispatch_uid="fairdm.reconcile_portal_roles",
        )

    @staticmethod
    def _reconcile_portal_roles(**kwargs) -> None:
        """Install the shipped portal roles."""
        from fairdm.portal_roles import PortalRoles

        PortalRoles.reconcile()

    def _check_production_configuration(self) -> None:
        """Refuse to boot on the production baseline when a critical check fails.

        The gate is the composed settings, not an exact match on ``production``, so an
        unrecognised ``DJANGO_ENV`` (``prod``, the empty string) is checked as production.
        Every failure is named in one error.

        Raises:
            SystemCheckError: A production-critical deployment check reported a serious issue.
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
