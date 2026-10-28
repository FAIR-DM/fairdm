"""Forms for the Sample app."""

import logging

from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext_lazy as _
from mvp_forms.widgets import ImageInput

from fairdm.contrib.autocomplete.fields import DatasetChoiceField
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.forms import ConceptSelectField, ManagerOnlyFieldsMixin
from fairdm.core.image_utils import IMAGE_HELP_TEXT, validate_image_file_size
from fairdm.core.vocabularies import SAMPLE_STATUS_UNKNOWN
from fairdm.utils.location.forms import LocationFormMixin

from .models import Sample

logger = logging.getLogger(__name__)


class SampleFormMixin(LocationFormMixin, ManagerOnlyFieldsMixin):
    """Mixin giving sample model forms the dataset field and the location input.

    Use it with the ``ModelForm`` of a concrete sample type. The dataset choices are the datasets
    the requesting user may edit. For a sample that already exists the dataset is offered only to
    someone who can manage the sample. A form given no authenticated user offers no dataset at all,
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

    manager_only_fields = ("dataset",)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        self.withhold_manager_only_fields(self.request)

        if "dataset" in self.fields:
            current = self.fields["dataset"]
            self.fields["dataset"] = DatasetChoiceField(
                scope="edit",
                label=current.label,
                required=current.required,
                help_text=current.help_text,
            )

            from fairdm.core.dataset.models import Dataset

            # `all_objects` is only the base the level check narrows. Assigning it
            # unconditionally would offer every private dataset to a caller that proved nothing.
            if (
                self.request
                and hasattr(self.request, "user")
                and self.request.user.is_authenticated
            ):
                self.fields["dataset"].queryset = Dataset.all_objects.accessible_to(
                    self.request.user, ContributionLevel.EDIT
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
            # A drop-down of the few custody states, in place of the search box.
            current = self.fields["status"]
            status = Sample._meta.get_field("status").formfield(
                form_class=ConceptSelectField,
                widget=forms.Select(attrs={"class": "form-select"}),
                initial=SAMPLE_STATUS_UNKNOWN,
                label=current.label,
                help_text=current.help_text,
                required=current.required,
            )
            status.queryset = status.queryset.complex_filter(
                status.get_limit_choices_to()
            )
            self.fields["status"] = status

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
        widget=ImageInput(aspect_ratio=3 / 2, show_input=False, height=9),
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
