"""Unit tests for Sample forms."""

import pytest
from django import forms
from django.test import Client, RequestFactory
from django.urls import reverse

from demo.factories import RockSampleFactory
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


def _request_for(user):
    """A minimal request carrying an authenticated user."""
    request = RequestFactory().get("/")
    request.user = user
    return request


@pytest.mark.django_db
class TestSampleFormDefaults:
    def test_form_defaults_status_to_unknown(self):

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "status"]

        form = RockSampleForm()

        assert form.fields["status"].initial == f"{SAMPLE_STATUS}/unknown"


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
        user = UserFactory(is_active=True)
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
        user = UserFactory(is_active=True)
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


@pytest.mark.django_db
class TestSampleFormDatasetChoices:
    def test_form_with_a_user_offers_exactly_that_users_datasets(self):
        user = UserFactory(is_active=True)
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

    def test_form_with_no_user_offers_no_dataset_at_all(self):
        DatasetFactory()
        DatasetFactory()

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        form = RockSampleForm()

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
        editor = UserFactory(is_active=True)
        ContributionFactory(
            content_object=sample, contributor=editor, level=ContributionLevel.EDIT
        )

        assert "dataset" not in self._form(sample, editor).fields

    def test_an_editors_post_cannot_move_the_sample(self):
        sample = RockSampleFactory(name="Original")
        elsewhere = DatasetFactory()
        editor = UserFactory(is_active=True)
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
        manager = UserFactory(is_active=True)
        ContributionFactory(
            content_object=sample, contributor=manager, level=ContributionLevel.MANAGE
        )
        ContributionFactory(
            content_object=sample.dataset,
            contributor=manager,
            level=ContributionLevel.MANAGE,
        )

        assert "dataset" in self._form(sample, manager).fields


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

    def test_a_value_that_cannot_be_used_is_refused_and_nothing_is_saved(
        self, sample_editor
    ):
        sample, client, _ = sample_editor
        url, payload = edit_page(client, sample)
        payload.update(location_first="91", location_second="8.4115")

        response = client.post(url, payload)

        assert response.status_code == 200
        assert "location" in response.context["form"].errors
        stored = RockSample.objects.get(pk=sample.pk)
        assert stored.location is None
        assert stored.location_elevation is None
        assert stored.location_uncertainty is None
