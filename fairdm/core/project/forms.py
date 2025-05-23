from django import forms
from django.utils.translation import gettext as _

from fairdm.forms import ImageCroppingWidget

from ..forms import BaseForm
from .models import Project


class ProjectForm(BaseForm):
    image = forms.ImageField(
        widget=ImageCroppingWidget(
            width=1200,
            height=int(1200 * 9 / 21),
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
    name = forms.CharField(label=_("Project name"), help_text=_("Give your new project a name"))
    status = forms.ChoiceField(
        label=_("Current status"),
        choices=Project.STATUS_CHOICES.choices,
        help_text=_("In which stage of it's lifecycle is this project?"),
    )

    class Meta:
        model = Project
        fields = [
            "image",
            "name",
            "status",
        ]
