"""Tests for PersonListView."""

import pytest
from django.urls import reverse


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
        SocialAccount.objects.create(user=person, provider="orcid", uid=identifier.value)
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
