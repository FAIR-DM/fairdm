"""Views tests for fairdm.contrib.collections.views.DataTableView (US2)."""

import datetime

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from pytest_django.asserts import assertContains

from fairdm.contrib.collections.views import DataTableView
from fairdm.core.sample.models import Sample
from fairdm.registry import registry
from fairdm_demo.factories import (
    CustomSampleFactory,
    ExampleMeasurementFactory,
    RockSampleFactory,
    SoilSampleFactory,
)
from fairdm_demo.models import CustomSample, ExampleMeasurement, RockSample, SoilSample


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
        samples = RockSampleFactory.create_batch(25, dataset=published_dataset)
        # `Sample`'s default ordering is `added` (auto_now_add), and a tight creation
        # loop can leave several rows with the same timestamp - a stable default order
        # with a tie-break is T041's deliverable (US-3, D5), not this story's. Space
        # the timestamps out here so paging is deterministic without it.
        base = timezone.now()
        for offset, sample in enumerate(samples):
            Sample.objects.filter(pk=sample.pk).update(
                added=base + datetime.timedelta(seconds=offset)
            )
        slug = registry.get_for_model(RockSample).get_slug()
        url = reverse(f"{slug}-list")

        first_page = client.get(url)
        second_page = client.get(url, {"page": 2})

        assert first_page.status_code == 200
        assert second_page.status_code == 200
        assert first_page.context["page_obj"].number == 1
        assert second_page.context["page_obj"].number == 2

        # `context["object_list"]` is the view's own, unpaginated queryset - the table
        # is the only paginator here (`MVPTableViewMixin.paginate_queryset`) - so the
        # slice actually shown on each page is read from the table instead.
        first_ids = {row.record.pk for row in first_page.context["table"].paginated_rows}
        second_ids = {
            row.record.pk for row in second_page.context["table"].paginated_rows
        }
        assert first_ids.isdisjoint(second_ids)


@pytest.mark.django_db
class TestEmptyState:
    """FR-018: a listing with no published records to show says so - in this
    feature's own words, not the application shell's authoring copy."""

    def test_a_type_with_no_published_records_shows_this_features_own_empty_state(
        self, client
    ):
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        content = response.content.decode()
        assert "Click the button below to get started" not in content
        empty_state = response.context["empty_state"]
        assert empty_state["heading"]
        assert empty_state["message"]
        assert str(empty_state["heading"]) in content
        assert str(empty_state["message"]) in content


@pytest.mark.django_db
class TestRowLinksToRecord:
    """FR-019, Acceptance Scenario 9: selecting a row opens that record's own page -
    for a measurement listing as well as a sample listing."""

    def test_a_sample_listing_row_links_to_the_samples_own_page(
        self, client, published_sample
    ):
        slug = registry.get_for_model(RockSample).get_slug()
        response = client.get(reverse(f"{slug}-list"))
        assertContains(response, published_sample.get_absolute_url())

    def test_a_measurement_listing_row_links_to_the_measurements_own_page(
        self, client, published_dataset
    ):
        sample = RockSampleFactory(dataset=published_dataset)
        measurement = ExampleMeasurementFactory(
            sample=sample, dataset=published_dataset
        )
        slug = registry.get_for_model(ExampleMeasurement).get_slug()
        response = client.get(reverse(f"{slug}-list"))
        assertContains(response, measurement.get_absolute_url())


@pytest.mark.django_db
class TestQueryCount:
    """FR-020, SC-006: the number of database queries a listing issues does not grow
    with the number of rows it shows - for the measurement listing as well as the
    sample listing.

    Measured around the table's own rendering rather than a full `client.get()`: this
    project's test environment fires a query-logging signal on every template render
    (visible as `orbit_orbitentry` inserts) whose handler `repr()`s the render context,
    which forces a fresh, unrelated re-evaluation of any queryset the context carries -
    once per template node rendered, so the noise itself scales with row count and
    would swamp a page-wide query count either way. Excluded below by table name,
    alongside building the table the view would and calling its own `as_html()`,
    which measures the thing FR-020 actually constrains.
    """

    def _table_query_count(self, rf, url, model_class):
        from django.contrib.auth.models import AnonymousUser

        config = registry.get_for_model(model_class)
        request = rf.get(url)
        request.user = AnonymousUser()
        view = DataTableView(model=model_class, model_config=config, request=request)
        view.setup(request)
        view.object_list = view.get_queryset()
        table = view.get_table()

        with CaptureQueriesContext(connection) as ctx:
            table.as_html(request)

        return len(
            [q for q in ctx.captured_queries if "orbit_orbitentry" not in q["sql"]]
        )

    def test_sample_listing_query_count_is_flat(self, rf, published_dataset):
        RockSampleFactory(dataset=published_dataset)
        slug = registry.get_for_model(RockSample).get_slug()
        url = reverse(f"{slug}-list")

        one_row_count = self._table_query_count(rf, url, RockSample)

        RockSampleFactory.create_batch(19, dataset=published_dataset)  # a full page

        full_page_count = self._table_query_count(rf, url, RockSample)

        assert full_page_count == one_row_count

    def test_measurement_listing_query_count_is_flat(self, rf, published_dataset):
        sample = RockSampleFactory(dataset=published_dataset)
        ExampleMeasurementFactory(sample=sample, dataset=published_dataset)
        slug = registry.get_for_model(ExampleMeasurement).get_slug()
        url = reverse(f"{slug}-list")

        one_row_count = self._table_query_count(rf, url, ExampleMeasurement)

        other_samples = RockSampleFactory.create_batch(19, dataset=published_dataset)
        for other_sample in other_samples:
            ExampleMeasurementFactory(sample=other_sample, dataset=published_dataset)

        full_page_count = self._table_query_count(rf, url, ExampleMeasurement)

        assert full_page_count == one_row_count
