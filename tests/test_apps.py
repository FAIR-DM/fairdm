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


def _boot_in_subprocess(env_overrides):
    """Run ``import django; django.setup()`` in a fresh process with the given env."""
    env = {**os.environ, **env_overrides}
    return subprocess.run(  # noqa: S603
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
        import fairdm
        from fairdm.apps import FairDMConfig
        from django.test import override_settings

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
                "DATABASE_URL": "",
                "POSTGRES_DB": "",  # fairdm.E101 — SQLite fallback
                "REDIS_URL": "",  # fairdm.E200 — LocMem fallback
            }
        )

        assert result.returncode != 0, result.stdout + result.stderr
        # Every failure is named, not just the first.
        for check_id in ("fairdm.E001", "fairdm.E004", "fairdm.E101", "fairdm.E200"):
            assert check_id in result.stderr, (
                f"{check_id} missing from output:\n{result.stderr}"
            )
