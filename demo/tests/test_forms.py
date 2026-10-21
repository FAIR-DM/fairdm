"""Tests for the demo forms that show the record search fields."""

import pytest
from django.test import RequestFactory
from django_tomselect.middleware import _request_local

from demo.factories import RockSampleFactory, WaterSampleFactory
from demo.forms import SampleReferenceFormExample
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import ContributionFactory, DatasetFactory, UserFactory


@pytest.fixture
def in_request():
    """Make a request for one user the current one, as the middleware does."""

    def enter(user):
        request = RequestFactory().get("/some/page/")
        request.user = user
        _request_local.request = request

    yield enter
    if hasattr(_request_local, "request"):
        del _request_local.request


@pytest.fixture
def viewer(db):
    return UserFactory()


@pytest.fixture
def viewable_dataset(viewer):
    dataset = DatasetFactory()
    ContributionFactory(
        content_object=dataset, contributor=viewer, level=ContributionLevel.VIEW
    )
    return dataset


@pytest.mark.django_db
class TestSampleReferenceFormExample:
    def test_a_rock_sample_the_user_may_view_is_accepted(
        self, viewer, in_request, viewable_dataset
    ):
        rock = RockSampleFactory(dataset=viewable_dataset)
        in_request(viewer)

        form = SampleReferenceFormExample({"rock_sample": rock.pk})

        assert form.is_valid(), form.errors
        assert form.cleaned_data["rock_sample"].pk == rock.pk

    def test_a_sample_of_another_type_is_refused(
        self, viewer, in_request, viewable_dataset
    ):
        water = WaterSampleFactory(dataset=viewable_dataset)
        in_request(viewer)

        form = SampleReferenceFormExample({"rock_sample": water.pk})

        assert form.has_error("rock_sample", code="invalid_choice")

    def test_a_rock_sample_the_user_may_not_view_is_refused(self, viewer, in_request):
        rock = RockSampleFactory(dataset=DatasetFactory())
        in_request(viewer)

        form = SampleReferenceFormExample({"rock_sample": rock.pk})

        assert form.has_error("rock_sample", code="invalid_choice")
