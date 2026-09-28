"""Tests for Sample filtering and search functionality."""

import pytest
from django.contrib.auth import get_user_model

from demo.filters import RockSampleFilter
from demo.models import RockSample, WaterSample
from fairdm.core.models import Dataset
from fairdm.core.sample.filters import SampleFilter, SampleFilterMixin

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestSampleFilterDatasetFiltering:
    def test_filter_by_dataset(self, user, project):
        # Left private, which is the model's default and the ordinary case: the
        # filter's "dataset" choices come from `Dataset.all_objects`, so filtering
        # by one works.
        dataset1 = Dataset.objects.create(name="Dataset 1", project=project)
        dataset2 = Dataset.objects.create(name="Dataset 2", project=project)

        sample1 = RockSample.objects.create(
            name="Rock in Dataset 1",
            dataset=dataset1,
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        sample2 = RockSample.objects.create(
            name="Rock in Dataset 2",
            dataset=dataset2,
            rock_type="sedimentary",
            collection_date="2024-01-01",
        )

        filterset = SampleFilter(
            data={"dataset": dataset1.id}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert sample1 in filterset.qs
        assert sample2 not in filterset.qs


class TestSampleFilterStatusFiltering:
    def test_filter_by_status(self, dataset):
        available = RockSample.objects.create(
            name="Available Rock",
            dataset=dataset,
            status="available",
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        stored = RockSample.objects.create(
            name="Stored Rock",
            dataset=dataset,
            status="stored",
            rock_type="igneous",
            collection_date="2024-01-01",
        )

        filterset = SampleFilter(
            data={"status": "available"}, queryset=RockSample.objects.all()
        )

        assert filterset.is_valid()
        assert available in filterset.qs
        assert stored not in filterset.qs


class TestSampleFilterPolymorphicTypeFiltering:
    def test_filter_by_polymorphic_type(self, user, project, dataset):
        from django.contrib.contenttypes.models import ContentType

        rock_sample = RockSample.objects.create(
            name="Rock Sample",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        water_sample = WaterSample.objects.create(
            name="Water Sample",
            dataset=dataset,
            water_source="river",
            temperature_celsius=15.5,
            ph_level=7.2,
        )

        rock_ct = ContentType.objects.get_for_model(RockSample)
        water_ct = ContentType.objects.get_for_model(WaterSample)

        from fairdm.core.sample.models import Sample

        filterset = SampleFilter(
            data={"polymorphic_ctype": rock_ct.id}, queryset=Sample.objects.all()
        )
        assert filterset.is_valid()
        assert rock_sample in filterset.qs
        assert water_sample not in filterset.qs

        filterset = SampleFilter(
            data={"polymorphic_ctype": water_ct.id}, queryset=Sample.objects.all()
        )
        assert filterset.is_valid()
        assert water_sample in filterset.qs
        assert rock_sample not in filterset.qs


class TestSampleFilterSearchFunctionality:
    def test_search_by_name_local_id_uuid(self, user, project, dataset):
        sample1 = RockSample.objects.create(
            name="Granite Sample XYZ",
            local_id="ROCK-001",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        sample2 = RockSample.objects.create(
            name="Basalt Sample",
            local_id="ROCK-002",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-01",
        )

        filterset = SampleFilter(
            data={"search": "Granite"}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert sample1 in filterset.qs
        assert sample2 not in filterset.qs

        filterset = SampleFilter(
            data={"search": "ROCK-002"}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert sample2 in filterset.qs
        assert sample1 not in filterset.qs

        uuid_fragment = str(sample1.uuid)[:8]
        filterset = SampleFilter(
            data={"search": uuid_fragment}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert sample1 in filterset.qs


class TestSampleFilterDescriptionFiltering:
    @pytest.mark.skip(
        reason="Description filtering requires SampleDescription model implementation"
    )
    def test_filter_by_description_content(self, user, project, dataset):
        sample1 = RockSample.objects.create(
            name="Rock 1",
            dataset=dataset,
            collection_date="2024-01-01",
            temperature_celsius=25,
        )
        sample1.descriptions.create(text="Contains high silica content")

        sample2 = RockSample.objects.create(
            name="Rock 2",
            dataset=dataset,
            collection_date="2024-01-01",
            temperature_celsius=25,
        )
        sample2.descriptions.create(text="Rich in iron oxide minerals")

        filterset = SampleFilter(
            data={"description": "silica"}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert sample1 in filterset.qs
        assert sample2 not in filterset.qs


class TestSampleFilterDateRangeFiltering:
    @pytest.mark.skip(reason="Date filtering requires SampleDate model implementation")
    def test_filter_by_date_range(self, user, project, dataset):
        sample1 = RockSample.objects.create(
            name="Rock 1",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        sample1.dates.create(date="2024-01-15", type="analysis")

        sample2 = RockSample.objects.create(
            name="Rock 2",
            dataset=dataset,
            rock_type="sedimentary",
            collection_date="2024-01-01",
        )
        sample2.dates.create(date="2024-02-20", type="analysis")

        filterset = SampleFilter(
            data={"date_after": "2024-01-10", "date_before": "2024-02-01"},
            queryset=RockSample.objects.all(),
        )
        assert filterset.is_valid()
        assert sample1 in filterset.qs
        assert sample2 not in filterset.qs


class TestSampleFilterCombinedFilters:
    @pytest.mark.skip(
        reason="Combined filters with descriptions require SampleDescription model implementation"
    )
    def test_combined_filters(self, user, project, dataset):
        target_sample = RockSample.objects.create(
            name="Target Rock",
            dataset=dataset,
            status="available",
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        target_sample.descriptions.create(text="Special properties")

        excluded_sample1 = RockSample.objects.create(
            name="Excluded Rock 1",
            dataset=dataset,
            status="unavailable",
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        excluded_sample1.descriptions.create(text="Special properties")

        excluded_sample2 = RockSample.objects.create(
            name="Excluded Rock 2",
            dataset=dataset,
            status="available",
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        excluded_sample2.descriptions.create(text="Normal properties")

        filterset = SampleFilter(
            data={"status": "available", "description": "Special"},
            queryset=RockSample.objects.all(),
        )
        assert filterset.is_valid()
        assert target_sample in filterset.qs
        assert excluded_sample1 not in filterset.qs
        assert excluded_sample2 not in filterset.qs


class TestSampleFilterMixinConfiguration:
    def test_mixin_provides_common_filters(self):
        expected_filters = ["status", "dataset", "polymorphic_ctype", "search"]

        filter_instance = SampleFilter()
        for filter_name in expected_filters:
            assert filter_name in filter_instance.filters, (
                f"Expected filter '{filter_name}' not found in SampleFilter"
            )


class TestSampleFilterMixinInheritance:
    def test_inheriting_filter_set_carries_the_mixins_declared_filters(self):
        filterset = RockSampleFilter()

        assert "image" in filterset.filters
        assert "rock_type" in filterset.filters
        assert "mineral_content" in filterset.filters
        assert "grain_size" in filterset.filters

    def test_mixin_declares_only_image(self):
        assert set(SampleFilterMixin.declared_filters) == {"image"}


class TestSampleFilterBehaviour:
    def test_image_filter_narrows_to_samples_with_an_image(self, dataset):
        with_image = RockSample.objects.create(
            name="Rock With Image",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-01",
            image="samples/has-image.jpg",
        )
        without_image = RockSample.objects.create(
            name="Rock Without Image",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-01",
        )

        filterset = RockSampleFilter(
            data={"image": "true"}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid(), filterset.errors
        assert with_image in filterset.qs
        assert without_image not in filterset.qs


class TestCustomSampleFilterIntegration:
    @pytest.mark.skip(
        reason="RockSampleFilter rock_type field not configured in Meta.fields"
    )
    def test_custom_filter_inherits_from_mixin(self, user, project, dataset):
        rock_sample = RockSample.objects.create(
            name="Granite",
            dataset=dataset,
            rock_type="igneous",
            collection_date="2024-01-01",
        )

        filterset = RockSampleFilter(
            data={"search": "Granite"}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert rock_sample in filterset.qs

        assert "search" in filterset.filters
        assert "rock_type" in filterset.filters
