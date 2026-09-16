"""``PersonListView`` (T038, django-mvp 0.23 upgrade): creation is handled by a
separate view, so the list page draws no create action - covered here rather
than assumed, since the attribute that suppresses it was renamed upstream."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestPersonListViewDrawsNoCreateAction:
    def test_the_people_list_page_renders(self, client):
        response = client.get(reverse("people-list"))

        assert response.status_code == 200

    def test_the_empty_state_offers_no_create_action(self, client):
        """``show_create_action`` is False, so ``get_empty_state_message``
        (``mvp.views.list``) withholds the message that would otherwise point
        at the create button - the one observable trace of the suppressed
        action, since this view sets no ``create_form_class`` of its own."""
        response = client.get(reverse("people-list"))

        assert response.context["empty_state"]["message"] is None
