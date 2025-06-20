from dal import autocomplete
from django import forms

from fairdm.contrib.contributors.models import Contribution, Contributor, Organization, Person
from fairdm.forms import Form

from .widgets import ContributorSelectMultipleWidget


class BaseFormMixin:
    def __init__(self, *args, **kwargs):
        self.base_object = kwargs.pop("base_object", None)
        super().__init__(*args, **kwargs)


class ContributionBaseForm(BaseFormMixin, forms.ModelForm):
    roles = forms.MultipleChoiceField(
        choices=[],
        required=False,
        help_text="Select roles for the contributor.",
        widget=autocomplete.Select2Multiple(
            attrs={
                "placeholder": "Click or type to select roles...",
                "data-theme": "bootstrap5",
            },
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["roles"].choices = self.base_object.CONTRIBUTOR_ROLES.choices


class CreateContributionForm(ContributionBaseForm):
    type = forms.ChoiceField(
        choices=[
            ("person", "Person"),
            ("organization", "Organization"),
        ],
        initial="person",
    )
    source = forms.ChoiceField(
        choices=[
            ("existing", "Existing Contributor"),
            ("orcid", "ORCID"),
            ("ror", "ROR"),
            ("manual", "Manual Entry"),
        ],
        initial="manual",
        help_text="Select how you want to add the contributor.",
    )
    existing = forms.CharField(
        required=False,
        help_text="If you want to add an existing contributor, enter their UUID here.",
    )

    from_orcid = forms.CharField(
        required=False,
        help_text="If you want to add a contributor from ORCID, enter their ORCID ID here.",
    )

    from_ror = forms.CharField(
        required=False,
        help_text="If you want to add a contributor from ROR, enter their ROR ID here.",
    )
    name = forms.CharField(
        required=False,
        help_text="Name of the contributor. If you are adding a person, this will be their full name.",
    )
    first_name = forms.CharField(
        required=False,
        help_text="First name of the contributor.",
    )
    last_name = forms.CharField(
        required=False,
        help_text="Last name of the contributor.",
    )
    affiliation = forms.CharField(
        required=False,
        help_text="Affiliation of the contributor, if applicable.",
    )

    class Meta:
        model = Contribution
        fields = []


class AddExistingPersonForm(ContributionBaseForm):
    """Form to add an existing person as a contributor."""

    contributor = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        required=True,
        label="Contributor",
        help_text="Select an existing contributor to add.",
        widget=autocomplete.ModelSelect2(
            url="person-autocomplete",
            attrs={
                # Set some placeholder
                # 'data-placeholder': 'Autocomplete ...',
                # Only trigger autocompletion after 3 characters have been typed
                "data-minimum-input-length": 3,
                "data-theme": "bootstrap5",
            },
        ),
    )
    affiliation = forms.ModelChoiceField(
        queryset=Organization.objects.all(),  # This will be populated dynamically
        required=False,
        label="Affiliation",
        help_text="Select an appropriate affiliation for this contributor.",
        widget=autocomplete.ModelSelect2(
            url="organization-autocomplete",
            forward=["contributor"],  # Forward the selected contributor to the autocomplete view
            attrs={
                "data-theme": "bootstrap5",
                # Set some placeholder
                # 'data-placeholder': 'Autocomplete ...',
                # Only trigger autocompletion after 3 characters have been typed
            },
        ),
    )

    class Meta:
        model = Contribution
        fields = ["contributor", "affiliation", "roles"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields["contributor"].queryset = Contribution.objects.filter(type="person")


class UpdateContributionForm(ContributionBaseForm):
    """Form to update an existing contribution."""

    affiliation = forms.ModelChoiceField(
        queryset=Person.objects.none(),  # This will be populated dynamically
        required=False,
        label="Affiliation",
        help_text="Select an appropriate affiliation for this contributor.",
    )

    class Meta:
        model = Contribution
        fields = ["roles"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["affiliation"].queryset = self.instance.contributor.affiliations.all()


class QuickAddContributionForm(Form):
    contributors = forms.ModelMultipleChoiceField(
        queryset=Contributor.objects.all(),
        required=True,
        label="",
        widget=ContributorSelectMultipleWidget(
            attrs={
                "data-placeholder": "Search for contributors...",
                "data-minimum-input-length": 2,
            }
        ),
    )

    class Meta:
        fields = ["contributors"]


class AddContributorForm(ContributionBaseForm):
    """Form to add a new contributor."""

    contributor = forms.ModelChoiceField(
        queryset=Person.objects.all(),
        required=True,
        label="Contributor",
        help_text="Select an existing contributor to add.",
        widget=autocomplete.ModelSelect2(
            url="person-autocomplete",
            attrs={
                "data-minimum-input-length": 3,
                "data-theme": "bootstrap5",
            },
        ),
    )

    class Meta:
        model = Contribution
        fields = ["contributor", "roles"]
