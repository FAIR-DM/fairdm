"""Tests for the autocomplete fields, on forms built inside a request."""

import pytest
from django import forms

from demo.factories import RockSampleFactory
from demo.models import RockSample
from fairdm.contrib.autocomplete.fields import (
    DatasetChoiceField,
    DatasetMultipleChoiceField,
    OrganizationMultipleChoiceField,
    PersonChoiceField,
    ProjectChoiceField,
    ProjectMultipleChoiceField,
    SampleChoiceField,
    SampleMultipleChoiceField,
)
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import UserFactory
from fairdm.utils.choices import Visibility
from tests.factories import ConcreteSampleFactory
from tests.registry_models.models import ConcreteMeasurement, ConcreteSample


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


class PreferringSampleForm(forms.Form):
    dataset = DatasetChoiceField(scope="edit", required=False)
    sample = SampleChoiceField(prefer="dataset")


@pytest.mark.django_db
class TestPreferringFields:
    def test_the_widget_is_told_to_prefer_the_dataset_and_not_to_filter_by_it(
        self, researcher, in_request
    ):
        in_request(researcher)

        context = PreferringSampleForm()["sample"].field.widget.get_context(
            "sample", None, {}
        )

        assert context["widget"]["prefer"] == "dataset"
        assert not context["widget"].get("filters")

    def test_a_sample_of_another_dataset_the_person_may_see_is_accepted(
        self, researcher, in_request, make_dataset, make_sample
    ):
        chosen = make_dataset("Chosen", holder=researcher)
        other = make_dataset("Other", holder=researcher)
        sample = make_sample("Elsewhere", dataset=other)
        in_request(researcher)

        form = PreferringSampleForm({"dataset": chosen.pk, "sample": sample.pk})

        assert form.is_valid(), form.errors
        assert form.cleaned_data["sample"] == sample

    def test_a_sample_the_person_may_not_see_is_refused(
        self, researcher, in_request, make_dataset, make_sample
    ):
        chosen = make_dataset("Chosen", holder=researcher)
        sample = make_sample("Hidden", dataset=make_dataset("Unseen"))
        in_request(researcher)

        form = PreferringSampleForm({"dataset": chosen.pk, "sample": sample.pk})

        assert form.has_error("sample", code="invalid_choice")

    def test_a_field_cannot_prefer_what_its_view_does_not_filter_by(self):
        with pytest.raises(ValueError, match="prefer"):
            DatasetChoiceField(prefer="project")


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


class TestPersonAndOrganizationFields:
    @pytest.mark.parametrize("scope", ["view", "edit"])
    def test_a_person_or_organization_field_is_offered_at_one_scope_only(self, scope):
        from fairdm.contrib.autocomplete.fields import (
            OrganizationChoiceField,
            PersonMultipleChoiceField,
        )

        for field_class in (OrganizationChoiceField, PersonMultipleChoiceField):
            with pytest.raises(ValueError, match="scope must be one of public"):
                field_class(scope=scope)

    def test_both_fields_of_a_pair_default_to_that_scope(self):
        from fairdm.contrib.autocomplete.fields import (
            PersonChoiceField,
            PersonMultipleChoiceField,
        )

        assert PersonChoiceField().scope == "public"
        assert PersonMultipleChoiceField().scope == "public"


class ProjectSettingsForm(forms.Form):
    project = ProjectChoiceField()


class ManyProjectsForm(forms.Form):
    projects = ProjectMultipleChoiceField()


class RockSampleForm(forms.Form):
    sample = SampleChoiceField(type=RockSample)


class OwnedProjectsForm(forms.Form):
    project = ProjectMultipleChoiceField()

    def __init__(self, *args, owner, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["project"] = ProjectMultipleChoiceField(owner=owner)


@pytest.mark.django_db
class TestFieldSettings:
    def test_a_field_with_nothing_configured_offers_what_the_person_may_view(
        self, researcher, in_request, make_project
    ):
        own = make_project("Own private", holder=researcher)
        public = make_project("Open", visibility=Visibility.PUBLIC)
        unseen = make_project("Unseen")
        in_request(researcher)

        assert ProjectSettingsForm({"project": own.pk}).is_valid()
        assert ProjectSettingsForm({"project": public.pk}).is_valid()
        assert ProjectSettingsForm({"project": unseen.pk}).has_error(
            "project", code="invalid_choice"
        )

    def test_a_multiple_field_with_nothing_configured_offers_a_private_record_the_person_may_view(
        self, researcher, in_request, make_project
    ):
        private = make_project(
            "Viewable", holder=researcher, level=ContributionLevel.VIEW
        )
        public = make_project("Open", visibility=Visibility.PUBLIC)
        in_request(researcher)

        form = ManyProjectsForm({"projects": [private.pk, public.pk]})

        assert form.is_valid(), form.errors
        assert set(form.cleaned_data["projects"]) == {private, public}

    def test_the_multiple_field_saves_every_chosen_record(
        self, researcher, in_request, make_project
    ):
        first = make_project("First", holder=researcher)
        second = make_project("Second", holder=researcher)
        third = make_project("Third", holder=researcher)
        in_request(researcher)

        form = ManyProjectsForm({"projects": [first.pk, second.pk, third.pk]})

        assert form.is_valid()
        assert set(form.cleaned_data["projects"]) == {first, second, third}

    def test_edit_scope_offers_only_what_the_person_may_edit(
        self, researcher, in_request, make_project
    ):
        class EditForm(forms.Form):
            project = ProjectChoiceField(scope="edit")

        editable = make_project("Editable", holder=researcher)
        view_only = make_project(
            "View only", holder=researcher, level=ContributionLevel.VIEW
        )
        in_request(researcher)

        assert EditForm({"project": editable.pk}).is_valid()
        assert EditForm({"project": view_only.pk}).has_error(
            "project", code="invalid_choice"
        )

    def test_public_scope_offers_no_private_record_of_the_person(
        self, researcher, in_request, make_project
    ):
        class PublicForm(forms.Form):
            project = ProjectChoiceField(scope="public")

        private = make_project("Private", holder=researcher)
        public = make_project("Open", visibility=Visibility.PUBLIC)
        in_request(researcher)

        assert PublicForm({"project": public.pk}).is_valid()
        assert PublicForm({"project": private.pk}).has_error(
            "project", code="invalid_choice"
        )

    def test_a_scope_the_kind_does_not_offer_is_refused(self):
        with pytest.raises(ValueError, match="scope must be one of"):
            ProjectChoiceField(scope="everything")

    def test_a_sample_field_narrowed_to_a_type_accepts_that_type_and_no_other(
        self, researcher, in_request, make_dataset
    ):
        dataset = make_dataset("Data", holder=researcher)
        rock = RockSampleFactory(dataset=dataset)
        other = ConcreteSampleFactory(dataset=dataset)
        in_request(researcher)

        accepted = RockSampleForm({"sample": rock.pk})
        refused = RockSampleForm({"sample": other.pk})

        assert accepted.is_valid(), accepted.errors
        assert refused.has_error("sample", code="invalid_choice")

    def test_a_field_narrowed_to_a_type_tells_the_address_to_filter_by_it(
        self, researcher, in_request
    ):
        from django.contrib.contenttypes.models import ContentType

        in_request(researcher)

        context = RockSampleForm()["sample"].field.widget.get_context(
            "sample", None, {}
        )

        filters = context["widget"]["filters"]
        assert [(f["source"], f["lookup"], f["source_type"]) for f in filters] == [
            (
                str(ContentType.objects.get_for_model(RockSample).pk),
                "polymorphic_ctype",
                "const",
            )
        ]

    def test_a_field_cannot_be_narrowed_to_a_type_its_kind_does_not_have(self):
        with pytest.raises(ValueError, match="type"):
            ProjectChoiceField(type=RockSample)

    def test_a_sample_field_cannot_be_narrowed_to_a_model_that_is_not_a_sample(self):
        with pytest.raises(ValueError, match="type"):
            SampleChoiceField(type=ConcreteMeasurement)

    def test_the_owners_private_records_are_offered_to_the_owner(
        self, researcher, in_request, make_project
    ):
        private = make_project("Private", holder=researcher)
        public = make_project("Open", visibility=Visibility.PUBLIC, holder=researcher)
        in_request(researcher)

        form = OwnedProjectsForm({"project": [private.pk, public.pk]}, owner=researcher)

        assert form.is_valid(), form.errors

    def test_the_owners_private_records_are_not_offered_to_anyone_else(
        self, researcher, in_request, make_project
    ):
        owner = UserFactory()
        private = make_project("Private", holder=owner)
        shared = make_project("Shared", holder=researcher, level=ContributionLevel.VIEW)
        public = make_project("Open", visibility=Visibility.PUBLIC, holder=owner)
        in_request(researcher)

        assert OwnedProjectsForm({"project": [public.pk]}, owner=owner).is_valid()
        assert OwnedProjectsForm({"project": [private.pk]}, owner=owner).has_error(
            "project", code="invalid_choice"
        )
        assert OwnedProjectsForm({"project": [shared.pk]}, owner=owner).has_error(
            "project", code="invalid_choice"
        )

    def test_the_owner_fields_address_is_the_profile_address_carrying_the_owner(
        self, researcher, in_request
    ):
        in_request(researcher)

        widget = OwnedProjectsForm(owner=researcher)["project"].field.widget
        context = widget.get_context("project", None, {})

        assert widget.url == "autocomplete:project-profile"
        assert context["widget"]["autocomplete_params"] == f"owner={researcher.pk}"

    def test_a_person_or_organization_field_has_no_owner(self, researcher):
        with pytest.raises(ValueError, match="owner"):
            PersonChoiceField(owner=researcher)

    def test_an_owner_and_a_scope_cannot_be_given_together(self, researcher):
        with pytest.raises(ValueError, match="owner"):
            ProjectChoiceField(owner=researcher, scope="edit")

    def test_the_multiple_field_narrowed_by_another_field_offers_only_its_records(
        self, researcher, in_request, make_dataset, make_sample
    ):
        class InDatasetForm(forms.Form):
            dataset = DatasetChoiceField(scope="edit", required=False)
            samples = SampleMultipleChoiceField(depends_on="dataset")

        chosen = make_dataset("Chosen", holder=researcher)
        other = make_dataset("Other", holder=researcher)
        inside = make_sample("Inside", dataset=chosen)
        outside = make_sample("Outside", dataset=other)
        in_request(researcher)

        accepted = InDatasetForm({"dataset": chosen.pk, "samples": [inside.pk]})
        refused = InDatasetForm({"dataset": chosen.pk, "samples": [outside.pk]})

        assert accepted.is_valid(), accepted.errors
        assert refused.has_error("samples", code="invalid_choice")

    @pytest.mark.parametrize(
        "field_class",
        [
            ProjectChoiceField,
            ProjectMultipleChoiceField,
            DatasetChoiceField,
            SampleChoiceField,
            PersonChoiceField,
            OrganizationMultipleChoiceField,
        ],
    )
    def test_a_rendered_field_waits_for_two_characters_and_throttles_loads_to_300_ms(
        self, researcher, in_request, field_class
    ):
        in_request(researcher)

        class RenderedForm(forms.Form):
            record = field_class()

        context = RenderedForm()["record"].field.widget.get_context("record", None, {})

        assert context["widget"]["minimum_query_length"] == 2
        assert context["widget"]["load_throttle"] == 300
