"""Tests for ``RecordMultipleFilter`` and the list filters built on it."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from demo.factories import CustomSampleFactory
from demo.models import CustomSample
from fairdm.contrib.autocomplete.filters import RecordMultipleFilter, TagFilter
from fairdm.core.project.filters import ProjectFilter
from fairdm.core.project.models import Project
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


@pytest.mark.django_db
class TestTagFilter:
    @pytest.fixture
    def projects(self, make_project):
        """A public project tagged "basalt", one tagged "granite", one untagged, and a private one tagged "secret"."""
        basalt = make_project("Basalt", visibility=Visibility.PUBLIC)
        basalt.tags.add("basalt")
        granite = make_project("Granite", visibility=Visibility.PUBLIC)
        granite.tags.add("granite")
        bare = make_project("Bare", visibility=Visibility.PUBLIC)
        make_project("Hidden").tags.add("secret")
        return {"basalt": basalt, "granite": granite, "bare": bare}

    def filterset(self, in_request, data, user=None):
        request = in_request(user or AnonymousUser())
        return ProjectFilter(data=data, queryset=Project.objects.all(), request=request)

    def test_the_project_lists_tag_filter_is_a_tag_filter(self):
        assert isinstance(ProjectFilter().filters["tags"], TagFilter)

    def test_two_chosen_tags_narrow_the_list_to_the_projects_with_either(
        self, in_request, projects
    ):
        filterset = self.filterset(in_request, {"tags": ["basalt", "granite"]})

        assert filterset.is_valid(), filterset.errors
        assert set(filterset.qs) == {projects["basalt"], projects["granite"]}

    def test_a_project_with_both_tags_is_listed_once(self, in_request, projects):
        projects["basalt"].tags.add("granite")

        filterset = self.filterset(in_request, {"tags": ["basalt", "granite"]})

        assert list(filterset.qs).count(projects["basalt"]) == 1

    def test_a_tag_used_only_on_a_private_project_is_refused(
        self, in_request, projects
    ):
        filterset = self.filterset(in_request, {"tags": ["secret"]})

        assert not filterset.is_valid()
        assert "tags" in filterset.errors

    def test_a_researcher_is_offered_the_same_tags_as_a_visitor(
        self, in_request, researcher, make_project, projects
    ):
        make_project("Mine", holder=researcher).tags.add("mine")

        filterset = self.filterset(in_request, {"tags": ["mine"]}, user=researcher)

        assert not filterset.is_valid()

    def test_a_tag_nothing_uses_is_refused_so_the_filter_adds_none(
        self, in_request, projects
    ):
        filterset = self.filterset(in_request, {"tags": ["brand-new"]})

        assert not filterset.is_valid()

    def test_the_control_offers_no_way_to_add_a_tag(self, in_request):
        filterset = self.filterset(in_request, {})

        assert filterset.form.fields["tags"].widget.create is False
