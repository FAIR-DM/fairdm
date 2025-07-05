from crispy_forms.bootstrap import StrictButton, Tab, TabHolder
from crispy_forms.layout import HTML, Column, Div, Fieldset, Layout, Row
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django_countries import countries
from django_select2.forms import Select2Widget

from fairdm.contrib.contributors.models import Organization
from fairdm.forms import ModelForm
from fairdm.forms.fields import LatitudeField, LongitudeField

from .widgets import RORWidget

ADD_MANUALLY_HELP_TEXT = _(
    "If the organization you wish to add is not in the Research Organization Registry (ROR), you can add it manually by filling out the form below. Please provide as much information as possible to ensure accurate representation."
)

ADD_FROM_ROR_HELP_TEXT = _("Search for an organization using the Research Organization Registry (ROR).")


class OrgMixin:
    name = forms.CharField(
        required=False,
        help_text=_("This is how the organization will be displayed within the portal and on any published materials."),
    )
    lat = LatitudeField(
        required=False,
        label=_("Latitude"),
        help_text=_("The latitude of the organization's location."),
    )
    lon = LongitudeField(
        required=False,
        label=_("Longitude"),
        help_text=_("The longitude of the organization's location."),
    )
    country = forms.ChoiceField(
        required=False,
        choices=countries,
        label=_("Country"),
        help_text=_("The country where the organization is based."),
        widget=Select2Widget,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = False


class OrganizationCreateForm(OrgMixin, ModelForm):
    """Form to create a new contributor from ORCID or manually from form data."""

    from_ror = forms.CharField(
        label="ROR ID",
        required=False,
        widget=RORWidget(
            attrs={
                "data-placeholder": _("Search for an organization..."),
                "data-minimum-input-length": 3,
            }
        ),
    )

    class Meta:
        model = Organization
        fields = ["from_ror", "name", "lat", "lon", "country"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        location_text = "Provide an optional location for the organization. This allows us to include the organization in maps and geographic visualizations."
        self.helper.layout = Layout(
            Div(
                TabHolder(
                    Tab(
                        _("Search ROR"),
                        HTML(f"<p class='text-muted'>{ADD_FROM_ROR_HELP_TEXT}</p>"),
                        "from_ror",
                        StrictButton(
                            _("Add organization"),
                            name="action",
                            value="from_ror",
                            type="submit",
                            css_class="btn btn-primary",
                        ),
                        css_class="py-3",
                    ),
                    Tab(
                        _("Add Manually"),
                        HTML(f"<p class='text-muted'>{ADD_MANUALLY_HELP_TEXT}</p>"),
                        Fieldset(
                            _("Required"),
                            "name",
                            "country",
                        ),
                        Fieldset(
                            _("Optional"),
                            HTML(f"<p>{location_text}</p>"),
                            Row(
                                Column("lat"),
                                Column("lon"),
                            ),
                        ),
                        StrictButton(
                            _("Add organization"),
                            name="action",
                            value="from_form",
                            type="submit",
                            css_class="btn btn-primary",
                        ),
                        css_class="py-3",
                    ),
                ),
                x_data={},
            )
        )
        self.action = None
        if self.data:
            self.action = self.data.get("action")

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if self.action == "from_form" and not name:
            raise ValidationError("This field is required.")
        return name

    def clean_country(self):
        country = self.cleaned_data.get("country")
        if self.action == "from_form" and not country:
            raise ValidationError("This field is required.")
        return country

    def clean_from_ror(self):
        ror_id = self.cleaned_data.get("from_ror")
        if self.action == "from_ror" and not ror_id:
            raise ValidationError("This field is required.")
        return ror_id

    def save(self, commit: bool = True):
        if self.action == "from_ror":
            if ror_id := self.cleaned_data.get("from_ror"):
                # Fetch organization data from ROR and populate the form fields
                # This is a placeholder for the actual implementation
                self.instance, created = Organization.from_ror(ror_id, commit=commit)
                return self.instance
        return super().save(commit)


class OrganizationProfileForm(OrgMixin, ModelForm):
    """Form to edit an existing organization profile."""

    # image = forms.ImageField(
    #     widget=ClientsideCroppingWidget(
    #         width=600,
    #         height=400,
    #         preview_width="100%",
    #         preview_height="auto",
    #         file_name="logo.jpg",
    #     ),
    #     required=False,
    #     label=False,
    # )

    # hopefully this can be removed when this issue is solved: https://github.com/koendewit/django-client-side-image-cropping/issues/15

    class Meta:
        model = Organization
        fields = ["image", "name", "country", "lat", "lon", "profile"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            Row(
                Column(
                    "image",
                    css_class="col-md-4",
                ),
                Column(
                    "name",
                    "country",
                    Row(Column("lat"), Column("lon")),
                    "profile",
                    # css_class="col-md-8",
                ),
                css_class="gx-4 flex-md-row-reverse",
            ),
        )
        self.helper.form_id = "user-profile-form"
