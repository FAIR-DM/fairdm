"""Tests for the visibility rules samples and measurements share."""

import pytest
from django.contrib.auth.models import AnonymousUser

from demo.factories import RockSampleFactory, XRFMeasurementFactory
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.core.utils import assign_perm
from fairdm.factories import DatasetFactory, PersonFactory
from fairdm.utils.choices import Visibility


def _sample(dataset):
    return RockSampleFactory(dataset=dataset)


def _measurement(dataset):
    return XRFMeasurementFactory(dataset=dataset, sample=_sample(dataset))


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("model", "make"), [(Sample, _sample), (Measurement, _measurement)]
)
class TestRecordVisibilityMixin:
    """Both querysets decide by the record's own dataset."""

    def test_a_visitor_sees_only_records_in_public_published_datasets(
        self, model, make
    ):
        released = make(DatasetFactory(visibility=Visibility.PUBLIC, published=True))
        make(DatasetFactory(visibility=Visibility.PUBLIC, published=False))

        assert set(model.objects.visible_to(AnonymousUser())) == {released}

    def test_a_team_member_also_sees_their_datasets_records(self, model, make):
        held = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        mine = make(held)
        make(DatasetFactory(visibility=Visibility.PRIVATE, published=False))
        user = PersonFactory(is_active=True)
        assign_perm("view_dataset", user, held)

        assert set(model.objects.visible_to(user)) == {mine}

    def test_published_keeps_the_records_of_published_datasets(self, model, make):
        kept = make(DatasetFactory(published=True))
        make(DatasetFactory(published=False))

        assert set(model.objects.published()) == {kept}
