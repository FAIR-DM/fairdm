"""Tests for the control room mounted in the administration interface."""

import importlib
import os

import pytest
import redis
from bs4 import BeautifulSoup
from celery import current_app
from django.apps import apps as django_apps
from django.contrib import admin
from django.urls import clear_url_caches, reverse

from fairdm.conf import urls as root_urls
from fairdm.contrib.admin import urls as admin_urls
from fairdm.factories import PersonFactory
from fairdm.portal_roles import PortalRoles

CLOSED_PORT_URL = "redis://127.0.0.1:1/0"
SHORT_TIMEOUT = 0.2

DASHBOARD = "dj_control_room:index"
APP_LABELS = [
    "dj_control_room_base",
    "dj_redis_panel",
    "dj_cache_panel",
    "dj_celery_panel",
    "dj_control_room",
]
CONTROL_ROOM_APPS = [*APP_LABELS]
PANEL_INDEXES = [
    "dj_redis_panel:index",
    "dj_cache_panel:index",
    "dj_celery_panel:index",
]
CONTROL_ROOM_PAGES = [DASHBOARD, *PANEL_INDEXES]
DEVELOPMENT_PANEL_APPS = ["dj_urls_panel", "dj_signals_panel"]
DEVELOPMENT_PANEL_INDEXES = ["dj_urls_panel:index", "dj_signals_panel:index"]


@pytest.fixture(autouse=True)
def reconciled_roles(db):
    PortalRoles.reconcile()


@pytest.fixture
def superuser():
    return PersonFactory(is_staff=True, is_superuser=True, password="password")


@pytest.fixture
def staff_user():
    return PersonFactory(is_staff=True, is_superuser=False, password="password")


def role_holder(role_name):
    from django.contrib.auth.models import Group

    person = PersonFactory(password="password")
    person.groups.add(Group.objects.get(name=role_name))
    return person


@pytest.fixture
def unreachable_services(settings):
    """Point Redis, the cache and Celery at a port nothing listens on."""
    settings.DJ_REDIS_PANEL_SETTINGS = {
        "REQUIRE_SUPERUSER": True,
        "INSTANCES": {"default": {"url": CLOSED_PORT_URL}},
        "socket_timeout": SHORT_TIMEOUT,
        "socket_connect_timeout": SHORT_TIMEOUT,
    }
    settings.CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": CLOSED_PORT_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
                "SOCKET_CONNECT_TIMEOUT": SHORT_TIMEOUT,
                "SOCKET_TIMEOUT": SHORT_TIMEOUT,
            },
        }
    }
    conf = current_app.conf
    saved = {
        name: conf[name]
        for name in ("broker_url", "broker_connection_timeout", "result_backend")
    }
    conf.update(
        broker_url=CLOSED_PORT_URL,
        result_backend=CLOSED_PORT_URL,
        broker_connection_timeout=SHORT_TIMEOUT,
        broker_connection_retry=False,
        broker_connection_max_retries=0,
    )
    yield
    conf.update(**saved)


@pytest.fixture
def reload_urls(settings, monkeypatch):
    """Return a function that rebuilds the admin URLs, and rebuild them as they were after the test."""

    def reload():
        importlib.reload(admin_urls)
        importlib.reload(root_urls)
        clear_url_caches()

    admin_url = settings.ADMIN_URL
    yield reload
    monkeypatch.undo()
    settings.ADMIN_URL = admin_url
    reload()


@pytest.fixture
def role_name():
    """One role that carries rights: which role it is makes no difference to the check."""
    return PortalRoles.rights_carrying()[0]


def statuses_of(client, url_names):
    """Return the status each address answers, by address name."""
    return {name: client.get(reverse(name)).status_code for name in url_names}


@pytest.mark.django_db
class TestControlRoomAccess:
    def test_a_superuser_opens_every_page(self, client, superuser):
        client.force_login(superuser)

        assert statuses_of(client, CONTROL_ROOM_PAGES) == dict.fromkeys(
            CONTROL_ROOM_PAGES, 200
        )

    def test_a_staff_account_that_is_not_a_superuser_is_refused(
        self, client, staff_user
    ):
        client.force_login(staff_user)

        assert statuses_of(client, CONTROL_ROOM_PAGES) == dict.fromkeys(
            CONTROL_ROOM_PAGES, 403
        )

    def test_a_holder_of_a_rights_carrying_role_is_refused(self, client, role_name):
        client.force_login(role_holder(role_name))

        assert statuses_of(client, CONTROL_ROOM_PAGES) == dict.fromkeys(
            CONTROL_ROOM_PAGES, 403
        )

    def test_an_anonymous_visitor_is_sent_to_the_admin_sign_in(self, client):
        responses = {name: client.get(reverse(name)) for name in CONTROL_ROOM_PAGES}

        assert {name: r.status_code for name, r in responses.items()} == dict.fromkeys(
            CONTROL_ROOM_PAGES, 302
        )
        assert all(
            r["Location"].startswith(reverse("admin:login")) for r in responses.values()
        )

    def test_the_agent_interface_does_not_exist(self, client, superuser):
        client.force_login(superuser)

        response = client.post(reverse("dj_control_room:mcp"), data={})

        assert response.status_code == 404


@pytest.mark.django_db
class TestDashboardListsItsPanels:
    @staticmethod
    def links_on_dashboard(client):
        soup = BeautifulSoup(client.get(reverse(DASHBOARD)).content, "html.parser")
        return {tag["href"] for tag in soup.select("a[href]")}

    def test_the_dashboard_links_to_each_panel(self, client, superuser):
        client.force_login(superuser)
        links = self.links_on_dashboard(client)

        missing = [
            name
            for name in PANEL_INDEXES + DEVELOPMENT_PANEL_INDEXES
            if reverse(name) not in links
        ]

        assert missing == []


@pytest.mark.django_db
class TestControlRoomAdminIndex:
    @staticmethod
    def links_on_admin_index(client):
        soup = BeautifulSoup(client.get(reverse("admin:index")).content, "html.parser")
        return {tag["href"] for tag in soup.select("a[href]")}

    def test_a_superuser_is_offered_the_dashboard(self, client, superuser):
        client.force_login(superuser)
        entry = reverse("admin:dj_control_room_djcontrolroomdashboard_changelist")

        links = self.links_on_admin_index(client)
        followed = client.get(entry)

        assert entry in links
        assert followed.status_code == 302
        assert followed["Location"] == reverse(DASHBOARD)

    def assert_no_control_room_link(self, client):
        for link in self.links_on_admin_index(client):
            assert not any(f"/{label}/" in link for label in APP_LABELS)

    def test_a_role_holder_is_offered_no_link(self, client, role_name):
        client.force_login(role_holder(role_name))

        self.assert_no_control_room_link(client)


@pytest.mark.django_db
class TestControlRoomUnderAnotherAdminAddress:
    def test_the_dashboard_follows_the_admin_address(
        self, client, superuser, settings, reload_urls
    ):
        settings.ADMIN_URL = "manage/"
        reload_urls()
        client.force_login(superuser)

        address = reverse(DASHBOARD)
        response = client.get(address)

        assert address.startswith("/manage/")
        assert response.status_code == 200


def without_apps(monkeypatch, labels):
    """Make the URL configuration see the apps as not installed, as in a process that never had them."""
    is_installed = django_apps.is_installed
    monkeypatch.setattr(
        django_apps,
        "is_installed",
        lambda label: label not in labels and is_installed(label),
    )


@pytest.mark.django_db
class TestPortalWithoutTheControlRoom:
    def test_the_admin_stays_up_and_the_dashboard_is_gone(
        self, client, superuser, monkeypatch, reload_urls
    ):
        # A process that never installed the apps never registered their admin entries;
        # this one did at start-up, so they are dropped for the duration.
        remaining = {
            model: model_admin
            for model, model_admin in admin.site._registry.items()
            if model._meta.app_label not in CONTROL_ROOM_APPS
        }
        monkeypatch.setattr(admin.site, "_registry", remaining)
        # Patched rather than removed with modify_settings, which would re-run every
        # app's start-up and duplicate menu entries for later tests.
        without_apps(monkeypatch, CONTROL_ROOM_APPS)
        reload_urls()
        client.force_login(superuser)

        index = client.get(reverse("admin:index"))
        dashboard = client.get("/admin/dj-control-room/")

        assert index.status_code == 200
        assert dashboard.status_code == 404


@pytest.mark.django_db
class TestDevelopmentOnlyPanelAccess:
    def test_a_superuser_opens_the_panels(self, client, superuser):
        client.force_login(superuser)

        assert statuses_of(client, DEVELOPMENT_PANEL_INDEXES) == dict.fromkeys(
            DEVELOPMENT_PANEL_INDEXES, 200
        )

    def test_a_staff_account_that_is_not_a_superuser_is_refused(
        self, client, staff_user
    ):
        client.force_login(staff_user)

        assert statuses_of(client, DEVELOPMENT_PANEL_INDEXES) == dict.fromkeys(
            DEVELOPMENT_PANEL_INDEXES, 403
        )

    def test_a_superuser_cannot_send_requests_from_the_url_panel(
        self, client, superuser
    ):
        client.force_login(superuser)

        response = client.post(
            reverse("dj_urls_panel:execute_request"),
            data={"url": "http://localhost/", "method": "GET"},
            content_type="application/json",
        )

        assert response.status_code == 403

    def test_the_panels_are_gone_when_their_apps_are_not_installed(
        self, client, superuser, monkeypatch, reload_urls
    ):
        # Removing the apps with modify_settings would re-run every app's start-up and
        # duplicate menu entries for later tests; the URL conf reads only is_installed.
        addresses = [reverse(name) for name in DEVELOPMENT_PANEL_INDEXES]
        without_apps(monkeypatch, DEVELOPMENT_PANEL_APPS)
        reload_urls()
        client.force_login(superuser)

        statuses = [client.get(address).status_code for address in addresses]

        assert statuses == [404, 404]


class TestDevelopmentOnlyPanelPackages:
    def test_production_dependencies_name_neither_panel_nor_their_extras(self):
        import tomllib
        from pathlib import Path

        import fairdm

        pyproject = Path(fairdm.__file__).parent.parent / "pyproject.toml"
        dependencies = tomllib.loads(pyproject.read_text())["project"]["dependencies"]

        for requirement in dependencies:
            assert "dj-urls-panel" not in requirement
            assert "dj-signals-panel" not in requirement
            if requirement.startswith("dj-control-room"):
                extras = requirement.split("[")[1].split("]")[0].split(",")
                assert {"urls", "signals"}.isdisjoint(extras)


@pytest.mark.django_db
class TestControlRoomWithServicesDown:
    @pytest.mark.parametrize(
        "url_name", PANEL_INDEXES, ids=lambda name: name.split(":")[0]
    )
    def test_every_panel_answers_without_its_service(
        self, client, superuser, unreachable_services, url_name
    ):
        client.force_login(superuser)

        response = client.get(reverse(url_name))

        assert response.status_code == 200


@pytest.mark.django_db
class TestRedisPanelIsReadOnly:
    @pytest.fixture
    def live_redis_key(self, settings):
        location = os.environ.get("REDIS_URL")
        if not location:
            pytest.skip("Needs a live Redis at REDIS_URL to hold a key to open.")
        panel_settings = settings.DJ_REDIS_PANEL_SETTINGS
        settings.DJ_REDIS_PANEL_SETTINGS = {
            **panel_settings,
            "INSTANCES": {
                "default": {**panel_settings["INSTANCES"]["default"], "url": location}
            },
        }
        connection = redis.Redis.from_url(location)
        connection.set("control-room-read-only", "value")
        yield "control-room-read-only"
        connection.delete("control-room-read-only")

    def test_a_key_page_offers_no_way_to_change_the_key(
        self, client, superuser, live_redis_key
    ):
        client.force_login(superuser)
        url = reverse(
            "dj_redis_panel:key_detail",
            kwargs={
                "instance_alias": "default",
                "db_number": 0,
                "key_name": live_redis_key,
            },
        )

        response = client.get(url)

        soup = BeautifulSoup(response.content, "html.parser")
        assert response.status_code == 200
        assert b"value" in response.content
        assert soup.select("input[name=action]") == []
        assert soup.select("form[method=post]:not(#logout-form)") == []
