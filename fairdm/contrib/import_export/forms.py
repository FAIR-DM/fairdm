"""Forms for importing and exporting records."""

from django import forms
from django.utils.translation import gettext_lazy as _

from fairdm.forms import Form

from .utils import export_choices


class ImportForm(Form):
    """Form for uploading a file to import."""

    file = forms.FileField(
        help_text=_("Select a file to import."),
    )

    class Meta:
        fields = ["file"]
        helper_attrs = {
            "id": "import-form",
            "form_tag": True,
            "form_class": "form-horizontal",
        }


class ExportForm(Form):
    """Form for choosing the export format."""

    format = forms.ChoiceField(choices=export_choices)
