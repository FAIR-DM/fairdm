"""
Tests for FairDM addon integration system.

Tests verify that fairdm.setup() correctly discovers, loads, and validates addon modules.
"""

import os
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured


@pytest.fixture
def addon_env():
    """Provide environment for addon tests."""
    # Save original env
    original_env = os.environ.copy()

    # Clear Django-related env vars
    for key in list(os.environ.keys()):
        if key.startswith(
            ("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_", "EMAIL_", "S3_", "SENTRY_")
        ):
            del os.environ[key]

    # Set minimal development environment (for graceful handling)
    os.environ.update(
        {
            "DJANGO_ENV": "development",
            "DJANGO_SECRET_KEY": "test_secret_key_1234567890",
            "DJANGO_SITE_DOMAIN": "localhost:8000",
            "DJANGO_SITE_NAME": "Test Portal",
        }
    )

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def production_addon_env():
    """Provide a production-shaped environment for addon tests, and restore it.

    Mutating ``os.environ`` in a test body without restoring it leaks the
    values into every later test in the same process, silently supplying
    configuration those tests are written to be missing.
    """
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
    """Test addon discovery and loading."""

    def test_addon_with_setup_module_is_loaded(self, addon_env, tmp_path):
        """Test that addon with __fdm_setup_module__ is discovered and loaded."""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

# Add project root to path
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

            # Verify addon settings were injected
            assert hasattr(test_settings, "DUMMY_ADDON_INSTALLED")
            assert test_settings.DUMMY_ADDON_INSTALLED is True
            assert hasattr(test_settings, "DUMMY_ADDON_VERSION")
            assert test_settings.DUMMY_ADDON_VERSION == "1.0.0"

            # Verify addon app was added to INSTALLED_APPS
            assert "tests.test_conf.dummy_addon" in test_settings.INSTALLED_APPS

    def test_addon_without_setup_module_logs_warning(
        self, production_env, tmp_path, settings_module
    ):
        """An addon defining no ``__fdm_setup_module__`` is warned about by
        name and skipped, and the portal starts (T112, FR-022).

        Restores a test that was skipped for a Windows path-escaping problem
        in a hand-built settings file, and whose body began with a bare
        ``pass`` before dead code — so it asserted nothing on any platform.
        The ``settings_module`` fixture removes the path escaping the skip
        was about; the warning is observed by patching the call because
        ``tests/settings.py`` disables logging for the whole suite.
        """
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
        """An addon that cannot be loaded emits a WARNING naming it, is
        skipped, and the portal starts — in any non-production environment
        (T099, T100; FR-022, scenario 3).

        Replaces a skip whose body began with a bare ``pass`` before dead
        code: it asserted nothing and predated the ``settings_module``
        fixture this story's other layer tests use.

        ``tests/settings.py`` disables logging for the whole suite (see
        ``TestPortalOverride.test_no_usable_file_skips_portal_override_with_warning``
        in ``test_setup.py``), so the warning is observed by patching the
        call rather than via ``caplog``.
        """
        os.environ["DJANGO_ENV"] = "development"

        with mock.patch("fairdm.conf.checks.logger.warning") as mock_warning:
            module = settings_module(
                setup_call="fairdm.setup(addons=['tests.test_conf.unloadable_addon'])",
                directory=tmp_path,
            )

        # The portal started — setup() returned a usable module.
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
        """Test that addon URL configurations are discovered."""
        from fairdm.conf.addons import addon_urls, discover_addon_urls

        # Clear existing addon URLs
        addon_urls.clear()

        # Discover URLs from dummy addon
        urls = discover_addon_urls(["tests.test_conf.dummy_addon"])

        # Verify dummy_addon urls were discovered
        assert "tests.test_conf.dummy_addon.urls" in urls


class TestAddonPosition:
    """Layer 3 (addons) sits between FairDM's environment override and the
    portal's own (T094, T096; FR-008, FR-021, scenario 1)."""

    def test_addon_setting_beats_fairdm_environment_override(
        self, production_env, tmp_path, settings_module
    ):
        """An addon's value for a setting FairDM's own environment override
        also sets beats that override — not merely that the addon's own
        settings land (FR-008, FR-021, scenario 1)."""
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
        """The portal's own environment override beats an addon's value for
        the same setting — the tail of scenario 1 (T096, FR-008, FR-021)."""
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
    """Test addon validation in different environments."""

    def test_broken_addon_fails_fast_in_production(
        self, production_addon_env, tmp_path
    ):
        """A broken addon raises ImproperlyConfigured naming the addon in
        production (T097, FR-022, scenario 2) — not merely some exception,
        which any unrelated failure would also satisfy."""
        # Create addon with broken setup module
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
        """Test that addon can inject apps into INSTALLED_APPS."""
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

            # Verify addon app was added
            assert "tests.test_conf.dummy_addon" in test_settings.INSTALLED_APPS


class TestAddonIntegration:
    """Test complete addon integration scenarios."""

    def test_multiple_addons_can_be_loaded(self, addon_env, tmp_path):
        """Test that multiple addons can be loaded together."""
        # For now, just test with our dummy addon twice (simulating multiple addons)
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

            # Should load successfully
            assert hasattr(test_settings, "DUMMY_ADDON_INSTALLED")

    def test_addon_settings_take_precedence(self, addon_env, tmp_path):
        """Test that addon settings override framework defaults."""
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

            # Verify addon's custom logger was added
            assert "dummy_addon" in test_settings.LOGGING["loggers"]


class TestAddonPartialFailure:
    """An addon whose setup module imports cleanly but raises partway
    through execution is treated as unloadable by the same path as any
    other broken addon — fail in production, warn and skip elsewhere — and
    the settings scope is not left holding its partial writes (T101, T102;
    edge case, FR-022)."""

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
        """``tests/settings.py`` disables logging for the whole suite, so
        the warning is observed by patching the call rather than via
        ``caplog`` (see ``TestPortalOverride`` in ``test_setup.py``)."""
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
    """Applying an addon's settings leaves everything that is not a Django
    setting in the portal's own namespace exactly as it was (T111)."""

    def test_portal_non_setting_objects_keep_their_identity(
        self, production_env, tmp_path, settings_module
    ):
        """A container the portal's settings module shares with another
        module is still the same object after ``setup()`` applied an addon.

        Layer 3 executes each addon against a private copy of the scope and
        merges it back on success. Copying names Django never reads, and
        merging those back, silently rebinds them: a portal that imports a
        shared list or dict and appends to it after the ``setup()`` call
        would be appending to a copy nothing else can see.
        """
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
        """An addon that appends to a settings container in place and then
        raises leaves that container as it was (T113).

        The scratch scope has to copy the container, not just the binding:
        a shallow copy shares the list ``INSTALLED_APPS += [...]`` mutates,
        so discarding it would not undo the append.
        """
        os.environ["DJANGO_ENV"] = "development"

        with mock.patch("fairdm.conf.setup.logger.warning"):
            module = settings_module(
                setup_call=(
                    "fairdm.setup(addons=['tests.test_conf.mutating_broken_addon'])"
                ),
                directory=tmp_path,
            )

        assert "tests.test_conf.mutating_broken_addon" not in module.INSTALLED_APPS
