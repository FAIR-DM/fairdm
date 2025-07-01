from django import forms
from django_select2.forms import ModelSelect2MultipleWidget, ModelSelect2Widget, Select2Mixin


class ContributorSelectWidget(ModelSelect2Widget):
    model = "contributor.Contributor"
    search_fields = ["name__icontains"]
    attrs = {
        "data-placeholder": "Search for a contributor...",
        "data-minimum-input-length": 2,
        "data-theme": "bootstrap5",
    }


class ContributorSelectMultipleWidget(ModelSelect2MultipleWidget):
    model = "contributor.Contributor"
    search_fields = ["name__icontains"]
    attrs = {
        "data-placeholder": "Search for contributors...",
        "data-minimum-input-length": 2,
        "data-theme": "bootstrap5",
    }


class RORWidget(Select2Mixin, forms.Select):
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
