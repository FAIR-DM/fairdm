"""Tests for ``fairdm/conf/settings/cache.py``."""

import os


class TestCache:
    def test_configures_redis_from_redis_url(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["REDIS_URL"] = "redis://cachehost:6380/2"

        module = settings_module()

        assert module.CACHES["default"]["BACKEND"] == "django_redis.cache.RedisCache"
        assert module.CACHES["default"]["LOCATION"] == "redis://cachehost:6380/2"
