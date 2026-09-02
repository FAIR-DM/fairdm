"""Views tests for fairdm.contrib.collections.views.DataTableView (US2)."""

import pytest
from django.urls import reverse

from fairdm.registry import registry
from fairdm_demo.factories import (
    CustomSampleFactory,
    RockSampleFactory,
    SoilSampleFactory,
)
from fairdm_demo.models import CustomSample, RockSample, SoilSample


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


@pytest.mark.django_db
class TestColumnsPerType:
    """FR-014, SC-003: a listing's columns come from its type's own registration, so
    two types with different declarations produce different columns."""

    def test_two_types_with_different_field_declarations_produce_different_columns(
        self, client, published_dataset
    ):
        RockSampleFactory(dataset=published_dataset)
        SoilSampleFactory(dataset=published_dataset)

        rock_slug = registry.get_for_model(RockSample).get_slug()
        soil_slug = registry.get_for_model(SoilSample).get_slug()

        rock_response = client.get(reverse(f"{rock_slug}-list"))
        soil_response = client.get(reverse(f"{soil_slug}-list"))

        rock_columns = {c.name for c in rock_response.context["table"].columns}
        soil_columns = {c.name for c in soil_response.context["table"].columns}

        assert "rock_type" in rock_columns
        assert "rock_type" not in soil_columns
        assert "soil_type" in soil_columns
        assert "soil_type" not in rock_columns


@pytest.mark.django_db
class TestDefaultColumns:
    """FR-015: a type registered with no field declarations still produces a working
    listing from the framework's own defaults, rather than failing."""

    def test_a_type_with_no_field_declarations_renders_with_framework_defaults(
        self, client, published_dataset
    ):
        CustomSampleFactory(dataset=published_dataset)
        slug = registry.get_for_model(CustomSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        assert response.status_code == 200
        assert list(response.context["table"].columns)


@pytest.mark.django_db
class TestPaging:
    """FR-017: a listing pages its results, and every page is reachable."""

    def test_a_second_page_returns_the_next_slice_and_carries_paging_controls(
        self, client, published_dataset
    ):
        RockSampleFactory.create_batch(25, dataset=published_dataset)
        slug = registry.get_for_model(RockSample).get_slug()
        url = reverse(f"{slug}-list")

        first_page = client.get(url)
        second_page = client.get(url, {"page": 2})

        assert first_page.status_code == 200
        assert second_page.status_code == 200
        assert first_page.context["page_obj"].number == 1
        assert second_page.context["page_obj"].number == 2

        first_ids = {s.pk for s in first_page.context["object_list"]}
        second_ids = {s.pk for s in second_page.context["object_list"]}
        assert first_ids.isdisjoint(second_ids)
