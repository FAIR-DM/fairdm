"""Tests for ``fairdm/conf/settings/control_room.py``."""

import os

import pytest

PANEL_APPS = ["dj_redis_panel", "dj_cache_panel", "dj_celery_panel"]
RUNTIME_APPS = ["dj_control_room_base", *PANEL_APPS, "dj_control_room"]
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
    def test_the_hub_and_its_three_panels_are_installed(self, production_module):
        for app in RUNTIME_APPS:
            assert app in production_module.INSTALLED_APPS

    def test_the_hub_comes_after_every_panel(self, production_module):
        apps = production_module.INSTALLED_APPS

        for panel in PANEL_APPS:
            assert apps.index(panel) < apps.index("dj_control_room")

    def test_the_development_only_panels_are_not_installed(self, production_module):
        assert "dj_urls_panel" not in production_module.INSTALLED_APPS
        assert "dj_signals_panel" not in production_module.INSTALLED_APPS


class TestControlRoomAccess:
    @pytest.mark.parametrize("name", SETTINGS_NAMES)
    def test_every_package_requires_a_superuser(self, production_module, name):
        assert getattr(production_module, name)["REQUIRE_SUPERUSER"] is True

    def test_the_redis_panel_reads_the_cache_location(self, production_module):
        instances = production_module.DJ_REDIS_PANEL_SETTINGS["INSTANCES"]

        assert list(instances) == ["default"]
        assert (
            instances["default"]["url"]
            == (production_module.CACHES["default"]["LOCATION"])
        )

    def test_the_redis_panel_leaves_editing_at_its_default(self, production_module):
        assert "features" not in production_module.DJ_REDIS_PANEL_SETTINGS

    def test_the_urls_panel_sends_no_requests(self, production_module):
        assert production_module.DJ_URLS_PANEL_SETTINGS["ENABLE_TESTING"] is False

    @pytest.mark.parametrize("name", SETTINGS_NAMES)
    def test_the_agent_interface_is_not_turned_on(self, production_module, name):
        assert not getattr(production_module, name).get("MCP_ENABLED")


class TestControlRoomPortalOverrides:
    def test_a_portal_dict_assigned_after_setup_is_kept(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"
        portal_dict = {"REQUIRE_SUPERUSER": False, "features": {"ALLOW_KEY_EDIT": True}}

        module = settings_module(after=f"DJ_REDIS_PANEL_SETTINGS = {portal_dict!r}")

        assert module.DJ_REDIS_PANEL_SETTINGS == portal_dict

    def test_a_portal_can_remove_the_control_room_apps(
        self, isolated_env, settings_module
    ):
        os.environ["DJANGO_ENV"] = "qa"
        removed = ", ".join(repr(app) for app in RUNTIME_APPS)

        module = settings_module(
            after=(
                "INSTALLED_APPS = [app for app in INSTALLED_APPS "
                f"if app not in [{removed}]]"
            )
        )

        for app in RUNTIME_APPS:
            assert app not in module.INSTALLED_APPS
