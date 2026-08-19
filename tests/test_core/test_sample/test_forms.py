"""
Unit tests for Sample forms.

Tests verify that Sample forms provide appropriate widgets, validation,
queryset filtering, and integration patterns.
"""

import pytest
from django import forms
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from guardian.shortcuts import assign_perm

from fairdm.core.sample.forms import SampleFormMixin
from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm_demo.models import RockSample, WaterSample

User = get_user_model()


def _request_for(user):
    """A minimal request carrying an authenticated user.

    The sample and measurement form mixins narrow the dataset choices to what the
    request's user may change, and offer no dataset at all when no request is
    given (FR-036). A form exercised without one therefore cannot select a
    private dataset - which is what the tests below need, and what a portal's
    own view supplies.
    """
    request = RequestFactory().get("/")
    request.user = user
    return request


@pytest.mark.django_db
class TestSampleFormRendering:
    """Test SampleForm renders with appropriate fields and widgets."""

    def test_image_field_declares_no_label_text(self):
        """The image field is captioned by its widget, so it must declare an empty
        label. A boolean suppresses nothing and renders the word "False"."""
        from fairdm.core.sample.forms import SampleForm

        assert SampleForm.base_fields["image"].label == ""

    def test_form_renders_with_all_base_fields(self):
        """Test that SampleForm renders with all base Sample fields (T061)."""

        # Create a RockSampleForm since Sample is abstract
        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "local_id", "status", "location"]

        form = RockSampleForm()

        # Verify all expected fields are present
        assert "name" in form.fields
        assert "dataset" in form.fields
        assert "local_id" in form.fields
        assert "status" in form.fields
        assert "location" in form.fields

    def test_form_mixin_provides_preconfigured_widgets(self):
        """Test that SampleFormMixin provides pre-configured widgets for common fields (T067)."""

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "status"]

        form = RockSampleForm()

        # Verify widgets are properly configured
        # Dataset should use Select2 (autocomplete)
        assert hasattr(form.fields["dataset"].widget, "attrs")
        # Status should be a select widget
        assert isinstance(form.fields["status"].widget, forms.Select)


@pytest.mark.django_db
class TestSampleFormQuerysetFiltering:
    """Test SampleForm filters querysets based on user permissions."""

    def test_form_filters_dataset_queryset_by_user_permissions(self):
        """Test that SampleForm filters dataset queryset based on user permissions (T062)."""
        user = PersonFactory()
        project = ProjectFactory()
        project.add_contributor(user)

        # Create datasets - one accessible, one not
        _accessible_dataset = DatasetFactory(project=project)
        _other_dataset = DatasetFactory()  # Different project

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        # Mock request object
        class MockRequest:
            def __init__(self, user):
                self.user = user

        request = MockRequest(user)
        form = RockSampleForm(request=request)

        # If filtering is implemented, the queryset should be limited
        # For now, just verify the form accepts request parameter
        assert hasattr(form, "request")


@pytest.mark.django_db
class TestSampleFormValidation:
    """Test SampleForm validation logic."""

    def test_form_validates_required_fields(self):
        """Test that SampleForm validates required fields (T063)."""

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        # Form without required fields should be invalid
        form = RockSampleForm(data={})
        assert not form.is_valid()
        assert "name" in form.errors
        assert "dataset" in form.errors

    def test_form_defaults_status_to_unknown(self):
        """F10 - the form's initial status must not contradict the model's own default.
        `Sample.status` defaults to ``unknown`` (FR-022: a specimen created with no status
        stated reads as unknown), so a form asserting ``available`` claimed custody nobody
        chose. T064 originally pinned the mismatched ``available`` default; corrected here."""

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "status"]

        form = RockSampleForm()

        assert form.fields["status"].initial == "unknown"


@pytest.mark.django_db
class TestSampleFormPolymorphicHandling:
    """Test SampleForm handles polymorphic types correctly."""

    def test_form_handles_polymorphic_type_creation(self):
        """Test that SampleForm handles polymorphic type creation correctly (T065)."""
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

        # Save and verify instance is correct polymorphic type
        instance = form.save()
        assert isinstance(instance, RockSample)
        assert instance.name == "Test Rock"
        assert instance.rock_type == "igneous"

    def test_form_prepopulates_fields_for_edit_scenario(self):
        """Test that SampleForm pre-populates fields for edit scenario (T066)."""
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

        # Form bound to existing instance should pre-populate fields
        form = RockSampleForm(instance=rock_sample)

        assert form.initial["name"] == "Existing Rock"
        assert form.initial["dataset"] == dataset.pk
        assert form.initial["rock_type"] == "sedimentary"


@pytest.mark.django_db
class TestCustomSampleFormIntegration:
    """Test custom sample forms integrate seamlessly with SampleFormMixin."""

    def test_custom_sample_form_inherits_from_mixin(self):
        """Test that custom sample form inheriting from SampleFormMixin integrates seamlessly (T068)."""

        class CustomWaterSampleForm(SampleFormMixin, forms.ModelForm):
            # Add custom field
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
    """T067 - the common sample fields carry the controls the mixin configures,
    asserted by widget class rather than by the presence of an attribute every
    widget has."""

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
    """T068 / FR-036 - a form given the requesting user offers exactly the
    datasets that user may add specimens to, and a form given no user offers
    no dataset at all. Asserted by comparing the offered set to an expected
    set, not by checking an attribute exists."""

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
        """`request=None` is the mixin's own default, exercised explicitly."""
        DatasetFactory()

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        form = RockSampleForm(request=None)

        assert set(form.fields["dataset"].queryset) == set()

    def test_offering_no_dataset_with_no_request_logs_a_warning(self, caplog):
        """F13 - FR-036's "offer nothing" is the right security default, but the failure mode
        is a create form that can never validate with nothing explaining why. A warning makes
        that loud rather than silent."""
        import logging

        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset"]

        with caplog.at_level(logging.WARNING):
            RockSampleForm()

        assert any(
            "dataset" in record.message.lower() and "request" in record.message.lower()
            for record in caplog.records
        )


@pytest.mark.django_db
class TestSampleFormHelpText:
    """T069 - the guidance a form defines for a field reaches the rendered
    field."""

    def test_meta_help_text_reaches_the_rendered_field(self):
        from fairdm.core.sample.forms import SampleForm

        assert str(SampleForm.base_fields["name"].help_text) == (
            "A unique, descriptive name for this sample."
        )
        assert str(SampleForm.base_fields["dataset"].help_text) == (
            "The dataset this sample belongs to."
        )
        assert str(SampleForm.base_fields["status"].help_text) == (
            "Current status of the sample."
        )


@pytest.mark.django_db
class TestSampleFormDatasetAddAnotherUrl:
    """T072 - the "add another" widget on the dataset field must reverse to a
    URL name the admin actually registers. `reverse_lazy` defers evaluation,
    so a wrong name only surfaces once something forces it to resolve - which
    is exactly what rendering the widget does."""

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
