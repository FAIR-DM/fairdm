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
    """Mixin giving sample model forms Select2 widgets for dataset and location.

    Use it with the ``ModelForm`` of a concrete sample type. The dataset choices are the datasets
    the requesting user may change. A form given no authenticated user offers no dataset at all,
    which is the safe default, and logs a warning because a create form that can never validate
    explains nothing on its own. The status defaults to ``unknown``, matching the model default,
    so a form never asserts where a specimen is when nobody chose.

    Args:
        *args: Positional arguments passed to ``ModelForm``.
        **kwargs: Keyword arguments passed to ``ModelForm``. ``request`` is removed first and
            is used to limit the dataset choices.

    Example:
        ```python
        class RockSampleForm(SampleFormMixin, forms.ModelForm):
            class Meta:
                model = RockSample
                fields = ["name", "dataset", "rock_type"]


        form = RockSampleForm(request=request, data=request.POST)
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

            # `all_objects` is only the base the permission check narrows. Assigning it
            # unconditionally would offer every private dataset to a caller that proved nothing.
            if (
                self.request
                and hasattr(self.request, "user")
                and self.request.user.is_authenticated
            ):
                from guardian.shortcuts import get_objects_for_user

                self.fields["dataset"].queryset = get_objects_for_user(
                    self.request.user,
                    "dataset.change_dataset",
                    klass=Dataset.all_objects.all(),
                )
            else:
                logger.warning(
                    "%s offers no dataset choices: no request (or no authenticated "
                    "user on it) was passed, so FR-036's safe default excludes every "
                    "dataset, including public ones.",
                    type(self).__name__,
                )
                self.fields["dataset"].queryset = Dataset.objects.none()

        if "status" in self.fields:
            self.fields["status"].widget = forms.Select(attrs={"class": "form-select"})
            self.fields["status"].initial = "unknown"

        if "location" in self.fields:
            self.fields["location"].widget = ModelSelect2Widget(
                search_fields=["name__icontains"],
                attrs={"data-placeholder": _("Select a location...")},
            )

        self.helper = FormHelper()
        self.helper.form_tag = False


class SampleForm(SampleFormMixin, forms.ModelForm):
    """Base form for samples, which refuses to create a bare ``Sample``.

    Build forms for concrete sample types on ``SampleFormMixin`` instead. This class exists for
    registry auto-generation and as a reference implementation.
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
        """Refuse to create a bare ``Sample``."""
        cleaned_data = super().clean()

        if not self.instance.pk and self._meta.model == Sample:
            raise forms.ValidationError(
                _(
                    "Cannot create base Sample instances directly. Please use a specific sample type subclass."
                )
            )

        return cleaned_data
