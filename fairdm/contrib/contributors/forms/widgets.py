from django import forms
from django_select2.forms import ModelSelect2MultipleWidget

from ..models import Contributor, Organization, Person


class RORWidget(forms.TextInput):
    """Widget for ROR (Research Organization Registry) ID input."""

    template_name = "widgets/ror.html"


class OrcidInputWidget(forms.TextInput):
    template_name = "widgets/orcid.html"


class LatitudeWidget(forms.TextInput):
    def __init__(self, attrs=None, precision=5):
        self.precision = precision
        x_precision = "9" * self.precision  # Adjusting max_digits based on precision
        default_attrs = {"x-mask:dynamic": f"$input.startsWith('-') ? '-99.{x_precision}' : '99.{x_precision}'"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class LongitudeWidget(forms.TextInput):
    def __init__(self, attrs=None, precision=5):
        self.precision = precision
        x_precision = "9" * self.precision  # Adjusting max_digits based on precision
        default_attrs = {"x-mask:dynamic": f"$input.startsWith('-') ? '-999.{x_precision}' : '999.{x_precision}'"}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


class ContributorSelect2Widget(ModelSelect2MultipleWidget):
    queryset = Contributor.objects.all()
    search_fields = ["name__icontains"]


class PersonSelect2Widget(ModelSelect2MultipleWidget):
    queryset = Person.objects.all()
    search_fields = ["first_name__icontains", "last_name__icontains"]


class OrganizationSelect2Widget(ModelSelect2MultipleWidget):
    queryset = Organization.objects.all()
    search_fields = ["name__icontains"]
