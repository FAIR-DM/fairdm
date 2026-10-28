"""Unit tests for Sample forms."""

import pytest
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point as GEOSPoint
from django.test import Client, RequestFactory
from django.urls import reverse

from demo.factories import RockSampleFactory, WaterSampleFactory
from demo.models import RockSample, WaterSample
from fairdm.contrib.autocomplete.fields import DatasetChoiceField
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.sample.forms import SampleFormMixin
from fairdm.core.vocabularies import SAMPLE_STATUS
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.registry import registry
from fairdm.utils.choices import Visibility
from fairdm.utils.location.forms import LocationField
from tests.test_core.test_editing import form_payload, main_form

User = get_user_model()


def _request_for(user):
    """A minimal request carrying an authenticated user."""
    request = RequestFactory().get("/")
    request.user = user
    return request


@pytest.mark.django_db
class TestSampleFormRendering:
    def test_form_renders_with_all_base_fields(self):

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "local_id", "status", "location"]

        form = RockSampleForm()

        assert "name" in form.fields
        assert "dataset" in form.fields
        assert "local_id" in form.fields
        assert "status" in form.fields
        assert "location" in form.fields

    def test_form_mixin_provides_preconfigured_widgets(self):

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "status"]

        form = RockSampleForm()

        assert hasattr(form.fields["dataset"].widget, "attrs")
        assert isinstance(form.fields["status"].widget, forms.Select)


@pytest.mark.django_db
class TestSampleFormQuerysetFiltering:
    def test_form_filters_dataset_queryset_by_user_permissions(self):
        user = PersonFactory()
        project = ProjectFactory()
        project.add_contributor(user)

        _accessible_dataset = DatasetFactory(project=project)
        _other_dataset = DatasetFactory()

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        class MockRequest:
            def __init__(self, user):
                self.user = user

        request = MockRequest(user)
        form = RockSampleForm(request=request)

        assert hasattr(form, "request")


@pytest.mark.django_db
class TestSampleFormValidation:
    def test_form_validates_required_fields(self):

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        form = RockSampleForm(data={})
        assert not form.is_valid()
        assert "name" in form.errors
        assert "dataset" in form.errors

    def test_form_defaults_status_to_unknown(self):

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "status"]

        form = RockSampleForm()

        assert form.fields["status"].initial == f"{SAMPLE_STATUS}/unknown"


@pytest.mark.django_db
class TestSampleFormPolymorphicHandling:
    def test_form_handles_polymorphic_type_creation(self):
        from datetime import date

        user = UserFactory()
        dataset = DatasetFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "rock_type", "collection_date"]

        form_data = {
            "name": "Test Rock",
            "dataset": dataset.pk,
            "rock_type": "igneous",
            "collection_date": date.today().isoformat(),
        }

        form = RockSampleForm(data=form_data, request=_request_for(user))
        assert form.is_valid(), f"Form errors: {form.errors}"

        instance = form.save()
        assert isinstance(instance, RockSample)
        assert instance.name == "Test Rock"
        assert instance.rock_type == "igneous"

    def test_form_prepopulates_fields_for_edit_scenario(self):
        from datetime import date

        dataset = DatasetFactory()
        rock_sample = RockSample.objects.create(
            name="Existing Rock",
            dataset=dataset,
            rock_type="sedimentary",
            collection_date=date.today(),
        )

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "rock_type"]

        form = RockSampleForm(instance=rock_sample)

        assert form.initial["name"] == "Existing Rock"
        assert form.initial["dataset"] == dataset.pk
        assert form.initial["rock_type"] == "sedimentary"


@pytest.mark.django_db
class TestCustomSampleFormIntegration:
    def test_custom_sample_form_inherits_from_mixin(self):

        class CustomWaterSampleForm(SampleFormMixin, forms.ModelForm):
            custom_note = forms.CharField(required=False)

            class Meta:
                model = WaterSample
                fields = [
                    "name",
                    "dataset",
                    "water_source",
                    "ph_level",
                    "temperature_celsius",
                ]

        user = UserFactory()
        dataset = DatasetFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        form_data = {
            "name": "Water Sample 1",
            "dataset": dataset.pk,
            "water_source": "river",
            "ph_level": "7.2",
            "temperature_celsius": "15.5",
            "custom_note": "Test note",
        }

        form = CustomWaterSampleForm(data=form_data, request=_request_for(user))
        assert form.is_valid(), f"Form errors: {form.errors}"

        instance = form.save()
        assert isinstance(instance, WaterSample)
        assert instance.name == "Water Sample 1"
        assert instance.water_source == "river"


@pytest.mark.django_db
class TestSampleFormMixinWidgets:
    def _form(self):
        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "status", "location"]

        return RockSampleForm()

    def test_dataset_field_is_the_dataset_field_at_edit_scope(self):
        form = self._form()

        field = form.fields["dataset"]
        assert isinstance(field, DatasetChoiceField)
        assert field.scope == "edit"

    def test_a_sample_saved_through_the_form_belongs_to_the_chosen_dataset(self):
        user = UserFactory()
        dataset = DatasetFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "rock_type", "collection_date"]

        form = RockSampleForm(
            data={
                "name": "Basalt",
                "dataset": dataset.pk,
                "rock_type": "basalt",
                "collection_date": "2026-01-02",
            },
            request=_request_for(user),
        )

        assert form.is_valid(), form.errors
        assert form.save().dataset == dataset

    def test_a_sample_is_refused_a_dataset_its_editor_may_only_view(self):
        user = UserFactory()
        dataset = DatasetFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.VIEW
        )

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "rock_type"]

        form = RockSampleForm(
            data={"name": "Basalt", "dataset": dataset.pk, "rock_type": "basalt"},
            request=_request_for(user),
        )

        assert form.has_error("dataset", code="invalid_choice")

    def test_status_field_uses_a_select_widget(self):
        form = self._form()

        assert isinstance(form.fields["status"].widget, forms.Select)

    def test_location_field_is_the_location_input(self):
        form = self._form()

        assert isinstance(form.fields["location"], LocationField)
        assert form.fields["location"].full


@pytest.mark.django_db
class TestSampleFormDatasetChoices:
    def test_form_with_a_user_offers_exactly_that_users_datasets(self):
        user = UserFactory()
        allowed = DatasetFactory()
        other = DatasetFactory()
        ContributionFactory(
            content_object=allowed, contributor=user, level=ContributionLevel.EDIT
        )

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        form = RockSampleForm(request=_request_for(user))

        offered = set(form.fields["dataset"].queryset)
        assert offered == {allowed}
        assert other not in offered

    def test_a_dataset_the_user_may_only_view_is_not_offered(self):
        user = UserFactory()
        viewed = DatasetFactory()
        ContributionFactory(
            content_object=viewed, contributor=user, level=ContributionLevel.VIEW
        )

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        form = RockSampleForm(request=_request_for(user))

        assert set(form.fields["dataset"].queryset) == set()

    def test_a_level_on_the_project_offers_the_datasets_in_it(self):
        user = UserFactory()
        project = ProjectFactory()
        inside = DatasetFactory(project=project)
        DatasetFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        form = RockSampleForm(request=_request_for(user))

        assert set(form.fields["dataset"].queryset) == {inside}

    def test_a_stored_guardian_row_alone_offers_no_dataset(self):
        from fairdm.core.utils import assign_perm

        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("change_dataset", user, dataset)

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        form = RockSampleForm(request=_request_for(user))

        assert set(form.fields["dataset"].queryset) == set()

    def test_form_with_no_user_offers_no_dataset_at_all(self):
        DatasetFactory()
        DatasetFactory()

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        form = RockSampleForm()

        assert set(form.fields["dataset"].queryset) == set()

    def test_form_given_a_request_with_no_request_object_offers_no_dataset(self):
        DatasetFactory()

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        form = RockSampleForm(request=None)

        assert set(form.fields["dataset"].queryset) == set()

    def test_offering_no_dataset_with_no_request_logs_a_warning(self, caplog):
        import logging

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        with caplog.at_level(logging.WARNING):
            RockSampleForm()

        assert any(record.levelno == logging.WARNING for record in caplog.records)


@pytest.mark.django_db
class TestSampleFormOnAnExistingSample:
    """The dataset a sample sits in is offered only to someone who can manage the sample."""

    def _form(self, sample, user):
        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        return RockSampleForm(instance=sample, request=_request_for(user))

    def test_an_editor_is_not_offered_the_dataset(self):
        sample = RockSampleFactory()
        editor = UserFactory()
        ContributionFactory(
            content_object=sample, contributor=editor, level=ContributionLevel.EDIT
        )

        assert "dataset" not in self._form(sample, editor).fields

    def test_an_editors_post_cannot_move_the_sample(self):
        sample = RockSampleFactory(name="Original")
        elsewhere = DatasetFactory()
        editor = UserFactory()
        ContributionFactory(
            content_object=sample, contributor=editor, level=ContributionLevel.EDIT
        )
        ContributionFactory(
            content_object=elsewhere, contributor=editor, level=ContributionLevel.EDIT
        )
        form = self._form(sample, editor)
        form.data = {"name": "Renamed", "dataset": elsewhere.pk}
        form.is_bound = True

        form.is_valid()
        saved = form.save(commit=False)

        assert saved.dataset_id == sample.dataset_id

    def test_a_manager_is_offered_the_dataset(self):
        sample = RockSampleFactory()
        manager = UserFactory()
        ContributionFactory(
            content_object=sample, contributor=manager, level=ContributionLevel.MANAGE
        )
        ContributionFactory(
            content_object=sample.dataset,
            contributor=manager,
            level=ContributionLevel.MANAGE,
        )

        assert "dataset" in self._form(sample, manager).fields

    def test_a_form_for_a_new_sample_leaves_nothing_out(self):
        editor = UserFactory()

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        form = RockSampleForm(request=_request_for(editor))

        assert "dataset" in form.fields


@pytest.mark.django_db
class TestRegisteredSampleTypeLocationInput:
    def test_a_type_listing_location_gets_the_location_input(self):
        form_class = registry.get_for_model(RockSample).get_form_class()

        field = form_class(request=None).fields["location"]

        assert isinstance(field, LocationField)
        assert field.full

    def test_a_type_not_listing_location_has_no_location_input(self):
        form_class = registry.get_for_model(WaterSample).get_form_class()

        assert "location" not in form_class(request=None).fields


@pytest.fixture
def sample_editor(db):
    """A rock sample in a public dataset, with a client signed in as a person who may edit it."""
    dataset = DatasetFactory(
        project=ProjectFactory(visibility=Visibility.PUBLIC),
        visibility=Visibility.PUBLIC,
        published=True,
    )
    sample = RockSampleFactory(dataset=dataset, name="Basalt", rock_type="basalt")
    editor = PersonFactory(is_active=True, is_claimed=True, password="x")
    ContributionFactory(
        content_object=sample, contributor=editor, level=ContributionLevel.EDIT
    )
    client = Client()
    client.force_login(editor)
    return sample, client, editor


def edit_page(client, sample):
    """Open a sample's edit page and return its address and what a browser would send."""
    url = reverse("sample:edit", kwargs={"uuid": sample.uuid})
    response = client.get(url)
    assert response.status_code == 200
    return url, form_payload(main_form(response))


@pytest.mark.django_db
class TestSampleEditPageLocation:
    def test_a_location_in_decimal_degrees_is_saved_as_the_wgs84_point(
        self, sample_editor
    ):
        sample, client, _ = sample_editor
        url, payload = edit_page(client, sample)
        payload.update(location_first="49.0094", location_second="8.4115")

        response = client.post(url, payload)

        assert response.status_code == 302
        stored = RockSample.objects.get(pk=sample.pk)
        assert stored.location.srid == 4326
        assert stored.location.x == pytest.approx(8.4115, abs=1e-5)
        assert stored.location.y == pytest.approx(49.0094, abs=1e-5)

    def test_elevation_and_uncertainty_are_saved_with_the_point(self, sample_editor):
        sample, client, _ = sample_editor
        url, payload = edit_page(client, sample)
        payload.update(
            location_first="49.0094",
            location_second="8.4115",
            location_elevation="-12.5",
            location_uncertainty="3",
        )

        client.post(url, payload)

        stored = RockSample.objects.get(pk=sample.pk)
        assert (stored.location_elevation, stored.location_uncertainty) == (-12.5, 3)

    def test_the_one_left_out_is_saved_as_empty(self, sample_editor):
        sample, client, _ = sample_editor
        url, payload = edit_page(client, sample)
        payload.update(
            location_first="49.0094",
            location_second="8.4115",
            location_elevation="40",
            location_uncertainty="",
        )

        client.post(url, payload)

        stored = RockSample.objects.get(pk=sample.pk)
        assert stored.location_elevation == 40
        assert stored.location_uncertainty is None

    @pytest.mark.parametrize(
        "parts",
        [
            {"location_first": "91", "location_second": "8.4115"},
            {"location_first": "49.0094", "location_second": "181"},
            {"location_first": "49 0 33.84 N", "location_second": "8.4115"},
            {"location_first": "somewhere", "location_second": "8.4115"},
            {"location_first": "49.0094", "location_second": ""},
            {"location_first": "", "location_second": "", "location_elevation": "5"},
            {"location_first": "", "location_second": "", "location_uncertainty": "5"},
            {
                "location_first": "49.0094",
                "location_second": "8.4115",
                "location_uncertainty": "-1",
            },
        ],
    )
    def test_a_value_that_cannot_be_used_is_refused_and_nothing_is_saved(
        self, sample_editor, parts
    ):
        sample, client, _ = sample_editor
        url, payload = edit_page(client, sample)
        payload.update(parts)

        response = client.post(url, payload)

        assert response.status_code == 200
        assert "location" in response.context["form"].errors
        stored = RockSample.objects.get(pk=sample.pk)
        assert stored.location is None
        assert stored.location_elevation is None
        assert stored.location_uncertainty is None

    def test_the_form_holds_the_stored_location_in_wgs84_decimal_degrees(
        self, sample_editor
    ):
        sample, client, _ = sample_editor
        sample.location = GEOSPoint(8.4115, 49.0094, srid=4326)
        sample.location_elevation = 112.0
        sample.location_uncertainty = 5.0
        sample.save()

        response = client.get(reverse("sample:edit", kwargs={"uuid": sample.uuid}))

        form = main_form(response)
        shown = {
            name: form.select_one(f'[name="location_{name}"]')["value"]
            for name in ("first", "second", "elevation", "uncertainty")
        }
        assert shown == {
            "first": "49.0094",
            "second": "8.4115",
            "elevation": "112.0",
            "uncertainty": "5.0",
        }

    def test_a_type_not_listing_location_has_no_location_input_on_its_page(
        self, sample_editor
    ):
        rock, client, editor = sample_editor
        water = WaterSampleFactory(dataset=rock.dataset)
        ContributionFactory(
            content_object=water, contributor=editor, level=ContributionLevel.EDIT
        )

        response = client.get(reverse("sample:edit", kwargs={"uuid": water.uuid}))

        assert response.status_code == 200
        assert main_form(response).select('[name^="location"]') == []
