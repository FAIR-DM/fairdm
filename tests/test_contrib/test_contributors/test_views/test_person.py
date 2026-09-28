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
