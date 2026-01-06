"""Static and Media Files Configuration

Production-ready static file serving with WhiteNoise and optional S3 media storage.

Production: Uses WhiteNoise for static files, S3/local for media files
Development: Uses local filesystem for both static and media

This is the production baseline. Environment-specific overrides in local.py/staging.py.
"""

import os
from pathlib import Path
import logging

# Access environment variables via shared env instance
env = globals()["env"]
BASE_DIR = globals()["BASE_DIR"]
SITE_DOMAIN = globals()["SITE_DOMAIN"]

logger = logging.getLogger(__name__)

# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = COMPRESS_ROOT = str(BASE_DIR / "static")

# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = COMPRESS_URL = "/static/"


# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
if os.path.exists(str(BASE_DIR / "assets")):
    STATICFILES_DIRS = [
        # this is where the end user will store their static files
        str(BASE_DIR / "assets"),
    ]

# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "compressor.finders.CompressorFinder",
]


# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(BASE_DIR / "media")

# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "/media/"

# ======= WHITENOISE =================================
WHITENOISE_MANIFEST_STRICT = False


# ======= Django Compressor ========================
# https://django-compressor.readthedocs.io/en/latest/settings/

COMPRESS_ENABLED = True
COMPRESS_STORAGE = "compressor.storage.GzipCompressorFileStorage"
COMPRESS_OFFLINE = True  # Offline compression is required when using Whitenoise
COMPRESS_FILTERS = {
    "css": [
        "compressor.filters.css_default.CssAbsoluteFilter",
        "compressor.filters.cssmin.rCSSMinFilter",
    ],
    "js": ["compressor.filters.jsmin.JSMinFilter"],
}
COMPRESS_PRECOMPILERS = (("text/x-scss", "django_libsass.SassCompiler"),)

# STATIC
# ------------------------

STORAGES = {
    "staticfiles": {
        # using whitenosie.storage.CompressedManifestStaticFilesStorage is more problematic than it's worth
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
    # https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    }

# STORAGES
# ------------------------------------------------------------------------------
AWS_ACCESS_KEY_ID = env("S3_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = env("S3_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = env("S3_BUCKET_NAME")
AWS_S3_REGION_NAME = env("S3_REGION_NAME")

# AWS_ACCESS_KEY_ID = env("S3_ACCESS_KEY_ID")
# THUMBNAIL_DEFAULT_STORAGE = STORAGES["default"]


# 1MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB

# EASY-THUMBNAILS CONFIGURATION
# https://easy-thumbnails.readthedocs.io/

THUMBNAIL_CACHE_DIMENSIONS = True
THUMBNAIL_SUBDIR = "thumbs"
THUMBNAIL_DEBUG = True

THUMBNAIL_ALIASES = {
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
