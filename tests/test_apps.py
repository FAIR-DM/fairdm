"""Tests for ``fairdm.apps.FairDMConfig`` and the production-critical check gate that runs from ``ready()``."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

#: PARLER_LANGUAGES narrowed to agree with ``LANGUAGES = [en, de]``.
CONSISTENT_PARLER_LANGUAGES = (
    "PARLER_LANGUAGES = {\n"
    '    1: ({"code": "en"}, {"code": "de"}),\n'
    '    "default": {"fallback": "en", "hide_untranslated": False},\n'
    "}\n"
)


def _boot_in_subprocess(env_overrides):
    """Run ``import django; django.setup()`` in a fresh process with the given env."""
    env = {**os.environ, **env_overrides}
    return subprocess.run(
        [sys.executable, "-c", "import django; django.setup()"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestFairDMConfigReady:
    def test_resolved_environment_reads_the_django_env_setting(self):
        import fairdm
        from fairdm.apps import FairDMConfig

        config = FairDMConfig("fairdm", fairdm)

        # tests/settings.py calls fairdm.setup() under DJANGO_ENV=development
        # (set process-wide by pytest-env), which records it as a setting.
        assert config.resolved_environment() == "development"

    def test_resolved_environment_defaults_to_production_when_unset(self):
        from django.test import override_settings

        import fairdm
        from fairdm.apps import FairDMConfig

        config = FairDMConfig("fairdm", fairdm)

        with override_settings():
            from django.conf import settings

            del settings.DJANGO_ENV
            assert config.resolved_environment() == "production"


class TestProductionBoot:
    def test_boot_fails_naming_every_missing_or_unsafe_value(self):
        result = _boot_in_subprocess(
            {
                "DJANGO_ENV": "production",
                "DJANGO_SETTINGS_MODULE": "config.settings",
                # Absent/unsafe together, exercising four distinct checks:
                "DJANGO_SECRET_KEY": "",  # fairdm.E001 — empty
                "DJANGO_ALLOWED_HOSTS": "*",  # fairdm.E004 — wildcard
                # settings/database.py no longer falls back to SQLite, so an unconfigured NAME fails fairdm.E102
                # ("malformed") rather than fairdm.E101. E101 still fires when a portal configures SQLite itself.
                "DATABASE_URL": "",
                "POSTGRES_DB": "",  # fairdm.E102 — composes to an empty NAME
                # settings/cache.py always composes a Redis-shaped CACHES with checks.UNCONFIGURED_REDIS_LOCATION,
                # so check_cache_backend can tell an unset REDIS_URL from a real one.
                "REDIS_URL": "",  # fairdm.E200 — unconfigured placeholder
            }
        )

        assert result.returncode != 0, result.stdout + result.stderr
        for check_id in ("fairdm.E001", "fairdm.E004", "fairdm.E102", "fairdm.E200"):
            assert check_id in result.stderr, (
                f"{check_id} missing from output:\n{result.stderr}"
            )


class TestUnrecognisedEnvironmentBoot:
    MISCONFIGURED = {
        "DJANGO_SETTINGS_MODULE": "config.settings",
        "DJANGO_SECRET_KEY": "",
        "DJANGO_ALLOWED_HOSTS": "*",
        "DATABASE_URL": "",
        "POSTGRES_DB": "",
        "REDIS_URL": "",
    }

    @pytest.mark.parametrize(
        "django_env",
        [
            pytest.param("Production", id="case-variant"),
            pytest.param("prod", id="abbreviation"),
            pytest.param("", id="empty-string"),
            pytest.param("staging", id="portal-supplied-name-fairdm-does-not-ship"),
        ],
    )
    def test_boot_is_refused_for_an_environment_fairdm_ships_no_override_for(
        self, django_env
    ):
        result = _boot_in_subprocess({**self.MISCONFIGURED, "DJANGO_ENV": django_env})

        assert result.returncode != 0, (
            f"DJANGO_ENV={django_env!r} booted on the production baseline with no "
            f"secret key and no database:\n{result.stdout}{result.stderr}"
        )
        assert "fairdm.E001" in result.stderr, result.stdout + result.stderr


class TestParlerLanguagesCheck:
    # parler validates PARLER_LANGUAGES while models import, before ready() runs, so setup() applies
    # the rule as well.
    def _boot_with_portal_override(
        self, tmp_path, portal_override_body, settings_tail="", apps=""
    ):
        settings_dir = tmp_path / "config"
        settings_dir.mkdir()
        (settings_dir / "__init__.py").write_text("")
        (settings_dir / "settings.py").write_text(
            f"import fairdm\n\nfairdm.setup({apps})\n{settings_tail}"
        )
        (settings_dir / "production.py").write_text(portal_override_body)

        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(
                (
                    "DJANGO_",
                    "DATABASE_",
                    "REDIS_",
                    "POSTGRES_",
                    "EMAIL_",
                    "S3_",
                    "SENTRY_",
                )
            )
        }
        env |= {
            "DJANGO_ENV": "production",
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_ROOT_URLCONF": "fairdm.conf.urls",
            "DJANGO_SECRET_KEY": "b" * 60,
            "DJANGO_SITE_DOMAIN": "example.com",
            "DJANGO_ALLOWED_HOSTS": "example.com",
            "DATABASE_URL": "postgresql://portal:portal@localhost:5432/portal",
            "REDIS_URL": "redis://localhost:6379/0",
            "PYTHONPATH": f"{tmp_path}{os.pathsep}{REPO_ROOT}",
        }
        return subprocess.run(
            [sys.executable, "-c", "import django; django.setup()"],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )

    def test_narrowed_languages_without_narrowed_parler_languages_names_both_settings(
        self, tmp_path
    ):
        result = self._boot_with_portal_override(
            tmp_path, 'LANGUAGES = [("en", "English"), ("de", "German")]\n'
        )

        assert result.returncode != 0, result.stdout + result.stderr
        assert "fairdm.E400" in result.stderr, result.stderr
        assert "PARLER_LANGUAGES" in result.stderr
        assert "LANGUAGES" in result.stderr
        assert "fr" in result.stderr
        # Not django-parler's own traceback, which names neither setting.
        assert "does not exist in LANGUAGES" not in result.stderr

    def test_narrowing_both_settings_together_boots_cleanly(self, tmp_path):
        result = self._boot_with_portal_override(
            tmp_path,
            'LANGUAGES = [("en", "English"), ("de", "German")]\n'
            + CONSISTENT_PARLER_LANGUAGES,
        )

        assert result.returncode == 0, result.stdout + result.stderr

    def test_portal_app_importing_parler_models_still_gets_the_named_error(
        self, tmp_path
    ):
        # A portal's apps register before FairDM's AppConfig exists, so only the setup() call site is early enough.
        app_dir = tmp_path / "portalapp"
        app_dir.mkdir()
        (app_dir / "__init__.py").write_text("")
        (app_dir / "models.py").write_text("import parler.models  # noqa: F401\n")

        result = self._boot_with_portal_override(
            tmp_path,
            'LANGUAGES = [("en", "English"), ("de", "German")]\n',
            apps='apps=["portalapp"]',
        )

        assert result.returncode != 0, result.stdout + result.stderr
        assert "fairdm.E400" in result.stderr, result.stderr
        assert "fr" in result.stderr
        assert "does not exist in LANGUAGES" not in result.stderr

    def test_narrowing_languages_after_setup_returns_still_gets_the_named_error(
        self, tmp_path
    ):
        result = self._boot_with_portal_override(
            tmp_path,
            'LANGUAGES = [("en", "English"), ("de", "German")]\n'
            + CONSISTENT_PARLER_LANGUAGES,
            settings_tail=(
                "PARLER_LANGUAGES = {\n"
                '    1: ({"code": "en"}, {"code": "fr"}),\n'
                '    "default": {"fallback": "en", "hide_untranslated": False},\n'
                "}\n"
            ),
        )

        assert result.returncode != 0, result.stdout + result.stderr
        assert "fairdm.E400" in result.stderr, result.stderr
        assert "fr" in result.stderr
        assert "does not exist in LANGUAGES" not in result.stderr

    def test_a_language_settings_disagreement_django_owns_does_not_block_boot(
        self, tmp_path
    ):
        result = self._boot_with_portal_override(
            tmp_path,
            'LANGUAGES = [("en", "English"), ("de", "German")]\n'
            + CONSISTENT_PARLER_LANGUAGES
            + 'LANGUAGE_CODE = "fr"\n',
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "translation.E004" not in result.stderr


class TestNonProductionBoot:
    def test_boot_succeeds_with_no_check_output(self):
        result = _boot_in_subprocess(
            {
                "DJANGO_ENV": "development",
                "DJANGO_SETTINGS_MODULE": "config.settings",
                "DJANGO_SECRET_KEY": "",
                "DJANGO_ALLOWED_HOSTS": "*",
                "DATABASE_URL": "",
                "POSTGRES_DB": "",
                "REDIS_URL": "",
            }
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "fairdm.E" not in result.stdout
        assert "fairdm.E" not in result.stderr

    def test_check_ids_remain_registered(self):
        probe = (
            "import django\n"
            "django.setup()\n"
            "from django.core.checks.registry import registry\n"
            "names = {\n"
            "    getattr(check, '__name__', '')\n"
            "    for check in registry.get_checks(include_deployment_checks=True)\n"
            "}\n"
            "print('check_secret_key_exists' in names)\n"
        )
        env = {
            **os.environ,
            "DJANGO_ENV": "development",
            "DJANGO_SETTINGS_MODULE": "config.settings",
        }
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-c", probe],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )

        assert result.stdout.strip() == "True", result.stdout + result.stderr


@pytest.mark.django_db
class TestPortalRolesReconciliation:
    def test_migrate_installs_the_four_roles(self, disconnect_shipped_role_guard):
        from django.contrib.auth.models import Group
        from django.core.management import call_command

        from fairdm.portal_roles import PortalRoles

        Group.objects.all().delete()

        call_command("migrate", verbosity=0)

        assert set(
            Group.objects.filter(name__in=PortalRoles.shipped_names()).values_list(
                "name", flat=True
            )
        ) == set(PortalRoles.shipped_names())

    def test_migrate_restores_a_permission_removed_by_hand(
        self, disconnect_shipped_role_guard
    ):
        from django.contrib.auth.models import Group
        from django.core.management import call_command

        from fairdm.portal_roles import PortalRoles

        Group.objects.all().delete()
        call_command("migrate", verbosity=0)
        curator_group = Group.objects.get(name=PortalRoles.DATA_CURATOR.name)
        curator_group.permissions.clear()

        call_command("migrate", verbosity=0)

        curator_group.refresh_from_db()
        assert curator_group.permissions.filter(codename="view_dataset").exists()


class TestPluginRegistryValidatedAtStartup:
    @pytest.fixture(autouse=True)
    def restore_registry(self):
        from fairdm import plugins

        saved = {
            model: list(entries)
            for model, entries in plugins.registry._registry.items()
        }
        yield
        plugins.registry._registry.clear()
        plugins.registry._registry.update(saved)

    def test_ready_refuses_a_declaration_that_cannot_work(self):
        from django.views.generic import TemplateView

        import fairdm
        from fairdm import plugins
        from fairdm.apps import FairDMConfig
        from fairdm.contrib.location.models import Point
        from fairdm.contrib.plugins import Plugin
        from fairdm.contrib.plugins.checks import PluginRegistrationError

        @plugins.register(Point, place="action")
        class LocationAction(Plugin, TemplateView):
            template_name = "base.html"

        with pytest.raises(PluginRegistrationError, match="LocationAction"):
            FairDMConfig("fairdm", fairdm).ready()

    def test_ready_accepts_the_plugins_the_framework_ships(self):
        import fairdm
        from fairdm.apps import FairDMConfig

        FairDMConfig("fairdm", fairdm).ready()
