"""Tables tests for fairdm.contrib.collections.tables (US2)."""

import pytest
from django.urls import reverse

from fairdm.factories import DatasetFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility
from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm_demo.models import ExampleMeasurement, RockSample


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

        # Scoped to the row's own "sample" cell, not the whole page: a filter
        # widget elsewhere on the page legitimately lists every sample by name,
        # published or not (FR-030's scoping is a later story).
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
