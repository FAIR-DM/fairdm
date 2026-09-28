"""Unit tests for Sample forms."""

import pytest
from django import forms
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from guardian.shortcuts import assign_perm

from demo.models import RockSample, WaterSample
from fairdm.core.sample.forms import SampleFormMixin
from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)

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

        assert form.fields["status"].initial == "unknown"


@pytest.mark.django_db
class TestSampleFormPolymorphicHandling:
    def test_form_handles_polymorphic_type_creation(self):
        from datetime import date

        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("change_dataset", user, dataset)

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
        assign_perm("change_dataset", user, dataset)
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
        from django_addanother.widgets import AddAnotherWidgetWrapper
        from django_select2.forms import ModelSelect2Widget

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "status", "location"]

        return RockSampleForm(), AddAnotherWidgetWrapper, ModelSelect2Widget

    def test_dataset_field_uses_the_add_another_wrapped_select2_widget(self):
        form, AddAnotherWidgetWrapper, ModelSelect2Widget = self._form()

        widget = form.fields["dataset"].widget
        assert isinstance(widget, AddAnotherWidgetWrapper)
        assert isinstance(widget.widget, ModelSelect2Widget)

    def test_status_field_uses_a_select_widget(self):
        form, _, _ = self._form()

        assert isinstance(form.fields["status"].widget, forms.Select)

    def test_location_field_uses_a_select2_widget(self):
        form, _, ModelSelect2Widget = self._form()

        assert isinstance(form.fields["location"].widget, ModelSelect2Widget)


@pytest.mark.django_db
class TestSampleFormDatasetChoices:
    def test_form_with_a_user_offers_exactly_that_users_datasets(self):
        user = UserFactory()
        allowed = DatasetFactory()
        other = DatasetFactory()
        assign_perm("change_dataset", user, allowed)

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
class TestSampleFormDatasetAddAnotherUrl:
    # reverse_lazy defers evaluation, so a wrong URL name only surfaces once the
    # widget renders.
    def test_add_related_url_resolves_to_the_dataset_admin_add_view(self):
        from django.urls import reverse

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        form = RockSampleForm()

        # `str()` is what forces the lazy proxy to resolve, the same way
        # template rendering would. The dataset app's label is "dataset", not
        # "core", so "admin:core_dataset_add" raises `NoReverseMatch` here.
        add_url = str(form.fields["dataset"].widget.add_related_url)
        assert add_url == reverse("admin:dataset_dataset_add")
