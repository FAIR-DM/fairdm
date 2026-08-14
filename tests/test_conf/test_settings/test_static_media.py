"""
Tests for ``fairdm/conf/settings/static_media.py`` — the baseline static and
media file configuration (FR-002, FR-003).
"""

import os


class TestStaticMedia:
    """The baseline configures static and media handling from the
    environment (FR-002, FR-003)."""

    def test_local_filesystem_storage_when_s3_unconfigured(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands

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

        settings_module()  # must not raise
