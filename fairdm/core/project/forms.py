from django import forms
from django.utils.translation import gettext as _

from fairdm.forms import ModelForm

from .models import Project


class ProjectForm(ModelForm):
    """Form for creating and editing Project instances.

    Provides fields for project image, name, visibility, and status with
    custom widgets and help text to guide users through project creation.
    """

    image = forms.ImageField(
        required=False,
        label=False,
    )
    name = forms.CharField(
        label=_("Project name"),
        help_text=_("Provide the name of your project."),
    )
    visibility = forms.ChoiceField(
        label=_("Visibility"),
        choices=Project.VISIBILITY.choices,
        help_text=_("Should this project be visible to the public?"),
    )
    status = forms.ChoiceField(
        label=_("Current status"),
        choices=Project.STATUS_CHOICES.choices,
        help_text=_("In what phase of it's lifecycle is this project?"),
    )

    class Meta:
        model = Project
        fields = [
            "image",
            "name",
            "visibility",
            "status",
        ]
