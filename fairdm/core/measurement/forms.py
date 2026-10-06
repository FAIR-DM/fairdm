"""Forms for creating and editing measurements."""

from crispy_forms.helper import FormHelper
from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django_addanother.widgets import AddAnotherWidgetWrapper
from django_select2.forms import ModelSelect2Widget
from easy_thumbnails.widgets import ImageClearableFileInput

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.image_utils import IMAGE_HELP_TEXT, validate_image_file_size

from .models import Measurement


class MeasurementFormMixin:
    """Mixin giving measurement model forms Select2 widgets for dataset and sample.

    Use it with the ``ModelForm`` of a concrete measurement type. The dataset choices are limited
    to the datasets the requesting user may change. See docs/portal-development/measurements.md.

    Args:
        *args: Positional arguments passed to ``ModelForm``.
        **kwargs: Keyword arguments passed to ``ModelForm``. ``request`` is removed first and
            is used to limit the dataset choices.

    Example:
        ```python
        class XRFMeasurementForm(MeasurementFormMixin, forms.ModelForm):
            class Meta:
                model = XRFMeasurement
                fields = ["name", "dataset", "sample", "element", "concentration_ppm"]


        form = XRFMeasurementForm(request=request, data=request.POST)
        ```
    """

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if "dataset" in self.fields:
            select2_widget = ModelSelect2Widget(
                search_fields=["name__icontains", "title__icontains"],
                attrs={"data-placeholder": _("Select a dataset...")},
            )
            self.fields["dataset"].widget = AddAnotherWidgetWrapper(
                select2_widget,
                add_related_url=reverse_lazy("admin:dataset_dataset_add"),
            )

            from fairdm.core.dataset.models import Dataset

            # `all_objects` is only the base the permission check narrows. A caller that omits the
            # optional `request` keeps the privacy-first default queryset, never every private dataset.
            if (
                self.request
                and hasattr(self.request, "user")
                and self.request.user is not None
                and self.request.user.is_authenticated
            ):
                self.fields["dataset"].queryset = Dataset.all_objects.accessible_to(
                    self.request.user, ContributionLevel.EDIT
                )

        if "sample" in self.fields:
            # The sample choices are filtered by JavaScript, from the selected dataset.
            self.fields["sample"].widget = ModelSelect2Widget(
                search_fields=["name__icontains"],
                attrs={
                    "data-placeholder": _("Select a sample..."),
                    "data-depends-on": "dataset",
                },
            )

        self.helper = FormHelper()
        self.helper.form_tag = False


class MeasurementForm(MeasurementFormMixin, forms.ModelForm):
    """Base form for measurements, which refuses to create a bare ``Measurement``.

    ``Measurement`` is a concrete polymorphic base with its own table, but direct instantiation
    is refused here and in ``Measurement.clean()``. Build forms for concrete measurement types on
    ``MeasurementFormMixin`` instead. This class exists for registry auto-generation and as a
    reference implementation.
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
        }
        help_texts = {
            "name": _("A unique, descriptive name for this measurement."),
            "dataset": _("The dataset this measurement belongs to."),
            "sample": _(
                "The sample that was measured (can be from a different dataset)."
            ),
            "tags": _("Keywords or tags for categorization."),
        }

    def clean(self):
        """Refuse to create a bare ``Measurement``."""
        cleaned_data = super().clean()

        if not self.instance.pk and self._meta.model == Measurement:
            raise forms.ValidationError(
                _(
                    "Cannot create base Measurement instances directly. Please use a specific measurement type subclass."
                )
            )

        return cleaned_data
