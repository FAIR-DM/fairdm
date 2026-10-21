"""Tests for ``RecordMultipleFilter`` and the list filters built on it."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from demo.factories import CustomSampleFactory
from demo.models import CustomSample
from fairdm.contrib.autocomplete.filters import RecordMultipleFilter
from fairdm.core.sample.filters import SampleFilter
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestRecordMultipleFilter:
    @pytest.fixture
    def datasets(self, make_dataset):
        """Two public datasets, a private one, and a sample in each."""
        datasets = {
            "first": make_dataset(
                "First", visibility=Visibility.PUBLIC, published=True
            ),
            "second": make_dataset(
                "Second", visibility=Visibility.PUBLIC, published=True
            ),
            "third": make_dataset(
                "Third", visibility=Visibility.PUBLIC, published=True
            ),
            "private": make_dataset("Hidden", published=True),
        }
        datasets["samples"] = {
            key: CustomSampleFactory(dataset=dataset, name=f"Sample of {key}")
            for key, dataset in datasets.items()
        }
        return datasets

    def offered(self, filterset):
        return set(filterset.form.fields["dataset"].offered())

    def test_the_sample_lists_dataset_filter_is_a_record_filter_at_public_scope(self):
        dataset_filter = SampleFilter().filters["dataset"]

        assert isinstance(dataset_filter, RecordMultipleFilter)
        assert dataset_filter.field.scope == "public"

    def test_a_visitor_is_offered_public_datasets(self, in_request, datasets):
        request = in_request(AnonymousUser())

        offered = self.offered(SampleFilter(request=request))

        assert offered == {datasets["first"], datasets["second"], datasets["third"]}

    def test_a_researcher_with_a_private_dataset_is_offered_the_same(
        self, in_request, researcher, make_dataset, datasets
    ):
        make_dataset("Mine", holder=researcher)
        request = in_request(researcher)

        offered = self.offered(SampleFilter(request=request))

        assert offered == {datasets["first"], datasets["second"], datasets["third"]}

    def test_two_ticked_datasets_narrow_the_list_to_their_samples(
        self, in_request, datasets
    ):
        request = in_request(AnonymousUser())

        filterset = SampleFilter(
            data={"dataset": [datasets["first"].pk, datasets["second"].pk]},
            queryset=CustomSample.objects.all(),
            request=request,
        )

        assert filterset.is_valid(), filterset.errors
        assert set(filterset.qs) == {
            datasets["samples"]["first"],
            datasets["samples"]["second"],
        }

    def test_a_private_dataset_is_refused_whoever_asks(
        self, in_request, researcher, make_dataset, datasets
    ):
        mine = make_dataset("Mine", holder=researcher)
        request = in_request(researcher)

        filterset = SampleFilter(
            data={"dataset": [mine.pk]},
            queryset=CustomSample.objects.all(),
            request=request,
        )

        assert not filterset.is_valid()
        assert "dataset" in filterset.errors

    def test_the_values_come_back_from_the_lists_address(self, client, datasets):
        first, second = datasets["first"], datasets["second"]

        response = client.get(
            reverse("customsample-list"), {"dataset": [first.pk, second.pk]}
        )

        assert response.status_code == 200
        filterset = response.context["filter"]
        assert filterset.form["dataset"].value() == [str(first.pk), str(second.pk)]
        assert {sample.dataset for sample in filterset.qs} == {first, second}

    def test_the_filter_keeps_its_choices_with_the_lists_search_applied(
        self, client, datasets
    ):
        first = datasets["first"]

        response = client.get(
            reverse("customsample-list"),
            {"dataset": [first.pk], "q": "Sample of first"},
        )

        assert response.status_code == 200
        filterset = response.context["filter"]
        assert filterset.form["dataset"].value() == [str(first.pk)]
        assert [sample.name for sample in filterset.qs] == ["Sample of first"]
        assert first.name in str(filterset.form["dataset"])

    def test_a_filter_set_built_with_a_request_needs_no_current_one(self, datasets):
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.user = AnonymousUser()

        filterset = SampleFilter(
            data={"dataset": [datasets["first"].pk]},
            queryset=CustomSample.objects.all(),
            request=request,
        )

        assert filterset.is_valid(), filterset.errors
        assert [sample.dataset for sample in filterset.qs] == [datasets["first"]]
