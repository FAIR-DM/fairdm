"""Forms for the Measurement app (T011, T012 - Phase 6)."""

from crispy_forms.helper import FormHelper
from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django_addanother.widgets import AddAnotherWidgetWrapper
from django_select2.forms import ModelSelect2Widget

from .models import Measurement


class MeasurementFormMixin:
    """Mixin providing pre-configured widgets and behavior for Measurement forms.

    This mixin provides standard widget configurations and request handling
    for forms based on Measurement model. It's designed to be used with ModelForm
    subclasses for concrete measurement types (XRFMeasurement, ICP_MS_Measurement, etc.).

    Features:
        - Pre-configured widgets (Select2 for dataset and sample)
        - Request parameter handling for queryset filtering
        - Dataset-scoped sample selection
        - Crispy forms integration
        - Add another functionality for dataset field

    See Also:
        - Developer Guide: docs/portal-development/measurements.md#step-4-custom-forms-and-filters
        - Forms Documentation: docs/portal-development/forms-and-filters/

    Usage:
        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample", "element", "concentration_ppm"]

        # In view:
        form = XRFMeasurementForm(request=request, data=request.POST)
    """

    def __init__(self, *args, **kwargs):
        """Initialize form with optional request context.

        Args:
            request: Optional request object for permission-based filtering
            *args: Positional arguments passed to ModelForm
            **kwargs: Keyword arguments passed to ModelForm
        """
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # Configure widgets for common Measurement fields
        if "dataset" in self.fields:
            # Use Select2 with autocomplete and add another functionality
            select2_widget = ModelSelect2Widget(
                search_fields=["name__icontains", "title__icontains"],
                attrs={"data-placeholder": _("Select a dataset...")},
            )
            self.fields["dataset"].widget = AddAnotherWidgetWrapper(
                select2_widget,
                add_related_url=reverse_lazy("admin:core_dataset_add"),
            )

            # Filter dataset queryset based on user permissions
            if (
                self.request
                and hasattr(self.request, "user")
                and self.request.user is not None
                and self.request.user.is_authenticated
            ):
                # Filter to datasets where user has change_dataset permission
                from guardian.shortcuts import get_objects_for_user

                self.fields["dataset"].queryset = get_objects_for_user(
                    self.request.user,
                    "dataset.change_dataset",
                    klass=self.fields["dataset"].queryset.model,
                )

        if "sample" in self.fields:
            # Use Select2 for sample with dataset-scoped filtering
            # Note: This provides the widget; actual filtering is done via JavaScript
            # based on the selected dataset value
            self.fields["sample"].widget = ModelSelect2Widget(
                search_fields=["name__icontains"],
                attrs={
                    "data-placeholder": _("Select a sample..."),
                    "data-depends-on": "dataset",  # Hint for JavaScript filtering
                },
            )

        # Initialize crispy forms helper
        self.helper = FormHelper()
        self.helper.form_tag = False


class MeasurementForm(MeasurementFormMixin, forms.ModelForm):
    """Base form for creating and editing Measurement instances.

    This form should typically NOT be used directly since Measurement is an abstract
    polymorphic model. Instead, create forms for concrete measurement types
    (XRFMeasurement, ICP_MS_Measurement, etc.) that inherit from MeasurementFormMixin.

    This class exists for registry auto-generation and as a reference
    implementation.

    Note:
        Direct instantiation will fail validation since Measurement cannot be
        instantiated directly. Use concrete subclass forms instead.
    """

    class Meta:
        model = Measurement
        fields = [
            "name",
            "dataset",
            "sample",
            "image",
            "tags",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter measurement name..."),
                }
            ),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }
        help_text = {
            "name": _("A unique, descriptive name for this measurement."),
            "dataset": _("The dataset this measurement belongs to."),
            "sample": _("The sample that was measured (can be from a different dataset)."),
            "image": _("Optional image or diagram of the measurement."),
            "tags": _("Keywords or tags for categorization."),
        }

    def clean(self):
        """Validate form data.

        Raises:
            ValidationError: If attempting to create base Measurement instance
        """
        cleaned_data = super().clean()

        # Prevent direct Measurement instantiation
        if not self.instance.pk and self._meta.model == Measurement:
            raise forms.ValidationError(
                _("Cannot create base Measurement instances directly. Please use a specific measurement type subclass.")
            )

        return cleaned_data
