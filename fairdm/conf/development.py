"""Development overrides for the production baseline.

Applied after the settings modules load when ``DJANGO_ENV=development``.
"""

env = globals()["env"]
BASE_DIR = globals()["BASE_DIR"]

INSTALLED_APPS = globals().get("INSTALLED_APPS", [])
MIDDLEWARE = globals().get("MIDDLEWARE", [])

INSTALLED_APPS += [
    "django_browser_reload",
]

MIDDLEWARE += [
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

DEBUG = True

# Surface thumbnail failures instead of degrading to a blank image.
THUMBNAIL_DEBUG = True

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="django-insecure-dev-key-CHANGE-THIS-IN-PRODUCTION",
)

# Never "*", and never in the production baseline, where an unset domain resolves to [].
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# `env()` defaults REDIS_URL to "", so test for a value. The baseline already reads the broker
# and the caches from it when it is set.
if not env("REDIS_URL"):
    import warnings

    warnings.warn(
        "REDIS_URL not set. Celery tasks will execute synchronously (CELERY_TASK_ALWAYS_EAGER=True) "
        "and every cache is held in process memory. Set REDIS_URL to test against Redis.",
        stacklevel=2,
    )
    CELERY_TASK_ALWAYS_EAGER = True

    # An unreachable Redis cache fails silently, and allauth's rate limiter reads that as
    # "limit reached": every sign-in returns 429.
    CACHES = {
        alias: {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": alias,
        }
        for alias in globals()["CACHES"]
    }

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

ACCOUNT_EMAIL_VERIFICATION = "none"

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# Browsers discard a `__Secure-` prefixed cookie sent without `Secure` (RFC 6265bis 4.1.3),
# so the baseline's prefix has to go with the flag or every POST fails CSRF.
CSRF_COOKIE_NAME = "csrftoken"
SESSION_COOKIE_NAME = "sessionid"

SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

COMPRESS_ENABLED = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "fairdm": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
