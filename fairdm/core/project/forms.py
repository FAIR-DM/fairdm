from django import forms
from django.utils.translation import gettext as _

from fairdm.forms import ImageCroppingWidget, ModelForm

from .models import Project


class ProjectForm(ModelForm):
    image = forms.ImageField(
        widget=ImageCroppingWidget(
            width=1200,
            height=int(1200 * 9 / 16),
            empty_text=_("Select cover image"),
            config={
                "enableOrientation": True,
            },
            result={
                "format": "jpeg",
            },
        ),
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
