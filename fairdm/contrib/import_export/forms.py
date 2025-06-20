from django import forms
from django.utils.translation import gettext_lazy as _

from fairdm.forms import Form

from .utils import export_choices, import_choices


class ImportForm(Form):
    file = forms.FileField(
        help_text=_("Select a file to import."),
    )

    class Meta:
        fields = ["file"]
        help_text = "Select a file to import. The following formats are supported: {}".format(", ".join(import_choices))
        helper_attrs = {
            "id": "import-form",
            "form_tag": True,
            "form_class": "form-horizontal",
        }
        # inputs = [
        #     Reset("reset", "Reset", css_class="btn btn-secondary"),
        #     Submit("submit", "Import", css_class="btn btn-primary"),
        # ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.helper.layout.append(Submit("submit", "Import", css_class="btn btn-primary"))


class ExportForm(Form):
    format = forms.ChoiceField(choices=export_choices)
