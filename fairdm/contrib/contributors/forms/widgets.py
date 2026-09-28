"""Widgets for identifiers and contributor selection."""

from django import forms
from django_select2.forms import ModelSelect2MultipleWidget

from ..models import Contributor, Organization, Person


class RORWidget(forms.TextInput):
    """Text input for a ROR id."""

    template_name = "widgets/ror.html"


class OrcidInputWidget(forms.TextInput):
    """Text input for an ORCID iD."""

    template_name = "widgets/orcid.html"


class ContributorSelect2Widget(ModelSelect2MultipleWidget):
    """Multi-select that searches contributors by name."""

    queryset = Contributor.objects.all()
    search_fields = ["name__icontains"]


class PersonSelect2Widget(ModelSelect2MultipleWidget):
    """Multi-select that searches people by first or last name."""

    queryset = Person.objects.all()
    search_fields = ["first_name__icontains", "last_name__icontains"]


class OrganizationSelect2Widget(ModelSelect2MultipleWidget):
    """Multi-select that searches organisations by name."""

    queryset = Organization.objects.all()
    search_fields = ["name__icontains"]
