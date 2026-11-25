"""The sidebar's user menu."""

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse


@pytest.mark.django_db
class TestTheUserMenu:
    def test_a_signed_in_person_has_a_link_to_their_profile(self, authenticated_client, user):
        page = BeautifulSoup(authenticated_client.get(reverse("project-list")).content, "html.parser")

        assert page.select_one(f'.mvp-sidebar-footer a[href="{user.get_absolute_url()}"]')

    def test_a_visitor_who_is_not_signed_in_has_no_profile_link(self, client):
        page = BeautifulSoup(client.get(reverse("project-list")).content, "html.parser")

        assert page.select_one('.mvp-sidebar-footer a[href^="/contributor/"]') is None
