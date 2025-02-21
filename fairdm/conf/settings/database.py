import logging

env = globals()["env"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

logger = logging.getLogger(__name__)


# FAIRDM Docs: Choosing a database backend

# Env var precedence: DATABASE_URL > POSTGRES_DB (and associated vars) > SQLITE_DB (default)

# Typical FairDM distributions will be built using a PostgreSQL database. However, the DATABASE_URL env takes precedence
# to allow customization (e.g. managed databases). If neither DATABASE_URL or any POSTGRES_* vars are set, FairDM will
# default to SQLite.
if env("DATABASE_URL"):
    logging.info(f"Database: {env('DATABASE_URL')}")
    DATABASES = {
        "default": env.db(),
    }

elif env("POSTGRES_DB"):
    logging.info("Database: PostgreSQL via POSTGRES_* vars")
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
    logging.info("Database: SQLite")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)  # noqa F405


DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {"location": "/app/dbbackups/"}


DBBACKUP_FILENAME_TEMPLATE = "{databasename}-{servername}-{datetime}.{extension}"

DBBACKUP_MEDIA_FILENAME_TEMPLATE = "{databasename}_media-{servername}-{datetime}.{extension}"

# DBBACKUP_CLEANUP_FILTER = ''

DBBACKUP_CLEANUP_KEEP = 10
