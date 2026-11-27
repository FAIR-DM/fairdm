"""Tests for ``fairdm/conf/settings/control_room.py``."""

import os

import pytest

PANEL_APPS = ["dj_redis_panel", "dj_cache_panel", "dj_celery_panel"]
SETTINGS_NAMES = [
    "DJ_CONTROL_ROOM_SETTINGS",
    "DJ_CONTROL_ROOM_BASE_SETTINGS",
    "DJ_REDIS_PANEL_SETTINGS",
    "DJ_CACHE_PANEL_SETTINGS",
    "DJ_CELERY_PANEL_SETTINGS",
    "DJ_URLS_PANEL_SETTINGS",
    "DJ_SIGNALS_PANEL_SETTINGS",
]


@pytest.fixture
def production_module(isolated_env, settings_module):
    os.environ["DJANGO_ENV"] = "qa"
    os.environ["REDIS_URL"] = "redis://cachehost:6380/3"
    return settings_module()


class TestControlRoomApps:
    def test_the_hub_comes_after_every_panel(self, production_module):
        apps = production_module.INSTALLED_APPS

        for panel in PANEL_APPS:
            assert apps.index(panel) < apps.index("dj_control_room")


class TestControlRoomAccess:
    def test_the_redis_panel_reads_the_cache_location(self, production_module):
        instances = production_module.DJ_REDIS_PANEL_SETTINGS["INSTANCES"]

        assert list(instances) == ["default"]
        assert (
            instances["default"]["url"]
            == (production_module.CACHES["default"]["LOCATION"])
        )

    def test_every_package_requires_a_superuser_and_leaves_the_agent_interface_off(
        self, production_module
    ):
        failures = []
        for name in SETTINGS_NAMES:
            panel_settings = getattr(production_module, name)
            if panel_settings["REQUIRE_SUPERUSER"] is not True:
                failures.append(f"{name} does not require a superuser")
            if panel_settings.get("MCP_ENABLED"):
                failures.append(f"{name} turns the agent interface on")

        assert not failures, "\n".join(failures)
