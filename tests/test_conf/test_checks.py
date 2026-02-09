"""
Integration tests for fairdm.conf configuration checks.

These tests verify that Django's check framework integration works correctly
and that all configuration validation logic is properly tested.
"""

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

    @override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.postgresql", "NAME": "test"}})
    def test_check_database_configured_valid(self):
        """Check returns empty list when database is properly configured."""
        from fairdm.conf.checks import check_database_configured

        errors = check_database_configured(app_configs=None)

        assert errors == []

    @override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "db.sqlite3"}})
    def test_check_database_production_ready_sqlite(self):
        """Check returns ERROR when using SQLite."""
        from fairdm.conf.checks import check_database_production_ready

        errors = check_database_production_ready(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E101"
        assert "SQLite" in errors[0].msg
        assert "PostgreSQL" in errors[0].hint

    @override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.postgresql", "NAME": "test"}})
    def test_check_database_production_ready_postgresql(self):
        """Check returns empty list when using PostgreSQL."""
        from fairdm.conf.checks import check_database_production_ready

        errors = check_database_production_ready(app_configs=None)

        assert errors == []


class TestCacheChecks:
    """Tests for cache configuration checks."""

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
    def test_check_cache_backend_locmem(self):
        """Check returns ERROR when using locmem cache."""
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E200"
        assert "locmem" in errors[0].msg.lower()
        assert "Redis" in errors[0].hint

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}})
    def test_check_cache_backend_dummy(self):
        """Check returns ERROR when using dummy cache."""
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert "dummy" in errors[0].msg.lower()

    @override_settings(
        CACHES={"default": {"BACKEND": "django_redis.cache.RedisCache", "LOCATION": "redis://localhost:6379/1"}}
    )
    def test_check_cache_backend_redis(self):
        """Check returns empty list when using Redis cache."""
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert errors == []


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
        DATABASES={"default": {"ENGINE": "django.db.backends.postgresql", "NAME": "test"}},
        CACHES={"default": {"BACKEND": "django_redis.cache.RedisCache", "LOCATION": "redis://localhost:6379/1"}},
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
