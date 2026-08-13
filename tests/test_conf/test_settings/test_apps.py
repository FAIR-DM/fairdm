"""
Tests for ``fairdm/conf/settings/apps.py`` — the baseline application stack
composition (FR-005).
"""

import os
import subprocess
import sys
from pathlib import Path


class TestInstalledApps:
    """Portal apps are composed ahead of FairDM's own apps and the
    third-party set, while staying behind the Django contrib apps that must
    load first (FR-005)."""

    def test_portal_apps_precede_fairdm_core(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands

        module = settings_module(
            setup_call="fairdm.setup(apps=['a_portal_app'])",
        )

        portal_index = module.INSTALLED_APPS.index("a_portal_app")
        fairdm_index = module.INSTALLED_APPS.index("fairdm")

        assert portal_index < fairdm_index

    def test_portal_apps_precede_third_party_apps(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module(
            setup_call="fairdm.setup(apps=['a_portal_app'])",
        )

        portal_index = module.INSTALLED_APPS.index("a_portal_app")
        allauth_index = module.INSTALLED_APPS.index("allauth")

        assert portal_index < allauth_index

    def test_portal_apps_stay_behind_django_contrib_apps(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module(
            setup_call="fairdm.setup(apps=['a_portal_app'])",
        )

        portal_index = module.INSTALLED_APPS.index("a_portal_app")
        auth_index = module.INSTALLED_APPS.index("django.contrib.auth")

        assert portal_index > auth_index

    def test_no_apps_argument_still_boots(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()  # must not raise


class TestTemplateAndStaticPrecedence:
    """When a portal and FairDM both define a template or static file at the
    same path, the portal's earlier app position makes its file win
    (FR-005, scenario 3).

    Run out-of-process, like ``TestBundledPortalBoots`` — swapping
    ``INSTALLED_APPS`` in the live test-session app registry runs every
    app's ``ready()`` against a portal it doesn't recognise (django-cleanup's
    among them), which fails for reasons unrelated to template resolution.
    """

    def test_portal_template_wins_over_fairdm_template_at_the_same_path(
        self, isolated_env, tmp_path
    ):
        repo_root = Path(__file__).resolve().parents[3]

        # A minimal portal app shadowing a real FairDM template path
        # (fairdm/templates/base.html) with its own file of the same name.
        app_dir = tmp_path / "a_shadowing_portal_app"
        (app_dir / "templates").mkdir(parents=True)
        (app_dir / "__init__.py").write_text("")
        (app_dir / "templates" / "base.html").write_text("PORTAL OVERRIDE\n")

        settings_dir = tmp_path / "config"
        settings_dir.mkdir()
        (settings_dir / "__init__.py").write_text("")
        (settings_dir / "settings.py").write_text(
            "import fairdm\n"
            "fairdm.setup(apps=['a_shadowing_portal_app'])\n"
        )

        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(
                ("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_", "EMAIL_", "S3_", "SENTRY_")
            )
        }
        env |= {
            "DJANGO_ENV": "qa",  # no override module — baseline stands
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "PYTHONPATH": f"{tmp_path}{os.pathsep}{repo_root}",
        }
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import django; django.setup()\n"
                "from django.template import loader\n"
                "print(loader.get_template('base.html').origin.name)",
            ],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )

        assert result.returncode == 0, result.stderr[-3000:]
        assert "a_shadowing_portal_app" in result.stdout
