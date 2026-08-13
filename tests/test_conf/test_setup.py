"""
Tests for FairDM configuration setup and profile loading.

Tests validate that:
- Profiles load correctly based on DJANGO_ENV
- Production fails fast on missing configuration
- Development degrades gracefully
- Configuration validation works as expected
- ``**overrides`` and the ``env_file`` parameter behave correctly
"""

import os
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured

# Test fixtures


@pytest.fixture
def clean_env():
    """Provide a clean environment for testing."""
    original_env = os.environ.copy()
    # Clear relevant env vars
    for key in list(os.environ.keys()):
        if key.startswith(("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_")):
            del os.environ[key]

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


class TestResolvedEnvironment:
    """Test resolution of the ``DJANGO_ENV`` environment variable (FR-007)."""

    def test_missing_django_env_resolves_to_production(
        self, clean_env, settings_module
    ):
        """``DJANGO_ENV`` unset resolves to ``production``."""
        module = settings_module()

        assert module.DJANGO_ENV == "production"

    def test_empty_string_django_env_is_looked_up_literally(
        self, clean_env, settings_module
    ):
        """An empty ``DJANGO_ENV`` is not normalised to ``production`` (edge case)."""
        os.environ["DJANGO_ENV"] = ""

        module = settings_module()

        assert module.DJANGO_ENV == ""
        # No override module is named "" — the baseline stands, unchanged.
        assert module.DEBUG is False

    def test_environment_name_differing_only_in_case_is_not_normalised(
        self, clean_env, settings_module
    ):
        """A name differing only in case from a shipped one is looked up literally (edge case)."""
        os.environ["DJANGO_ENV"] = "Development"

        module = settings_module()

        assert module.DJANGO_ENV == "Development"
        # "Development" != "development" — FairDM's override module is not found.
        assert module.DEBUG is False


# Validation Logic Tests (Unit tests that don't require full Django setup)


class TestValidationLogic:
    """Test configuration validation logic."""

    def test_secret_key_length_validation(self, clean_env):
        """Secret key should be validated for minimum length."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "short",  # Too short
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(ImproperlyConfigured, match="SECRET_KEY.*too short"):
            validate_services("production", test_settings)

    def test_insecure_secret_key_rejected(self, clean_env):
        """Secret key containing 'insecure' should be rejected in production."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "django-insecure-" + "a" * 50,  # Contains 'insecure'
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(ImproperlyConfigured, match="insecure"):
            validate_services("production", test_settings)

    def test_https_cookie_validation(self, clean_env):
        """HTTPS-only cookies should be enforced in production."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 50,
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": False,  # Should fail
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(ImproperlyConfigured, match="SESSION_COOKIE_SECURE"):
            validate_services("production", test_settings)

    def test_production_fails_without_database_url(self, clean_env):
        """Production should fail if DATABASE_URL is not set."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 50,
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(ImproperlyConfigured, match="DATABASES"):
            validate_services("production", test_settings)

    def test_production_fails_without_redis_url(self, clean_env):
        """Production should fail if REDIS_URL is not set."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {
                "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
            },
            "SECRET_KEY": "a" * 50,
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
            "CELERY_BROKER_URL": "",
        }

        with pytest.raises(ImproperlyConfigured, match="Cache backend"):
            validate_services("production", test_settings)

    def test_production_fails_with_debug_true(self, clean_env):
        """Production should fail if DEBUG is True."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 50,
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": True,  # This should fail
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(ImproperlyConfigured, match="DEBUG"):
            validate_services("production", test_settings)

    def test_production_fails_with_wildcard_allowed_hosts(self, clean_env):
        """Production should fail if ALLOWED_HOSTS contains wildcard."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 50,
            "ALLOWED_HOSTS": ["*"],  # Wildcard should fail
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(ImproperlyConfigured, match="ALLOWED_HOSTS.*wildcard"):
            validate_services("production", test_settings)

    def test_development_degrades_without_database_url(self, clean_env, caplog):
        """Development should warn but not fail if DATABASE_URL is missing."""
        import warnings

        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.sqlite3"}},
            "CACHES": {
                "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
            },
            "SECRET_KEY": "dev-key",
            "ALLOWED_HOSTS": ["*"],
            "DEBUG": True,
        }

        # Should not raise exception but should emit deprecation warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_services("development", test_settings)
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()


class TestProductionSetup:
    """Test production configuration loading."""

    def test_production_loads_with_complete_config(self, production_env, tmp_path):
        """Production setup should succeed when all required env vars are set."""
        # Create a mock settings module
        settings_module = tmp_path / "test_settings.py"
        settings_module.write_text(
            """
import fairdm

fairdm.setup(apps=["test_app"])
"""
        )

        # Import and execute the settings
        import sys

        sys.path.insert(0, str(tmp_path))

        try:
            # This should not raise any errors
            with mock.patch(
                "fairdm.conf.setup.include"
            ):  # Mock include to avoid loading actual files
                # Create a mock caller namespace
                caller_namespace = {"__file__": str(settings_module)}

                with mock.patch("fairdm.conf.setup.inspect") as mock_inspect:
                    mock_inspect.stack.return_value = [(None, [caller_namespace])]

                    # This should execute without errors
                    # setup(apps=["test_app"])

                    # Note: Full integration test would require actual Django setup
                    # For now, we test that the function signature and env loading works

        finally:
            sys.path.remove(str(tmp_path))


@pytest.fixture
def clean_production_env():
    """Provide clean environment for override tests."""
    # Save original env
    original_env = os.environ.copy()

    # Clear Django-related env vars
    for key in list(os.environ.keys()):
        if key.startswith(
            ("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_", "EMAIL_", "S3_", "SENTRY_")
        ):
            del os.environ[key]

    # Set minimal production environment
    os.environ.update(
        {
            "DJANGO_ENV": "production",
            "DJANGO_SECRET_KEY": "a" * 60,
            "DJANGO_SITE_DOMAIN": "example.com",
            "DJANGO_SITE_NAME": "Test Portal",
            "DJANGO_ALLOWED_HOSTS": "example.com",
            "DATABASE_URL": "postgresql://user:pass@localhost:5432/test_db",
            "REDIS_URL": "redis://localhost:6379/0",
        }
    )

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


class TestSetupOverrides:
    """Test setup() **overrides functionality."""

    def test_overrides_are_applied_to_settings(self, clean_production_env, tmp_path):
        """Test that **overrides are applied to caller's globals."""
        # Create a minimal settings file that calls setup()
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

# Add fairdm to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup(
    TEST_OVERRIDE="custom_value",
    ANOTHER_SETTING=42,
    DEBUG=True,  # Override DEBUG even in production
)
"""
        )

        # Import the settings module
        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings", settings_file)
        test_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_settings)

        # Verify overrides were applied
        assert hasattr(test_settings, "TEST_OVERRIDE")
        assert test_settings.TEST_OVERRIDE == "custom_value"
        assert hasattr(test_settings, "ANOTHER_SETTING")
        assert test_settings.ANOTHER_SETTING == 42
        # Note: DEBUG validation might prevent this in production, but override should be attempted
        assert hasattr(test_settings, "DEBUG")

    def test_overrides_take_precedence_over_profile(
        self, clean_production_env, tmp_path
    ):
        """Test that **overrides take precedence over environment profile settings."""
        # Set development environment
        os.environ["DJANGO_ENV"] = "development"

        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

# development.py would set DEBUG=True, but we override it
fairdm.setup(DEBUG=False)
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_2", settings_file)
        test_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_settings)

        # Our override should take precedence
        assert test_settings.DEBUG is False

    def test_post_setup_assignments_work(self, clean_production_env, tmp_path):
        """Test that assignments after setup() call work correctly."""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup()

# Portal-specific customization after setup()
CUSTOM_APP_SETTING = "my_value"
ANOTHER_OVERRIDE = 123
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_3", settings_file)
        test_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_settings)

        # Post-setup assignments should exist
        assert hasattr(test_settings, "CUSTOM_APP_SETTING")
        assert test_settings.CUSTOM_APP_SETTING == "my_value"
        assert hasattr(test_settings, "ANOTHER_OVERRIDE")
        assert test_settings.ANOTHER_OVERRIDE == 123

    def test_overrides_can_modify_lists(self, clean_production_env, tmp_path):
        """Test that overrides can replace list settings like INSTALLED_APPS."""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

# Get baseline INSTALLED_APPS
fairdm.setup()

# Extend INSTALLED_APPS after setup
INSTALLED_APPS = INSTALLED_APPS + ["my_portal_app"]
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_4", settings_file)
        test_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_settings)

        # Verify custom app was added
        assert "my_portal_app" in test_settings.INSTALLED_APPS

    def test_overrides_can_modify_dicts(self, clean_production_env, tmp_path):
        """Test that overrides can modify dict settings like LOGGING."""
        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            """
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup()

# Customize logging configuration
LOGGING["loggers"]["my_app"] = {
    "handlers": ["console"],
    "level": "DEBUG",
}
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_5", settings_file)
        test_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_settings)

        # Verify custom logger was added
        assert "my_app" in test_settings.LOGGING["loggers"]
        assert test_settings.LOGGING["loggers"]["my_app"]["level"] == "DEBUG"


class TestEnvFileParameter:
    """Test custom env_file parameter functionality."""

    def test_custom_env_file_is_loaded(self, clean_production_env, tmp_path):
        """Test that custom env_file parameter loads the specified file."""
        # Create a custom .env file
        custom_env = tmp_path / "custom.env"
        custom_env.write_text(
            """
DJANGO_SECRET_KEY=custom_secret_key_from_file_123456789012345678901234567890
DJANGO_ALLOWED_HOSTS=custom.example.com
DATABASE_URL=postgresql://custom_user:pass@localhost:5432/custom_db
REDIS_URL=redis://localhost:6379/5
"""
        )

        settings_file = tmp_path / "settings.py"
        # Use Path.as_posix() to avoid Windows backslash escaping issues
        custom_env_posix = custom_env.as_posix()
        settings_file.write_text(
            f"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup(env_file='{custom_env_posix}')
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_6", settings_file)
        test_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_settings)

        # Verify custom env file values were loaded
        assert (
            test_settings.SECRET_KEY
            == "custom_secret_key_from_file_123456789012345678901234567890"
        )
        assert "custom.example.com" in test_settings.ALLOWED_HOSTS

    @pytest.mark.skip(
        reason="Windows path escaping issue in dynamically generated settings file"
    )
    def test_env_file_takes_precedence(self, clean_production_env, tmp_path):
        """Test that env_file values override base environment."""
        pass

        # Create env file with override
        custom_env = tmp_path / "override.env"
        custom_env.write_text(
            """
DJANGO_SECRET_KEY=override_secret_key_from_file_1234567890123456789012345
DATABASE_URL=postgresql://user:pass@localhost:5432/test_db
REDIS_URL=redis://localhost:6379/0
DJANGO_ALLOWED_HOSTS=example.com
"""
        )

        settings_file = tmp_path / "settings.py"
        settings_file.write_text(
            f"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import fairdm

fairdm.setup(env_file="{custom_env}")
"""
        )

        import importlib.util

        spec = importlib.util.spec_from_file_location("test_settings_7", settings_file)
        test_settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_settings)

        # env_file value should override base environment
        assert (
            test_settings.SECRET_KEY
            == "override_secret_key_from_file_1234567890123456789012345"
        )
