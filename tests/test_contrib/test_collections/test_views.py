"""Views tests for fairdm.contrib.collections.views.DataTableView (US2)."""

import pytest
from django.urls import reverse

from fairdm.registry import registry
from fairdm_demo.models import RockSample


@pytest.mark.django_db
class TestPublicationFiltering:
    """FR-011, SC-002, SC-010: a listing shows only published records, identically for
    every viewer - the four FR-011 names explicitly, and the staff client is the one
    most likely to be widened by accident."""

    @pytest.fixture(autouse=True)
    def _records(self, published_sample, unpublished_sample):
        self.published_sample = published_sample
        self.unpublished_sample = unpublished_sample

    def _get(self, client):
        slug = registry.get_for_model(RockSample).get_slug()
        return client.get(reverse(f"{slug}-list"))

    def test_signed_out_visitor_sees_only_the_published_record(self, client):
        response = self._get(client)
        entries = list(response.context["object_list"])
        assert self.published_sample in entries
        assert self.unpublished_sample not in entries

    def test_the_records_owner_sees_only_the_published_record(
        self, client, dataset_owner
    ):
        client.force_login(dataset_owner)
        response = self._get(client)
        entries = list(response.context["object_list"])
        assert self.published_sample in entries
        assert self.unpublished_sample not in entries

    def test_a_contributor_sees_only_the_published_record(
        self, client, dataset_contributor
    ):
        client.force_login(dataset_contributor)
        response = self._get(client)
        entries = list(response.context["object_list"])
        assert self.published_sample in entries
        assert self.unpublished_sample not in entries

    def test_portal_staff_sees_only_the_published_record(self, client, staff_user):
        client.force_login(staff_user)
        response = self._get(client)
        entries = list(response.context["object_list"])
        assert self.published_sample in entries
        assert self.unpublished_sample not in entries
