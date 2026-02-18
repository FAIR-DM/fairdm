from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django_addanother.widgets import AddAnotherWidgetWrapper
from django_select2.forms import HeavySelect2MultipleWidget, HeavySelect2Widget
from research_vocabs.models import Concept

from fairdm.contrib.contributors.models import (
    Contribution,
    Contributor,
    Organization,
    Person,
)
from fairdm.forms import Form, ModelForm

from .widgets import ContributorSelect2Widget, OrcidInputWidget


class PersonCreateForm(ModelForm):
    """Form for creating a new person contributor.

    Provides two methods of creation:
    1. Search ORCID - Fetch person data from ORCID registry
    2. Add Manually - Enter person information manually

    The form uses action-based validation to ensure only the active method's
    fields are validated.
    """

    from_orcid = forms.CharField(
        label=_("ORCID iD"),
        required=False,
        widget=OrcidInputWidget,
        help_text=_(
            "Enter the ORCID iD to automatically retrieve contributor information. "
            "Search for ORCIDs at https://orcid.org/orcid-search/search"
        ),
    )
    affiliations = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        label=_("Affiliation"),
        help_text=_(
            "Select the contributor's organizational affiliation. Use the + button to add a new organization if needed."
        ),
        widget=AddAnotherWidgetWrapper(
            HeavySelect2Widget(data_view="organization-autocomplete"),
            reverse_lazy("organization-add"),
        ),
    )
    is_primary = forms.BooleanField(
        required=False,
        label=_("Primary affiliation"),
        help_text=_("Primary affiliation implies current affiliation."),
    )
    is_current = forms.BooleanField(
        required=False,
        label=_("Current affiliation"),
        help_text=_("Uncheck if this is a past affiliation."),
    )

    class Meta:
        model = Person
        fields = [
            "from_orcid",
            "name",
            "first_name",
            "last_name",
            "affiliations",
            "is_primary",
            "is_current",
        ]
        help_texts = {
            "name": _(
                "Full name as it should appear in citations. If blank, will be generated from first and last name."
            ),
            "first_name": _("Given name of the contributor."),
            "last_name": _("Family name of the contributor."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action = self.data.get("action") if self.data else None

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name", "")
        if self.action == "from_form" and not first_name:
            raise ValidationError(_("First name is required when adding manually."))
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name", "")
        if self.action == "from_form" and not last_name:
            raise ValidationError(_("Last name is required when adding manually."))
        return last_name

    def clean_affiliations(self):
        affiliation = self.cleaned_data.get("affiliations")
        if self.action == "from_form" and not affiliation:
            raise ValidationError(_("Affiliation is required when adding manually."))
        return affiliation

    def clean_from_orcid(self):
        orcid_id = self.cleaned_data.get("from_orcid", "")
        if self.action == "from_orcid" and not orcid_id:
            raise ValidationError(_("ORCID iD is required when searching ORCID."))
        return orcid_id

    def save(self, commit=True):
        if self.action == "from_orcid":
            orcid_id = self.cleaned_data.get("from_orcid")
            self.instance, _ = Person.from_orcid(orcid_id)
            return self.instance

        self.instance = super().save(commit)
        affiliations = self.cleaned_data.get("affiliations")
        if commit and affiliations:
            is_primary = self.cleaned_data.get("is_primary", False)
            is_current = is_primary or self.cleaned_data.get("is_current", False)
            self.instance.affiliations.create(
                is_primary=is_primary,
                is_current=is_current,
                organization=affiliations,
            )
        return self.instance


class UpdateContributionForm(ModelForm):
    """Form for editing an existing contribution's roles and affiliation.

    Dynamically filters available roles based on the object type (Project,
    Dataset, etc.) and available affiliations based on the contributor's
    organization memberships.
    """

    roles = forms.ModelMultipleChoiceField(
        queryset=Concept.objects.none(),
        widget=HeavySelect2MultipleWidget(data_view="concept-autocomplete"),
    )
    affiliation = forms.ModelChoiceField(
        queryset=Person.contributors.all(),
        required=False,
    )

    class Meta:
        model = Contribution
        fields = ["roles", "affiliation"]
        labels = {
            "affiliation": _("Affiliation"),
        }
        help_texts = {
            "roles": _("Select one or more contributor roles."),
            "affiliation": _(
                "The contributor's organizational affiliation for this contribution. Past affiliations are acceptable."
            ),
        }

    def __init__(self, *args, **kwargs):
        self.base_object = kwargs.pop("base_object", None)
        super().__init__(*args, **kwargs)
        self.fields["affiliation"].queryset = self.instance.contributor.affiliations.all()
        roles_qs = Concept.get_for_vocabulary(Contribution.roles_vocab.__class__).filter(
            name__in=self.base_object.CONTRIBUTOR_ROLES.values
        )
        self.fields["roles"].queryset = roles_qs
        self.fields["roles"].choices = roles_qs.values_list("id", "label")


class QuickAddContributionForm(Form):
    """Simple form for quickly adding multiple contributors at once."""

    contributors = forms.ModelMultipleChoiceField(
        queryset=Contributor.objects.all(),
        required=True,
        label=_("Contributors"),
        help_text=_("Search and select contributors to add. Type to search."),
        widget=ContributorSelect2Widget,
    )

    class Meta:
        fields = ["contributors"]

    def __init__(self, base_object, *args, **kwargs):
        self.base_object = base_object
        super().__init__(*args, **kwargs)
