"""The application-shell settings in ``fairdm/conf/settings/addons.py``."""

import json
from urllib.parse import urlsplit

import pytest
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.staticfiles import finders
from django.urls import reverse
from waffle import get_waffle_sample_model, sample_is_active


class TestWaffleSamples:
    def test_a_sample_code_asks_for_is_created(self, db):
        sample_is_active("sample-nobody-created")

        assert (
            get_waffle_sample_model()
            .objects.filter(name="sample-nobody-created")
            .exists()
        )


class TestSidebarFooterSettingIsNotDeclared:
    def test_the_sidebar_settings_declare_no_footer_key(self):
        assert "footer" not in settings.MVP_CONFIG["layout"]["sidebar"]


@pytest.mark.django_db
class TestSidebarFooterControls:
    def sidebar(self, client):
        response = client.get(reverse("project-list"))
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.find("aside", class_="mvp-sidebar")

    def test_a_visitor_who_is_not_signed_in_can_log_in_from_the_drawer(self, client):
        sidebar = self.sidebar(client)

        assert sidebar is not None
        login_url = reverse("account_login")
        assert any(
            urlsplit(link["href"]).path == login_url
            for link in sidebar.find_all("a", href=True)
        )

    def test_the_theme_toggle_is_in_the_drawer(self, client):
        sidebar = self.sidebar(client)

        assert sidebar is not None
        assert sidebar.find(attrs={"data-toggle-theme": True}) is not None


@pytest.mark.django_db
class TestInstallableApp:
    def test_the_app_is_named_after_the_portal(self, client):
        manifest = json.loads(client.get(reverse("mvp-pwa-manifest")).content)

        assert manifest["name"] == settings.SITE_NAME

    def test_every_image_the_app_names_is_in_the_static_files(self):
        missing = [
            name
            for name in (
                "brand/pwa/icon-192.png",
                "brand/pwa/icon-512.png",
                "brand/pwa/icon-maskable-512.png",
                "brand/pwa/apple-touch-icon.png",
            )
            if finders.find(name) is None
        ]

        assert missing == []
