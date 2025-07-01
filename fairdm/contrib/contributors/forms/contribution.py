from crispy_forms.bootstrap import StrictButton, Tab, TabHolder
from crispy_forms.layout import HTML, Column, Div, Layout, Row
from dal import autocomplete
from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django_addanother.widgets import AddAnotherWidgetWrapper
from django_select2.forms import ModelSelect2Widget

from fairdm.contrib.contributors.models import Contribution, Contributor, Organization, Person
from fairdm.forms import Form, ModelForm

from .widgets import ContributorSelectMultipleWidget, OrcidInputWidget

ADD_USER_MANUALLY_HELP_TEXT = _(
    "If the person you wish to add is not yet in our system and they do not have an ORCID ID, you can add their information manually. Please fill in the required fields below."
)

ADD_FROM_ORCID_HELP_TEXT = [
    _(
        "If the person you wish to add has an ORCID ID, you can enter it below to retrieve their information automatically. This will help ensure that their contributions are accurately recorded and linked to their ORCID profile."
    ),
    _(
        "If you are unsure of their ORCID ID, you can search for them on the <a href='https://orcid.org/orcid-search/search' target='_blank'>ORCID website</a>."
    ),
]

p_joiner = "</p><p class='text-muted'>"


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


class PersonCreateForm(ModelForm):
    """Form to create a new contributor from ORCID or manually from form data."""

    from_orcid = forms.CharField(
        label="ORCID ID",
        required=False,
        widget=OrcidInputWidget,
    )
    name = forms.CharField(
        required=False,
        help_text=_(
            "Please add the full name of the contributor as it should appear in our system and in formal citations. If left blank, this will be populated from the first and last name fields below."
        ),
    )
    first_name = forms.CharField(
        required=False,
        help_text=_("First name of the contributor."),
    )
    last_name = forms.CharField(
        required=False,
        help_text=_("Last name of the contributor."),
    )
    affiliations = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        required=False,
        label="Affiliation",
        help_text=_(
            "Select an affiliation for this contributor. If you cannot find the correct affiliation, use the plus icon on the right to add a new organization to our system."
        ),
        widget=AddAnotherWidgetWrapper(
            ModelSelect2Widget(
                search_fields=["name__icontains"],
            ),
            reverse_lazy("organization-add"),
        ),
    )

    is_primary = forms.BooleanField(
        required=False,
        label=_("Primary Affiliation"),
        help_text=_(
            "Check this box if this is the primary affiliation of this contributor. Marking as primary implies that this is also a current affiliation."
        ),
    )

    is_current = forms.BooleanField(
        required=False,
        label=_("Current Affiliation"),
        help_text=_(
            "Check this box if this person is currently affiliated with this organization. If not checked, it will be marked as a past affiliation."
        ),
    )

    class Meta:
        model = Person
        fields = ["from_orcid", "name", "first_name", "last_name", "affiliations", "is_primary", "is_current"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            Div(
                TabHolder(
                    Tab(
                        _("Search ORCID"),
                        HTML(f"<p class='text-muted'>{p_joiner.join(ADD_FROM_ORCID_HELP_TEXT)}</p>"),
                        "from_orcid",
                        StrictButton(
                            _("Add contributor"),
                            name="action",
                            value="from_orcid",
                            type="submit",
                            css_class="btn btn-primary",
                        ),
                        css_class="py-3",
                    ),
                    Tab(
                        _("Add Manually"),
                        HTML(f"<p class='text-muted'>{ADD_USER_MANUALLY_HELP_TEXT}</p>"),
                        "name",
                        Row(
                            Column("first_name"),
                            Column("last_name"),
                        ),
                        "affiliations",
                        "is_primary",
                        "is_current",
                        # Row(
                        # Column("is_primary"),
                        # Column("is_current"),
                        # ),
                        StrictButton(
                            _("Add contributor"),
                            name="action",
                            value="from_form",
                            type="submit",
                            css_class="btn btn-primary",
                        ),
                        css_class="py-3",
                    ),
                ),
                x_data={"orcid": ""},
            )
        )
        self.action = None
        if self.data:
            self.action = self.data.get("action")

    # def clean_name(self):
    #     name = self.cleaned_data.get("name", "")
    #     if self.action == "from_form" and not name:
    #         raise ValidationError("This field is required.")
    #     return name

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name", "")
        if self.action == "from_form" and not first_name:
            raise ValidationError("This field is required.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name", "")
        if self.action == "from_form" and not last_name:
            raise ValidationError("This field is required.")
        return last_name

    def clean_affiliations(self):
        affiliation = self.cleaned_data.get("affiliations")
        if self.action == "from_form" and not affiliation:
            raise ValidationError("This field is required.")
        return affiliation

    def clean_from_orcid(self):
        orcid_id = self.cleaned_data.get("from_orcid", "")
        if self.action == "from_orcid" and not orcid_id:
            raise ValidationError("This field is required.")
        return orcid_id

    def save(self, commit=True):
        if self.action == "from_orcid":
            orcid_id = self.cleaned_data.get("from_orcid")
            # Fetch person data from ORCID and populate the form fields
            # This is a placeholder for the actual implementation
            self.instance, created = Person.from_orcid(orcid_id)
            return self.instance

        self.instance = super().save(commit)
        affiliations = self.cleaned_data.get("affiliations")
        if commit and affiliations:
            is_primary = self.cleaned_data.get("is_primary")
            is_current = True if is_primary else self.cleaned_data.get("is_current", False)
            self.instance.organization_memberships.create(
                is_primary=is_primary,
                is_current=is_current,
                organization=affiliations,
            )
            # self.instance.affiliations.add(affiliations)
            # self.instance.save()
        return self.instance


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
