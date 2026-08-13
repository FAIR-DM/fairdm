"""Cache Configuration

Owns: CACHES, always Redis-shaped, read from ``REDIS_URL`` (FR-002, FR-003).
Leaves to a portal: the Redis instance itself, and any per-cache options
beyond ``IGNORE_EXCEPTIONS``.

A portal that omits ``REDIS_URL`` resolves to
``fairdm.conf.checks.UNCONFIGURED_REDIS_LOCATION`` rather than raising on
read (research R6's principle, applied here as much as to the
security-critical variables) — the read is never what refuses a boot. Unlike
``DATABASES``, this can't be an empty string: some installed apps touch the
cache eagerly at import time (a vocabulary field building its graph), and
django_redis's client raises ``ImproperlyConfigured`` at construction —
before any network call, so ``IGNORE_EXCEPTIONS`` can't catch it — when its
location is empty. A syntactically valid placeholder lets construction
succeed; ``IGNORE_EXCEPTIONS`` then absorbs the connection failure at actual
use, and ``fairdm.conf.checks.check_cache_backend`` recognises the
placeholder itself to refuse it in production (BACKEND alone can no longer
tell a real deployment from an unset one, now that it never varies).
Development degrades to LocMemCache in ``development.py``, not here.

This is the production baseline. Environment-specific overrides in development.py (FairDM) or a same-named module beside the portal's settings module.
"""

from fairdm.conf.checks import UNCONFIGURED_REDIS_LOCATION

# Access environment variables via shared env instance
env = globals()["env"]

# CACHE CONFIGURATION
# Production expects Redis for performance and session management.


def _redis_cache() -> dict:
    """A fresh dict per alias, so a portal overriding one cache's OPTIONS
    after ``setup()`` never mutates the others through a shared reference."""
    return {
        "BACKEND": "django_redis.cache.RedisCache",
        # `or` rather than env()'s own `default=` because a variable
        # explicitly set to "" still reaches this line as "" (the shared
        # Env's schema default only applies when the variable is absent from
        # the process environment altogether).
        "LOCATION": env("REDIS_URL") or UNCONFIGURED_REDIS_LOCATION,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Mimic memcache behavior - ignore connection errors gracefully
            # https://github.com/jazzband/django-redis#memcached-exceptions-behavior
            "IGNORE_EXCEPTIONS": True,
        },
    }


CACHES = {
    "default": _redis_cache(),
    "select2": _redis_cache(),
    "vocabularies": _redis_cache(),
}

# Tell select2 which cache configuration to use:
SELECT2_CACHE_BACKEND = "select2"
SELECT2_THEME = "bootstrap-5"
SELECT2_JS = "https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"
SELECT2_CSS = [
    "https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css",
    "https://cdn.jsdelivr.net/npm/select2-bootstrap-5-theme@1.3.0/dist/select2-bootstrap-5-theme.min.css",
]
COLLECTFASTA_CACHE = "collectfasta"

COLLECTFASTA_THREADS = 8

VOCABULARY_DEFAULT_CACHE = "default"
