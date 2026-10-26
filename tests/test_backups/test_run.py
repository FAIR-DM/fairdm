"""Tests for ``fairdm/backups/run.py``."""

import shutil
import subprocess

import psycopg
import pytest
from dbbackup.db.exceptions import CommandConnectorError
from dbbackup.db.postgresql import PgDumpBinaryConnector
from django.contrib.gis.geos import Point
from django.db import connection
from psycopg import sql

from demo.factories import RockSampleFactory
from fairdm.backups.run import run_backup
from fairdm.core.sample.models import Sample
from tests.test_backups.conftest import KEEP


def connection_url(name):
    """Return a PostgreSQL URL for database ``name`` on the test database server."""
    config = connection.settings_dict
    return (
        f"postgresql://{config['USER']}:{config['PASSWORD']}"
        f"@{config['HOST'] or 'localhost'}:{config['PORT'] or 5432}/{name}"
    )


@pytest.mark.django_db(transaction=True)
class TestRunBackup:
    def test_database_backup_writes_one_database_backup(self, backup_storage):
        run_backup("database")

        assert len(backup_storage.list_backups(content_type="db")) == 1
        assert backup_storage.list_backups(content_type="media") == []

    def test_media_backup_writes_one_media_archive(self, backup_storage):
        run_backup("media")

        assert len(backup_storage.list_backups(content_type="media")) == 1
        assert backup_storage.list_backups(content_type="db") == []

    def test_database_backup_restores_a_sample_and_its_location_into_an_empty_database(
        self, backup_storage
    ):
        RockSampleFactory(name="Basalt", location=Point(11.5, 48.1, srid=4326))
        run_backup("database")
        (backup,) = backup_storage.list_backups(content_type="db")
        dump = backup_storage.storage.path(backup)
        target = f"{connection.settings_dict['NAME']}_restore"
        admin_url = connection_url("postgres")

        with psycopg.connect(admin_url, autocommit=True) as admin:
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target)))
        try:
            subprocess.run(  # noqa: S603
                [
                    shutil.which("pg_restore"),
                    f"--dbname={connection_url(target)}",
                    dump,
                ],
                check=True,
                capture_output=True,
            )
            with psycopg.connect(connection_url(target)) as restored:
                row = restored.execute(
                    sql.SQL(
                        "SELECT ST_AsText(location) FROM {} WHERE name = %s"
                    ).format(sql.Identifier(Sample._meta.db_table)),
                    ["Basalt"],
                ).fetchone()
        finally:
            with psycopg.connect(admin_url, autocommit=True) as admin:
                admin.execute(
                    sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                        sql.Identifier(target)
                    )
                )

        assert row == ("POINT(11.5 48.1)",)

    def test_a_new_database_backup_removes_the_oldest_and_keeps_the_count(
        self, backup_storage, seed_backups
    ):
        earlier = seed_backups("db", KEEP)

        run_backup("database")

        kept = backup_storage.list_backups(content_type="db")
        assert len(kept) == KEEP
        assert earlier[0] not in kept
        assert earlier[1] in kept

    def test_a_new_media_backup_removes_the_oldest_and_keeps_the_count(
        self, backup_storage, seed_backups
    ):
        earlier = seed_backups("media", KEEP)

        run_backup("media")

        kept = backup_storage.list_backups(content_type="media")
        assert len(kept) == KEEP
        assert earlier[0] not in kept

    def test_database_and_media_backups_are_counted_separately(
        self, backup_storage, seed_backups
    ):
        seed_backups("db", KEEP)
        media = seed_backups("media", KEEP)

        run_backup("database")

        assert sorted(backup_storage.list_backups(content_type="media")) == media

    def test_a_failing_dump_raises_and_leaves_every_existing_backup(
        self, backup_storage, seed_backups, monkeypatch
    ):
        earlier = seed_backups("db", KEEP)
        monkeypatch.setattr(PgDumpBinaryConnector, "dump_cmd", "false")

        with pytest.raises(CommandConnectorError):
            run_backup("database")

        assert sorted(backup_storage.list_backups(content_type="db")) == earlier
