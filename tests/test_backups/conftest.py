"""Shared fixtures for tests/test_backups."""

import pytest
from dbbackup import settings as dbbackup_settings
from dbbackup import utils
from dbbackup.storage import get_storage
from django.core.files.base import ContentFile
from django.db import connection

KEEP = 2


@pytest.fixture
def backup_storage(monkeypatch, settings, tmp_path):
    """Point django-dbbackup at a temporary directory and give media one file.

    django-dbbackup reads its settings once, at import, so ``override_settings`` does not
    reach it: the attributes of ``dbbackup.settings`` are patched instead.

    Returns:
        The ``dbbackup.storage.Storage`` the backup commands write to.
    """
    monkeypatch.setattr(
        dbbackup_settings, "STORAGE", "django.core.files.storage.FileSystemStorage"
    )
    monkeypatch.setattr(
        dbbackup_settings, "STORAGE_OPTIONS", {"location": str(tmp_path / "backups")}
    )
    monkeypatch.setattr(dbbackup_settings, "CLEANUP_KEEP", KEEP)
    monkeypatch.setattr(dbbackup_settings, "CLEANUP_KEEP_MEDIA", KEEP)

    media = tmp_path / "media"
    media.mkdir()
    (media / "photo.txt").write_text("a file of the portal's media")
    settings.MEDIA_ROOT = str(media)

    return get_storage()


@pytest.fixture
def seed_backups(backup_storage):
    """Return a function writing earlier backups of one kind into the backup storage."""

    def seed(content_type, count):
        """Write ``count`` backups dated 2020, oldest first, and return their names.

        Args:
            content_type: ``"db"`` or ``"media"``.
            count: How many backups to write.

        Returns:
            The file names written, oldest first.
        """
        extension = "psql.bin" if content_type == "db" else "tar.gz"
        names = []
        for day in range(1, count + 1):
            name = utils.filename_generate(
                extension,
                database_name=connection.settings_dict["NAME"],
                content_type=content_type,
                wildcard=f"2020-01-0{day}-000000",
            )
            backup_storage.write_file(ContentFile(b"an earlier backup"), name)
            names.append(name)
        return names

    return seed
