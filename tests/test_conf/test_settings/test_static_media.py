"""Tests for ``fairdm/conf/settings/static_media.py``."""

import os


class TestStaticMedia:
    def test_local_filesystem_storage_when_s3_unconfigured(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert (
            module.STORAGES["default"]["BACKEND"]
            == "django.core.files.storage.FileSystemStorage"
        )
        assert module.STATIC_URL == "/static/"
        assert module.MEDIA_URL == "/media/"

    def test_s3_storage_when_s3_vars_configured(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["S3_ACCESS_KEY_ID"] = "access-key"
        os.environ["S3_SECRET_ACCESS_KEY"] = "secret-key"
        os.environ["S3_BUCKET_NAME"] = "my-bucket"
        os.environ["S3_REGION_NAME"] = "eu-west-1"

        module = settings_module()

        assert (
            module.STORAGES["default"]["BACKEND"]
            == "storages.backends.s3boto3.S3Boto3Storage"
        )
        assert module.AWS_STORAGE_BUCKET_NAME == "my-bucket"
        assert module.AWS_S3_REGION_NAME == "eu-west-1"

    def test_reading_unconfigured_static_media_never_raises(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()


class TestBackupStorage:
    def test_local_media_backs_up_to_a_filesystem_storage_at_backup_dir(
        self, isolated_env, settings_module, monkeypatch
    ):
        os.environ["DJANGO_ENV"] = "qa"
        monkeypatch.setenv("BACKUP_DIR", "/var/lib/fairdm/backups")

        module = settings_module()

        assert module.STORAGES["dbbackup"] == {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {"location": "/var/lib/fairdm/backups"},
        }

    def test_backup_dir_defaults_to_a_directory_beside_the_project(
        self, isolated_env, settings_module, monkeypatch
    ):
        os.environ["DJANGO_ENV"] = "qa"
        monkeypatch.delenv("BACKUP_DIR", raising=False)

        module = settings_module()

        location = module.STORAGES["dbbackup"]["OPTIONS"]["location"]
        assert location == str(module.BASE_DIR / "backups")

    def test_a_portal_assigning_its_own_backup_storage_after_setup_keeps_it(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"
        own = {"BACKEND": "django.core.files.storage.InMemoryStorage"}

        module = settings_module(after=f'STORAGES["dbbackup"] = {own!r}')

        assert module.STORAGES["dbbackup"] == own
