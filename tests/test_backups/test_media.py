"""Tests for ``fairdm/backups/media.py`` and backup retention on an S3 backup storage."""

import io
import tarfile

import pytest
from dbbackup import settings as dbbackup_settings
from dbbackup import utils
from dbbackup.storage import Storage
from django.core.files.base import ContentFile
from django.core.management import call_command

from fairdm.backups.media import SkippingMediaBackup
from fairdm.backups.run import run_backup
from tests.test_backups.s3_stand_in import InMemoryS3Storage

S3_BACKEND = "tests.test_backups.s3_stand_in.InMemoryS3Storage"
LOCAL_BACKEND = "django.core.files.storage.FileSystemStorage"

MEDIA_FILES = {
    "photos/a.jpg": b"a photo",
    "backups-notes/readme.txt": b"a directory whose name only starts like the backups",
}
EARLIER_BACKUP = "backups/earlier.tar.gz"


@pytest.fixture(autouse=True)
def buckets(monkeypatch):
    """Start each test with no buckets."""
    monkeypatch.setattr(InMemoryS3Storage, "buckets", {})
    return InMemoryS3Storage.buckets


@pytest.fixture
def storages(monkeypatch, settings):
    """Return a function that points the media and backup storages at the stand-in.

    The function takes ``media`` and ``backup`` options for the two storages, each of
    ``(backend, options)``, and fills the media bucket with ``MEDIA_FILES`` and an
    earlier backup.
    """

    def configure(media, backup):
        media_backend, media_options = media
        backup_backend, backup_options = backup
        settings.STORAGES = {
            **settings.STORAGES,
            "default": {"BACKEND": media_backend, "OPTIONS": media_options},
        }
        monkeypatch.setattr(dbbackup_settings, "STORAGE", backup_backend)
        monkeypatch.setattr(dbbackup_settings, "STORAGE_OPTIONS", backup_options)
        monkeypatch.setattr(dbbackup_settings, "CLEANUP_KEEP_MEDIA", 10)
        monkeypatch.setattr(dbbackup_settings, "TMP_DIR", None)
        media_storage = InMemoryS3Storage(**media_options)
        for name, content in MEDIA_FILES.items():
            media_storage.save(name, ContentFile(content))

    return configure


def archived_names(bucket, before):
    """Return the names inside the one archive written to ``bucket`` after ``before``."""
    (key,) = [key for key in bucket if key not in before and key.endswith(".tar.gz")]
    with tarfile.open(fileobj=io.BytesIO(bucket[key]), mode="r:gz") as archive:
        return set(archive.getnames())


class TestSkippingMediaBackup:
    def test_a_shared_bucket_leaves_everything_under_the_backup_location_out(
        self, storages, buckets
    ):
        options = {"bucket_name": "portal"}
        storages(
            (S3_BACKEND, options),
            (S3_BACKEND, {**options, "location": "backups"}),
        )
        buckets["portal"][EARLIER_BACKUP] = b"an earlier archive"
        before = set(buckets["portal"])

        call_command(SkippingMediaBackup(), compress=True)

        assert archived_names(buckets["portal"], before) == set(MEDIA_FILES)

    def test_separate_buckets_leave_nothing_out(self, storages, buckets):
        storages(
            (S3_BACKEND, {"bucket_name": "media"}),
            (S3_BACKEND, {"bucket_name": "backups", "location": "backups"}),
        )
        buckets["media"][EARLIER_BACKUP] = b"a media file that is not a backup"
        before = set(buckets["backups"])

        call_command(SkippingMediaBackup(), compress=True)

        assert archived_names(buckets["backups"], before) == {
            *MEDIA_FILES,
            EARLIER_BACKUP,
        }

    def test_backups_on_local_disk_leave_nothing_out(self, storages, buckets, tmp_path):
        storages(
            (S3_BACKEND, {"bucket_name": "portal"}),
            (LOCAL_BACKEND, {"location": str(tmp_path / "backups")}),
        )
        buckets["portal"][EARLIER_BACKUP] = b"a media file that is not a backup"

        call_command(SkippingMediaBackup(), compress=True)

        (archive,) = (tmp_path / "backups").glob("*.tar.gz")
        with tarfile.open(archive) as opened:
            assert set(opened.getnames()) == {*MEDIA_FILES, EARLIER_BACKUP}

    def test_a_backup_location_inside_a_media_location_leaves_out_that_part(
        self, storages, buckets
    ):
        storages(
            (S3_BACKEND, {"bucket_name": "portal", "location": "site"}),
            (S3_BACKEND, {"bucket_name": "portal", "location": "site/backups"}),
        )
        buckets["portal"]["site/" + EARLIER_BACKUP] = b"an earlier archive"
        buckets["portal"]["elsewhere/file.txt"] = b"outside the media location"
        before = set(buckets["portal"])

        call_command(SkippingMediaBackup(), compress=True)

        assert archived_names(buckets["portal"], before) == set(MEDIA_FILES)

    def test_a_backup_location_outside_the_media_location_leaves_nothing_out(
        self, storages, buckets
    ):
        storages(
            (S3_BACKEND, {"bucket_name": "portal", "location": "site"}),
            (S3_BACKEND, {"bucket_name": "portal", "location": "backups"}),
        )
        buckets["portal"]["site/" + EARLIER_BACKUP] = b"a media file"
        before = set(buckets["portal"])

        call_command(SkippingMediaBackup(), compress=True)

        assert archived_names(buckets["portal"], before) == {
            *MEDIA_FILES,
            EARLIER_BACKUP,
        }

    def test_run_backup_of_media_leaves_the_backups_out_of_the_archive(
        self, storages, buckets, settings
    ):
        settings.BACKUP_PUBLIC_KEY = ""
        options = {"bucket_name": "portal"}
        storages(
            (S3_BACKEND, options),
            (S3_BACKEND, {**options, "location": "backups"}),
        )
        buckets["portal"][EARLIER_BACKUP] = b"an earlier archive"
        before = set(buckets["portal"])

        run_backup("media")

        assert archived_names(buckets["portal"], before) == set(MEDIA_FILES)


class TestRetentionOnS3:
    def test_retention_lists_and_deletes_only_under_the_backup_location(
        self, storages, buckets
    ):
        options = {"bucket_name": "portal"}
        storages(
            (S3_BACKEND, options),
            (S3_BACKEND, {**options, "location": "backups"}),
        )
        names = [
            utils.filename_generate(
                "psql.bin",
                database_name="default",
                content_type="db",
                wildcard=f"2020-01-0{day}-000000",
            )
            for day in range(1, 5)
        ]
        for name in names:
            buckets["portal"][f"backups/{name}"] = b"a backup"
        # A look-alike outside the backup location is not the backups' to delete.
        buckets["portal"][names[0]] = b"not a backup of this portal"

        Storage(S3_BACKEND, **options, location="backups").clean_old_backups(
            content_type="db", keep_number=2
        )

        assert sorted(buckets["portal"]) == sorted(
            [
                *MEDIA_FILES,
                names[0],
                f"backups/{names[2]}",
                f"backups/{names[3]}",
            ]
        )
