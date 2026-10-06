"""Unit tests for Measurement forms."""

import pytest
from django import forms
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from demo.models import ExampleMeasurement, XRFMeasurement
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.measurement.forms import MeasurementFormMixin
from fairdm.factories import (
    ContributionFactory,
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
class TestMeasurementFormRendering:
    def test_form_renders_with_all_base_fields(self):

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample", "element", "concentration_ppm"]

        form = XRFMeasurementForm()

        assert "name" in form.fields
        assert "dataset" in form.fields
        assert "sample" in form.fields
        assert "element" in form.fields
        assert "concentration_ppm" in form.fields

    def test_form_mixin_provides_preconfigured_widgets(self):

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        form = XRFMeasurementForm()

        assert hasattr(form.fields["dataset"].widget, "attrs")
        assert hasattr(form.fields["sample"].widget, "attrs")


@pytest.mark.django_db
class TestMeasurementFormQuerysetFiltering:
    def test_form_filters_dataset_queryset_by_user_permissions(self):
        user = PersonFactory()
        project = ProjectFactory()
        project.add_contributor(user)

        _accessible_dataset = DatasetFactory(project=project)
        _other_dataset = DatasetFactory()

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        class MockRequest:
            def __init__(self, user):
                self.user = user

        request = MockRequest(user)
        form = XRFMeasurementForm(request=request)

        assert hasattr(form, "request")

    def test_form_filters_sample_queryset_by_dataset(self):
        dataset1 = DatasetFactory()
        dataset2 = DatasetFactory()

        sample1 = RockSampleFactory(dataset=dataset1)
        _sample2 = RockSampleFactory(dataset=dataset2)

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        form = XRFMeasurementForm(data={"dataset": dataset1.pk})

        assert hasattr(form.fields["sample"].widget, "attrs")


@pytest.mark.django_db
class TestMeasurementFormDatasetChoices:
    def test_form_with_a_user_offers_exactly_that_users_datasets(self):
        user = UserFactory()
        allowed = DatasetFactory()  # private by default
        other = DatasetFactory()
        ContributionFactory(
            content_object=allowed, contributor=user, level=ContributionLevel.EDIT
        )

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

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

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

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

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        form = XRFMeasurementForm(request=_request_for(user))

        assert set(form.fields["dataset"].queryset) == {inside}

    def test_a_stored_guardian_row_alone_offers_no_dataset(self):
        from fairdm.core.utils import assign_perm

        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("change_dataset", user, dataset)

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        form = XRFMeasurementForm(request=_request_for(user))

        assert set(form.fields["dataset"].queryset) == set()

    def test_form_with_no_user_offers_no_dataset_at_all(self):
        DatasetFactory()
        DatasetFactory()

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

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

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

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
class TestMeasurementFormValidation:
    def test_form_validates_required_fields(self):

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        form = XRFMeasurementForm(data={})
        assert not form.is_valid()
        assert "name" in form.errors
        assert "dataset" in form.errors
        assert "sample" in form.errors

    def test_form_prevents_base_measurement_instantiation(self):
        from fairdm.core.measurement.forms import MeasurementForm

        dataset = DatasetFactory()
        sample = RockSampleFactory(dataset=dataset)

        form_data = {
            "name": "Test Measurement",
            "dataset": dataset.pk,
            "sample": sample.pk,
        }

        form = MeasurementForm(data=form_data)

        assert not form.is_valid()
        non_field_errors = " ".join(form.errors.get("__all__", []))
        assert "subclass" in non_field_errors or "directly" in non_field_errors


@pytest.mark.django_db
class TestMeasurementFormPolymorphicHandling:
    def test_form_handles_polymorphic_type_creation(self):
        user = UserFactory()
        dataset = DatasetFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        sample = RockSampleFactory(dataset=dataset)

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample", "element", "concentration_ppm"]

        form_data = {
            "name": "XRF Test",
            "dataset": dataset.pk,
            "sample": sample.pk,
            "element": "Fe",
            "concentration_ppm": "25.5",
        }

        form = XRFMeasurementForm(data=form_data, request=_request_for(user))
        assert form.is_valid(), f"Form errors: {form.errors}"

        instance = form.save()
        assert isinstance(instance, XRFMeasurement)
        assert instance.name == "XRF Test"

    def test_form_handles_cross_dataset_sample_reference(self):
        user = UserFactory()
        dataset1 = DatasetFactory()
        dataset2 = DatasetFactory()
        ContributionFactory(
            content_object=dataset1, contributor=user, level=ContributionLevel.EDIT
        )
        sample_in_dataset2 = RockSampleFactory(dataset=dataset2)

        class ExampleMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = ExampleMeasurement
                fields = ["name", "dataset", "sample", "decimal_field", "float_field"]

        form_data = {
            "name": "Cross-dataset Measurement",
            "dataset": dataset1.pk,
            "sample": sample_in_dataset2.pk,
            "decimal_field": "42.0",
            "float_field": "1.5",
        }

        form = ExampleMeasurementForm(data=form_data, request=_request_for(user))
        assert form.is_valid(), f"Form errors: {form.errors}"

        instance = form.save()
        assert instance.dataset == dataset1
        assert instance.sample == sample_in_dataset2
        assert instance.sample.dataset == dataset2


@pytest.mark.django_db
class TestMeasurementFormHelperConfiguration:
    def test_form_has_crispy_forms_helper(self):

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        form = XRFMeasurementForm()

        assert hasattr(form, "helper")
        assert form.helper.form_tag is False


@pytest.mark.django_db
class TestMeasurementFormRequestContext:
    def test_form_accepts_request_parameter(self):

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        class MockRequest:
            def __init__(self):
                self.user = None

        request = MockRequest()
        form = XRFMeasurementForm(request=request)

        assert form.request == request


@pytest.mark.django_db
class TestMeasurementFormDatasetAddAnotherUrl:
    def test_add_related_url_resolves_to_the_dataset_admin_add_view(self):
        from django.urls import reverse

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        form = XRFMeasurementForm()

        # `str()` is what forces the lazy proxy to resolve, the same way
        # template rendering would. The dataset app's label is "dataset",
        # not "core", so "admin:core_dataset_add" raises `NoReverseMatch`
        # here.
        add_url = str(form.fields["dataset"].widget.add_related_url)
        assert add_url == reverse("admin:dataset_dataset_add")
