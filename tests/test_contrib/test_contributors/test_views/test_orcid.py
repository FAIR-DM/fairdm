"""Tests for the ORCID sign-in addresses."""

import pytest
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.urls import reverse

from fairdm.factories import PersonFactory

ORCID_ROUTES = ["orcid_login", "orcid_callback"]


@pytest.mark.django_db
class TestOrcidRoutes:
    @pytest.mark.parametrize("route", ORCID_ROUTES)
    def test_a_visitor_gets_a_404_with_no_orcid_application(self, client, route):
        assert client.get(reverse(route)).status_code == 404

    @pytest.mark.parametrize("route", ORCID_ROUTES)
    def test_a_signed_in_user_gets_a_404_with_no_orcid_application(self, client, route):
        client.force_login(PersonFactory())

        assert client.get(reverse(route)).status_code == 404

    @pytest.mark.parametrize(
        ("route", "status"), [("orcid_login", 200), ("orcid_callback", 401)]
    )
    def test_the_routes_reach_allauth_once_an_application_is_configured(
        self, client, route, status
    ):
        app = SocialApp.objects.create(
            provider="orcid", name="ORCID", client_id="id", secret="secret"
        )
        app.sites.add(Site.objects.get_current())

        assert client.get(reverse(route)).status_code == status
