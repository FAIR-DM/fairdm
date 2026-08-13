"""
Tests for ``fairdm.apps.FairDMConfig`` — the production-critical check gate
that runs from ``ready()``, the first point in the boot sequence where
Django's check framework has a populated app registry to run against
(research R1, US-3).

``FairDMConfig.ready()`` executes exactly once per process, when Django's
app registry is populated. Exercising its environment-dependent behaviour
under more than one ``DJANGO_ENV`` therefore needs a fresh process per case —
the same pattern ``tests/test_conf/test_setup.py``'s ``TestBundledPortalBoots``
already uses for the real baseline.
"""

import os
import subprocess
import sys
from pathlib import Path

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
    """``setup()`` records the resolved environment where ``ready()`` can read it (R1)."""

    def test_resolved_environment_reads_the_django_env_setting(self):
        import fairdm
        from fairdm.apps import FairDMConfig

        config = FairDMConfig("fairdm", fairdm)

        # tests/settings.py calls fairdm.setup() under DJANGO_ENV=development
        # (set process-wide by pytest-env), which records it as a setting.
        assert config.resolved_environment() == "development"

    def test_resolved_environment_defaults_to_production_when_unset(self):
        """The safe direction when nothing recorded an environment (D2)."""
        from django.test import override_settings

        import fairdm
        from fairdm.apps import FairDMConfig

        config = FairDMConfig("fairdm", fairdm)

        with override_settings():
            from django.conf import settings

            del settings.DJANGO_ENV
            assert config.resolved_environment() == "production"


class TestProductionBoot:
    """Several production-critical values missing at once names every failure (FR-013, SC-003)."""

    def test_boot_fails_naming_every_missing_or_unsafe_value(self):
        result = _boot_in_subprocess(
            {
                "DJANGO_ENV": "production",
                "DJANGO_SETTINGS_MODULE": "config.settings",
                # Absent/unsafe together, exercising four distinct checks:
                "DJANGO_SECRET_KEY": "",  # fairdm.E001 — empty
                "DJANGO_ALLOWED_HOSTS": "*",  # fairdm.E004 — wildcard
                # settings/database.py no longer falls back to SQLite when
                # unconfigured (FS-001 US-1, FR-003, D4) — it always composes
                # a postgres-shaped URL, so an empty NAME fails fairdm.E102
                # ("malformed"), not fairdm.E101 ("SQLite"). E101 still fires
                # if a portal explicitly configures SQLite; it just can't be
                # reached from an unconfigured baseline any more.
                "DATABASE_URL": "",
                "POSTGRES_DB": "",  # fairdm.E102 — composes to an empty NAME
                # settings/cache.py no longer falls back to LocMem either — it
                # always composes a Redis-shaped CACHES, substituting
                # checks.UNCONFIGURED_REDIS_LOCATION so check_cache_backend
                # can still tell an unset REDIS_URL apart from a real one.
                "REDIS_URL": "",  # fairdm.E200 — unconfigured placeholder
            }
        )

        assert result.returncode != 0, result.stdout + result.stderr
        # Every failure is named, not just the first.
        for check_id in ("fairdm.E001", "fairdm.E004", "fairdm.E102", "fairdm.E200"):
            assert check_id in result.stderr, (
                f"{check_id} missing from output:\n{result.stderr}"
            )


class TestParlerLanguagesCheck:
    """django-parler validates PARLER_LANGUAGES against LANGUAGES inside its
    own ``parler.appsettings`` module, imported while ``apps.populate()`` is
    still importing models (Phase 2) — before ``ready()`` (Phase 3) starts,
    so ``FairDMConfig.ready()`` can't reach this in time. Two call sites cover
    it between them (FR-012, US-5 T107): ``setup()`` applies the rule to the
    settings scope it composed, which is ahead of *every* app's models
    including a portal's own (registered before FairDM's, D11), and
    ``FairDMConfig.import_models()`` applies it again to the loaded settings,
    which is the only point after a portal's post-``setup()`` assignments
    (layer 5). Run out-of-process for the same reason ``TestProductionBoot``
    is: ``apps.populate()`` isn't reentrant.
    """

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
                ("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_", "EMAIL_", "S3_", "SENTRY_")
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
        """The reproducer named in the brief: a portal narrows LANGUAGES to
        (en, de) and leaves PARLER_LANGUAGES at the baseline (en, fr, de) —
        fr is the code the error must name."""
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
        """A portal's own apps are registered ahead of FairDM's (D11), so one
        whose models import parler.models reaches parler's validation before
        ``fairdm``'s AppConfig exists. Only the ``setup()`` call site is early
        enough for this portal; without it the bare parler traceback returns."""
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
        """Layer 5 — the assignment a portal makes after ``setup()`` returns
        (FR-012). ``setup()`` has already run and seen a consistent pair, so
        only the ``import_models()`` call site can catch this one."""
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
        """LANGUAGE_CODE not being among LANGUAGES is ``translation.E004``,
        Django's own check and a ``manage.py check`` finding — not something
        FairDM refuses a boot over, in production or anywhere else. The portal
        here narrows both parler settings consistently and leaves the
        baseline's ``LANGUAGE_CODE = "en"`` in place."""
        result = self._boot_with_portal_override(
            tmp_path,
            'LANGUAGES = [("en", "English"), ("de", "German")]\n'
            + CONSISTENT_PARLER_LANGUAGES
            + 'LANGUAGE_CODE = "fr"\n',
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "translation.E004" not in result.stderr


class TestNonProductionBoot:
    """The same missing values under development start silently (FR-014, FR-015, SC-004)."""

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
        """The FR-014 guard skips running the checks, not registering them."""
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
