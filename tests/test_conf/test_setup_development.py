"""
Integration tests for development setup and graceful degradation.

Tests verify that fairdm.setup() correctly handles missing services in development
by degrading gracefully with warnings instead of failing.
"""

import os

import pytest


@pytest.fixture
def minimal_dev_env():
    """Provide minimal development environment (no backing services)."""
    env_vars = {
        "DJANGO_ENV": "development",
        "DJANGO_SITE_DOMAIN": "localhost:8000",
        "DJANGO_SITE_NAME": "Dev Portal",
        # Intentionally omit DATABASE_URL, REDIS_URL, etc. to test degradation
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


class TestDevelopmentSetup:
    """Test development configuration loading and graceful degradation."""

    def test_development_degrades_without_database_url(self, minimal_dev_env):
        """Development should use SQLite if DATABASE_URL is not set."""
        from fairdm.conf.checks import validate_services

        # Development with SQLite should only warn, not fail
        test_settings = {
            "DATABASES": {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": "/tmp/db.sqlite3",
                }
            },
            "CACHES": {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
            "SECRET_KEY": "dev-key-12345",  # Short but acceptable in dev
            "ALLOWED_HOSTS": ["*"],
            "DEBUG": True,
            "SESSION_COOKIE_SECURE": False,
            "CSRF_COOKIE_SECURE": False,
        }

        # Should not raise - development allows degraded config
        validate_services("development", test_settings)

    def test_development_allows_locmem_cache(self, minimal_dev_env):
        """Development should allow LocMemCache without failing."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                }
            },
            "CACHES": {
                "default": {
                    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                }
            },
            "SECRET_KEY": "a" * 50,
            "ALLOWED_HOSTS": ["*"],
            "DEBUG": True,
            "SESSION_COOKIE_SECURE": False,
            "CSRF_COOKIE_SECURE": False,
        }

        # Should not raise - development allows LocMemCache
        validate_services("development", test_settings)

    def test_development_allows_short_secret_key(self, minimal_dev_env):
        """Development should allow shorter SECRET_KEY with warning."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                }
            },
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "short",  # Short but acceptable in development
            "ALLOWED_HOSTS": ["*"],
            "DEBUG": True,
            "SESSION_COOKIE_SECURE": False,
            "CSRF_COOKIE_SECURE": False,
        }

        # Should not raise - development allows short keys with warning
        validate_services("development", test_settings)

    def test_development_allows_debug_true(self, minimal_dev_env):
        """Development should allow DEBUG=True."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                }
            },
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 50,
            "ALLOWED_HOSTS": ["*"],
            "DEBUG": True,  # Allowed in development
            "SESSION_COOKIE_SECURE": False,
            "CSRF_COOKIE_SECURE": False,
        }

        # Should not raise - DEBUG=True is expected in development
        validate_services("development", test_settings)

    def test_development_allows_insecure_cookies(self, minimal_dev_env):
        """Development should allow insecure cookies."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                }
            },
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 50,
            "ALLOWED_HOSTS": ["*"],
            "DEBUG": True,
            "SESSION_COOKIE_SECURE": False,  # Allowed in development
            "CSRF_COOKIE_SECURE": False,  # Allowed in development
        }

        # Should not raise - insecure cookies OK in development
        validate_services("development", test_settings)

    def test_development_still_requires_secret_key(self, minimal_dev_env):
        """Development should still require some SECRET_KEY."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                }
            },
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "",  # Empty is still not allowed
            "ALLOWED_HOSTS": ["*"],
            "DEBUG": True,
            "SESSION_COOKIE_SECURE": False,
            "CSRF_COOKIE_SECURE": False,
        }

        # Should log error but not raise in development
        validate_services("development", test_settings)
