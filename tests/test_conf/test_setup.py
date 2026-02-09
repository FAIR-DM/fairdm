"""
Tests for FairDM configuration setup and profile loading.

Tests validate that:
- Profiles load correctly based on DJANGO_ENV
- Production fails fast on missing configuration
- Development degrades gracefully
- Configuration validation works as expected
"""

import os

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
            "CACHES": {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
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
            "CACHES": {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
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
