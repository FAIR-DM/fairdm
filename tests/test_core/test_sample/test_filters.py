"""Tests for Sample filtering and search functionality."""

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from demo.factories import RockSampleFactory
from demo.filters import RockSampleFilter
from demo.models import RockSample, WaterSample
from fairdm.core.models import Dataset, Sample
from fairdm.core.sample.filters import SampleFilter
from fairdm.core.vocabularies import DATE_TYPES, SAMPLE_STATUS
from fairdm.factories import ProjectFactory, SampleDateFactory, SampleDescriptionFactory
from fairdm.utils.choices import Visibility

User = get_user_model()

pytestmark = pytest.mark.django_db


def request_for(user):
    """A minimal request carrying a user."""
    request = RequestFactory().get("/")
    request.user = user
    return request


class TestSampleFilterDatasetFiltering:
    def test_filter_by_dataset(self, user):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset1 = Dataset.objects.create(
            name="Dataset 1", project=project, visibility=Visibility.PUBLIC
        )
        dataset2 = Dataset.objects.create(
            name="Dataset 2", project=project, visibility=Visibility.PUBLIC
        )

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
            data={"dataset": [dataset1.id]},
            queryset=RockSample.objects.all(),
            request=request_for(user),
        )
        assert filterset.is_valid()
        assert sample1 in filterset.qs
        assert sample2 not in filterset.qs


class TestSampleFilterStatusFiltering:
    def test_filter_by_status(self, dataset):
        available = RockSample.objects.create(
            name="Available Rock",
            dataset=dataset,
            status_id=f"{SAMPLE_STATUS}/available",
            rock_type="igneous",
            collection_date="2024-01-01",
        )
        stored = RockSample.objects.create(
            name="Stored Rock",
            dataset=dataset,
            status_id=f"{SAMPLE_STATUS}/stored",
            rock_type="igneous",
            collection_date="2024-01-01",
        )

        filterset = SampleFilter(
            data={"status": "available"},
            queryset=RockSample.objects.all(),
        )

        assert filterset.is_valid()
        assert available in filterset.qs
        assert stored not in filterset.qs


class TestSampleFilterPolymorphicTypeFiltering:
    def test_each_type_is_labelled_with_its_verbose_name(self):
        field = SampleFilter().form.fields["polymorphic_ctype"]

        labels = [label for value, label in field.choices if value]

        assert str(RockSample._meta.verbose_name) in labels
        assert all(" | " not in label for label in labels)

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
            data={"q": "Granite"}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert sample1 in filterset.qs
        assert sample2 not in filterset.qs

        filterset = SampleFilter(
            data={"q": "ROCK-002"}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert sample2 in filterset.qs
        assert sample1 not in filterset.qs

        uuid_fragment = str(sample1.uuid)[:8]
        filterset = SampleFilter(
            data={"q": uuid_fragment}, queryset=RockSample.objects.all()
        )
        assert filterset.is_valid()
        assert sample1 in filterset.qs


class TestSampleFilterDescriptionFiltering:
    def test_filter_by_description_content(self, dataset):
        silica = RockSampleFactory(dataset=dataset)
        iron = RockSampleFactory(dataset=dataset)
        SampleDescriptionFactory(related=silica, value="Contains high silica content")
        SampleDescriptionFactory(related=iron, value="Rich in iron oxide minerals")

        filterset = SampleFilter(
            data={"description": "silica"}, queryset=Sample.objects.all()
        )

        assert filterset.is_valid()
        assert set(filterset.qs) == {silica}


class TestSampleFilterDateRangeFiltering:
    def test_filter_by_date_range(self, dataset):
        inside = RockSampleFactory(dataset=dataset)
        before = RockSampleFactory(dataset=dataset)
        after = RockSampleFactory(dataset=dataset)
        SampleDateFactory(
            related=inside, type=f"{DATE_TYPES}/collected", value="2024-01-15"
        )
        SampleDateFactory(
            related=before, type=f"{DATE_TYPES}/collected", value="2023-12-31"
        )
        SampleDateFactory(
            related=after, type=f"{DATE_TYPES}/collected", value="2024-02-20"
        )

        filterset = SampleFilter(
            data={"date_after": "2024-01-10", "date_before": "2024-02-01"},
            queryset=Sample.objects.all(),
        )

        assert filterset.is_valid()
        assert set(filterset.qs) == {inside}


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
