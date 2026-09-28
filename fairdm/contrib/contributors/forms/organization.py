"""Forms for creating and editing organisations."""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django_countries import countries

from fairdm.contrib.contributors.models import Organization
from fairdm.forms import ModelForm

from .widgets import RORWidget


class OrganizationCreateForm(ModelForm):
    """Create an organisation by ROR lookup or by entering its details.

    Only the fields of the submitted ``action`` (``from_ror`` or ``from_form``) are required.

    Args:
        *args: Passed to ``ModelForm``.
        **kwargs: Passed to ``ModelForm``.

    Attributes:
        from_ror: The ROR record to look up.
        country: The organisation's country.
    """

    from_ror = forms.CharField(
        label=_("ROR ID"),
        required=False,
        help_text=_(
            "Search the Research Organization Registry. Type at least 3 characters."
        ),
        widget=RORWidget(
            attrs={
                "data-placeholder": _("Search for an organization..."),
                "data-minimum-input-length": "3",
            }
        ),
    )
    country = forms.ChoiceField(
        required=False,
        choices=countries,
        widget=forms.Select,
    )

    class Meta:
        model = Organization
        fields = ["from_ror", "name", "location", "country"]
        labels = {
            "country": _("Country"),
        }
        help_texts = {
            "name": _(
                "How the organization will be displayed in the portal and publications."
            ),
            "country": _("The country where the organization is based."),
            "location": _("Geographic location or address."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action = self.data.get("action") if self.data else None

    def clean_name(self):
        """Require a name when adding manually."""
        name = self.cleaned_data.get("name")
        if self.action == "from_form" and not name:
            raise ValidationError(
                _("Organization name is required when adding manually.")
            )
        return name

    def clean_country(self):
        """Require a country when adding manually."""
        country = self.cleaned_data.get("country")
        if self.action == "from_form" and not country:
            raise ValidationError(_("Country is required when adding manually."))
        return country

    def clean_from_ror(self):
        """Require a ROR id when searching ROR."""
        ror_id = self.cleaned_data.get("from_ror")
        if self.action == "from_ror" and not ror_id:
            raise ValidationError(_("ROR ID is required when searching ROR."))
        return ror_id

    def save(self, commit: bool = True):
        """Create the organisation from ROR, or save the entered details."""
        if self.action == "from_ror":  # noqa: SIM102
            if ror_id := self.cleaned_data.get("from_ror"):
                self.instance, _created = Organization.from_ror(ror_id, commit=commit)
                return self.instance
        return super().save(commit)


class OrganizationProfileForm(ModelForm):
    """Edit an organisation's logo, name, country, location and profile.

    Args:
        *args: Passed to ``ModelForm``.
        **kwargs: Passed to ``ModelForm``.

    Attributes:
        country: The organisation's country.
    """

    country = forms.ChoiceField(
        choices=countries,
        widget=forms.Select,
    )

    class Meta:
        model = Organization
        fields = ["image", "name", "country", "location", "profile"]
        labels = {
            "image": _("Logo"),
            "profile": _("About"),
        }
        help_texts = {
            "image": _("Upload an organization logo or representative image."),
            "name": _("Official name of the organization."),
            "country": _("Country where the organization is headquartered."),
            "location": _("Specific location or address."),
            "profile": _(
                "Brief description of the organization's purpose and activities."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_id = "organization-profile-form"
