"""Widgets for identifiers."""

from django import forms


class RORWidget(forms.TextInput):
    """Text input for a ROR id."""

    template_name = "widgets/ror.html"


class OrcidInputWidget(forms.TextInput):
    """Text input for an ORCID iD."""

    template_name = "widgets/orcid.html"
