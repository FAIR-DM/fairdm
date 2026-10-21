"""Tests for the autocomplete fields, on forms built inside a request."""

import pytest
from django import forms

from fairdm.contrib.autocomplete.fields import (
    DatasetChoiceField,
    DatasetMultipleChoiceField,
    ProjectChoiceField,
)
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.utils.choices import Visibility
from tests.factories import ConcreteSampleFactory
from tests.registry_models.models import ConcreteSample


class PlacementForm(forms.Form):
    dataset = DatasetChoiceField(scope="edit")


class ManyPlacementsForm(forms.Form):
    datasets = DatasetMultipleChoiceField(scope="edit")


class StoredDatasetForm(forms.ModelForm):
    dataset = DatasetChoiceField(scope="edit")

    class Meta:
        model = ConcreteSample
        fields = ["name", "dataset"]


@pytest.mark.django_db
class TestRecordFields:
    def test_a_dataset_the_user_can_edit_is_accepted(
        self, researcher, in_request, make_dataset
    ):
        dataset = make_dataset("Editable", holder=researcher)
        in_request(researcher)

        form = PlacementForm({"dataset": dataset.pk})

        assert form.is_valid()
        assert form.cleaned_data["dataset"] == dataset

    def test_a_dataset_the_user_may_only_view_is_refused(
        self, researcher, in_request, make_dataset
    ):
        dataset = make_dataset(
            "Read only", holder=researcher, level=ContributionLevel.VIEW
        )
        in_request(researcher)

        form = PlacementForm({"dataset": dataset.pk})

        assert form.has_error("dataset", code="invalid_choice")

    def test_a_dataset_the_user_cannot_see_is_refused(
        self, researcher, in_request, make_dataset
    ):
        dataset = make_dataset("Unseen")
        in_request(researcher)

        form = PlacementForm({"dataset": dataset.pk})

        assert form.has_error("dataset", code="invalid_choice")

    def test_the_field_validates_at_its_own_scope_whatever_the_page_asks(
        self, researcher, in_request, make_dataset
    ):
        editable = make_dataset("Editable", holder=researcher)
        view_only = make_dataset(
            "Read only", holder=researcher, level=ContributionLevel.VIEW
        )
        in_request(
            researcher,
            q="matches nothing",
            f=f"field__visibility={int(Visibility.PUBLIC)}",
            e=f"field__pk={editable.pk}",
        )

        accepted = PlacementForm({"dataset": editable.pk})
        refused = PlacementForm({"dataset": view_only.pk})

        assert accepted.is_valid()
        assert refused.has_error("dataset", code="invalid_choice")

    def test_a_visitor_is_refused_a_dataset_at_edit(
        self, client, in_request, make_dataset
    ):
        from django.contrib.auth.models import AnonymousUser

        dataset = make_dataset("Open", visibility=Visibility.PUBLIC)
        in_request(AnonymousUser())

        form = PlacementForm({"dataset": dataset.pk})

        assert form.has_error("dataset", code="invalid_choice")

    def test_a_dataset_that_was_made_private_after_it_was_chosen_is_refused(
        self, researcher, in_request, make_dataset
    ):
        dataset = make_dataset("Was open", holder=researcher)
        chosen = dataset.pk
        in_request(researcher)
        researcher.contributions.all().delete()

        form = PlacementForm({"dataset": chosen})

        assert form.has_error("dataset", code="invalid_choice")

    def test_the_multiple_field_accepts_every_dataset_it_offers_and_no_other(
        self, researcher, in_request, make_dataset
    ):
        first = make_dataset("First", holder=researcher)
        second = make_dataset("Second", holder=researcher)
        unseen = make_dataset("Unseen")
        in_request(researcher)

        accepted = ManyPlacementsForm({"datasets": [first.pk, second.pk]})
        refused = ManyPlacementsForm({"datasets": [first.pk, unseen.pk]})

        assert accepted.is_valid()
        assert set(accepted.cleaned_data["datasets"]) == {first, second}
        assert refused.has_error("datasets", code="invalid_choice")

    def test_a_project_field_offers_projects_at_its_own_scope(
        self, researcher, in_request, make_project
    ):
        class ProjectForm(forms.Form):
            project = ProjectChoiceField(scope="edit")

        editable = make_project("Editable", holder=researcher)
        view_only = make_project(
            "Read only", holder=researcher, level=ContributionLevel.VIEW
        )
        in_request(researcher)

        assert ProjectForm({"project": editable.pk}).is_valid()
        assert ProjectForm({"project": view_only.pk}).has_error(
            "project", code="invalid_choice"
        )


@pytest.mark.django_db
class TestStoredLinkTheEditorCannotSee:
    @pytest.fixture
    def sample_in_unseen_dataset(self, make_dataset):
        unseen = make_dataset("Secret dataset name")
        return ConcreteSampleFactory(dataset=unseen), unseen

    def test_the_stored_dataset_is_kept_when_the_form_is_submitted_unchanged(
        self, researcher, in_request, sample_in_unseen_dataset
    ):
        sample, unseen = sample_in_unseen_dataset
        in_request(researcher)

        form = StoredDatasetForm(
            {"name": "Renamed", "dataset": unseen.pk}, instance=sample
        )

        assert form.is_valid()
        form.save()
        sample.refresh_from_db()
        assert sample.dataset_id == unseen.pk

    def test_another_dataset_the_editor_cannot_see_is_still_refused(
        self, researcher, in_request, sample_in_unseen_dataset, make_dataset
    ):
        sample, _unseen = sample_in_unseen_dataset
        other = make_dataset("Another unseen")
        in_request(researcher)

        form = StoredDatasetForm(
            {"name": "Renamed", "dataset": other.pk}, instance=sample
        )

        assert form.has_error("dataset", code="invalid_choice")

    def test_the_widget_shows_the_stored_dataset_without_its_name(
        self, researcher, in_request, sample_in_unseen_dataset
    ):
        sample, unseen = sample_in_unseen_dataset
        in_request(researcher)

        html = str(StoredDatasetForm(instance=sample)["dataset"])

        assert f"allItems.push('{unseen.pk}')" in html
        assert unseen.name not in html

    def test_the_widget_shows_a_dataset_the_editor_can_see_by_name(
        self, researcher, in_request, make_dataset
    ):
        visible = make_dataset("Visible dataset name", holder=researcher)
        sample = ConcreteSampleFactory(dataset=visible)
        in_request(researcher)

        html = str(StoredDatasetForm(instance=sample)["dataset"])

        assert f"allItems.push('{visible.pk}')" in html
        assert visible.name in html
