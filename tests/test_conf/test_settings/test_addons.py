"""The application-shell settings in ``fairdm/conf/settings/addons.py``."""

import pytest
from bs4 import BeautifulSoup
from django.conf import settings
from django.urls import reverse


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
            link.get("href") == login_url for link in sidebar.find_all("a", href=True)
        )

    def test_the_theme_toggle_is_in_the_drawer(self, client):
        sidebar = self.sidebar(client)

        assert sidebar is not None
        assert sidebar.find(attrs={"data-toggle-theme": True}) is not None
