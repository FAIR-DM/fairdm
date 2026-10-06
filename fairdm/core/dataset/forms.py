"""Forms for creating and editing datasets."""

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.widgets import ImageClearableFileInput
from licensing.models import License

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.forms import ManagerOnlyFieldsMixin
from fairdm.core.image_utils import IMAGE_HELP_TEXT, validate_image_file_size
from fairdm.core.models import Project
from fairdm.forms import ModelForm
from fairdm.utils.choices import Visibility

from .models import Dataset


class DatasetForm(ManagerOnlyFieldsMixin, ModelForm):
    """Form for creating and editing a dataset.

    With a request, the project field offers only the authenticated user's own projects, and an
    anonymous user sees none. Without one, every project is offered. The licence defaults to
    CC BY 4.0, or the ``FAIRDM_DEFAULT_LICENSE`` setting. External identifiers are edited as rows
    on the update page, not through a field here.

    Args:
        request: The current request, used to limit the project choices.
        *args: Positional arguments passed to ``ModelForm``.
        **kwargs: Keyword arguments passed to ``ModelForm``, such as ``instance``.

    Attributes:
        image: Optional cover image.
        name: The dataset's name.
        project: The project the dataset belongs to.
        license: The licence the dataset's data is published under.
        reference: The literature item that is the dataset's data publication.
        visibility: Whether the dataset's metadata may be read by anyone using the portal.
    """

    image = forms.ImageField(
        required=False,
        label=_("Cover Image"),
        help_text=IMAGE_HELP_TEXT,
        validators=[validate_image_file_size],
        widget=ImageClearableFileInput(
            thumbnail_options={"size": (150, 100), "crop": True}
        ),
    )

    name = forms.CharField(
        label=_("Name"),
        help_text=_(
            "Give your dataset a descriptive name that reflects its purpose and content. "
            "This will help others discover and understand your data."
        ),
        required=True,
        max_length=300,
    )

    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        label=_("Project"),
        help_text=_(
            "Select the research project this dataset belongs to. Datasets can be "
            "organized under projects for better management."
        ),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    license = forms.ModelChoiceField(
        queryset=License.objects.all(),
        label=_("License"),
        help_text=_(
            "Choose a license that defines how others can use this dataset. "
            "CC BY 4.0 (default) allows sharing and adaptation with attribution. "
            "You can change this until the dataset is published."
        ),
    )

    # The queryset is set in __init__ to avoid AppRegistryNotReady.
    reference: forms.ModelChoiceField = forms.ModelChoiceField(
        queryset=None,
        label=_("Data Publication"),
        help_text=_(
            "Link to the primary data publication (paper, report, or other literature) "
            "that describes this dataset."
        ),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    visibility = forms.TypedChoiceField(
        label=_("Visibility"),
        choices=Visibility.choices,
        coerce=int,
        initial=Visibility.PUBLIC,
        help_text=_(
            "Whether this dataset's metadata may be read by anyone using the portal. "
            "The data held beneath the dataset is governed separately."
        ),
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Dataset
        fields = ["image", "name", "project", "license", "reference", "visibility"]
        # The update page already opens a `<form>`, so the crispy helper must not nest another.
        helper_attrs = {"form_tag": False}

    manager_only_fields = ("visibility", "project")

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.withhold_manager_only_fields(request)

        # Read at call time, not as a module constant, so `override_settings` is honoured.
        license_field = self.fields.get("license")
        if license_field:
            default_license_name = getattr(
                settings, "FAIRDM_DEFAULT_LICENSE", "CC BY 4.0"
            )
            license_field.initial = License.objects.filter(
                name=default_license_name
            ).first()

        project_field = self.fields.get("project")
        if project_field and self.request:
            if (
                hasattr(self.request, "user")
                and self.request.user is not None
                and self.request.user.is_authenticated
            ):
                project_field.queryset = Project.objects.accessible_to(
                    self.request.user, ContributionLevel.EDIT
                )
            else:
                project_field.queryset = Project.objects.none()

        # The literature app is optional.
        reference_field = self.fields.get("reference")
        if reference_field:
            try:
                from literature.models import LiteratureItem

                reference_field.queryset = LiteratureItem.objects.all()
            except (ImportError, LookupError):
                from django.apps import apps

                try:
                    LiteratureItem = apps.get_model("literature", "LiteratureItem")
                    reference_field.queryset = LiteratureItem.objects.all()
                except LookupError:
                    del self.fields["reference"]
                    if hasattr(self.Meta, "fields") and "reference" in self.Meta.fields:
                        self.Meta.fields = [
                            f for f in self.Meta.fields if f != "reference"
                        ]


class DatasetCreateForm(DatasetForm):
    """Form for creating a dataset, asking only for name, project, licence and visibility.

    The other fields are available after creation on the update page.

    Args:
        request: The current request, used to limit the project choices.
        *args: Positional arguments passed to ``DatasetForm``.
        **kwargs: Keyword arguments passed to ``DatasetForm``.
    """

    class Meta(DatasetForm.Meta):
        fields = ["name", "project", "license", "visibility"]
