from crispy_forms.bootstrap import InlineRadios
from crispy_forms.helper import FormHelper, Layout
from django import forms
from django.utils.translation import gettext as _
from easy_thumbnails.widgets import ImageClearableFileInput

from fairdm.contrib.contributors.models import Organization
from fairdm.core.choices import ProjectStatus
from fairdm.core.image_utils import IMAGE_HELP_TEXT, validate_image_file_size
from fairdm.forms import ModelForm
from fairdm.utils.choices import Visibility

from .models import Project


class ProjectForm(ModelForm):
    """Base form for Project instances.

    Centralises all field declarations, help_texts, and widgets. Used directly
    by the update view and subclassed by ProjectCreateForm.
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
    name = forms.CharField(
        label=_("Project name"),
        max_length=255,
        help_text=_("A clear, descriptive name for your project."),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    status = forms.TypedChoiceField(
        label=_("Status"),
        choices=ProjectStatus.choices,
        coerce=int,
        help_text=_("Current phase of the project lifecycle."),
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    visibility = forms.TypedChoiceField(
        label=_("Visibility"),
        choices=Visibility.choices,
        coerce=int,
        initial=Visibility.PUBLIC,
        help_text=_("Who can view this project?"),
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
    owner: forms.ModelChoiceField = forms.ModelChoiceField(
        label=_("Owner organization"),
        queryset=None,  # Set in __init__
        help_text=_("The organization that owns this project."),
        widget=forms.Select(attrs={"class": "form-control"}),
        required=False,
    )

    class Meta:
        model = Project
        fields = ["image", "name", "status", "visibility", "owner"]

    def __init__(self, *args, **kwargs):
        """Initialize form and set owner queryset if the field is present."""
        super().__init__(*args, **kwargs)
        if "owner" in self.fields:
            self.fields["owner"].queryset = Organization.objects.all()

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            "image",
            "name",
            "status",
            InlineRadios("visibility"),
            "owner",
        )


class ProjectCreateForm(ProjectForm):
    """Streamlined form for creating new Project instances.

    Restricts fields to the minimum required for project creation. Users can
    add detailed metadata through the edit interface after creation.
    """

    class Meta(ProjectForm.Meta):
        fields = ["name", "status", "visibility"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            "name",
            "status",
            InlineRadios(
                "visibility"
            ),  # BUG: Inline radios is causing a layout error with crispy forms. Submit buttons render inside the radio group. Need to investigate and fix this issue.
        )
