"""Tests for the autocomplete fields, on forms built inside a request."""

import pytest
from django import forms

from fairdm.contrib.autocomplete.fields import (
    DatasetChoiceField,
    DatasetMultipleChoiceField,
    ProjectChoiceField,
    SampleChoiceField,
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

    def test_a_form_built_outside_any_request_offers_nothing_by_default(
        self, researcher, make_dataset
    ):
        dataset = make_dataset("Editable", holder=researcher)

        form = PlacementForm({"dataset": dataset.pk})

        assert form.has_error("dataset", code="invalid_choice")

    def test_a_form_built_outside_any_request_uses_the_queryset_it_was_given(
        self, make_dataset
    ):
        from fairdm.core.dataset.models import Dataset

        dataset = make_dataset("Given")

        class GivenForm(forms.Form):
            dataset = DatasetChoiceField(scope="edit")

        form = GivenForm({"dataset": dataset.pk})
        form.fields["dataset"].queryset = Dataset.all_objects.all()

        assert form.is_valid()

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


class DependentSampleForm(forms.Form):
    dataset = DatasetChoiceField(scope="edit", required=False)
    sample = SampleChoiceField(depends_on="dataset")


@pytest.mark.django_db
class TestDependentFields:
    def test_the_field_hands_the_widget_the_hook_that_narrows_by_the_dataset(
        self, researcher, in_request
    ):
        in_request(researcher)

        context = DependentSampleForm()["sample"].field.widget.get_context(
            "sample", None, {}
        )

        filters = context["widget"]["filters"]
        assert [(f["source"], f["lookup"], f["source_type"]) for f in filters] == [
            ("dataset", "dataset", "field")
        ]

    def test_a_sample_of_the_chosen_dataset_is_accepted(
        self, researcher, in_request, make_dataset, make_sample
    ):
        chosen = make_dataset("Chosen", holder=researcher)
        sample = make_sample("Inside", dataset=chosen)
        in_request(researcher)

        form = DependentSampleForm({"dataset": chosen.pk, "sample": sample.pk})

        assert form.is_valid()
        assert form.cleaned_data["sample"] == sample

    def test_a_sample_of_another_dataset_is_refused(
        self, researcher, in_request, make_dataset, make_sample
    ):
        chosen = make_dataset("Chosen", holder=researcher)
        other = make_dataset("Other", holder=researcher)
        sample = make_sample("Elsewhere", dataset=other)
        in_request(researcher)

        form = DependentSampleForm({"dataset": chosen.pk, "sample": sample.pk})

        assert form.has_error("sample", code="invalid_choice")

    def test_the_dataset_is_read_from_the_forms_data_and_not_from_the_page(
        self, researcher, in_request, make_dataset, make_sample
    ):
        chosen = make_dataset("Chosen", holder=researcher)
        other = make_dataset("Other", holder=researcher)
        sample = make_sample("Elsewhere", dataset=other)
        in_request(researcher, f=f"'dataset__dataset={other.pk}'")

        form = DependentSampleForm({"dataset": chosen.pk, "sample": sample.pk})

        assert form.has_error("sample", code="invalid_choice")

    def test_a_dataset_value_that_is_not_a_key_refuses_the_sample_and_does_not_fail(
        self, researcher, in_request, make_dataset, make_sample
    ):
        sample = make_sample("Any", dataset=make_dataset("D", holder=researcher))
        in_request(researcher)

        form = DependentSampleForm({"dataset": "not a key", "sample": sample.pk})

        assert form.has_error("sample", code="invalid_choice")

    def test_a_field_cannot_depend_on_what_its_view_does_not_filter_by(self):
        with pytest.raises(ValueError, match="depends_on"):
            DatasetChoiceField(depends_on="project")
