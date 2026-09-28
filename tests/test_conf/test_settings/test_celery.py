"""Tests for ``fairdm/conf/settings/celery.py``."""

import os


class TestCelery:
    def test_broker_and_result_backend_come_from_redis_url(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["REDIS_URL"] = "redis://cachehost:6380/3"

        module = settings_module()

        assert module.CELERY_BROKER_URL == "redis://cachehost:6380/3"
        assert module.CELERY_RESULT_BACKEND == "redis://cachehost:6380/3"

    def test_timezone_comes_from_django_time_zone(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"
        os.environ["DJANGO_TIME_ZONE"] = "Europe/Berlin"

        module = settings_module()

        assert module.CELERY_TIMEZONE == "Europe/Berlin"

    def test_tasks_are_not_eager_by_default(self, isolated_env, settings_module):
        os.environ["DJANGO_ENV"] = "qa"

        module = settings_module()

        assert module.CELERY_TASK_ALWAYS_EAGER is False

    def test_reading_unconfigured_celery_never_raises(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"

        settings_module()
