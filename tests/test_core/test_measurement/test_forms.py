"""Unit tests for Measurement forms."""

import pytest
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point as GEOSPoint
from django.test import Client, RequestFactory
from django.urls import reverse

from demo.factories import (
    ExampleMeasurementFactory,
    ICP_MS_MeasurementFactory,
    RockSampleFactory,
    XRFMeasurementFactory,
)
from demo.models import ExampleMeasurement, ICP_MS_Measurement, XRFMeasurement
from fairdm.contrib.autocomplete.fields import DatasetChoiceField, SampleChoiceField
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.measurement.forms import MeasurementFormMixin
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


class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
    class Meta:
        model = XRFMeasurement
        fields = ["name", "dataset", "sample"]


@pytest.mark.django_db
class TestMeasurementFormDatasetChoices:
    def test_form_with_a_user_offers_exactly_that_users_datasets(self):
        user = UserFactory()
        allowed = DatasetFactory()  # private by default
        other = DatasetFactory()
        ContributionFactory(
            content_object=allowed, contributor=user, level=ContributionLevel.EDIT
        )

        form = XRFMeasurementForm(request=_request_for(user))

        offered = set(form.fields["dataset"].queryset)
        assert offered == {allowed}
        assert other not in offered

    def test_a_dataset_the_user_may_only_view_is_not_offered(self):
        user = UserFactory()
        viewed = DatasetFactory()
        ContributionFactory(
            content_object=viewed, contributor=user, level=ContributionLevel.VIEW
        )

        form = XRFMeasurementForm(request=_request_for(user))

        assert set(form.fields["dataset"].queryset) == set()

    def test_a_level_on_the_project_offers_the_datasets_in_it(self):
        user = UserFactory()
        project = ProjectFactory()
        inside = DatasetFactory(project=project)
        DatasetFactory()
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )

        form = XRFMeasurementForm(request=_request_for(user))

        assert set(form.fields["dataset"].queryset) == {inside}

    def test_a_stored_guardian_row_alone_offers_no_dataset(self):
        from fairdm.core.utils import assign_perm

        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("change_dataset", user, dataset)

        form = XRFMeasurementForm(request=_request_for(user))

        assert set(form.fields["dataset"].queryset) == set()

    def test_form_with_no_user_offers_no_dataset_at_all(self):
        DatasetFactory()
        DatasetFactory()

        form = XRFMeasurementForm()

        assert set(form.fields["dataset"].queryset) == set()

    def test_scoping_derives_from_the_requests_own_user(self):
        user1 = UserFactory()
        user2 = UserFactory()
        dataset1 = DatasetFactory()
        dataset2 = DatasetFactory()
        ContributionFactory(
            content_object=dataset1, contributor=user1, level=ContributionLevel.EDIT
        )
        ContributionFactory(
            content_object=dataset2, contributor=user2, level=ContributionLevel.EDIT
        )

        form = XRFMeasurementForm(request=_request_for(user1))

        offered = set(form.fields["dataset"].queryset)
        assert offered == {dataset1}
        assert dataset2 not in offered


@pytest.mark.django_db
class TestMeasurementFormOnAnExistingMeasurement:
    """The dataset a measurement sits in is offered only to someone who can manage it."""

    def _measurement(self):
        dataset = DatasetFactory()
        return ExampleMeasurementFactory(
            dataset=dataset, sample=RockSampleFactory(dataset=dataset)
        )

    def _form(self, measurement, user):
        class MeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = ExampleMeasurement
                fields = ["name", "dataset", "sample"]

        return MeasurementForm(instance=measurement, request=_request_for(user))

    def test_an_editor_is_not_offered_the_dataset(self):
        measurement = self._measurement()
        editor = UserFactory()
        ContributionFactory(
            content_object=measurement,
            contributor=editor,
            level=ContributionLevel.EDIT,
        )

        assert "dataset" not in self._form(measurement, editor).fields

    def test_a_manager_is_offered_the_dataset(self):
        measurement = self._measurement()
        manager = UserFactory()
        ContributionFactory(
            content_object=measurement,
            contributor=manager,
            level=ContributionLevel.MANAGE,
        )

        assert "dataset" in self._form(measurement, manager).fields

    def test_a_form_for_a_new_measurement_leaves_nothing_out(self):
        class MeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = ExampleMeasurement
                fields = ["name", "dataset", "sample"]

        form = MeasurementForm(request=_request_for(UserFactory()))

        assert "dataset" in form.fields


@pytest.mark.django_db
class TestMeasurementFormDatasetField:
    def test_dataset_field_is_the_dataset_field_at_edit_scope(self):

        field = XRFMeasurementForm().fields["dataset"]

        assert isinstance(field, DatasetChoiceField)
        assert field.scope == "edit"


@pytest.mark.django_db
class TestRegisteredMeasurementTypeLocationInput:
    def test_a_type_listing_location_gets_the_location_input(self):
        form_class = registry.get_for_model(XRFMeasurement).get_form_class()

        field = form_class(request=None).fields["location"]

        assert isinstance(field, LocationField)
        assert field.full

    def test_a_type_not_listing_location_has_no_location_input(self):
        form_class = registry.get_for_model(ICP_MS_Measurement).get_form_class()

        assert "location" not in form_class(request=None).fields


@pytest.fixture
def measurement_editor(db):
    """An XRF measurement in a public dataset, with a client signed in as a person who may edit it."""
    dataset = DatasetFactory(
        project=ProjectFactory(visibility=Visibility.PUBLIC),
        visibility=Visibility.PUBLIC,
        published=True,
    )
    sample = RockSampleFactory(
        dataset=dataset, location=GEOSPoint(8.5, 49.5, srid=4326)
    )
    measurement = XRFMeasurementFactory(dataset=dataset, sample=sample)
    editor = PersonFactory(is_active=True, is_claimed=True, password="x")
    ContributionFactory(
        content_object=measurement, contributor=editor, level=ContributionLevel.EDIT
    )
    client = Client()
    client.force_login(editor)
    return measurement, client, editor


def measurement_edit_page(client, measurement):
    """Open a measurement's edit page and return its address and what a browser would send."""
    url = reverse("measurement:edit", kwargs={"uuid": measurement.uuid})
    response = client.get(url)
    assert response.status_code == 200
    return url, form_payload(main_form(response))


@pytest.mark.django_db
class TestMeasurementEditPageLocation:
    def test_a_typed_location_is_saved_as_the_wgs84_point_with_its_extras(
        self, measurement_editor
    ):
        measurement, client, _ = measurement_editor
        url, payload = measurement_edit_page(client, measurement)
        payload.update(
            location_first="49.0094",
            location_second="8.4115",
            location_elevation="112",
            location_uncertainty="25",
        )

        response = client.post(url, payload)

        assert response.status_code == 302
        stored = XRFMeasurement.objects.get(pk=measurement.pk)
        assert stored.location.srid == 4326
        assert stored.location.x == pytest.approx(8.4115, abs=1e-5)
        assert stored.location.y == pytest.approx(49.0094, abs=1e-5)
        assert (stored.location_elevation, stored.location_uncertainty) == (112, 25)

    def test_a_value_that_cannot_be_used_is_refused_and_nothing_is_saved(
        self, measurement_editor
    ):
        measurement, client, _ = measurement_editor
        url, payload = measurement_edit_page(client, measurement)
        payload.update(
            location_first="91", location_second="8.4115", location_elevation="5"
        )

        response = client.post(url, payload)

        assert response.status_code == 200
        assert "location" in response.context["form"].errors
        stored = XRFMeasurement.objects.get(pk=measurement.pk)
        assert stored.location is None
        assert stored.location_elevation is None

    def test_clearing_the_location_clears_the_elevation_and_uncertainty(
        self, measurement_editor
    ):
        measurement, client, _ = measurement_editor
        measurement.location = GEOSPoint(8.4115, 49.0094, srid=4326)
        measurement.location_elevation = 112.0
        measurement.location_uncertainty = 5.0
        measurement.save()
        url, payload = measurement_edit_page(client, measurement)
        payload.update(
            location_first="",
            location_second="",
            location_elevation="",
            location_uncertainty="",
        )

        client.post(url, payload)

        stored = XRFMeasurement.objects.get(pk=measurement.pk)
        assert stored.location is None
        assert stored.location_elevation is None
        assert stored.location_uncertainty is None

    def test_saving_the_measurements_location_leaves_its_samples_alone(
        self, measurement_editor
    ):
        measurement, client, _ = measurement_editor
        url, payload = measurement_edit_page(client, measurement)
        payload.update(location_first="49.0094", location_second="8.4115")

        client.post(url, payload)

        own = XRFMeasurement.objects.get(pk=measurement.pk).location
        sample = measurement.sample
        sample.refresh_from_db()
        assert (own.x, own.y) == (8.4115, 49.0094)
        assert (sample.location.x, sample.location.y) == (8.5, 49.5)

    def test_a_type_not_listing_location_has_no_location_input_on_its_page(
        self, measurement_editor
    ):
        xrf, client, editor = measurement_editor
        icp = ICP_MS_MeasurementFactory(dataset=xrf.dataset, sample=xrf.sample)
        ContributionFactory(
            content_object=icp, contributor=editor, level=ContributionLevel.EDIT
        )

        response = client.get(reverse("measurement:edit", kwargs={"uuid": icp.uuid}))

        assert response.status_code == 200
        assert main_form(response).select('[name^="location"]') == []


@pytest.mark.django_db
class TestMeasurementSampleField:
    """The sample is chosen from every sample the person may see, those of the chosen dataset first."""

    def _editor_of(self, *datasets):
        user = UserFactory()
        for dataset in datasets:
            ContributionFactory(
                content_object=dataset, contributor=user, level=ContributionLevel.EDIT
            )
        return user

    def test_the_sample_field_prefers_the_dataset_field_and_is_not_bound_to_it(self):
        form = XRFMeasurementForm()

        assert isinstance(form.fields["sample"], SampleChoiceField)
        assert form.fields["sample"].prefer == "dataset"
        assert form.fields["sample"].depends_on is None

    def test_a_sample_of_another_dataset_the_person_may_see_is_accepted(self):
        chosen, other = DatasetFactory(), DatasetFactory()
        sample = RockSampleFactory(dataset=other)
        user = self._editor_of(chosen, other)

        form = XRFMeasurementForm(
            data={"name": "Run", "dataset": chosen.pk, "sample": sample.pk},
            request=_request_for(user),
        )

        assert form.is_valid(), form.errors
        assert form.cleaned_data["sample"] == sample

    def test_a_sample_the_person_may_not_see_is_refused(self):
        chosen, unseen = DatasetFactory(), DatasetFactory()
        sample = RockSampleFactory(dataset=unseen)
        user = self._editor_of(chosen)

        form = XRFMeasurementForm(
            data={"name": "Run", "dataset": chosen.pk, "sample": sample.pk},
            request=_request_for(user),
        )

        assert form.has_error("sample", code="invalid_choice")

    def test_a_sample_of_the_chosen_dataset_is_accepted(self):
        chosen = DatasetFactory()
        sample = RockSampleFactory(dataset=chosen)
        user = self._editor_of(chosen)

        form = XRFMeasurementForm(
            data={"name": "Run", "dataset": chosen.pk, "sample": sample.pk},
            request=_request_for(user),
        )

        assert form.is_valid(), form.errors
        assert form.cleaned_data["sample"] == sample
