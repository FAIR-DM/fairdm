"""Tests for the entrance pages' layout, ``mvp_accounts/entrance/base.html``."""

import pytest
from django.urls import reverse

from fairdm.contrib.identity.models import Authority, Identity

ENTRANCE_PAGES = ["account_login", "account_reset_password"]


@pytest.mark.django_db
class TestEntranceLayout:
    @pytest.mark.parametrize("url_name", ENTRANCE_PAGES)
    def test_page_has_one_top_level_heading(self, client, url_name):
        content = client.get(reverse(url_name)).content.decode()

        assert content.count("<h1") == 1

    @pytest.mark.parametrize("url_name", ENTRANCE_PAGES)
    def test_page_links_the_layout_stylesheet(self, client, url_name):
        content = client.get(reverse(url_name)).content.decode()

        assert "css/daisy-cotton-ext.css" in content

    def test_pane_names_the_saved_portal(self, client):
        identity = Identity.get_solo()
        identity.name = "PORTAL-MARKER"
        identity.description = "DESCRIPTION-MARKER"
        identity.save()

        content = client.get(reverse("account_login")).content.decode()

        assert "PORTAL-MARKER" in content
        assert "DESCRIPTION-MARKER" in content

    def test_pane_falls_back_to_the_description_setting(self, client, settings):
        settings.PORTAL_DESCRIPTION = "SETTING-MARKER"

        content = client.get(reverse("account_login")).content.decode()

        assert "SETTING-MARKER" in content

    def test_pane_links_the_authority(self, client):
        authority = Authority.get_solo()
        authority.name = "AUTHORITY-MARKER"
        authority.url = "https://authority.example"
        authority.save()

        content = client.get(reverse("account_login")).content.decode()

        assert 'href="https://authority.example"' in content
        assert "AUTHORITY-MARKER" in content
