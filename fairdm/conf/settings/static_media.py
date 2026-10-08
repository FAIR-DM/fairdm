"""Static and media file settings: WhiteNoise, compressor, storages and thumbnails.

Owns static serving via WhiteNoise and media storage. Media storage is the local filesystem,
switching to S3 when ``S3_ACCESS_KEY_ID``, ``S3_SECRET_ACCESS_KEY`` and ``S3_BUCKET_NAME``
are all present. A portal supplies thumbnail aliases beyond the four core content types, and
any STORAGES entry it wants to add.
"""

import logging
import os

env = globals()["env"]
BASE_DIR = globals()["BASE_DIR"]
SITE_DOMAIN = globals()["SITE_DOMAIN"]

logger = logging.getLogger(__name__)

STATIC_ROOT = COMPRESS_ROOT = str(BASE_DIR / "static")

STATIC_URL = COMPRESS_URL = "/static/"

if os.path.exists(str(BASE_DIR / "assets")):
    STATICFILES_DIRS = [
        str(BASE_DIR / "assets"),
    ]

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]

MEDIA_ROOT = str(BASE_DIR / "media")

MEDIA_URL = "/media/"

WHITENOISE_MANIFEST_STRICT = False

COMPRESS_ENABLED = True
COMPRESS_STORAGE = "compressor.storage.GzipCompressorFileStorage"
# Whitenoise requires offline compression.
COMPRESS_OFFLINE = True
COMPRESS_FILTERS = {
    "css": [
        "compressor.filters.css_default.CssAbsoluteFilter",
        "compressor.filters.cssmin.rCSSMinFilter",
    ],
    "js": ["compressor.filters.jsmin.JSMinFilter"],
}
COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)

STORAGES = {
    "staticfiles": {
        # CompressedManifestStaticFilesStorage is more trouble than it is worth.
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "LOCATION": str(BASE_DIR / "media"),
    },
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
    # Aliases shared by Project, Dataset, Sample and Measurement: 3:2 for cards and lists, and
    # the 3:1 banner on the overview page, which is the shape an upload is stored in.
    "": {
        "core_small": {"size": (600, 400), "crop": "smart"},
        "core_large": {"size": (1200, 800), "crop": "smart"},
        "core_banner": {"size": (1800, 600), "crop": True},
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
    "fairdm.core.image_utils.crop_to_ratio",
    "easy_thumbnails.processors.scale_and_crop",
    "easy_thumbnails.processors.filters",
]

THUMBNAIL_WIDGET_OPTIONS = {"size": (150, 100)}
