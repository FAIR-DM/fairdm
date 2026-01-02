import re

from django.utils.log import RequireDebugTrue


env = globals()["env"]


DEBUG = env.bool("DJANGO_DEBUG")

ACCOUNT_EMAIL_VERIFICATION = "optional"
ALLOWED_HOSTS = ["*"]
AUTH_PASSWORD_VALIDATORS = []
AWS_USE_SSL = False

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
SECURE_SSL_REDIRECT = False


# STORAGES["default"] = {
#     "BACKEND": "django.core.files.storage.FileSystemStorage",
# }

THUMBNAIL_DEFAULT_STORAGE = "easy_thumbnails.storage.ThumbnailFileSystemStorage"

# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#         # "BACKEND": "django.core.cache.backends.dummy.DummyCache",
#         "LOCATION": "",
#     },
#     "select2": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#         "LOCATION": "",
#     },
# }


CACHES["vocabularies"] = {
    "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
    "LOCATION": BASE_DIR / ".vocabularies-cache",
}

VOCABULARY_DEFAULT_CACHE = "vocabularies"


SHELL_PLUS = "ipython"

INSTALLED_APPS.insert(0, "whitenoise.runserver_nostatic")
COMPRESS_OFFLINE = False
COMPRESS_ENABLED = False


if env("SHOW_DEBUG_TOOLBAR"):
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")

# django-browser-reload for automatic browser refresh during development
INSTALLED_APPS.append("django_browser_reload")
MIDDLEWARE.append("django_browser_reload.middleware.BrowserReloadMiddleware")


INTERNAL_IPS = ["127.0.0.1"]

CORS_ALLOW_ALL_ORIGINS = True

AWS_S3_URL_PROTOCOL = "http:"

# https://github.com/torchbox/django-libsass
LIBSASS_SOURCEMAPS = True

DEBUG_TOOLBAR_CONFIG = {
    # "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
    "SHOW_TEMPLATE_CONTEXT": False,  # CAREFUL: this can cause huge memory usage
    "ROOT_TAG_EXTRA_ATTRS": "hx-preserve",
    "SKIP_TEMPLATE_PREFIXES": ("cotton/",),
}


class IgnoreStaticAndMediaFilter:
    def filter(self, record):
        # Access the message in record and check if it's a static or media request
        message = record.getMessage()
        return not re.match(r'^"GET /(static|media)/', message) and not re.match(r'^"GET /__debug__/', message)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_true": {
            "()": RequireDebugTrue,  # Only log in DEBUG mode
        },
        "ignore_static_and_media": {
            "()": IgnoreStaticAndMediaFilter,
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "filters": ["require_debug_true", "ignore_static_and_media"],
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django.server": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "import_export": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}
