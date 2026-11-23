"""The choices a person makes about what a file may do."""

from django import forms
from django.utils.translation import gettext_lazy as _
from mvp_forms.widgets import CardSelect

from .models import ImportJob

MODE_DESCRIPTIONS = {
    ImportJob.Mode.BOTH: _("Rows that match a record update it. The rest become new records."),
    ImportJob.Mode.ADD: _("Rows that match a record are left out, so nothing stored changes."),
    ImportJob.Mode.UPDATE: _("Rows that match no record are left out, so nothing is added."),
}

EMPTY_CHOICES = [
    (ImportJob.Empty.KEEP, _("Keeps the stored value")),
    (ImportJob.Empty.CLEAR, _("Clears the stored value")),
]

EMPTY_DESCRIPTIONS = {
    ImportJob.Empty.KEEP: _("Safe for a file that leaves things out."),
    ImportJob.Empty.CLEAR: _("For an export you have edited, where an emptied cell means remove it."),
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
        super().__init__(*args, **kwargs)
        if brief:
            for field in self.fields.values():
                field.widget.descriptions = None

    def chosen(self, mode, empty):
        """Return the mode and empty-cell rule chosen, or the ones given for a choice not made.

        Args:
            mode: The mode to use when the form holds no valid one.
            empty: The empty-cell rule to use when the form holds no valid one.

        Returns:
            The mode and the empty-cell rule.
        """
        self.is_valid()
        return self.cleaned_data.get("mode", mode), self.cleaned_data.get("empty", empty)
