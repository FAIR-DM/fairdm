"""Tests for the collections tables."""

import pytest
from django.contrib.gis.geos import Point
from django.urls import reverse
from django.utils import timezone

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from demo.models import ExampleMeasurement, RockSample
from fairdm.contrib.collections.views import DataTableView
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.sample.models import Sample
from fairdm.factories import ContributionFactory, DatasetFactory, PersonFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestColumnClassNamespacing:
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
    def test_the_dataset_columns_header_is_empty_not_the_word_false(
        self, client, published_dataset
    ):
        RockSampleFactory(dataset=published_dataset)
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        header = str(response.context["table"].columns["dataset"].header)
        assert header == ""
        assert "False" not in response.content.decode()


@pytest.mark.django_db
class TestSampleListingLeadsWithIconColumns:
    def test_the_first_visible_column_is_the_dataset(
        self, client, published_dataset
    ):
        RockSampleFactory(dataset=published_dataset)
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        names = [c.name for c in response.context["table"].columns]
        assert names[0] == "dataset"

    def test_measurement_listing_column_order_is_unchanged(
        self, client, published_dataset
    ):
        sample = RockSampleFactory(dataset=published_dataset)
        ExampleMeasurementFactory(sample=sample, dataset=published_dataset)
        slug = registry.get_for_model(ExampleMeasurement).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        names = [c.name for c in response.context["table"].columns]
        assert names[:2] != ["dataset", "location"]


@pytest.mark.django_db
class TestColumnHeaderTitleFromHelpText:
    def test_a_column_mapped_to_a_field_with_help_text_gets_a_matching_title(
        self, client, published_dataset
    ):
        RockSampleFactory(dataset=published_dataset)
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        bound_column = response.context["table"].columns["dataset"]
        field = Sample._meta.get_field("dataset")
        assert field.help_text
        assert bound_column.attrs["th"]["title"] == str(field.help_text)

    def test_a_column_mapped_to_a_field_with_no_help_text_gets_no_title(
        self, client, published_dataset
    ):
        RockSampleFactory(dataset=published_dataset)
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        table = response.context["table"]
        bound_column = table.columns.columns["id"]
        field = Sample._meta.get_field("id")
        assert not field.help_text
        assert "title" not in bound_column.attrs["th"]


@pytest.mark.django_db
class TestSampleColumn:
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

        # Scoped to the row's own "sample" cell; the page's filter widgets are covered by
        # `TestFilterChoicesOnTheRenderedPage` in test_views.py.
        table = response.context["table"]
        row = next(r for r in table.rows if r.record == measurement)
        sample_cell = row.get_cell("sample")
        assert "Hidden Sample" not in sample_cell
        assert sample.get_absolute_url() not in sample_cell


@pytest.mark.django_db
class TestDatasetColumn:
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
        # are exactly what lets a page repeat or skip a row.
        # Enough rows to spill onto a second page at whatever page size the view is
        # configured for, rather than a literal that stops doing so when it changes.
        row_count = DataTableView.paginate_by + 5
        samples = RockSampleFactory.create_batch(row_count, dataset=published_dataset)
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
        assert len(set(first_ids) | set(second_ids)) == row_count

        # The behavioural check above can hold by coincidence of how Postgres
        # happens to break ties today - this pins the actual mechanism: the
        # table's effective order includes a unique column, so the guarantee
        # does not depend on physical row layout.
        order_by = first_page.context["table"].order_by
        assert order_by
        assert any(str(alias).lstrip("-") == "id" for alias in order_by)


@pytest.mark.django_db
class TestLocationColumns:
    """AS 2.12 to 2.14 and FR-027: latitude and longitude read the record's location."""

    @pytest.fixture
    def released(self):
        return DatasetFactory(published=True, visibility=Visibility.PUBLIC)

    @pytest.fixture
    def hidden(self):
        return DatasetFactory(published=False, visibility=Visibility.PRIVATE)

    @staticmethod
    def cells(response, record):
        table = response.context["table"]
        row = next(r for r in table.rows if r.record == record)
        return row.get_cell_value("latitude"), row.get_cell_value("longitude")

    def test_a_sample_row_reads_latitude_and_longitude_from_its_location(
        self, client, released
    ):
        sample = RockSampleFactory(
            dataset=released, location=Point(12.5, 41.9, srid=4326)
        )
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        assert self.cells(response, sample) == (41.9, 12.5)

    def test_a_listing_has_no_location_column(self, client, released):
        RockSampleFactory(dataset=released, location=Point(12.5, 41.9, srid=4326))
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        names = [c.name for c in response.context["table"].columns]
        assert "location" not in names
        assert {"latitude", "longitude"} <= set(names)

    def test_a_sample_with_no_location_still_lists(self, client, released):
        sample = RockSampleFactory(dataset=released)
        slug = registry.get_for_model(RockSample).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        assert response.status_code == 200
        assert self.cells(response, sample) == (None, None)

    def test_a_measurements_own_location_is_shown_before_its_samples(
        self, client, released
    ):
        sample = RockSampleFactory(
            dataset=released, location=Point(12.5, 41.9, srid=4326)
        )
        measurement = ExampleMeasurementFactory(
            sample=sample, dataset=released, location=Point(13.4, 52.5, srid=4326)
        )
        slug = registry.get_for_model(ExampleMeasurement).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        assert self.cells(response, measurement) == (52.5, 13.4)

    def test_a_measurement_with_none_shows_its_samples_location(
        self, client, released
    ):
        sample = RockSampleFactory(
            dataset=released, location=Point(12.5, 41.9, srid=4326)
        )
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)
        slug = registry.get_for_model(ExampleMeasurement).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        assert self.cells(response, measurement) == (41.9, 12.5)

    def test_a_samples_location_is_not_shown_to_a_viewer_who_may_not_open_it(
        self, client, released, hidden
    ):
        sample = RockSampleFactory(
            dataset=hidden, location=Point(12.5, 41.9, srid=4326)
        )
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)
        slug = registry.get_for_model(ExampleMeasurement).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        assert self.cells(response, measurement) == (None, None)

    def test_a_samples_location_is_shown_to_a_viewer_who_may_open_it(
        self, client, released, hidden
    ):
        sample = RockSampleFactory(
            dataset=hidden, location=Point(12.5, 41.9, srid=4326)
        )
        measurement = ExampleMeasurementFactory(sample=sample, dataset=released)
        member = PersonFactory(is_active=True)
        ContributionFactory(
            content_object=hidden, contributor=member, level=ContributionLevel.VIEW
        )
        client.force_login(member)
        slug = registry.get_for_model(ExampleMeasurement).get_slug()

        response = client.get(reverse(f"{slug}-list"))

        assert self.cells(response, measurement) == (41.9, 12.5)

    @pytest.mark.parametrize("model", [RockSample, ExampleMeasurement])
    def test_sorting_by_another_column_still_answers(self, client, released, model):
        # Plain names, so the database's collation and Python's sort agree on the order.
        sample = RockSampleFactory(
            name="Beta", dataset=released, location=Point(12.5, 41.9, srid=4326)
        )
        if model is RockSample:
            RockSampleFactory(name="Alpha", dataset=released)
        else:
            ExampleMeasurementFactory(name="Alpha", sample=sample, dataset=released)
            ExampleMeasurementFactory(name="Beta", sample=sample, dataset=released)
        slug = registry.get_for_model(model).get_slug()

        response = client.get(reverse(f"{slug}-list"), {"sort": "name"})

        names = [row.record.name for row in response.context["table"].rows]
        assert response.status_code == 200
        assert names == sorted(names)

    @pytest.mark.parametrize("model", [RockSample, ExampleMeasurement])
    @pytest.mark.parametrize("column", ["latitude", "longitude"])
    def test_a_coordinate_column_is_not_orderable(
        self, client, released, model, column
    ):
        sample = RockSampleFactory(dataset=released)
        if model is ExampleMeasurement:
            ExampleMeasurementFactory(sample=sample, dataset=released)
        slug = registry.get_for_model(model).get_slug()

        response = client.get(reverse(f"{slug}-list"), {"sort": column})

        table = response.context["table"]
        assert response.status_code == 200
        assert table.columns[column].orderable is False
