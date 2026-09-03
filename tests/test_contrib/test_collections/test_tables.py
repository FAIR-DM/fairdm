"""Tables tests for fairdm.contrib.collections.tables (US2, US3)."""

import pytest
from django.urls import reverse
from django.utils import timezone

from fairdm.core.sample.models import Sample
from fairdm.factories import DatasetFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility
from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm_demo.models import ExampleMeasurement, RockSample


@pytest.mark.django_db
class TestColumnClassNamespacing:
    """T081: a field's own name is namespaced before it becomes a header/cell CSS
    class, so no field name can ever collide with a DaisyUI component class
    (`.status`, `.badge`, `.link`, ... - all plausible model field names). The
    field-type class (`char`, `num`, `date`, ...) is unaffected."""

    def test_the_field_name_class_is_namespaced_on_both_header_and_data_cells(
        self, client, published_dataset
    ):
        RockSampleFactory(dataset=published_dataset)
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        bound_column = response.context["table"].columns["name"]
        th_classes = bound_column.attrs["th"]["class"].split()
        td_classes = bound_column.attrs["td"]["class"].split()

        assert "col-name" in th_classes
        assert "col-name" in td_classes
        assert "name" not in th_classes
        assert "name" not in td_classes

    def test_the_field_type_class_is_unaffected_by_namespacing(
        self, client, published_dataset
    ):
        RockSampleFactory(dataset=published_dataset)
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        bound_column = response.context["table"].columns["name"]
        td_classes = bound_column.attrs["td"]["class"].split()

        assert "char" in td_classes


@pytest.mark.django_db
class TestFalseyHeadersRenderEmpty:
    """T082: `BoundColumn.verbose_name` tests `is not None`, so a column declared
    `verbose_name=False` returns `False` as-is and the header renders the literal
    word "False". `verbose_name=""` short-circuits the same fallback and renders
    empty, which is the correct idiom."""

    def test_the_dataset_columns_header_is_empty_not_the_word_false(
        self, client, published_dataset
    ):
        RockSampleFactory(dataset=published_dataset)
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        header = str(response.context["table"].columns["dataset"].header)
        assert header == ""
        assert "False" not in response.content.decode()

    def test_the_sample_tables_location_columns_header_is_empty_not_the_word_false(
        self, client, published_dataset
    ):
        RockSampleFactory(dataset=published_dataset)
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        header = str(response.context["table"].columns["location"].header)
        assert header == ""

    def test_the_measurement_tables_location_columns_header_is_empty_not_the_word_false(
        self, client, published_dataset
    ):
        sample = RockSampleFactory(dataset=published_dataset)
        ExampleMeasurementFactory(sample=sample, dataset=published_dataset)
        slug = registry.get_for_model(ExampleMeasurement).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        header = str(response.context["table"].columns["location"].header)
        assert header == ""


@pytest.mark.django_db
class TestSampleColumn:
    """FR-013, D3: where a measurement's sample belongs to an unpublished dataset, the
    row shows neither the sample's name nor a link to it."""

    def test_a_measurement_whose_samples_dataset_is_unpublished_shows_no_name_and_no_link(
        self, client, published_dataset, unpublished_dataset
    ):
        sample = RockSampleFactory(name="Hidden Sample", dataset=unpublished_dataset)
        measurement = ExampleMeasurementFactory(
            sample=sample, dataset=published_dataset
        )

        slug = registry.get_for_model(ExampleMeasurement).get_slug()
        response = client.get(reverse(f"{slug}-list"))
        content = response.content.decode()

        assert measurement.name in content

        # Scoped to the row's own "sample" cell, because that is what this test is
        # about. The page's filter widgets are covered separately, by
        # `TestFilterChoicesOnTheRenderedPage` in test_views.py - FR-030 requires
        # them to withhold the same names, and it belongs to this feature.
        table = response.context["table"]
        row = next(r for r in table.rows if r.record == measurement)
        sample_cell = row.get_cell("sample")
        assert "Hidden Sample" not in sample_cell
        assert sample.get_absolute_url() not in sample_cell


@pytest.mark.django_db
class TestDatasetColumn:
    """D3 (extended at design review), research.md R14: a dataset that is published
    while its visibility is private is the ordinary state - its records appear, and
    the dataset column carries no link to a page the visitor cannot read."""

    def test_a_published_but_private_datasets_records_show_no_link_to_the_dataset(
        self, client
    ):
        dataset = DatasetFactory(published=True, visibility=Visibility.PRIVATE)
        sample = RockSampleFactory(name="Visible Sample", dataset=dataset)

        slug = registry.get_for_model(RockSample).get_slug()
        response = client.get(reverse(f"{slug}-list"))
        content = response.content.decode()

        assert "Visible Sample" in content
        assert dataset.get_absolute_url() not in content


@pytest.mark.django_db
class TestOrdering:
    """FR-032, FR-033, Acceptance Scenarios 8-9: a sortable column reorders
    rows in each direction, and the unsorted default order is stable and
    repeatable across pages, with no row repeated or skipped (D5)."""

    def test_sorting_a_column_both_directions_reorders_rows(
        self, client, published_dataset
    ):
        RockSampleFactory(name="Beta", dataset=published_dataset)
        RockSampleFactory(name="Alpha", dataset=published_dataset)

        slug = registry.get_for_model(RockSample).get_slug()
        url = reverse(f"{slug}-list")

        ascending = client.get(url, {"sort": "name"})
        descending = client.get(url, {"sort": "-name"})

        ascending_names = [row.record.name for row in ascending.context["table"].rows]
        descending_names = [row.record.name for row in descending.context["table"].rows]

        assert ascending_names == sorted(ascending_names)
        assert descending_names == sorted(descending_names, reverse=True)
        assert ascending_names != descending_names

    def test_unsorted_order_is_stable_and_repeatable_across_pages(
        self, client, published_dataset
    ):
        # Force every row to the same `added` timestamp - `Sample.Meta.ordering`
        # is `["added"]` alone, so without a unique tie-break, ties like these
        # are exactly what lets a page repeat or skip a row (D5, FR-033).
        samples = RockSampleFactory.create_batch(25, dataset=published_dataset)
        same_instant = timezone.now()
        Sample.objects.filter(pk__in=[s.pk for s in samples]).update(added=same_instant)

        slug = registry.get_for_model(RockSample).get_slug()
        url = reverse(f"{slug}-list")

        first_page = client.get(url)
        second_page = client.get(url, {"page": 2})
        first_page_again = client.get(url)

        first_ids = [
            row.record.pk for row in first_page.context["table"].paginated_rows
        ]
        second_ids = [
            row.record.pk for row in second_page.context["table"].paginated_rows
        ]
        first_ids_again = [
            row.record.pk for row in first_page_again.context["table"].paginated_rows
        ]

        assert first_ids == first_ids_again
        assert set(first_ids).isdisjoint(second_ids)
        assert len(set(first_ids) | set(second_ids)) == 25

        # The behavioural check above can hold by coincidence of how Postgres
        # happens to break ties today - this pins the actual mechanism: the
        # table's effective order includes a unique column, so the guarantee
        # does not depend on physical row layout (D5, FR-033).
        order_by = first_page.context["table"].order_by
        assert order_by
        assert any(str(alias).lstrip("-") == "id" for alias in order_by)
