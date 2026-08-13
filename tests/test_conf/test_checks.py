"""
Integration tests for fairdm.conf configuration checks.

These tests verify that Django's check framework integration works correctly
and that all configuration validation logic is properly tested, including the
legacy per-profile ``validate_services()`` function.
"""

import os

import pytest
from django.core.checks import Error
from django.core.management import call_command
from django.core.management.base import SystemCheckError
from django.test import override_settings


class TestDatabaseChecks:
    """Tests for database configuration checks."""

    @override_settings(DATABASES={})
    def test_check_database_configured_missing(self):
        """Check returns ERROR when DATABASES['default'] is not configured."""
        from fairdm.conf.checks import check_database_configured

        errors = check_database_configured(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E100"
        assert "DATABASES" in errors[0].msg
        assert "DATABASE_URL" in errors[0].hint

    @override_settings(DATABASES={"default": {}})
    def test_check_database_configured_empty(self):
        """Check returns ERROR when DATABASES['default'] is empty."""
        from fairdm.conf.checks import check_database_configured

        errors = check_database_configured(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)

    @override_settings(
        DATABASES={
            "default": {"ENGINE": "django.db.backends.postgresql", "NAME": "test"}
        }
    )
    def test_check_database_configured_valid(self):
        """Check returns empty list when database is properly configured."""
        from fairdm.conf.checks import check_database_configured

        errors = check_database_configured(app_configs=None)

        assert errors == []

    @override_settings(
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "db.sqlite3"}
        }
    )
    def test_check_database_production_ready_sqlite(self):
        """Check returns ERROR when using SQLite."""
        from fairdm.conf.checks import check_database_production_ready

        errors = check_database_production_ready(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E101"
        assert "SQLite" in errors[0].msg
        assert "PostgreSQL" in errors[0].hint

    @override_settings(
        DATABASES={
            "default": {"ENGINE": "django.db.backends.postgresql", "NAME": "test"}
        }
    )
    def test_check_database_production_ready_postgresql(self):
        """Check returns empty list when using PostgreSQL."""
        from fairdm.conf.checks import check_database_production_ready

        errors = check_database_production_ready(app_configs=None)

        assert errors == []


class TestSyntacticallyUnusableValue:
    """A production-critical value that is present but syntactically
    unusable fails distinctly from an absent value (edge case, FR-017)."""

    @override_settings(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "",
                "USER": "",
                "PASSWORD": "",
                "HOST": "",
                "PORT": "",
            }
        }
    )
    def test_malformed_database_url_fails_distinctly_from_absent(self):
        """DATABASE_URL='postgresql://' parses to a dict with ENGINE but no NAME —
        present and non-empty, so check_database_configured (fairdm.E100) does
        not fire, but the database is still unusable."""
        from fairdm.conf.checks import check_database_configured, check_database_usable

        assert check_database_configured(app_configs=None) == []

        errors = check_database_usable(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E102"


class TestCacheChecks:
    """Tests for cache configuration checks."""

    @override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    )
    def test_check_cache_backend_locmem(self):
        """Check returns ERROR when using locmem cache."""
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E200"
        assert "locmem" in errors[0].msg.lower()
        assert "Redis" in errors[0].hint

    @override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
    )
    def test_check_cache_backend_dummy(self):
        """Check returns ERROR when using dummy cache."""
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert "dummy" in errors[0].msg.lower()

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": "redis://localhost:6379/1",
            }
        }
    )
    def test_check_cache_backend_redis(self):
        """Check returns empty list when using Redis cache."""
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert errors == []

    @override_settings(CACHES={})
    def test_check_cache_backend_caches_absent(self):
        """Check returns ERROR when CACHES is not configured at all (FR-017)."""
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E200"

    @override_settings(CACHES={"default": {}})
    def test_check_cache_backend_default_empty(self):
        """Check returns ERROR when CACHES['default'] is an empty dict (FR-017)."""
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E200"

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
                "LOCATION": "/tmp/cache",
            }
        }
    )
    def test_check_cache_backend_filebased_is_not_shared(self):
        """A backend that is neither locmem nor dummy still fails if not shared (FR-017)."""
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E200"


class TestSecretKeyChecks:
    """Tests for SECRET_KEY configuration checks."""

    @override_settings(SECRET_KEY="")
    def test_check_secret_key_exists_empty(self):
        """Check returns ERROR when SECRET_KEY is empty."""
        from fairdm.conf.checks import check_secret_key_exists

        errors = check_secret_key_exists(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E001"
        assert "SECRET_KEY" in errors[0].msg
        assert "50+ characters" in errors[0].hint

    @override_settings(SECRET_KEY="a" * 50)
    def test_check_secret_key_exists_valid(self):
        """Check returns empty list when SECRET_KEY is set."""
        from fairdm.conf.checks import check_secret_key_exists

        errors = check_secret_key_exists(app_configs=None)

        assert errors == []

    @override_settings(SECRET_KEY="django-insecure-" + "a" * 50)
    def test_check_secret_key_exists_insecure_prefix(self):
        """Check returns ERROR when SECRET_KEY carries the published insecure prefix (FR-017, SC-006)."""
        from fairdm.conf.checks import check_secret_key_exists

        errors = check_secret_key_exists(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E001"
        assert "insecure" in errors[0].msg.lower()


class TestAllowedHostsChecks:
    """Tests for ALLOWED_HOSTS configuration checks."""

    @override_settings(ALLOWED_HOSTS=[])
    def test_check_allowed_hosts_configured_empty(self):
        """Check returns ERROR when ALLOWED_HOSTS is empty."""
        from fairdm.conf.checks import check_allowed_hosts_configured

        errors = check_allowed_hosts_configured(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E003"
        assert "ALLOWED_HOSTS" in errors[0].msg
        assert "DJANGO_ALLOWED_HOSTS" in errors[0].hint

    @override_settings(ALLOWED_HOSTS=["example.com"])
    def test_check_allowed_hosts_configured_valid(self):
        """Check returns empty list when ALLOWED_HOSTS is configured."""
        from fairdm.conf.checks import check_allowed_hosts_configured

        errors = check_allowed_hosts_configured(app_configs=None)

        assert errors == []

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_check_allowed_hosts_secure_wildcard(self):
        """Check returns ERROR when ALLOWED_HOSTS contains wildcard."""
        from fairdm.conf.checks import check_allowed_hosts_secure

        errors = check_allowed_hosts_secure(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E004"
        assert "wildcard" in errors[0].msg.lower()

    @override_settings(ALLOWED_HOSTS=["example.com", "www.example.com"])
    def test_check_allowed_hosts_secure_valid(self):
        """Check returns empty list when ALLOWED_HOSTS is secure."""
        from fairdm.conf.checks import check_allowed_hosts_secure

        errors = check_allowed_hosts_secure(app_configs=None)

        assert errors == []


class TestDebugChecks:
    """Tests for DEBUG mode configuration checks."""

    @override_settings(DEBUG=True)
    def test_check_debug_false_enabled(self):
        """Check returns ERROR when DEBUG is True."""
        from fairdm.conf.checks import check_debug_false

        errors = check_debug_false(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E005"
        assert "DEBUG" in errors[0].msg
        assert "production" in errors[0].msg

    @override_settings(DEBUG=False)
    def test_check_debug_false_disabled(self):
        """Check returns empty list when DEBUG is False."""
        from fairdm.conf.checks import check_debug_false

        errors = check_debug_false(app_configs=None)

        assert errors == []


class TestCeleryChecks:
    """Tests for Celery configuration checks."""

    @override_settings(CELERY_BROKER_URL="")
    def test_check_celery_broker_missing(self):
        """Check returns ERROR when CELERY_BROKER_URL is not set."""
        from fairdm.conf.checks import check_celery_broker

        errors = check_celery_broker(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E300"
        assert "CELERY_BROKER_URL" in errors[0].msg
        assert "redis://" in errors[0].hint

    @override_settings(CELERY_BROKER_URL="redis://localhost:6379/0")
    def test_check_celery_broker_configured(self):
        """Check returns empty list when CELERY_BROKER_URL is set."""
        from fairdm.conf.checks import check_celery_broker

        errors = check_celery_broker(app_configs=None)

        assert errors == []

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_check_celery_async_eager(self):
        """Check returns ERROR when CELERY_TASK_ALWAYS_EAGER is True."""
        from fairdm.conf.checks import check_celery_async

        errors = check_celery_async(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E301"
        assert "CELERY_TASK_ALWAYS_EAGER" in errors[0].msg
        assert "synchronously" in errors[0].msg

    @override_settings(CELERY_TASK_ALWAYS_EAGER=False)
    def test_check_celery_async_async(self):
        """Check returns empty list when CELERY_TASK_ALWAYS_EAGER is False."""
        from fairdm.conf.checks import check_celery_async

        errors = check_celery_async(app_configs=None)

        assert errors == []


class TestCheckCommandIntegration:
    """Integration tests for the check management command."""

    @override_settings(SECRET_KEY="")
    def test_check_deploy_fails_with_errors(self):
        """Running check --deploy raises SystemCheckError when configuration has errors."""
        with pytest.raises(SystemCheckError) as exc_info:
            call_command("check", deploy=True)

        assert "fairdm.E001" in str(exc_info.value)

    @override_settings(
        SECRET_KEY="a" * 50,
        DATABASES={
            "default": {"ENGINE": "django.db.backends.postgresql", "NAME": "test"}
        },
        CACHES={
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": "redis://localhost:6379/1",
            }
        },
        ALLOWED_HOSTS=["example.com"],
        DEBUG=False,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        CELERY_BROKER_URL="redis://localhost:6379/0",
        CELERY_TASK_ALWAYS_EAGER=False,
    )
    def test_check_deploy_passes_with_valid_config(self):
        """Running check --deploy succeeds with valid production configuration."""
        # Should not raise
        call_command("check", deploy=True)


class TestDeployCommand:
    """``manage.py check --deploy`` assesses against production standards
    regardless of the current resolved environment (FR-015)."""

    @pytest.mark.parametrize(
        "resolved_environment", ["production", "development", "qa", ""]
    )
    @override_settings(SECRET_KEY="")
    def test_deploy_check_reports_the_same_failure_regardless_of_django_env(
        self, resolved_environment, monkeypatch
    ):
        monkeypatch.setenv("DJANGO_ENV", resolved_environment)

        with pytest.raises(SystemCheckError) as exc_info:
            call_command("check", deploy=True)

        assert "fairdm.E001" in str(exc_info.value)


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
        if key.startswith(
            ("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_", "EMAIL_", "S3_", "SENTRY_")
        ):
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
            "CACHES": {
                "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
            },
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


class TestProductionSetup:
    """Test production configuration loading."""

    def test_production_requires_secret_key(self, production_env):
        """Production should fail without SECRET_KEY."""
        from fairdm.conf.checks import validate_services

        del os.environ["DJANGO_SECRET_KEY"]

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "",  # Empty secret key
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(Exception, match="SECRET_KEY"):
            validate_services("production", test_settings)

    def test_production_requires_allowed_hosts(self, production_env):
        """Production should fail without ALLOWED_HOSTS."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 60,
            "ALLOWED_HOSTS": [],  # Empty allowed hosts
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(Exception, match="ALLOWED_HOSTS"):
            validate_services("production", test_settings)

    def test_production_validates_database(self, production_env):
        """Production should validate database configuration."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {},  # No database configured
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 60,
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(Exception, match="DATABASE"):
            validate_services("production", test_settings)

    def test_production_rejects_debug_true(self, production_env):
        """Production should reject DEBUG=True."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 60,
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": True,  # DEBUG should be False in production
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(Exception, match="DEBUG"):
            validate_services("production", test_settings)

    def test_production_enforces_https_cookies(self, production_env):
        """Production should require secure cookies."""
        from fairdm.conf.checks import validate_services

        test_settings = {
            "DATABASES": {"default": {"ENGINE": "django.db.backends.postgresql"}},
            "CACHES": {"default": {"BACKEND": "django_redis.cache.RedisCache"}},
            "SECRET_KEY": "a" * 60,
            "ALLOWED_HOSTS": ["example.com"],
            "DEBUG": False,
            "SESSION_COOKIE_SECURE": False,  # Should be True
            "CSRF_COOKIE_SECURE": True,
        }

        with pytest.raises(Exception, match="SESSION_COOKIE_SECURE"):
            validate_services("production", test_settings)
