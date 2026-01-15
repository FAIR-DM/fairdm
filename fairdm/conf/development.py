"""
Development configuration overrides.

This file overrides the production baseline for local development convenience.
Applied after loading settings/* modules when DJANGO_ENV=development.
"""

# Access globals set by setup()
env = globals()["env"]
BASE_DIR = globals()["BASE_DIR"]

# =============================================================================
# DEVELOPMENT CONVENIENCE OVERRIDES
# =============================================================================

# Enable debug mode for development
DEBUG = True

# Use a default insecure key for development (production will fail without proper key)
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="django-insecure-dev-key-CHANGE-THIS-IN-PRODUCTION",
)

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# =============================================================================
# DATABASE (Degrade to SQLite if not configured)
# =============================================================================

# Try to use PostgreSQL if DATABASE_URL is set, otherwise fall back to SQLite
# try:
#     DATABASES = {
#         "default": env.db("DATABASE_URL"),
#     }
# except Exception:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# =============================================================================
# CACHE (Degrade to LocMem if Redis not configured)
# =============================================================================

# try:
#     CACHES = {
#         "default": env.cache("REDIS_URL"),
#     }
# except Exception:
#     import warnings

#     warnings.warn(
#         "REDIS_URL not set. Using LocMemCache for development. " "Set REDIS_URL to test Redis functionality.",
#         stacklevel=2,
#     )
#     CACHES = {
#         "default": {
#             "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#             "LOCATION": "unique-snowflake",
#         }
#     }

# =============================================================================
# CELERY (Degrade to eager execution if Redis not configured)
# =============================================================================

try:
    CELERY_BROKER_URL = env("REDIS_URL")
    CELERY_RESULT_BACKEND = env("REDIS_URL")
except Exception:
    import warnings

    warnings.warn(
        "REDIS_URL not set. Celery tasks will execute synchronously (CELERY_TASK_ALWAYS_EAGER=True). "
        "Set REDIS_URL to test async task functionality.",
        stacklevel=2,
    )
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# =============================================================================
# EMAIL (Console backend for development)
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =============================================================================
# SECURITY (Relaxed for development)
# =============================================================================

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# =============================================================================
# STATIC FILES (Development)
# =============================================================================

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Disable compression in development
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False

# =============================================================================
# DJANGO DEBUG TOOLBAR
# =============================================================================

# Add debug toolbar if installed
try:
    import debug_toolbar  # noqa: F401

    INSTALLED_APPS = globals().get("INSTALLED_APPS", [])
    if "debug_toolbar" not in INSTALLED_APPS:
        INSTALLED_APPS.insert(0, "debug_toolbar")

    MIDDLEWARE = globals().get("MIDDLEWARE", [])
    if "debug_toolbar.middleware.DebugToolbarMiddleware" not in MIDDLEWARE:
        MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS = ["127.0.0.1", "localhost"] + [ip[: ip.rfind(".")] + ".1" for ip in ips]

except ImportError:
    pass

# =============================================================================
# LOGGING (Verbose for development)
# =============================================================================

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
            "level": "WARNING",  # Set to DEBUG to see SQL queries
            "propagate": False,
        },
        "fairdm": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
