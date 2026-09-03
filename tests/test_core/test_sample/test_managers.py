"""T007: SampleQuerySet.published() decides presence by the sample's own dataset.

New file mirroring fairdm/core/sample/managers.py (craft-tdd's "mirror the source tree"
rule) - tests/test_core/test_sample/ carried no test_managers.py before this task.
"""

import pytest

from fairdm.core.sample.models import Sample
from fairdm.factories import DatasetFactory
from fairdm_demo.factories import RockSampleFactory


@pytest.mark.django_db
class TestPublished:
    """FR-011: a sample is present in `published()` if and only if its own dataset is."""

    def test_published_includes_a_sample_whose_dataset_is_published(self):
        sample = RockSampleFactory(dataset=DatasetFactory(published=True))

        assert sample in Sample.objects.published()

    def test_published_excludes_a_sample_whose_dataset_is_unpublished(self):
        sample = RockSampleFactory(dataset=DatasetFactory(published=False))

        assert sample not in Sample.objects.published()
