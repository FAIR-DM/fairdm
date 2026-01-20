"""Cache Configuration

Production-ready Redis cache configuration with graceful fallbacks for development.

Production/Staging: Requires REDIS_URL (fails fast if missing)
Local/Development: Falls back to LocMemCache with warning if no REDIS_URL

This is the production baseline. Environment-specific overrides in local.py/staging.py.
"""

import logging

# Access environment variables via shared env instance
env = globals()["env"]

logger = logging.getLogger(__name__)

# CACHE CONFIGURATION
# Production expects Redis for performance and session management
# Priority: REDIS_URL (Redis) > LocMemCache fallback > DummyCache (no caching)

if env("DJANGO_CACHE") and env("REDIS_URL"):
    logger.info("Cache Configuration: Redis")
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env("REDIS_URL"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                # Mimic memcache behavior - ignore connection errors gracefully
                # https://github.com/jazzband/django-redis#memcached-exceptions-behavior
                "IGNORE_EXCEPTIONS": True,
            },
        },
        "select2": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env("REDIS_URL"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
            },
        },
        "vocabularies": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env("REDIS_URL"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
            },
        },
    }
elif env("DJANGO_CACHE"):
    # LocMemCache fallback - acceptable for development
    # Production will fail validation if this path is taken
    logger.debug("Cache Configuration: LocMemCache fallback (not for production)")
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "default-cache",
        },
        "select2": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "select2-cache",
        },
        "vocabularies": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "vocabularies-cache",
        },
    }

else:
    # DummyCache - no caching at all (for testing only)
    logger.debug("Cache Configuration: DummyCache (no caching)")
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
            "LOCATION": "default-cache",
        },
        "select2": {
            # select2 needs at least LocMemCache to function properly
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "select2-cache",
        },
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
