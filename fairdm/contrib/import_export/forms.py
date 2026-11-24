"""The choices a person makes about a file, and the file itself."""

from django import forms
from django.utils.translation import gettext_lazy as _
from mvp_forms.widgets import CardSelect

from .models import ImportJob
from .reader import FileProblem, FileReader

MODE_DESCRIPTIONS = {
    ImportJob.Mode.BOTH: _(
        "Rows that match a record update it. The rest become new records."
    ),
    ImportJob.Mode.ADD: _(
        "Rows that match a record are left out, so nothing stored changes."
    ),
    ImportJob.Mode.UPDATE: _(
        "Rows that match no record are left out, so nothing is added."
    ),
}

EMPTY_CHOICES = [
    (ImportJob.Empty.KEEP, _("Keeps the stored value")),
    (ImportJob.Empty.CLEAR, _("Clears the stored value")),
]

EMPTY_DESCRIPTIONS = {
    ImportJob.Empty.KEEP: _("Safe for a file that leaves things out."),
    ImportJob.Empty.CLEAR: _(
        "For an export you have edited, where an emptied cell means remove it."
    ),
}


class ImportOptionsForm(forms.Form):
    """What the file may do, and what an empty cell means.

    Args:
        brief: Draw each choice by its label alone, without the line that explains it.
    """

    mode = forms.ChoiceField(
        label=_("What the file may do"),
        choices=ImportJob.Mode.choices,
        initial=ImportJob.Mode.BOTH,
        widget=CardSelect(columns=1, descriptions=MODE_DESCRIPTIONS),
    )
    empty = forms.ChoiceField(
        label=_("An empty cell"),
        choices=EMPTY_CHOICES,
        initial=ImportJob.Empty.KEEP,
        widget=CardSelect(columns=1, descriptions=EMPTY_DESCRIPTIONS),
    )

    def __init__(self, *args, brief=False, **kwargs):
        """Drop the descriptions from the choices when ``brief`` is set."""
        super().__init__(*args, **kwargs)
        if brief:
            for field in self.fields.values():
                field.widget.descriptions = None

    def chosen(self, mode, empty):
        """Return the mode and empty-cell rule chosen, or the ones given when none is.

        Args:
            mode: The mode to use when the form holds no valid one.
            empty: The empty-cell rule to use when the form holds no valid one.

        Returns:
            The mode and the empty-cell rule.
        """
        if not self.is_bound:
            return mode, empty
        self.is_valid()
        return self.cleaned_data.get("mode", mode), self.cleaned_data.get(
            "empty", empty
        )


class UploadForm(forms.Form):
    """The file to import. A file of another format or too large is refused."""

    MAX_BYTES = FileReader.MAX_BYTES

    file = forms.FileField(
        label=_("File"),
        help_text=_("A CSV, TSV, Excel or OpenDocument file of up to 20 MB."),
    )

    def clean_file(self):
        """Refuse a file of a format that is not read or larger than the limit.

        Returns:
            The uploaded file.

        Raises:
            ValidationError: With code ``format`` or ``too_large``.
        """
        upload = self.cleaned_data["file"]
        try:
            FileReader.file_format(upload.name)
        except FileProblem:
            raise forms.ValidationError(
                _("Upload a CSV, TSV, Excel or OpenDocument file."), code="format"
            ) from None
        if upload.size > FileReader.MAX_BYTES:
            raise forms.ValidationError(
                _("The file is larger than 20 MB."), code="too_large"
            )
        return upload
