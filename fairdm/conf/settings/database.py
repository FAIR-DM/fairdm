"""Database Configuration

Owns: DATABASES, always PostgreSQL-shaped, read from ``DATABASE_URL`` or
composed from the discrete ``POSTGRES_*`` variables when that is unset — never
SQLite, so the baseline stays production-grade unconditionally (FR-002,
FR-003). Leaves to a portal: which of the two forms it supplies, and any
per-portal connection tuning beyond ``CONN_MAX_AGE``.

A portal supplying neither resolves to a syntactically present but unusable
configuration rather than raising on read (research R6's principle, applied
here as much as to the security-critical variables) — the read is never what
refuses a boot. ``fairdm.conf.checks.check_database_configured`` and
``check_database_usable`` are what refuse it in production. Development
degrades to SQLite in ``development.py``, not here.

This is the production baseline. Environment-specific overrides in development.py (FairDM) or a same-named module beside the portal's settings module.
"""

from urllib.parse import quote

# Access environment variables via shared env instance
env = globals()["env"]
BASE_DIR = globals()["BASE_DIR"]

# Default for all Django models
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DATABASE CONFIGURATION
# django-environ reads DATABASE_URL when present; the composed POSTGRES_*
# URL is its `default` value, used only when DATABASE_URL is entirely unset
# — a single unconditional read, not a branch on which was supplied.
_postgres_url_from_parts = (
    f"postgresql://{quote(env('POSTGRES_USER'), safe='')}"
    f":{quote(env('POSTGRES_PASSWORD'), safe='')}"
    f"@{env('POSTGRES_HOST')}:{env('POSTGRES_PORT')}/{env('POSTGRES_DB')}"
)

DATABASES = {
    "default": env.db(default=_postgres_url_from_parts),
}

# Database performance settings
DATABASES["default"]["ATOMIC_REQUESTS"] = True  # Wrap each request in a transaction
DATABASES["default"]["CONN_MAX_AGE"] = env.int(
    "CONN_MAX_AGE", default=60
)  # Persistent connections (60s)

# DATABASE BACKUP CONFIGURATION (django-dbbackup)
# https://django-dbbackup.readthedocs.io/

DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {"location": "/app/dbbackups/"}

DBBACKUP_FILENAME_TEMPLATE = "{databasename}-{servername}-{datetime}.{extension}"
DBBACKUP_MEDIA_FILENAME_TEMPLATE = (
    "{databasename}_media-{servername}-{datetime}.{extension}"
)

# Keep last 10 backups
DBBACKUP_CLEANUP_KEEP = 10
