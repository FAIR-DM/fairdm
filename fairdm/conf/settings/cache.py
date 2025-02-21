env = globals()["env"]

# https://docs.djangoproject.com/en/dev/ref/settings/#caches
if env("DJANGO_CACHE") and env("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env("REDIS_URL"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                # Mimicing memcache behavior.
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
    }
elif env("DJANGO_CACHE"):
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
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
            "LOCATION": "default-cache",
        },
        "select2": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
            "LOCATION": "select2-cache",
        },
    }

# Tell select2 which cache configuration to use:
SELECT2_CACHE_BACKEND = "select2"

COLLECTFASTA_CACHE = "collectfasta"

COLLECTFASTA_THREADS = 8

VOCABULARY_DEFAULT_CACHE = "default"
