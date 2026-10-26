"""Database settings: a PostGIS DATABASES from ``DATABASE_URL`` or ``POSTGRES_*``.

Owns DATABASES, never SQLite, so the baseline stays production-grade. The engine is always
GeoDjango's PostGIS backend, whatever scheme ``DATABASE_URL`` names. A portal supplies
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
    "default": env.db(
        default=_postgres_url_from_parts,
        engine="django.contrib.gis.db.backends.postgis",
    ),
}

DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)

BACKUP_PUBLIC_KEY = env.str("BACKUP_PUBLIC_KEY", multiline=True)
DBBACKUP_HOSTNAME = env("BACKUP_SERVER_NAME")
DBBACKUP_CLEANUP_KEEP = DBBACKUP_CLEANUP_KEEP_MEDIA = env("BACKUP_KEEP")
# The custom format is compressed and restores PostGIS into an empty database with pg_restore.
DBBACKUP_CONNECTORS = {
    "default": {"CONNECTOR": "dbbackup.db.postgresql.PgDumpBinaryConnector"}
}

DBBACKUP_FILENAME_TEMPLATE = "{databasename}-{servername}-{datetime}.{extension}"
DBBACKUP_MEDIA_FILENAME_TEMPLATE = (
    "{databasename}_media-{servername}-{datetime}.{extension}"
)

# GeoDjango finds GDAL and GEOS on the system library path. None keeps that search.
GDAL_LIBRARY_PATH = env("GDAL_LIBRARY_PATH") or None
GEOS_LIBRARY_PATH = env("GEOS_LIBRARY_PATH") or None
