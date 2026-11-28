"""Tests for ``fairdm/conf/settings/database.py``."""

import os

import pytest
from django.core.exceptions import ImproperlyConfigured


class TestDatabase:
    def test_configures_postgres_from_database_url(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["DATABASE_URL"] = "postgresql://scott:tiger@dbhost:5433/mydatabase"

        module = settings_module()

        assert (
            module.DATABASES["default"]["ENGINE"]
            == "django.contrib.gis.db.backends.postgis"
        )
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

        assert (
            module.DATABASES["default"]["ENGINE"]
            == "django.contrib.gis.db.backends.postgis"
        )
        assert module.DATABASES["default"]["NAME"] == "mydatabase"
        assert module.DATABASES["default"]["HOST"] == "dbhost"
        assert module.DATABASES["default"]["PORT"] == 5433


class TestDatabaseBackup:
    def test_backup_keep_sets_the_count_of_each_kind(
        self, isolated_env, settings_module, monkeypatch
    ):
        os.environ["DJANGO_ENV"] = "qa"
        monkeypatch.setenv("BACKUP_KEEP", "7")

        module = settings_module()

        assert module.DBBACKUP_CLEANUP_KEEP == 7
        assert module.DBBACKUP_CLEANUP_KEEP_MEDIA == 7

    @pytest.mark.parametrize("keep", ["0", "-1"])
    def test_a_backup_keep_below_one_is_refused(
        self, isolated_env, settings_module, monkeypatch, keep
    ):
        os.environ["DJANGO_ENV"] = "qa"
        monkeypatch.setenv("BACKUP_KEEP", keep)

        with pytest.raises(ImproperlyConfigured, match="BACKUP_KEEP"):
            settings_module()

    def test_a_backup_keep_of_one_is_accepted(
        self, isolated_env, settings_module, monkeypatch
    ):
        os.environ["DJANGO_ENV"] = "qa"
        monkeypatch.setenv("BACKUP_KEEP", "1")

        module = settings_module()

        assert module.DBBACKUP_CLEANUP_KEEP == 1

    def test_backup_server_name_names_the_backup_files(
        self, isolated_env, settings_module, monkeypatch
    ):
        os.environ["DJANGO_ENV"] = "qa"
        monkeypatch.setenv("BACKUP_SERVER_NAME", "lab-portal")

        module = settings_module()

        assert module.DBBACKUP_HOSTNAME == "lab-portal"
