"""Forms for creating and editing projects."""

from crispy_forms.bootstrap import InlineRadios
from crispy_forms.helper import FormHelper, Layout
from django import forms
from django.utils.translation import gettext as _
from easy_thumbnails.widgets import ImageClearableFileInput

from fairdm.contrib.contributors.models import Organization
from fairdm.core.choices import ProjectStatus
from fairdm.core.forms import ManagerOnlyFieldsMixin
from fairdm.core.image_utils import IMAGE_HELP_TEXT, validate_image_file_size
from fairdm.forms import ModelForm
from fairdm.utils.choices import Visibility

from .models import Project


class ProjectForm(ManagerOnlyFieldsMixin, ModelForm):
    """Form for editing a project, and the base of ``ProjectCreateForm``.

    For a project that already exists, visibility and owner are offered only to someone who can
    manage it.

    Args:
        *args: Positional arguments passed to ``ModelForm``.
        request: The current request, which decides whether visibility and owner are offered.
        **kwargs: Keyword arguments passed to ``ModelForm``.

    Attributes:
        image: Optional cover image.
        name: The project's name.
        status: The project's stage, from concept to complete.
        visibility: Who can view the project.
        owner: The organization that owns the project.
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
        queryset=None,
        help_text=_("The organization that owns this project."),
        widget=forms.Select(attrs={"class": "form-control"}),
        required=False,
    )

    class Meta:
        model = Project
        fields = ["image", "name", "status", "visibility", "owner"]

    manager_only_fields = ("visibility", "owner")

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.withhold_manager_only_fields(request)
        if "owner" in self.fields:
            self.fields["owner"].queryset = Organization.objects.all()

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            *(
                InlineRadios(name) if name == "visibility" else name
                for name in ("image", "name", "status", "visibility", "owner")
                if name in self.fields
            )
        )


class ProjectCreateForm(ProjectForm):
    """Form for creating a project, asking only for name, status and visibility.

    The other fields are available after creation on the update page.

    Args:
        *args: Positional arguments passed to ``ProjectForm``.
        **kwargs: Keyword arguments passed to ``ProjectForm``.
    """

    class Meta(ProjectForm.Meta):
        fields = ["name", "status", "visibility"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            "name",
            "status",
            # BUG: InlineRadios makes crispy render the submit buttons inside the radio group.
            InlineRadios("visibility"),
        )
