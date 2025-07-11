from client_side_image_cropping import ClientsideCroppingWidget
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django import forms
from django.utils.translation import gettext as _
from django_select2.forms import Select2MultipleWidget, Select2Widget
from formset.widgets import UploadedFileInput

from fairdm.utils.choices import iso_639_1_languages

from ..models import Contribution, Contributor


class UserIdentifierForm(forms.ModelForm):
    class Meta:
        # model = Identifier
        fields = ["type", "value"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "type",
            "value",
            "delete",
        )
        self.helper.add_input(Submit("submit", "Save"))


class UserProfileForm(forms.ModelForm):
    image = forms.ImageField(
        widget=ClientsideCroppingWidget(
            width=300,
            height=300,
            preview_width=150,
            preview_height=150,
            file_name="profile.jpg",
        ),
        required=False,
        label=False,
    )
    lang = forms.ChoiceField(
        choices=iso_639_1_languages,
        initial="en",
        # widget=Selectize(),
        help_text=_("Preferred display language for this site (where possible)."),
        label=_("Language"),
    )

    name = forms.CharField(help_text=_("Your name as it will appear on this site."))

    class Meta:
        model = Contributor
        fields = [
            "image",
            "name",
            "lang",
            "profile",
        ]


class ContributionForm(forms.ModelForm):
    """Used to modify contributors on a project, dataset, etc. and assign roles."""

    class Meta:
        model = Contribution
        fields = [
            # "object",
            "contributor",
            "roles",
        ]
        widgets = {
            "contributor": Select2Widget(),
            "roles": Select2MultipleWidget,
        }


class ContributorForm(forms.ModelForm):
    image = forms.ImageField(
        widget=UploadedFileInput(
            attrs={
                "max-size": 1024 * 1024,
            }
        ),
        help_text="Please do not upload files larger than 1MB",
        required=False,
    )

    class Meta:
        model = Contributor
        fields = ["image", "name", "profile", "lang"]


class IdentifierForm(forms.ModelForm):
    min_siblings = 0

    id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    scheme = forms.ChoiceField(
        label=_("Scheme"),
        help_text=_("The scheme that the identifier is based on."),
        choices=[],  # set dynamically in __init__,
    )

    class Meta:
        fields = ["scheme", "identifier"]

    def __init__(self, scheme_choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["scheme"].choices = scheme_choices
