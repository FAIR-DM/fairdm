"""
Tests for ``fairdm/conf/settings/cache.py`` — the baseline cache
configuration (FR-002, FR-003).
"""

import os


class TestCache:
    """The baseline configures a shared cache from the environment, with no
    environment branching (FR-002, FR-003)."""

    def test_configures_redis_from_redis_url(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"  # no override module — baseline stands
        os.environ["REDIS_URL"] = "redis://cachehost:6380/2"

        module = settings_module()

        assert module.CACHES["default"]["BACKEND"] == "django_redis.cache.RedisCache"
        assert module.CACHES["default"]["LOCATION"] == "redis://cachehost:6380/2"
        assert module.CACHES["select2"]["BACKEND"] == "django_redis.cache.RedisCache"
        assert module.CACHES["vocabularies"]["BACKEND"] == "django_redis.cache.RedisCache"

    def test_never_falls_back_to_locmem_or_dummy_when_unconfigured(
        self, isolated_env, settings_module
    ):
        """No REDIS_URL at all still resolves to a Redis-shaped (if unusable)
        baseline — never LocMem or Dummy, which is the silent per-process
        degradation this baseline must not perform (FR-003, D4)."""
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.CACHES["default"]["BACKEND"] == "django_redis.cache.RedisCache"

    def test_reading_unconfigured_cache_never_raises(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()  # must not raise
