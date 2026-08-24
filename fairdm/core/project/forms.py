from crispy_forms.bootstrap import InlineRadios
from crispy_forms.helper import FormHelper, Layout
from django import forms
from django.core.exceptions import ValidationError
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


class ProjectDescriptionForm(ModelForm):
    """Form for adding/editing ProjectDescription instances.

    Validates that only one description of each type exists per project,
    enforcing the unique_together constraint at the form level.

    Fields:
    - type: Description type from controlled vocabulary
    - value: Description text content

    Validation:
    - Enforces uniqueness of (related, type) combination
    - Provides clear error messages for duplicate types

    Usage:
        form = ProjectDescriptionForm(data=request.POST)
        form.instance.related = project
        if form.is_valid():
            form.save()
    """

    type = forms.ChoiceField(
        label=_("Description type"),
        help_text=_("What kind of description is this?"),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    value = forms.CharField(
        label=_("Description"),
        help_text=_("Provide the description text."),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
            }
        ),
    )

    class Meta:
        from .models import ProjectDescription

        model = ProjectDescription
        fields = ["type", "value"]

    def __init__(self, *args, **kwargs):
        """Initialize form and set type choices from vocabulary."""
        super().__init__(*args, **kwargs)
        from .models import ProjectDescription

        # Set type choices from model vocabulary
        self.fields["type"].choices = ProjectDescription.VOCABULARY.choices

    def clean(self):
        """Validate that description type is unique for the project."""
        cleaned_data = super().clean()
        description_type = cleaned_data.get("type")

        # Check for duplicate description type on the same project
        if self.instance.related_id and description_type:
            from .models import ProjectDescription

            existing = (
                ProjectDescription.objects.filter(
                    related=self.instance.related, type=description_type
                )
                .exclude(pk=self.instance.pk)
                .exists()
            )

            if existing:
                raise ValidationError(
                    {
                        "type": _(
                            "A description of type '{type}' already exists for this project."
                        ).format(type=description_type)
                    }
                )

        return cleaned_data
