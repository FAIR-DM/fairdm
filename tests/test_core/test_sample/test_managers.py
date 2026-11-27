"""Tests for the sample queryset rules that tests/test_core/test_managers.py misses."""

import pytest

from demo.factories import RockSampleFactory
from fairdm.core.sample.models import Sample
from fairdm.factories import DatasetFactory
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestVisibleTo:
    def test_no_user_at_all_is_treated_as_a_visitor(self):
        released = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )
        RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        )

        assert set(Sample.objects.visible_to(None)) == {released}
