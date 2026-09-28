"""Tests for the sample queryset's published() presence rule."""

import pytest

from demo.factories import RockSampleFactory
from fairdm.core.sample.models import Sample
from fairdm.factories import DatasetFactory


@pytest.mark.django_db
class TestPublished:
    def test_published_includes_a_sample_whose_dataset_is_published(self):
        sample = RockSampleFactory(dataset=DatasetFactory(published=True))

        assert sample in Sample.objects.published()

    def test_published_excludes_a_sample_whose_dataset_is_unpublished(self):
        sample = RockSampleFactory(dataset=DatasetFactory(published=False))

        assert sample not in Sample.objects.published()
