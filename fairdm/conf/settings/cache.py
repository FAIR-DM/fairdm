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
}

COLLECTFASTA_CACHE = "collectfasta"

COLLECTFASTA_THREADS = 8
