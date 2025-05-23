import os
from pathlib import Path
import logging

env = globals()["env"]

logger = logging.getLogger(__name__)

BASE_DIR = globals()["BASE_DIR"]
SITE_DOMAIN = globals()["SITE_DOMAIN"]

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
        "OPTIONS": {
            "access_key": env("S3_ACCESS_KEY_ID"),
            "secret_key": env("S3_SECRET_ACCESS_KEY"),
            "bucket_name": env("S3_BUCKET_NAME"),
            "custom_domain": f"media.{SITE_DOMAIN}/{env('S3_BUCKET_NAME')}",
            "endpoint_url": "http://minio:9000",
            "object_parameters": {
                "CacheControl": "max-age=86400",
            },
            "region_name": env("S3_REGION_NAME"),
            # "url_protocol": "https:",
        },
    }

else:
    logger.info("Media storage: files stored locally")
    STORAGES["default"] = {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "LOCATION": str(BASE_DIR / "media"),
    }

# THUMBNAIL_DEFAULT_STORAGE = STORAGES["default"]


WEBPACK_LOADER = {
    "FAIRDM": {
        "CACHE": env("DJANGO_CACHE"),
        "STATS_FILE": Path(__file__).parent / "webpack-stats.prod.json",
    },
}

# 1MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB
