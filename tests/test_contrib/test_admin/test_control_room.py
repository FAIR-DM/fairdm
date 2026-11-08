"""Tests for the control room mounted in the administration interface."""

import importlib
import os

import pytest
import redis
from bs4 import BeautifulSoup
from celery import current_app
from django.contrib import admin
from django.test import modify_settings
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


@pytest.mark.django_db
class TestControlRoomAccess:
    @pytest.mark.parametrize("url_name", CONTROL_ROOM_PAGES)
    def test_a_superuser_opens_every_page(self, client, superuser, url_name):
        client.force_login(superuser)

        response = client.get(reverse(url_name))

        assert response.status_code == 200

    @pytest.mark.parametrize("url_name", CONTROL_ROOM_PAGES)
    def test_a_staff_account_that_is_not_a_superuser_is_refused(
        self, client, staff_user, url_name
    ):
        client.force_login(staff_user)

        response = client.get(reverse(url_name))

        assert response.status_code == 403

    @pytest.mark.parametrize("url_name", CONTROL_ROOM_PAGES)
    @pytest.mark.parametrize("role_name", PortalRoles.rights_carrying())
    def test_a_holder_of_a_rights_carrying_role_is_refused(
        self, client, role_name, url_name
    ):
        client.force_login(role_holder(role_name))

        response = client.get(reverse(url_name))

        assert response.status_code == 403

    @pytest.mark.parametrize("url_name", CONTROL_ROOM_PAGES)
    def test_an_anonymous_visitor_is_sent_to_the_admin_sign_in(self, client, url_name):
        response = client.get(reverse(url_name))

        assert response.status_code == 302
        assert response["Location"].startswith(reverse("admin:login"))

    def test_the_agent_interface_does_not_exist(self, client, superuser):
        client.force_login(superuser)

        response = client.post(reverse("dj_control_room:mcp"), data={})

        assert response.status_code == 404


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

    @pytest.mark.parametrize("role_name", PortalRoles.rights_carrying())
    def test_a_role_holder_is_offered_no_link(self, client, role_name):
        client.force_login(role_holder(role_name))

        self.assert_no_control_room_link(client)


@pytest.mark.django_db
class TestControlRoomUnderAnotherAdminAddress:
    def test_the_dashboard_follows_the_admin_address(self, client, superuser, settings):
        settings.ADMIN_URL = "manage/"
        importlib.reload(admin_urls)
        importlib.reload(root_urls)
        clear_url_caches()
        client.force_login(superuser)
        try:
            address = reverse(DASHBOARD)
            response = client.get(address)
        finally:
            settings.ADMIN_URL = "admin/"
            importlib.reload(admin_urls)
            importlib.reload(root_urls)
            clear_url_caches()

        assert address.startswith("/manage/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestPortalWithoutTheControlRoom:
    def test_the_admin_stays_up_and_the_dashboard_is_gone(
        self, client, superuser, monkeypatch
    ):
        # A process that never installed the apps never registered their admin entries;
        # this one did at start-up, so they are dropped for the duration.
        remaining = {
            model: model_admin
            for model, model_admin in admin.site._registry.items()
            if model._meta.app_label not in CONTROL_ROOM_APPS
        }
        monkeypatch.setattr(admin.site, "_registry", remaining)
        client.force_login(superuser)
        try:
            with modify_settings(INSTALLED_APPS={"remove": CONTROL_ROOM_APPS}):
                importlib.reload(admin_urls)
                importlib.reload(root_urls)
                clear_url_caches()
                index = client.get(reverse("admin:index"))
                dashboard = client.get("/admin/dj-control-room/")
        finally:
            monkeypatch.undo()
            importlib.reload(admin_urls)
            importlib.reload(root_urls)
            clear_url_caches()

        assert index.status_code == 200
        assert dashboard.status_code == 404


@pytest.mark.django_db
class TestControlRoomWithServicesDown:
    @pytest.mark.parametrize(
        "url",
        [
            lambda: reverse("dj_redis_panel:index"),
            lambda: reverse("dj_cache_panel:index"),
            lambda: reverse("dj_celery_panel:index"),
            lambda: reverse("dj_celery_panel:workers"),
            lambda: reverse("dj_celery_panel:queues"),
            lambda: reverse(
                "dj_redis_panel:instance_overview",
                kwargs={"instance_alias": "default"},
            ),
            lambda: reverse(
                "dj_redis_panel:key_search",
                kwargs={"instance_alias": "default", "db_number": 0},
            ),
            lambda: (
                reverse("dj_cache_panel:key_search", kwargs={"cache_name": "default"})
                + "?q=anything"
            ),
        ],
    )
    def test_every_page_answers_without_the_services(
        self, client, superuser, unreachable_services, url
    ):
        client.force_login(superuser)

        response = client.get(url())

        assert response.status_code == 200


@pytest.mark.django_db
class TestRedisPanelIsReadOnly:
    @pytest.fixture
    def live_redis_key(self, settings):
        location = os.environ["REDIS_URL"]
        settings.DJ_REDIS_PANEL_SETTINGS = {
            "REQUIRE_SUPERUSER": True,
            "INSTANCES": {"default": {"url": location}},
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
        assert soup.select("input[name=action]") == []
        assert soup.select("form[method=post]:not(#logout-form)") == []
