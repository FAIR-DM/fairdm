"""Integration tests for fairdm.conf configuration checks."""

import sys
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core.checks import Error
from django.core.management import call_command
from django.core.management.base import SystemCheckError
from django.db import utils as django_db_utils
from django.test import override_settings


class TestDatabaseChecks:
    @override_settings(DATABASES={})
    def test_check_database_configured_missing(self):
        from fairdm.conf.checks import check_database_configured

        errors = check_database_configured(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E100"
        assert "DATABASES" in errors[0].msg
        assert "DATABASE_URL" in errors[0].hint

    @override_settings(DATABASES={"default": {}})
    def test_check_database_configured_empty(self):
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
        from fairdm.conf.checks import check_database_configured

        errors = check_database_configured(app_configs=None)

        assert errors == []

    @override_settings(
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "db.sqlite3"}
        }
    )
    def test_check_database_production_ready_sqlite(self):
        from fairdm.conf.checks import check_database_production_ready

        errors = check_database_production_ready(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E101"

    @override_settings(
        DATABASES={
            "default": {"ENGINE": "django.db.backends.postgresql", "NAME": "test"}
        }
    )
    def test_check_database_production_ready_postgresql(self):
        from fairdm.conf.checks import check_database_production_ready

        errors = check_database_production_ready(app_configs=None)

        assert errors == []


class TestSyntacticallyUnusableValue:
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
        from fairdm.conf.checks import check_database_configured, check_database_usable

        assert check_database_configured(app_configs=None) == []

        errors = check_database_usable(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E102"


class TestCacheChecks:
    @override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    )
    def test_check_cache_backend_locmem(self):
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E200"

    @override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
    )
    def test_check_cache_backend_dummy(self):
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E200"

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django_redis.cache.RedisCache",
                "LOCATION": "redis://localhost:6379/1",
            }
        }
    )
    def test_check_cache_backend_redis(self):
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert errors == []

    @override_settings(CACHES={})
    def test_check_cache_backend_caches_absent(self):
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E200"

    @override_settings(CACHES={"default": {}})
    def test_check_cache_backend_default_empty(self):
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
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E200"

    def test_check_cache_backend_unconfigured_placeholder_fails(self):
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
        from fairdm.conf.checks import check_cache_backend

        errors = check_cache_backend(app_configs=None)

        assert errors == []


class TestSecretKeyChecks:
    @override_settings(SECRET_KEY="")
    def test_check_secret_key_exists_empty(self):
        from fairdm.conf.checks import check_secret_key_exists

        errors = check_secret_key_exists(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E001"
        assert "SECRET_KEY" in errors[0].msg

    @override_settings(SECRET_KEY="a" * 50)
    def test_check_secret_key_exists_valid(self):
        from fairdm.conf.checks import check_secret_key_exists

        errors = check_secret_key_exists(app_configs=None)

        assert errors == []

    @override_settings(SECRET_KEY="django-insecure-" + "a" * 50)
    def test_check_secret_key_exists_insecure_prefix(self):
        from fairdm.conf.checks import check_secret_key_exists

        errors = check_secret_key_exists(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E001"

    @override_settings(SECRET_KEY="short-key")
    def test_check_secret_key_exists_too_short(self):
        # Django reports the same condition as security.W009, a warning, which cannot block a boot.
        from fairdm.conf.checks import check_secret_key_exists

        errors = check_secret_key_exists(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E001"


class TestAllowedHostsChecks:
    @override_settings(ALLOWED_HOSTS=[])
    def test_check_allowed_hosts_configured_empty(self):
        from fairdm.conf.checks import check_allowed_hosts_configured

        errors = check_allowed_hosts_configured(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E003"
        assert "ALLOWED_HOSTS" in errors[0].msg
        assert "DJANGO_ALLOWED_HOSTS" in errors[0].hint

    @override_settings(ALLOWED_HOSTS=["example.com"])
    def test_check_allowed_hosts_configured_valid(self):
        from fairdm.conf.checks import check_allowed_hosts_configured

        errors = check_allowed_hosts_configured(app_configs=None)

        assert errors == []

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_check_allowed_hosts_secure_wildcard(self):
        from fairdm.conf.checks import check_allowed_hosts_secure

        errors = check_allowed_hosts_secure(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E004"

    @override_settings(ALLOWED_HOSTS=["example.com", "www.example.com"])
    def test_check_allowed_hosts_secure_valid(self):
        from fairdm.conf.checks import check_allowed_hosts_secure

        errors = check_allowed_hosts_secure(app_configs=None)

        assert errors == []


class TestDebugChecks:
    @override_settings(DEBUG=True)
    def test_check_debug_false_enabled(self):
        from fairdm.conf.checks import check_debug_false

        errors = check_debug_false(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E005"
        assert "DEBUG" in errors[0].msg

    @override_settings(DEBUG=False)
    def test_check_debug_false_disabled(self):
        from fairdm.conf.checks import check_debug_false

        errors = check_debug_false(app_configs=None)

        assert errors == []


class TestSecureCookiePrefixChecks:
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
        # The fault only occurs off production, so a check the plain command skipped would never fire where it matters.
        with pytest.raises(SystemCheckError) as excinfo:
            call_command("check", "--tag", "security", "--fail-level", "ERROR")

        assert "fairdm.E006" in str(excinfo.value)


class TestCeleryChecks:
    @override_settings(CELERY_BROKER_URL="")
    def test_check_celery_broker_missing(self):
        from fairdm.conf.checks import check_celery_broker

        errors = check_celery_broker(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E300"
        assert "CELERY_BROKER_URL" in errors[0].msg

    @override_settings(CELERY_BROKER_URL="redis://localhost:6379/0")
    def test_check_celery_broker_configured(self):
        from fairdm.conf.checks import check_celery_broker

        errors = check_celery_broker(app_configs=None)

        assert errors == []

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_check_celery_async_eager(self):
        from fairdm.conf.checks import check_celery_async

        errors = check_celery_async(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E301"
        assert "CELERY_TASK_ALWAYS_EAGER" in errors[0].msg

    @override_settings(CELERY_TASK_ALWAYS_EAGER=False)
    def test_check_celery_async_async(self):
        from fairdm.conf.checks import check_celery_async

        errors = check_celery_async(app_configs=None)

        assert errors == []


class TestParlerLanguagesChecks:
    @override_settings(
        LANGUAGES=[("en", "English"), ("de", "German")],
        PARLER_LANGUAGES={
            1: ({"code": "en"}, {"code": "fr"}, {"code": "de"}),
            "default": {"fallback": "en", "hide_untranslated": False},
        },
    )
    # parler enforces the same rule at import time, before any check runs. See
    # tests/test_apps.py::TestParlerLanguagesCheck for where FairDMConfig applies it.
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
        # The "default" entry has no code of its own, so parler falls back to PARLER_DEFAULT_LANGUAGE_CODE
        # and rejects the whole setting on it.
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
    @override_settings(SECRET_KEY="")
    def test_check_deploy_fails_with_errors(self):
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
        call_command("check", deploy=True)


class TestDeployCommand:
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
            # A harness that refuses database access outright (pytest-django with no `db` fixture) raises
            # this, not a django.db.utils error, so "unreadable" has to cover it.
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
        # A portal without DATABASE_URL composes a DATABASES entry that raises ImproperlyConfigured on the
        # first query, not OperationalError or ProgrammingError.
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
        from fairdm.conf.checks import check_portal_roles_present
        from fairdm.portal_roles import PortalRoles

        PortalRoles.reconcile()
        _delete_group_by_raw_sql(PortalRoles.DATA_CURATOR.name)
        monkeypatch.setattr(sys, "argv", ["manage.py", "runserver"])

        errors = check_portal_roles_present(app_configs=None)

        assert len(errors) == 1

    def test_check_deploy_reports_a_missing_role_regardless_of_environment(self, db):
        from fairdm.portal_roles import PortalRoles

        PortalRoles.reconcile()
        _delete_group_by_raw_sql(PortalRoles.DATA_CURATOR.name)

        with pytest.raises(SystemCheckError) as exc_info:
            call_command("check", deploy=True)

        assert "fairdm.E500" in str(exc_info.value)
        assert PortalRoles.DATA_CURATOR.name in str(exc_info.value)

    def test_check_is_registered_with_the_production_critical_deploy_tags(self):
        # Only `manage.py check --deploy` sees a check tagged deploy=True, and the production
        # configuration aggregate runs exactly the checks tagged production_critical.
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


class TestDevAccountsAbsent:
    @override_settings(DJANGO_ENV="production")
    def test_one_dev_address_on_a_production_portal_is_named(self, db):
        from fairdm.conf.checks import check_dev_accounts_absent
        from fairdm.management.commands.create_dev_accounts import DEV_ACCOUNTS

        Person = get_user_model()
        account = DEV_ACCOUNTS[0]
        Person.objects.create_user(
            email=account["email"],
            password="whatever",
            first_name=account["first_name"],
            last_name=account["last_name"],
        )

        errors = check_dev_accounts_absent(app_configs=None)

        assert len(errors) == 1
        assert isinstance(errors[0], Error)
        assert errors[0].id == "fairdm.E501"
        assert account["email"] in errors[0].msg

    @override_settings(DJANGO_ENV="production")
    def test_all_five_dev_addresses_on_a_production_portal_are_named_together(self, db):
        from fairdm.conf.checks import check_dev_accounts_absent
        from fairdm.management.commands.create_dev_accounts import DEV_ACCOUNTS

        Person = get_user_model()
        for account in DEV_ACCOUNTS:
            Person.objects.create_user(
                email=account["email"],
                password="whatever",
                first_name=account["first_name"],
                last_name=account["last_name"],
            )

        errors = check_dev_accounts_absent(app_configs=None)

        assert len(errors) == 1
        for account in DEV_ACCOUNTS:
            assert account["email"] in errors[0].msg

    @override_settings(DJANGO_ENV="production")
    def test_no_dev_addresses_on_a_production_portal_reports_nothing(self, db):
        from fairdm.conf.checks import check_dev_accounts_absent

        assert check_dev_accounts_absent(app_configs=None) == []

    def test_a_development_portal_holding_all_five_reports_nothing(self, db):
        from fairdm.conf.checks import check_dev_accounts_absent

        call_command("create_dev_accounts", verbosity=0)

        assert check_dev_accounts_absent(app_configs=None) == []

    @pytest.mark.parametrize(
        "exception_class",
        [
            django_db_utils.ProgrammingError,
            django_db_utils.OperationalError,
            # A harness that refuses database access outright (pytest-django with no `db` fixture) raises
            # this, not a django.db.utils error, so "unreadable" has to cover it.
            RuntimeError,
        ],
    )
    @override_settings(DJANGO_ENV="production")
    def test_an_unreadable_user_table_returns_nothing(self, db, exception_class):
        from fairdm.conf.checks import check_dev_accounts_absent

        Person = get_user_model()
        with mock.patch.object(
            Person.objects,
            "filter",
            side_effect=exception_class("no such table: contributors_person"),
        ):
            assert check_dev_accounts_absent(app_configs=None) == []

    @override_settings(DJANGO_ENV="production")
    def test_a_database_django_cannot_even_resolve_an_engine_for_returns_nothing(
        self, db
    ):
        from django.core.exceptions import ImproperlyConfigured

        from fairdm.conf.checks import check_dev_accounts_absent

        Person = get_user_model()
        with mock.patch.object(
            Person.objects,
            "filter",
            side_effect=ImproperlyConfigured(
                "settings.DATABASES is improperly configured."
            ),
        ):
            assert check_dev_accounts_absent(app_configs=None) == []

    def test_check_is_registered_with_the_same_tags_as_the_portal_roles_check(self):
        from django.core.checks.registry import registry

        from fairdm.conf.checks import (
            check_dev_accounts_absent,
            check_portal_roles_present,
        )

        assert check_dev_accounts_absent in registry.get_checks(
            include_deployment_checks=True
        )
        assert check_dev_accounts_absent.tags == check_portal_roles_present.tags

    def test_no_other_check_in_the_file_shares_fairdm_e501(self):
        import inspect

        from fairdm.conf import checks

        assert inspect.getsource(checks).count('"fairdm.E501"') == 1


class TestDevAccountsAbsentReportsTheExampleAccounts:
    """The accounts the overview development data signs in through are dev accounts too."""

    @pytest.mark.parametrize(
        "email",
        [
            "regular.user@example.com",
            "staff.user@example.com",
            "super.user@example.com",
        ],
    )
    @override_settings(DJANGO_ENV="production")
    def test_an_example_account_on_a_production_portal_is_named(self, db, email):
        from fairdm.conf.checks import check_dev_accounts_absent

        get_user_model().objects.create_user(email=email, password="whatever")

        errors = check_dev_accounts_absent(app_configs=None)

        assert len(errors) == 1
        assert errors[0].id == "fairdm.E501"
        assert email in errors[0].msg

    @override_settings(DJANGO_ENV="production")
    def test_the_framework_and_example_accounts_are_reported_together(self, db):
        from fairdm.conf.checks import check_dev_accounts_absent

        Person = get_user_model()
        Person.objects.create_user(email="staff.user@example.com", password="x")
        Person.objects.create_user(email="data.curator@fairdm.org", password="x")

        errors = check_dev_accounts_absent(app_configs=None)

        assert len(errors) == 1
        assert "staff.user@example.com" in errors[0].msg
        assert "data.curator@fairdm.org" in errors[0].msg

    def test_a_development_portal_holding_them_reports_nothing(self, db):
        from fairdm.conf.checks import check_dev_accounts_absent

        get_user_model().objects.create_user(
            email="staff.user@example.com", password="x"
        )

        assert check_dev_accounts_absent(app_configs=None) == []
