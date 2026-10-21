"""Widgets for identifiers."""

from django import forms


class OrcidInputWidget(forms.TextInput):
    """Text input for an ORCID iD."""

    template_name = "widgets/orcid.html"
