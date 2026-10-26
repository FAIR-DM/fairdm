"""Tests for ``fairdm/backups/management/commands/backup.py``."""

import pytest
from django.core.management import call_command


@pytest.mark.usefixtures("reseeded_after_flush", "transactional_db")
class TestBackupCommand:
    def test_writes_one_database_backup_and_one_media_archive(self, backup_storage):
        call_command("backup")

        assert len(backup_storage.list_backups(content_type="db")) == 1
        assert len(backup_storage.list_backups(content_type="media")) == 1

    def test_database_only_writes_one_database_backup(self, backup_storage):
        call_command("backup", "--database-only")

        assert len(backup_storage.list_backups(content_type="db")) == 1
        assert backup_storage.list_backups(content_type="media") == []

    def test_media_only_writes_one_media_archive(self, backup_storage):
        call_command("backup", "--media-only")

        assert len(backup_storage.list_backups(content_type="media")) == 1
        assert backup_storage.list_backups(content_type="db") == []
