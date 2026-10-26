"""Tests for ``fairdm/conf/settings/database.py``."""

import os


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

    def test_never_falls_back_to_sqlite_when_unconfigured(
        self, isolated_env, settings_module
    ):
        # SQLite would be a silent degradation of the baseline.
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert (
            module.DATABASES["default"]["ENGINE"]
            == "django.contrib.gis.db.backends.postgis"
        )

    def test_reading_unconfigured_database_never_raises(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()


class TestDatabaseBackup:
    def test_keeps_four_backups_of_each_kind_by_default(
        self, isolated_env, settings_module, monkeypatch
    ):
        os.environ["DJANGO_ENV"] = "qa"
        monkeypatch.delenv("BACKUP_KEEP", raising=False)

        module = settings_module()

        assert module.DBBACKUP_CLEANUP_KEEP == 4
        assert module.DBBACKUP_CLEANUP_KEEP_MEDIA == 4

    def test_backup_keep_sets_the_count_of_each_kind(
        self, isolated_env, settings_module, monkeypatch
    ):
        os.environ["DJANGO_ENV"] = "qa"
        monkeypatch.setenv("BACKUP_KEEP", "7")

        module = settings_module()

        assert module.DBBACKUP_CLEANUP_KEEP == 7
        assert module.DBBACKUP_CLEANUP_KEEP_MEDIA == 7

    def test_backup_server_name_names_the_backup_files(
        self, isolated_env, settings_module, monkeypatch
    ):
        os.environ["DJANGO_ENV"] = "qa"
        monkeypatch.setenv("BACKUP_SERVER_NAME", "lab-portal")

        module = settings_module()

        assert module.DBBACKUP_HOSTNAME == "lab-portal"

    def test_server_name_defaults_to_fairdm(
        self, isolated_env, settings_module, monkeypatch
    ):
        os.environ["DJANGO_ENV"] = "qa"
        monkeypatch.delenv("BACKUP_SERVER_NAME", raising=False)

        module = settings_module()

        assert module.DBBACKUP_HOSTNAME == "fairdm"

    def test_dumps_with_the_custom_format_connector(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.DBBACKUP_CONNECTORS == {
            "default": {"CONNECTOR": "dbbackup.db.postgresql.PgDumpBinaryConnector"}
        }

    def test_the_removed_django_dbbackup_storage_settings_are_not_set(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert not hasattr(module, "DBBACKUP_STORAGE")
        assert not hasattr(module, "DBBACKUP_STORAGE_OPTIONS")

    def test_a_portal_assigning_its_own_cleanup_count_after_setup_keeps_it(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module(after="DBBACKUP_CLEANUP_KEEP = 12")

        assert module.DBBACKUP_CLEANUP_KEEP == 12
