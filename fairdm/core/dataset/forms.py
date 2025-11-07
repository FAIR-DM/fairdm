from django import forms
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django_addanother.widgets import AddAnotherWidgetWrapper
from django_select2.forms import ModelSelect2Widget
from licensing.models import License

from fairdm.core.models import Project
from fairdm.forms import ImageCroppingWidget, ModelForm

from .models import Dataset

DEFAULT_LICENSE = getattr(settings, "FAIRDM_DEFAULT_LICENSE", "CC BY 4.0")


class DatasetForm(ModelForm):
    """Form for creating and editing Dataset instances.

    Provides fields for dataset name, image, project association, license,
    and DOI. The project field uses a Select2 widget with "add another"
    functionality. License defaults to the configured DEFAULT_LICENSE.
    The project queryset is filtered to only show projects the authenticated
    user has access to.
    """

    name = forms.CharField(
        label=_("Name"),
        help_text=_("Give your dataset a name that is descriptive and reflects it's purpose and content."),
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
        help_text=_(
            "If the dataset belongs to a specific research project, you can select it here. Use the plus icon to quickly create a new project."
        ),
        required=False,
        widget=AddAnotherWidgetWrapper(
            ModelSelect2Widget(
                search_fields=["name__icontains"],
            ),
            reverse_lazy("project-create"),
        ),
    )
    license = forms.ModelChoiceField(
        queryset=License.objects.all(),
        label=_("License"),
        help_text=_("Select a license for this dataset. You may change this up until you publish the dataset."),
    )
    doi = forms.CharField(
        label=_("DOI"),
        help_text=_("If this dataset already has a DOI, you can enter it here."),
        required=False,
    )

    class Meta:
        model = Dataset
        fields = ["project", "reference"]

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if license := self.fields.get("license"):
            license.initial = License.objects.filter(name=DEFAULT_LICENSE).first()
        self.request = request

        if self.request and self.request.user.is_authenticated and self.fields.get("project"):
            self.fields["project"].queryset = self.request.user.projects.all()
