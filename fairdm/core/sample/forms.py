"""Forms for the Sample app."""

import logging

from crispy_forms.helper import FormHelper
from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django_addanother.widgets import AddAnotherWidgetWrapper
from django_select2.forms import ModelSelect2Widget
from easy_thumbnails.widgets import ImageClearableFileInput

from fairdm.core.image_utils import IMAGE_HELP_TEXT, validate_image_file_size

from .models import Sample

logger = logging.getLogger(__name__)


class SampleFormMixin:
    """Mixin providing pre-configured widgets and behavior for Sample forms.

    This mixin provides standard widget configurations and request handling
    for forms based on Sample model. It's designed to be used with ModelForm
    subclasses for concrete sample types (RockSample, WaterSample, etc.).

    Features:
        - Pre-configured widgets (Select2 for dataset, Select for status)
        - Request parameter handling for queryset filtering
        - Default status value ('available')
        - Crispy forms integration
        - Add another functionality for dataset field

    Usage:
        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "rock_type"]

        # In view:
        form = RockSampleForm(request=request, data=request.POST)
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

        # Configure widgets for common Sample fields
        if "dataset" in self.fields:
            # Use Select2 with autocomplete and add another functionality
            select2_widget = ModelSelect2Widget(
                search_fields=["name__icontains", "title__icontains"],
                attrs={"data-placeholder": _("Select a dataset...")},
            )
            self.fields["dataset"].widget = AddAnotherWidgetWrapper(
                select2_widget,
                add_related_url=reverse_lazy("admin:dataset_dataset_add"),
            )

            from fairdm.core.dataset.models import Dataset

            # FR-036: a form given no user offers no dataset at all - the safe
            # default for a published package, and the only offer nothing
            # could satisfy or test. `all_objects` is only ever the base the
            # permission check below narrows, never the queryset the form is
            # left holding. Assigning `all_objects` unconditionally would have
            # offered every private dataset in the portal to a caller that had
            # proven nothing.
            if (
                self.request
                and hasattr(self.request, "user")
                and self.request.user.is_authenticated
            ):
                # Filter to datasets where the user holds change_dataset
                from guardian.shortcuts import get_objects_for_user

                self.fields["dataset"].queryset = get_objects_for_user(
                    self.request.user,
                    "dataset.change_dataset",
                    klass=Dataset.all_objects.all(),
                )
            else:
                # F13: the security argument for offering nothing is right, but the failure
                # mode - a create form that can never validate - explains nothing on its own.
                # Loud rather than silent.
                logger.warning(
                    "%s offers no dataset choices: no request (or no authenticated "
                    "user on it) was passed, so FR-036's safe default excludes every "
                    "dataset, including public ones.",
                    type(self).__name__,
                )
                self.fields["dataset"].queryset = Dataset.objects.none()

        if "status" in self.fields:
            # Use Select widget for status
            self.fields["status"].widget = forms.Select(attrs={"class": "form-select"})
            # F10: matches Sample.status's own model default ("unknown", FR-022) - a form
            # must not assert where a specimen physically is on the strength of nobody
            # having chosen.
            self.fields["status"].initial = "unknown"

        if "location" in self.fields:
            # Use Select2 for location
            self.fields["location"].widget = ModelSelect2Widget(
                search_fields=["name__icontains"],
                attrs={"data-placeholder": _("Select a location...")},
            )

        # Initialize crispy forms helper
        self.helper = FormHelper()
        self.helper.form_tag = False


class SampleForm(SampleFormMixin, forms.ModelForm):
    """Base form for creating and editing Sample instances.

    This form should typically NOT be used directly since Sample is an abstract
    polymorphic model. Instead, create forms for concrete sample types
    (RockSample, WaterSample, etc.) that inherit from SampleFormMixin.

    This class exists for registry auto-generation and as a reference
    implementation.

    Note:
        Direct instantiation will fail validation since Sample cannot be
        instantiated directly. Use concrete subclass forms instead.
    """

    image = forms.ImageField(
        required=False,
        label="",
        help_text=IMAGE_HELP_TEXT,
        validators=[validate_image_file_size],
        widget=ImageClearableFileInput(
            thumbnail_options={"size": (150, 100), "crop": True}
        ),
    )

    class Meta:
        model = Sample
        fields = [
            "name",
            "dataset",
            "local_id",
            "status",
            "location",
            "image",
            "tags",
            "related",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Enter sample name..."),
                }
            ),
            "local_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Optional local identifier..."),
                }
            ),
        }
        help_texts = {
            "name": _("A unique, descriptive name for this sample."),
            "dataset": _("The dataset this sample belongs to."),
            "local_id": _(
                "Optional local identifier used in your laboratory or collection."
            ),
            "status": _("Current status of the sample."),
            "location": _("Geographic location where the sample was collected."),
            "tags": _("Keywords or tags for categorization."),
            "related": _("Related samples (parent-child relationships)."),
        }

    def clean(self):
        """Validate form data.

        Raises:
            ValidationError: If attempting to create base Sample instance
        """
        cleaned_data = super().clean()

        # Prevent direct Sample instantiation
        if not self.instance.pk and self._meta.model == Sample:
            raise forms.ValidationError(
                _(
                    "Cannot create base Sample instances directly. Please use a specific sample type subclass."
                )
            )

        return cleaned_data
