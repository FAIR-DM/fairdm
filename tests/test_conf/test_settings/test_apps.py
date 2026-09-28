"""Tests for ``fairdm/conf/settings/apps.py``."""

import os
import subprocess
import sys
from pathlib import Path


class TestInstalledApps:
    def test_portal_apps_precede_fairdm_core(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"

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

        settings_module()


class TestContributorsAppRegistration:
    def test_contributors_app_is_installed(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert "fairdm.contrib.contributors" in module.INSTALLED_APPS

    def test_contributors_app_loads_behind_django_contrib_auth(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        contributors_index = module.INSTALLED_APPS.index("fairdm.contrib.contributors")
        auth_index = module.INSTALLED_APPS.index("django.contrib.auth")

        assert contributors_index > auth_index


class TestTemplateAndStaticPrecedence:
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
            "import fairdm\nfairdm.setup(apps=['a_shadowing_portal_app'])\n"
        )

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
            "DJANGO_ENV": "qa",
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "PYTHONPATH": f"{tmp_path}{os.pathsep}{repo_root}",
            # "qa" ships no override module, so it boots on the production baseline and the guard applies.
            # The guard reads configuration and never connects, so the values only have to be well-formed.
            "DJANGO_SECRET_KEY": "x" * 64,
            "DJANGO_ALLOWED_HOSTS": "portal.example.org",
            "DJANGO_DEBUG": "False",
            "DATABASE_URL": "postgres://portal:portal@localhost:5432/portal",
            "REDIS_URL": "redis://localhost:6379/1",
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


class TestGroupsFixtureRemoved:
    def test_the_groups_fixture_file_is_gone(self):
        repo_root = Path(__file__).resolve().parents[3]

        assert not (repo_root / "fairdm" / "fixtures" / "groups.json").exists()

    def test_on_initial_no_longer_loads_the_groups_fixture(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        on_initial = module.DJANGO_SETUP_TOOLS[""]["on_initial"]

        assert ("loaddata", "groups") not in on_initial
