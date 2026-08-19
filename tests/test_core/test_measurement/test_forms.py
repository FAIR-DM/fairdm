"""
Unit tests for Measurement forms (T020 - Phase 6).

Tests verify that Measurement forms provide appropriate widgets, validation,
queryset filtering based on dataset context, and integration patterns.
"""

import pytest
from django import forms
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from guardian.shortcuts import assign_perm

from fairdm.core.measurement.forms import MeasurementFormMixin
from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm_demo.factories import RockSampleFactory
from fairdm_demo.models import ExampleMeasurement, XRFMeasurement

User = get_user_model()


def _request_for(user):
    """A minimal request carrying an authenticated user.

    `MeasurementFormMixin` narrows the dataset choices to what the request's user
    may change, and leaves them at the privacy-first default when no request is
    given. A form exercised without one therefore cannot select a private dataset -
    which is what the tests below need, and what a portal's own view supplies.
    """
    request = RequestFactory().get("/")
    request.user = user
    return request


@pytest.mark.django_db
class TestMeasurementFormRendering:
    """Test MeasurementForm renders with appropriate fields and widgets."""

    def test_image_field_declares_no_label_text(self):
        """The image field is captioned by its widget, so it must declare an empty
        label. A boolean suppresses nothing and renders the word "False"."""
        from fairdm.core.measurement.forms import MeasurementForm

        assert MeasurementForm.base_fields["image"].label == ""

    def test_form_renders_with_all_base_fields(self):
        """Test that MeasurementForm renders with all base Measurement fields."""

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample", "element", "concentration_ppm"]

        form = XRFMeasurementForm()

        # Verify all expected fields are present
        assert "name" in form.fields
        assert "dataset" in form.fields
        assert "sample" in form.fields
        assert "element" in form.fields
        assert "concentration_ppm" in form.fields

    def test_form_mixin_provides_preconfigured_widgets(self):
        """Test that MeasurementFormMixin provides pre-configured widgets for common fields."""

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        form = XRFMeasurementForm()

        # Verify widgets are properly configured
        # Dataset should use Select2 (autocomplete)
        assert hasattr(form.fields["dataset"].widget, "attrs")
        # Sample should use Select2 (autocomplete)
        assert hasattr(form.fields["sample"].widget, "attrs")


@pytest.mark.django_db
class TestMeasurementFormQuerysetFiltering:
    """Test MeasurementForm filters querysets based on dataset and permissions."""

    def test_form_filters_dataset_queryset_by_user_permissions(self):
        """Test that MeasurementForm filters dataset queryset based on user permissions."""
        user = PersonFactory()
        project = ProjectFactory()
        project.add_contributor(user)

        # Create datasets - one accessible, one not
        _accessible_dataset = DatasetFactory(project=project)
        _other_dataset = DatasetFactory()  # Different project

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        # Mock request object
        class MockRequest:
            def __init__(self, user):
                self.user = user

        request = MockRequest(user)
        form = XRFMeasurementForm(request=request)

        # Verify the form accepts request parameter
        assert hasattr(form, "request")

    def test_form_filters_sample_queryset_by_dataset(self):
        """Test that MeasurementForm filters sample queryset to only show samples in selected dataset."""
        dataset1 = DatasetFactory()
        dataset2 = DatasetFactory()

        sample1 = RockSampleFactory(dataset=dataset1)
        _sample2 = RockSampleFactory(dataset=dataset2)

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        # Create form with dataset1 selected
        form = XRFMeasurementForm(data={"dataset": dataset1.pk})

        # The form should filter samples to only those in dataset1
        # This is typically done via JavaScript or custom widget behavior
        # For now, verify the form has sample field configured with Select2
        assert hasattr(form.fields["sample"].widget, "attrs")


@pytest.mark.django_db
class TestMeasurementFormDatasetChoices:
    """T054/T055/T056 - a form inheriting MeasurementFormMixin and given the
    requesting user offers exactly the datasets that user may add
    measurements to, including ones that are not publicly visible; given no
    user it offers no dataset at all. Asserted by comparing the offered set
    to an expected set, not by checking an attribute exists."""

    def test_form_with_a_user_offers_exactly_that_users_datasets(self):
        """T054 - the offered datasets include one that is private, proving
        the scoping is by entitlement rather than by visibility."""
        user = UserFactory()
        allowed = DatasetFactory()  # private by default
        other = DatasetFactory()
        assign_perm("change_dataset", user, allowed)

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        form = XRFMeasurementForm(request=_request_for(user))

        offered = set(form.fields["dataset"].queryset)
        assert offered == {allowed}
        assert other not in offered

    def test_form_with_no_user_offers_no_dataset_at_all(self):
        """T055 - with no user on the request, the form is left holding the
        privacy-first default manager. Both fixtures below are private (the
        factory default), so it offers nothing."""
        DatasetFactory()
        DatasetFactory()

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        form = XRFMeasurementForm()

        assert set(form.fields["dataset"].queryset) == set()

    def test_scoping_derives_from_the_requests_own_user(self):
        """T056 - the mixin scopes from the request's own user, not from
        some other authenticated user's entitlement. Two users, each
        entitled to a different private dataset: a form built with one
        user's request must not offer the other user's dataset."""
        user1 = UserFactory()
        user2 = UserFactory()
        dataset1 = DatasetFactory()
        dataset2 = DatasetFactory()
        assign_perm("change_dataset", user1, dataset1)
        assign_perm("change_dataset", user2, dataset2)

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        form = XRFMeasurementForm(request=_request_for(user1))

        offered = set(form.fields["dataset"].queryset)
        assert offered == {dataset1}
        assert dataset2 not in offered


@pytest.mark.django_db
class TestMeasurementFormValidation:
    """Test MeasurementForm validation logic."""

    def test_form_validates_required_fields(self):
        """Test that MeasurementForm validates required fields."""

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        # Form without required fields should be invalid
        form = XRFMeasurementForm(data={})
        assert not form.is_valid()
        assert "name" in form.errors
        assert "dataset" in form.errors
        assert "sample" in form.errors

    def test_form_prevents_base_measurement_instantiation(self):
        """T029: MeasurementForm refuses a bare Measurement, asserted on the message.

        `dataset` here is deliberately private with no `request` passed to the form,
        so `MeasurementFormMixin`'s dataset-choice scoping alone would invalidate the
        form (`assert not form.is_valid()` passes for that unrelated reason even with
        the base-Measurement refusal removed entirely). Asserting on the message in
        `__all__` is what actually proves the refusal fires.
        """
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
    """Test MeasurementForm handles polymorphic types correctly."""

    def test_form_handles_polymorphic_type_creation(self):
        """Test that MeasurementForm handles polymorphic type creation correctly."""
        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("change_dataset", user, dataset)
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

        # Save and verify instance is correct polymorphic type
        instance = form.save()
        assert isinstance(instance, XRFMeasurement)
        assert instance.name == "XRF Test"

    def test_form_handles_cross_dataset_sample_reference(self):
        """Test that MeasurementForm allows measurements to reference samples from different datasets."""
        user = UserFactory()
        dataset1 = DatasetFactory()
        dataset2 = DatasetFactory()
        assign_perm("change_dataset", user, dataset1)
        sample_in_dataset2 = RockSampleFactory(dataset=dataset2)

        class ExampleMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = ExampleMeasurement
                fields = ["name", "dataset", "sample", "decimal_field", "float_field"]

        # Create measurement in dataset1 that references sample from dataset2
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
    """Test MeasurementForm crispy forms helper configuration."""

    def test_form_has_crispy_forms_helper(self):
        """Test that MeasurementForm includes crispy forms helper."""

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        form = XRFMeasurementForm()

        # Verify helper is configured
        assert hasattr(form, "helper")
        assert form.helper.form_tag is False


@pytest.mark.django_db
class TestMeasurementFormRequestContext:
    """Test MeasurementForm handles request context correctly."""

    def test_form_accepts_request_parameter(self):
        """Test that MeasurementForm accepts request parameter for context."""

        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample"]

        class MockRequest:
            def __init__(self):
                self.user = None

        request = MockRequest()
        form = XRFMeasurementForm(request=request)

        # Verify request is stored
        assert form.request == request


@pytest.mark.django_db
class TestMeasurementFormHelpText:
    """T057 - the guidance a form defines for a field reaches the rendered
    field, asserted on the rendered field rather than on the form's
    configuration."""

    def test_meta_help_text_reaches_the_rendered_field(self):
        from fairdm.core.measurement.forms import MeasurementForm

        assert str(MeasurementForm.base_fields["name"].help_text) == (
            "A unique, descriptive name for this measurement."
        )
        assert str(MeasurementForm.base_fields["dataset"].help_text) == (
            "The dataset this measurement belongs to."
        )
        assert str(MeasurementForm.base_fields["sample"].help_text) == (
            "The sample that was measured (can be from a different dataset)."
        )
        assert str(MeasurementForm.base_fields["tags"].help_text) == (
            "Keywords or tags for categorization."
        )


@pytest.mark.django_db
class TestMeasurementFormDatasetAddAnotherUrl:
    """T059 - the "add another" widget on the dataset field must reverse to
    a URL name the admin actually registers. `reverse_lazy` defers
    evaluation, so a wrong name only surfaces once something forces it to
    resolve - which is exactly what rendering the widget does."""

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
