"""Cache settings: Redis-shaped CACHES read from ``REDIS_URL``.

Owns CACHES. A portal supplies the Redis instance and any per-cache options beyond
``IGNORE_EXCEPTIONS``. An unset ``REDIS_URL`` resolves to
``fairdm.conf.checks.UNCONFIGURED_REDIS_LOCATION`` rather than raising on read. Unlike
``DATABASES`` it cannot be empty: some apps touch the cache at import time and django_redis
raises ``ImproperlyConfigured`` on an empty location, before any network call.
``IGNORE_EXCEPTIONS`` then absorbs the connection failure at use, and
``fairdm.conf.checks.check_cache_backend`` refuses the placeholder in production.
"""

from fairdm.conf.checks import UNCONFIGURED_REDIS_LOCATION

env = globals()["env"]


def _redis_cache() -> dict:
    """Return a fresh cache configuration, so aliases never share OPTIONS."""
    return {
        "BACKEND": "django_redis.cache.RedisCache",
        # `or`, because a variable set to "" bypasses the schema default in `env()`.
        "LOCATION": env("REDIS_URL") or UNCONFIGURED_REDIS_LOCATION,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # https://github.com/jazzband/django-redis#memcached-exceptions-behavior
            "IGNORE_EXCEPTIONS": True,
        },
    }


CACHES = {
    "default": _redis_cache(),
    "select2": _redis_cache(),
    "vocabularies": _redis_cache(),
}

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
