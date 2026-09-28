"""Tests for ``fairdm/conf/settings/cache.py``."""

import os


class TestCache:
    def test_configures_redis_from_redis_url(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["REDIS_URL"] = "redis://cachehost:6380/2"

        module = settings_module()

        assert module.CACHES["default"]["BACKEND"] == "django_redis.cache.RedisCache"
        assert module.CACHES["default"]["LOCATION"] == "redis://cachehost:6380/2"
        assert module.CACHES["select2"]["BACKEND"] == "django_redis.cache.RedisCache"
        assert (
            module.CACHES["vocabularies"]["BACKEND"] == "django_redis.cache.RedisCache"
        )

    def test_never_falls_back_to_locmem_or_dummy_when_unconfigured(
        self, isolated_env, settings_module
    ):
        # LocMem or Dummy would silently degrade to per-process caching.
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.CACHES["default"]["BACKEND"] == "django_redis.cache.RedisCache"

    def test_reading_unconfigured_cache_never_raises(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()
