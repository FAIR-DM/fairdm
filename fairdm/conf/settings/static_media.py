"""Static and media file settings: WhiteNoise, storages and thumbnails.

Owns static serving via WhiteNoise, with hashed file names, and media storage.
Media storage is the local filesystem, switching to S3 when ``S3_ACCESS_KEY_ID``,
``S3_SECRET_ACCESS_KEY`` and ``S3_BUCKET_NAME`` are all present. Static files stay
with WhiteNoise either way. Backups follow the media: the local backup directory, or
the media bucket under ``backups`` (``BACKUP_S3_BUCKET_NAME`` names another
bucket). A portal supplies thumbnail aliases beyond the four core content types, and
any STORAGES entry it wants to add.
"""

import logging
import os

env = globals()["env"]
BASE_DIR = globals()["BASE_DIR"]
SITE_DOMAIN = globals()["SITE_DOMAIN"]

logger = logging.getLogger(__name__)

STATIC_ROOT = str(BASE_DIR / "static")

STATIC_URL = "/static/"

if os.path.exists(str(BASE_DIR / "assets")):
    STATICFILES_DIRS = [
        str(BASE_DIR / "assets"),
    ]

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

MEDIA_ROOT = str(BASE_DIR / "media")

MEDIA_URL = "/media/"

# A file in STATIC_ROOT that the manifest does not list is hashed when asked for,
# not refused. A path to a file that does not exist raises either way.
WHITENOISE_MANIFEST_STRICT = False

STORAGES = {
    "staticfiles": {
        # Hashed names, so a deploy never leaves a browser a stale stylesheet or
        # script. Each static path must name a file that exists, and static() must
        # not run at import time, or pages and collectstatic fail.
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "LOCATION": str(BASE_DIR / "media"),
    },
}

# django-dbbackup 5 reads its storage from here, not from DBBACKUP_STORAGE.
STORAGES["dbbackup"] = {
    "BACKEND": "django.core.files.storage.FileSystemStorage",
    "OPTIONS": {"location": env("BACKUP_DIR") or str(BASE_DIR / "backups")},
}

if all(
    [
        env("S3_ACCESS_KEY_ID"),
        env("S3_SECRET_ACCESS_KEY"),
        env("S3_BUCKET_NAME"),
    ]
):
    logger.info("Media storage: Using S3")
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    }
    STORAGES["dbbackup"] = {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": env("BACKUP_S3_BUCKET_NAME") or env("S3_BUCKET_NAME"),
            "location": "backups",
        },
    }

AWS_ACCESS_KEY_ID = env("S3_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("S3_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("S3_BUCKET_NAME")
AWS_S3_REGION_NAME = env("S3_REGION_NAME")

DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024

THUMBNAIL_CACHE_DIMENSIONS = True
THUMBNAIL_SUBDIR = "thumbs"
# On, easy-thumbnails re-raises instead of degrading to a blank image, turning a missing
# source file into a 500. Only conf/development.py enables it.
THUMBNAIL_DEBUG = False

THUMBNAIL_ALIASES = {
    # Shared by Project, Dataset, Sample and Measurement: 3:2 crops and the uncropped cover.
    "": {
        "core_small": {"size": (600, 400), "crop": "smart"},
        # The header of a record with an image: its full width, never cropped.
        "core_cover": {"size": (1200, 0)},
        "core_large": {"size": (1200, 800), "crop": "smart"},
    },
    "contributors": {
        "thumb": {"size": (48, 48), "crop": False},
        "small": {"size": (150, 150), "crop": False},
        "medium": {"size": (600, 600), "crop": False},
    },
}

THUMBNAIL_PROCESSORS = [
    "easy_thumbnails.processors.colorspace",
    "easy_thumbnails.processors.autocrop",
    "easy_thumbnails.processors.scale_and_crop",
    "easy_thumbnails.processors.filters",
]

THUMBNAIL_WIDGET_OPTIONS = {"size": (150, 100)}
