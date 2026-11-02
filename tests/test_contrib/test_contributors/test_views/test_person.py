"""Tests for PersonListView."""

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

from fairdm.core.project.models import Project
from fairdm.factories import OrganizationFactory, ProjectFactory


@pytest.mark.django_db
class TestPersonListViewDrawsNoCreateAction:
    def test_the_people_list_page_renders(self, client):
        response = client.get(reverse("people-list"))

        assert response.status_code == 200

    def test_the_empty_state_offers_no_create_action(self, client):
        response = client.get(reverse("people-list"))

        assert response.context["empty_state"]["message"] is None


@pytest.mark.django_db
class TestPersonListViewQueryCount:
    @staticmethod
    def add_person_with_everything_a_card_shows():
        from allauth.socialaccount.models import SocialAccount
        from django.contrib.auth.models import Group

        from fairdm.factories import (
            AffiliationFactory,
            ContributorIdentifierFactory,
            PersonFactory,
        )
        from fairdm.portal_roles import PortalRoles

        person = PersonFactory()
        identifier = ContributorIdentifierFactory(related=person)
        SocialAccount.objects.create(
            user=person, provider="orcid", uid=identifier.value
        )
        AffiliationFactory(person=person, is_primary=True)
        person.groups.add(Group.objects.get(name=PortalRoles.DATA_CURATOR.name))
        return person

    def test_each_person_on_the_page_costs_no_extra_query(
        self, client, django_assert_num_queries
    ):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        self.add_person_with_everything_a_card_shows()
        client.get(reverse("people-list"))  # The first request fills per-site caches.
        with CaptureQueriesContext(connection) as one_person:
            client.get(reverse("people-list"))
        for _ in range(3):
            self.add_person_with_everything_a_card_shows()

        with django_assert_num_queries(len(one_person)):
            response = client.get(reverse("people-list"))

        assert response.status_code == 200


@pytest.mark.django_db
class TestPersonListToolbar:
    def test_the_search_and_the_active_and_staff_switches_are_in_the_toolbar(
        self, client, filter_placement
    ):
        from fairdm.factories import PersonFactory

        PersonFactory()

        toolbar, panel = filter_placement(client.get(reverse("people-list")))

        assert {"q", "is_active", "is_staff"} <= toolbar
        assert {"city", "country"} <= panel


@pytest.mark.django_db
class TestOrganizationListToolbar:
    def test_the_search_and_country_are_in_the_toolbar_and_the_city_in_the_panel(
        self, client, filter_placement
    ):
        from fairdm.factories import OrganizationFactory

        OrganizationFactory()

        toolbar, panel = filter_placement(client.get(reverse("organization-list")))

        assert {"q", "country"} <= toolbar
        assert "city" in panel


@pytest.mark.django_db
class TestOrganizationCardCredits:
    def _badges(self, client):
        response = client.get(reverse("organization-list"))
        page = BeautifulSoup(response.content, "html.parser")
        return [" ".join(b.get_text().split()) for b in page.select(".badge")]

    def test_one_credit_reads_in_the_singular(self, client):
        OrganizationFactory().add_to(ProjectFactory())

        assert f"1 {Project._meta.verbose_name}" in self._badges(client)

    def test_several_credits_read_in_the_plural(self, client):
        organization = OrganizationFactory()
        organization.add_to(ProjectFactory())
        organization.add_to(ProjectFactory())

        assert f"2 {Project._meta.verbose_name_plural}" in self._badges(client)
