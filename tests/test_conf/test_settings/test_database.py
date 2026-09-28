"""Tests for ``fairdm/conf/settings/database.py``."""

import os


class TestDatabase:
    def test_configures_postgres_from_database_url(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["DATABASE_URL"] = "postgresql://scott:tiger@dbhost:5433/mydatabase"

        module = settings_module()

        assert module.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"
        assert module.DATABASES["default"]["NAME"] == "mydatabase"
        assert module.DATABASES["default"]["HOST"] == "dbhost"
        assert module.DATABASES["default"]["PORT"] == 5433

    def test_composes_postgres_from_discrete_vars_when_database_url_unset(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["POSTGRES_DB"] = "mydatabase"
        os.environ["POSTGRES_USER"] = "scott"
        os.environ["POSTGRES_PASSWORD"] = "tiger"
        os.environ["POSTGRES_HOST"] = "dbhost"
        os.environ["POSTGRES_PORT"] = "5433"

        module = settings_module()

        assert module.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"
        assert module.DATABASES["default"]["NAME"] == "mydatabase"
        assert module.DATABASES["default"]["HOST"] == "dbhost"
        assert module.DATABASES["default"]["PORT"] == 5433

    def test_never_falls_back_to_sqlite_when_unconfigured(
        self, isolated_env, settings_module
    ):
        # SQLite would be a silent degradation of the baseline.
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"

    def test_reading_unconfigured_database_never_raises(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()
