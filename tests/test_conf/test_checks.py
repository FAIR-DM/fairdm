"""
Integration tests for fairdm.conf configuration checks.

These tests verify that Django's check framework integration works
correctly and that all configuration validation logic is properly tested.
"""

import sys
from unittest import mock

import pytest
from django.core.checks import Error
from django.core.management import call_command
from django.core.management.base import SystemCheckError
from django.db import utils as django_db_utils
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

    def test_check_cache_backend_unconfigured_placeholder_fails(self):
        """settings/cache.py's baseline is always Redis-shaped (FS-001 US-1,
        FR-003), so BACKEND alone can no longer distinguish a real deployment
        from an unset REDIS_URL — the check must also recognise the
        placeholder LOCATION cache.py substitutes (FR-017)."""
        from fairdm.conf.checks import UNCONFIGURED_REDIS_LOCATION, check_cache_backend

        with override_settings(
            CACHES={
                "default": {
                    "BACKEND": "django_redis.cache.RedisCache",
                    "LOCATION": UNCONFIGURED_REDIS_LOCATION,
                }
            }
        ):
            errors = check_cache_backend(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E200"

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": "redis://real-redis-host:6379/1",
            }
        }
    )
    def test_check_cache_backend_real_redis_location_passes(self):
        """A genuine REDIS_URL still passes — the placeholder check is exact,
        not a broad Redis-shaped-with-any-empty-looking-value heuristic."""
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

    @override_settings(SECRET_KEY="django-insecure-" + "a" * 50)
    def test_check_secret_key_exists_insecure_prefix(self):
        """Check returns ERROR when SECRET_KEY carries the published insecure prefix (FR-017, SC-006)."""
        from fairdm.conf.checks import check_secret_key_exists

        errors = check_secret_key_exists(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E001"
        assert "insecure" in errors[0].msg.lower()

    @override_settings(SECRET_KEY="short-key")
    def test_check_secret_key_exists_too_short(self):
        """Check returns ERROR when SECRET_KEY is short enough to be brute-forced (FR-017).

        Django reports the same condition as security.W009, a warning, which
        cannot block a boot.
        """
        from fairdm.conf.checks import check_secret_key_exists

        errors = check_secret_key_exists(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E001"
        assert "50" in errors[0].hint


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


class TestSecureCookiePrefixChecks:
    """Tests for the cookie-name prefix check (fairdm.E006)."""

    @override_settings(CSRF_COOKIE_NAME="__Secure-csrftoken", CSRF_COOKIE_SECURE=False)
    def test_check_reports_a_prefixed_name_on_an_insecure_cookie(self):
        from fairdm.conf.checks import check_secure_cookie_prefixes_match_secure_flag

        errors = check_secure_cookie_prefixes_match_secure_flag(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E006"
        assert "CSRF_COOKIE_NAME" in errors[0].msg
        assert "__Secure-" in errors[0].msg

    @override_settings(CSRF_COOKIE_NAME="__Secure-csrftoken", CSRF_COOKIE_SECURE=True)
    def test_check_passes_when_the_prefixed_cookie_is_secure(self):
        from fairdm.conf.checks import check_secure_cookie_prefixes_match_secure_flag

        assert check_secure_cookie_prefixes_match_secure_flag(app_configs=None) == []

    @override_settings(CSRF_COOKIE_NAME="csrftoken", CSRF_COOKIE_SECURE=False)
    def test_check_passes_when_an_insecure_cookie_is_unprefixed(self):
        from fairdm.conf.checks import check_secure_cookie_prefixes_match_secure_flag

        assert check_secure_cookie_prefixes_match_secure_flag(app_configs=None) == []

    @override_settings(
        SESSION_COOKIE_NAME="__Host-sessionid", SESSION_COOKIE_SECURE=False
    )
    def test_check_covers_the_host_prefix_and_the_session_cookie(self):
        from fairdm.conf.checks import check_secure_cookie_prefixes_match_secure_flag

        errors = check_secure_cookie_prefixes_match_secure_flag(app_configs=None)

        assert [error.id for error in errors] == ["fairdm.E006"]
        assert "SESSION_COOKIE_NAME" in errors[0].msg
        assert "__Host-" in errors[0].msg

    @override_settings(
        CSRF_COOKIE_NAME="__Secure-csrftoken",
        CSRF_COOKIE_SECURE=False,
        SESSION_COOKIE_NAME="__Secure-sessionid",
        SESSION_COOKIE_SECURE=False,
    )
    def test_check_reports_every_mismatched_cookie_not_just_the_first(self):
        from fairdm.conf.checks import check_secure_cookie_prefixes_match_secure_flag

        errors = check_secure_cookie_prefixes_match_secure_flag(app_configs=None)

        assert len(errors) == 2
        reported = " ".join(error.msg for error in errors)
        assert "CSRF_COOKIE_NAME" in reported
        assert "SESSION_COOKIE_NAME" in reported

    @override_settings(CSRF_COOKIE_NAME="__Secure-csrftoken", CSRF_COOKIE_SECURE=False)
    def test_check_runs_without_the_deploy_flag(self):
        """The fault it catches only occurs off production, so a check the
        plain command does not run would never fire where it matters."""
        with pytest.raises(SystemCheckError) as excinfo:
            call_command("check", "--tag", "security", "--fail-level", "ERROR")

        assert "fairdm.E006" in str(excinfo.value)


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


class TestParlerLanguagesChecks:
    """PARLER_LANGUAGES must name only codes LANGUAGES also names — django-parler
    enforces the same rule itself, but at import time, before this check (or any
    Django check) can run; see ``tests/test_apps.py::TestParlerLanguagesCheck``
    for where ``FairDMConfig`` calls this early enough to matter (T107)."""

    @override_settings(
        LANGUAGES=[("en", "English"), ("de", "German")],
        PARLER_LANGUAGES={
            1: ({"code": "en"}, {"code": "fr"}, {"code": "de"}),
            "default": {"fallback": "en", "hide_untranslated": False},
        },
    )
    def test_check_names_the_code_missing_from_languages(self):
        from fairdm.conf.checks import check_parler_languages_subset_of_languages

        errors = check_parler_languages_subset_of_languages(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E400"
        assert "PARLER_LANGUAGES" in errors[0].msg
        assert "LANGUAGES" in errors[0].msg
        assert "fr" in errors[0].msg

    @override_settings(
        LANGUAGES=[("en", "English")],
        PARLER_LANGUAGES={
            1: ({"code": "en"}, {"code": "fr"}, {"code": "de"}),
            "default": {"fallback": "en", "hide_untranslated": False},
        },
    )
    def test_check_names_every_missing_code_not_just_the_first(self):
        from fairdm.conf.checks import check_parler_languages_subset_of_languages

        errors = check_parler_languages_subset_of_languages(app_configs=None)

        assert len(errors) == 1
        assert "fr" in errors[0].msg
        assert "de" in errors[0].msg

    @override_settings(
        LANGUAGES=[("en", "English"), ("de", "German")],
        PARLER_LANGUAGES={
            1: ({"code": "en"}, {"code": "de"}),
            "default": {"fallback": "en", "hide_untranslated": False},
        },
    )
    def test_check_passes_when_every_parler_code_is_in_languages(self):
        from fairdm.conf.checks import check_parler_languages_subset_of_languages

        errors = check_parler_languages_subset_of_languages(app_configs=None)

        assert errors == []

    @override_settings(
        LANGUAGES=[("fr", "French")],
        PARLER_DEFAULT_LANGUAGE_CODE="fr",
        PARLER_LANGUAGES={
            1: ({"code": "fr-ca"},),
            "default": {"fallback": "fr", "hide_untranslated": False},
        },
    )
    def test_base_subtag_match_is_accepted_like_django_parler_accepts_it(self):
        """django-parler's own ``is_supported_django_language()`` accepts a
        PARLER code whose base subtag (``fr`` from ``fr-ca``) is in
        LANGUAGES — this check must not flag what parler itself would not."""
        from fairdm.conf.checks import check_parler_languages_subset_of_languages

        errors = check_parler_languages_subset_of_languages(app_configs=None)

        assert errors == []

    @override_settings(
        LANGUAGES=[("de", "German")],
        PARLER_DEFAULT_LANGUAGE_CODE="en",
        PARLER_LANGUAGES={
            1: ({"code": "de"},),
            "default": {"fallback": "de", "hide_untranslated": False},
        },
    )
    def test_check_names_a_default_language_code_missing_from_languages(self):
        """The ``"default"`` entry names no ``code`` of its own, so parler
        falls back to PARLER_DEFAULT_LANGUAGE_CODE and rejects the whole
        setting on that before it looks at any site's choices — every site
        code here is valid. Verified against
        ``parler.utils.conf.add_default_language_settings``."""
        from fairdm.conf.checks import check_parler_languages_subset_of_languages

        errors = check_parler_languages_subset_of_languages(app_configs=None)

        assert len(errors) == 1
        assert errors[0].id == "fairdm.E400"
        assert "en" in errors[0].msg
        assert "PARLER_DEFAULT_LANGUAGE_CODE" in errors[0].hint

    @override_settings(
        LANGUAGES=[("de", "German")],
        PARLER_DEFAULT_LANGUAGE_CODE="en",
        PARLER_LANGUAGES={
            1: ({"code": "de"},),
            "default": {"code": "de", "fallback": "de", "hide_untranslated": False},
        },
    )
    def test_an_explicit_default_code_wins_over_parler_default_language_code(self):
        from fairdm.conf.checks import check_parler_languages_subset_of_languages

        assert check_parler_languages_subset_of_languages(app_configs=None) == []


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


def _delete_group_by_raw_sql(name: str) -> None:
    """Remove a group row, and its permission associations, without going through
    the ORM (research R6) - the ORM guard T021 installs on ``Group`` refuses this
    the same way it refuses an administrator, so a test that wants "the role does
    not exist yet" has to reach around it, exactly as a shell or a script could."""
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM auth_group WHERE name = %s", [name])
        row = cursor.fetchone()
        if row is None:
            return
        cursor.execute(
            "DELETE FROM auth_group_permissions WHERE group_id = %s", [row[0]]
        )
        cursor.execute("DELETE FROM auth_group WHERE id = %s", [row[0]])


class TestPortalRolesPresent:
    """T024/T025, FR-015 to FR-017: a serving portal missing a shipped role
    refuses to start and names it; the boot refusal stands down for the
    command that installs the roles (D11, research R4)."""

    def test_two_missing_roles_are_named_in_one_error(self, db):
        from fairdm.conf.checks import check_portal_roles_present
        from fairdm.portal_roles import PortalRoles

        PortalRoles.reconcile()
        _delete_group_by_raw_sql(PortalRoles.DATA_CURATOR.name)
        _delete_group_by_raw_sql(PortalRoles.COMMUNITY_MANAGER.name)

        errors = check_portal_roles_present(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E500"
        assert PortalRoles.DATA_CURATOR.name in errors[0].msg
        assert PortalRoles.COMMUNITY_MANAGER.name in errors[0].msg

    def test_all_four_present_returns_nothing(self, db):
        from fairdm.conf.checks import check_portal_roles_present
        from fairdm.portal_roles import PortalRoles

        PortalRoles.reconcile()

        assert check_portal_roles_present(app_configs=None) == []

    @pytest.mark.parametrize(
        "exception_class",
        [
            django_db_utils.ProgrammingError,
            django_db_utils.OperationalError,
            # A test harness that refuses database access outright (e.g.
            # pytest-django's own safeguard for a test with no `db` fixture)
            # raises this, not a django.db.utils error - "unreadable" covers
            # it too (D24, research R4).
            RuntimeError,
        ],
    )
    def test_an_absent_or_unreadable_group_table_returns_nothing(
        self, db, exception_class
    ):
        from fairdm.conf.checks import check_portal_roles_present

        with mock.patch(
            "django.contrib.auth.models.Group.objects.filter",
            side_effect=exception_class("no such table: auth_group"),
        ):
            assert check_portal_roles_present(app_configs=None) == []

    def test_a_database_django_cannot_even_resolve_an_engine_for_returns_nothing(
        self, db
    ):
        """A ``DATABASE_URL``-absent portal (``fairdm.E100``'s own case) composes an
        unusable ``DATABASES`` entry that raises ``ImproperlyConfigured`` the moment
        any query tries to compile SQL against it - not ``OperationalError`` or
        ``ProgrammingError``. Reproduced against ``TestProductionBoot`` failing with
        an uncaught traceback instead of a clean `SystemCheckError` before this was
        added to the except clause."""
        from django.core.exceptions import ImproperlyConfigured

        from fairdm.conf.checks import check_portal_roles_present

        with mock.patch(
            "django.contrib.auth.models.Group.objects.filter",
            side_effect=ImproperlyConfigured(
                "settings.DATABASES is improperly configured."
            ),
        ):
            assert check_portal_roles_present(app_configs=None) == []

    def test_stands_down_when_the_current_command_is_migrate(self, db, monkeypatch):
        from fairdm.conf.checks import check_portal_roles_present
        from fairdm.portal_roles import PortalRoles

        PortalRoles.reconcile()
        _delete_group_by_raw_sql(PortalRoles.DATA_CURATOR.name)
        monkeypatch.setattr(sys, "argv", ["manage.py", "migrate", "--noinput"])

        assert check_portal_roles_present(app_configs=None) == []

    def test_does_not_stand_down_for_an_unrelated_command(self, db, monkeypatch):
        """The stand-down is scoped to the command that installs the roles - D11
        names only ``migrate``, not every management command."""
        from fairdm.conf.checks import check_portal_roles_present
        from fairdm.portal_roles import PortalRoles

        PortalRoles.reconcile()
        _delete_group_by_raw_sql(PortalRoles.DATA_CURATOR.name)
        monkeypatch.setattr(sys, "argv", ["manage.py", "runserver"])

        errors = check_portal_roles_present(app_configs=None)

        assert len(errors) == 1

    def test_check_deploy_reports_a_missing_role_regardless_of_environment(self, db):
        """FR-017: development never refuses to start, but the framework's
        on-demand configuration check reports the condition all the same."""
        from fairdm.portal_roles import PortalRoles

        PortalRoles.reconcile()
        _delete_group_by_raw_sql(PortalRoles.DATA_CURATOR.name)

        with pytest.raises(SystemCheckError) as exc_info:
            call_command("check", deploy=True)

        assert "fairdm.E500" in str(exc_info.value)
        assert PortalRoles.DATA_CURATOR.name in str(exc_info.value)

    def test_check_is_registered_with_the_production_critical_deploy_tags(self):
        """The wiring FR-015/FR-016 depend on: `FairDMConfig._check_production_configuration`
        (fairdm/apps.py) aggregates exactly the checks tagged `DeployTags.production_critical`,
        and only `manage.py check --deploy` sees a check tagged `deploy=True` at all (research
        R4). Both are asserted directly against the registered check rather than exercised
        through a live production boot: doing that for real needs a PostgreSQL connection -
        every other production_critical check reads settings values only, so the existing
        subprocess boot tests never open one, but this check's job is to query the `Group`
        table, and SQLite cannot stand in (`fairdm.E101` fires for any non-development
        environment, unconditionally, and `_check_production_configuration` does not consult
        `SILENCED_SYSTEM_CHECKS`). `TestPortalRolesReconciliation` in `tests/test_apps.py`
        already proves `migrate` installs the roles against this suite's real (SQLite)
        database; the tests above prove the check's own query and stand-down logic; this proves
        the two are wired into the same gate every other production-critical check uses.
        """
        from django.core.checks.registry import registry

        from fairdm.conf.checks import DeployTags, check_portal_roles_present

        assert check_portal_roles_present in registry.get_checks(
            include_deployment_checks=True
        )
        assert set(check_portal_roles_present.tags) == {
            DeployTags.deploy,
            DeployTags.production_critical,
        }
        # deploy=True: only visible to `manage.py check --deploy`, not a plain check.
        assert check_portal_roles_present not in registry.get_checks(
            include_deployment_checks=False
        )
