from django import forms
from django.conf import settings
from django.utils.translation import gettext as _
from licensing.models import License

from fairdm.core.models import Project
from fairdm.forms import ImageCroppingWidget

from ..forms import BaseForm
from .models import Dataset

DEFAULT_LICENSE = getattr(settings, "FAIRDM_DEFAULT_LICENSE", "CC BY 4.0")


class DatasetForm(BaseForm):
    name = forms.CharField(
        label=_("Name"),
        help_text=_("What is the name of this dataset?"),
        required=True,
    )
    image = forms.ImageField(
        widget=ImageCroppingWidget(
            width=1200,
            height=int(1200 * 9 / 21),
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
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        label=_("Project"),
        help_text=_("What project does this dataset belong to?"),
        required=False,
    )
    license = forms.ModelChoiceField(
        queryset=License.objects.all(),
    )

    class Meta:
        model = Dataset
        fields = ["project", "reference"]

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if license := self.fields.get("license"):
            license.initial = License.objects.filter(name=DEFAULT_LICENSE).first()
        self.request = request
        if self.request and self.fields.get("project"):
            self.fields["project"].queryset = self.request.user.projects.all()


class BasicInfoForm(BaseForm):
    pass
