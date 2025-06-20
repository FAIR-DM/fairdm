from django_select2.forms import ModelSelect2MultipleWidget, ModelSelect2Widget


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
