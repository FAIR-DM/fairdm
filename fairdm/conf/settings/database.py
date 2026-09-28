"""Database settings: PostgreSQL-shaped DATABASES from ``DATABASE_URL`` or ``POSTGRES_*``.

Owns DATABASES, never SQLite, so the baseline stays production-grade. A portal supplies
either form and any connection tuning beyond ``CONN_MAX_AGE``. Supplying neither resolves to
a present but unusable configuration rather than raising on read;
``fairdm.conf.checks.check_database_configured`` and ``check_database_usable`` refuse it in
production.
"""

from urllib.parse import quote

env = globals()["env"]
BASE_DIR = globals()["BASE_DIR"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# The composed POSTGRES_* URL is only `env.db`'s default, used when DATABASE_URL is unset.
_postgres_url_from_parts = (
    f"postgresql://{quote(env('POSTGRES_USER'), safe='')}"
    f":{quote(env('POSTGRES_PASSWORD'), safe='')}"
    f"@{env('POSTGRES_HOST')}:{env('POSTGRES_PORT')}/{env('POSTGRES_DB')}"
)

DATABASES = {
    "default": env.db(default=_postgres_url_from_parts),
}

DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {"location": "/app/dbbackups/"}

DBBACKUP_FILENAME_TEMPLATE = "{databasename}-{servername}-{datetime}.{extension}"
DBBACKUP_MEDIA_FILENAME_TEMPLATE = (
    "{databasename}_media-{servername}-{datetime}.{extension}"
)

DBBACKUP_CLEANUP_KEEP = 10
