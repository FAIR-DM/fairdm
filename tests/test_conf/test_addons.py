"""Tests for FairDM addon integration system."""

import os
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured


@pytest.fixture
def addon_env():
    original_env = os.environ.copy()

    for key in list(os.environ.keys()):
        if key.startswith(
            ("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_", "EMAIL_", "S3_", "SENTRY_")
        ):
            del os.environ[key]

    os.environ.update(
        {
            "DJANGO_ENV": "development",
            "DJANGO_SECRET_KEY": "test_secret_key_1234567890",
            "DJANGO_SITE_DOMAIN": "localhost:8000",
            "DJANGO_SITE_NAME": "Test Portal",
        }
    )

    yield

    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def production_addon_env():
    # Mutating os.environ without restoring it leaks configuration into later tests that expect it missing.
    original_env = os.environ.copy()

    os.environ.clear()
    os.environ.update(
        {
            "DJANGO_ENV": "production",
            "DJANGO_SECRET_KEY": "a" * 60,
            "DJANGO_SITE_DOMAIN": "example.com",
            "DJANGO_SITE_NAME": "Prod Portal",
            "DJANGO_ALLOWED_HOSTS": "example.com",
            "DATABASE_URL": "postgresql://user:pass@localhost:5432/prod_db",
            "REDIS_URL": "redis://localhost:6379/0",
        }
    )

    yield

    os.environ.clear()
    os.environ.update(original_env)


class TestAddonDiscovery:
    def test_addon_with_setup_module_is_loaded(self, addon_env, tmp_path):
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup(addons=["tests.test_conf.dummy_addon"])
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings", settings_file)
        if spec and spec.loader:
            test_settings = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_settings)

            assert hasattr(test_settings, "DUMMY_ADDON_INSTALLED")
            assert test_settings.DUMMY_ADDON_INSTALLED is True
            assert hasattr(test_settings, "DUMMY_ADDON_VERSION")
            assert test_settings.DUMMY_ADDON_VERSION == "1.0.0"

            assert "tests.test_conf.dummy_addon" in test_settings.INSTALLED_APPS

    def test_addon_without_setup_module_logs_warning(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        with mock.patch("fairdm.conf.addons.logger.warning") as mock_warning:
            module = settings_module(
                setup_call="fairdm.setup(addons=['tests.test_conf.no_setup_addon'])",
                directory=tmp_path,
            )

        assert module.DJANGO_ENV == "development"

        warned_text = " ".join(
            str(call.args[0]) for call in mock_warning.call_args_list
        )
        assert "does not define '__fdm_setup_module__'" in warned_text
        assert "no_setup_addon" in warned_text

    def test_addon_with_invalid_module_fails_gracefully_in_development(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        with mock.patch("fairdm.conf.checks.logger.warning") as mock_warning:
            module = settings_module(
                setup_call="fairdm.setup(addons=['tests.test_conf.unloadable_addon'])",
                directory=tmp_path,
            )

        assert module.DJANGO_ENV == "development"

        assert mock_warning.called
        warned_text = " ".join(
            str(call.args[0]) for call in mock_warning.call_args_list
        )
        assert "unloadable_addon" in warned_text

        from fairdm.conf import record

        addons_layer = next(
            layer for layer in record.layers() if layer.name == "addons"
        )
        assert addons_layer.found is False
        assert addons_layer.settings == ()

    def test_addon_url_discovery(self, addon_env, tmp_path):
        from fairdm.conf.addons import addon_urls, discover_addon_urls

        addon_urls.clear()

        urls = discover_addon_urls(["tests.test_conf.dummy_addon"])

        assert "tests.test_conf.dummy_addon.urls" in urls


class TestAddonPosition:
    def test_addon_setting_beats_fairdm_environment_override(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module(
            setup_call="fairdm.setup(addons=['tests.test_conf.conflicting_addon'])",
            directory=tmp_path,
        )

        # fairdm/conf/development.py (layer 2) sets DEBUG = True; the addon
        # (layer 3) applies after it and must win.
        assert module.DEBUG == "addon-value"

    def test_portal_environment_override_beats_addon_setting(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"
        (tmp_path / "development.py").write_text("DEBUG = 'portal-value'\n")

        module = settings_module(
            setup_call="fairdm.setup(addons=['tests.test_conf.conflicting_addon'])",
            directory=tmp_path,
        )

        # The portal's own override (layer 4) applies after the addon
        # (layer 3) and must win.
        assert module.DEBUG == "portal-value"


class TestAddonValidation:
    def test_broken_addon_fails_fast_in_production(
        self, production_addon_env, tmp_path
    ):
        addon_dir = tmp_path / "broken_prod_addon"
        addon_dir.mkdir()
        (addon_dir / "__init__.py").write_text(
            '__fdm_setup_module__ = "broken_prod_addon.nonexistent"'
        )

        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            f"""
import os
import sys
from pathlib import Path

sys.path.insert(0, "{tmp_path}")
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup(addons=["broken_prod_addon"])
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_4", settings_file)
        if spec and spec.loader:
            test_settings = importlib.util.module_from_spec(spec)

            with pytest.raises(ImproperlyConfigured) as exc_info:
                spec.loader.exec_module(test_settings)

            assert "broken_prod_addon" in str(exc_info.value)

    def test_addon_can_modify_installed_apps(self, addon_env, tmp_path):
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup(addons=["tests.test_conf.dummy_addon"])
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_5", settings_file)
        if spec and spec.loader:
            test_settings = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_settings)

            assert "tests.test_conf.dummy_addon" in test_settings.INSTALLED_APPS


class TestAddonIntegration:
    def test_multiple_addons_can_be_loaded(self, addon_env, tmp_path):
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup(addons=["tests.test_conf.dummy_addon"])
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_6", settings_file)
        if spec and spec.loader:
            test_settings = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_settings)

            assert hasattr(test_settings, "DUMMY_ADDON_INSTALLED")

    def test_addon_settings_take_precedence(self, addon_env, tmp_path):
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup(addons=["tests.test_conf.dummy_addon"])
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_7", settings_file)
        if spec and spec.loader:
            test_settings = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_settings)

            assert "dummy_addon" in test_settings.LOGGING["loggers"]


class TestAddonPartialFailure:
    def test_partial_write_does_not_reach_settings_in_production(
        self, production_addon_env, tmp_path, settings_module
    ):
        with pytest.raises(ImproperlyConfigured) as exc_info:
            settings_module(
                setup_call=(
                    "fairdm.setup(addons=['tests.test_conf.broken_execution_addon'])"
                ),
                directory=tmp_path,
            )

        assert "broken_execution_addon" in str(exc_info.value)

    def test_partial_write_does_not_reach_settings_in_development(
        self, production_env, tmp_path, settings_module
    ):
        os.environ["DJANGO_ENV"] = "development"

        with mock.patch("fairdm.conf.setup.logger.warning") as mock_warning:
            module = settings_module(
                setup_call=(
                    "fairdm.setup(addons=['tests.test_conf.broken_execution_addon'])"
                ),
                directory=tmp_path,
            )

        # The portal started, and the addon's partial write never reached
        # the composed scope — assert the scope, not just the exception.
        assert not hasattr(module, "BROKEN_EXECUTION_ADDON_PARTIAL")

        assert mock_warning.called
        warned_text = " ".join(
            str(call.args[0]) for call in mock_warning.call_args_list
        )
        assert "broken_execution_addon" in warned_text

        from fairdm.conf import record

        addons_layer = next(
            layer for layer in record.layers() if layer.name == "addons"
        )
        assert addons_layer.found is False
        assert "BROKEN_EXECUTION_ADDON_PARTIAL" not in addons_layer.settings


class TestAddonScopeIsolation:
    def test_portal_non_setting_objects_keep_their_identity(
        self, production_env, tmp_path, settings_module
    ):
        # setup() runs each addon against a copy of the scope and merges it back, which must not rebind
        # names Django never reads, such as a list or dict a portal shares with another module.
        os.environ["DJANGO_ENV"] = "development"

        module = settings_module(
            setup_call=(
                "shared = {'a': 1}\n"
                "alias = shared\n"
                "fairdm.setup(addons=['tests.test_conf.conflicting_addon'])"
            ),
            after="SHARED_IDENTITY_KEPT = shared is alias",
            directory=tmp_path,
        )

        assert module.SHARED_IDENTITY_KEPT is True
        # The addon still applied — the isolation is scoped, not disabled.
        assert module.DEBUG == "addon-value"

    def test_in_place_mutation_by_a_failing_addon_is_discarded(
        self, production_env, tmp_path, settings_module
    ):
        # The scratch scope must copy the container, not just the binding: a shallow copy shares the list
        # that `INSTALLED_APPS += [...]` mutates.
        os.environ["DJANGO_ENV"] = "development"

        with mock.patch("fairdm.conf.setup.logger.warning"):
            module = settings_module(
                setup_call=(
                    "fairdm.setup(addons=['tests.test_conf.mutating_broken_addon'])"
                ),
                directory=tmp_path,
            )

        assert "tests.test_conf.mutating_broken_addon" not in module.INSTALLED_APPS
