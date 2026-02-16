"""
Integration tests for staging setup loading.

Tests verify that fairdm.setup() correctly loads staging configuration
with enhanced logging and production-like validation.
"""

import os

import pytest


@pytest.fixture
def staging_env():
    """Provide staging environment variables."""
    env_vars = {
        "DJANGO_ENV": "staging",
        "DJANGO_SECRET_KEY": "a" * 60,
        "DJANGO_SITE_DOMAIN": "staging.example.com",
        "DJANGO_SITE_NAME": "Staging Portal",
        "DJANGO_ALLOWED_HOSTS": "staging.example.com",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/staging_db",
        "REDIS_URL": "redis://localhost:6379/1",
        "EMAIL_HOST": "smtp.example.com",
        "EMAIL_PORT": "587",
        # Sentry optional in staging
    }

    # Save original env
    original_env = os.environ.copy()

    # Clear Django-related env vars
    for key in list(os.environ.keys()):
        if key.startswith(("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_", "EMAIL_", "S3_", "SENTRY_")):
            del os.environ[key]

    # Set test environment
    os.environ.update(env_vars)

    yield env_vars

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


class TestStagingSetup:
    """Test staging configuration loading."""

    def test_staging_requires_database_like_production(self, staging_env):
        """Staging should require proper database like production."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {},  # Missing database
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 60,
            "ALLOWED_HOSTS": ["staging.example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(Exception, match="DATABASE"):
            validate_services("staging", test_settings)

    def test_staging_requires_redis_like_production(self, staging_env):
        """Staging should require Redis cache like production."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {
                "default": {
                    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",  # Not production-grade
                }
            },
            "SECRET_KEY": "a" * 60,
            "ALLOWED_HOSTS": ["staging.example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(Exception, match="Cache backend.*not suitable for production"):
            validate_services("staging", test_settings)

    def test_staging_requires_secret_key(self, staging_env):
        """Staging should require SECRET_KEY like production."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "",  # Empty
            "ALLOWED_HOSTS": ["staging.example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(Exception, match="SECRET_KEY"):
            validate_services("staging", test_settings)

    def test_staging_rejects_debug_true(self, staging_env):
        """Staging should reject DEBUG=True like production."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 60,
            "ALLOWED_HOSTS": ["staging.example.com"],
            "DEBUG": True,  # Should be False
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(Exception, match="DEBUG"):
            validate_services("staging", test_settings)

    def test_staging_enforces_https_cookies(self, staging_env):
        """Staging should require secure cookies like production."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 60,
            "ALLOWED_HOSTS": ["staging.example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": False,  # Should be True
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(Exception, match="SESSION_COOKIE_SECURE"):
            validate_services("staging", test_settings)

    def test_staging_allows_missing_sentry(self, staging_env):
        """Staging should allow optional Sentry configuration."""
        import warnings

        from fairdm.conf.checks import validate_services

        # Remove SENTRY_DSN from environment
        if "SENTRY_DSN" in os.environ:
            del os.environ["SENTRY_DSN"]

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 60,
            "ALLOWED_HOSTS": ["staging.example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
            "CELERY_BROKER_URL": "redis://localhost:6379/0",  # Required for staging
        }

        # Should not raise - Sentry is optional in staging (but will emit deprecation warning)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_services("staging", test_settings)
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
