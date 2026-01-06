"""Database Configuration

Production-ready PostgreSQL configuration with graceful SQLite fallback for development.

Production/Staging: Requires DATABASE_URL or POSTGRES_* env vars (fails fast if missing)
Local/Development: Falls back to SQLite with warning if no DATABASE_URL

This is the production baseline. Environment-specific overrides in local.py/staging.py.
"""

import logging

# Access environment variables via shared env instance
env = globals()["env"]
BASE_DIR = globals()["BASE_DIR"]

logger = logging.getLogger(__name__)

# Default for all Django models
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DATABASE CONFIGURATION
# Priority: DATABASE_URL > POSTGRES_* vars > SQLite fallback
# Production expects DATABASE_URL or POSTGRES_* (validation in checks.py)

if env("DATABASE_URL"):
    logger.info(f"Database: PostgreSQL via DATABASE_URL")
    DATABASES = {
        "default": env.db(),
    }

elif env("POSTGRES_DB"):
    logger.info("Database: PostgreSQL via POSTGRES_* vars")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB"),
            "PASSWORD": env("POSTGRES_PASSWORD"),
            "USER": env("POSTGRES_USER"),
            "HOST": env("POSTGRES_HOST"),
            "PORT": env("POSTGRES_PORT"),
        }
    }

else:
    # SQLite fallback - only acceptable in development
    # Production will fail validation if this path is taken
    logger.warning("Database: SQLite fallback (not for production)")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Database performance settings
DATABASES["default"]["ATOMIC_REQUESTS"] = True  # Wrap each request in a transaction
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)  # Persistent connections (60s)

# DATABASE BACKUP CONFIGURATION (django-dbbackup)
# https://django-dbbackup.readthedocs.io/

DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {"location": "/app/dbbackups/"}

DBBACKUP_FILENAME_TEMPLATE = "{databasename}-{servername}-{datetime}.{extension}"
DBBACKUP_MEDIA_FILENAME_TEMPLATE = "{databasename}_media-{servername}-{datetime}.{extension}"

# Keep last 10 backups
DBBACKUP_CLEANUP_KEEP = 10
