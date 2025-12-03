from dal import autocomplete
from django import forms
from django.forms.models import BaseInlineFormSet
from django.utils.translation import gettext as _

from ..models import ContributorIdentifier, Organization, OrganizationMember, Person


class UserIdentifierFormSet(BaseInlineFormSet):
    """Custom formset for identifiers that tracks existing types to prevent duplicates."""

    def get_form_kwargs(self, index):
        """Pass existing types to each form so it can filter choices appropriately."""
        kwargs = super().get_form_kwargs(index)

        # Collect existing identifier types from the instance's saved identifiers
        # This gets called before forms are bound, so we need to look at the queryset
        existing_types = set()

        # Get the instance being edited in this form (if any)
        current_instance = None
        if self.queryset is not None and index is not None and index < len(self.queryset):
            current_instance = self.queryset[index]

        # Collect types from all existing identifiers except the current one
        if self.queryset is not None:
            for obj in self.queryset:
                if obj != current_instance:
                    existing_types.add(obj.type)

        kwargs["existing_types"] = existing_types
        return kwargs


class UserIdentifierForm(forms.ModelForm):
    """Form for editing user persistent identifiers (ORCID, etc.).

    Used in inline formset for managing multiple identifiers per user.
    Filters available identifier types based on contributor type (Person vs Organization)
    and excludes types that are already selected in other forms.
    """

    def __init__(self, *args, **kwargs):
        # Extract contributor_instance and existing_types from kwargs if provided
        contributor_instance = kwargs.pop("contributor_instance", None)
        existing_types = kwargs.pop("existing_types", set())
        super().__init__(*args, **kwargs)

        # Filter identifier type choices based on contributor type
        if contributor_instance:
            vocabulary = self._meta.model.VOCABULARY
            if isinstance(contributor_instance, Person):
                # Person: ORCID, ResearcherID
                filtered_vocab = vocabulary.from_collection("Person")
            elif isinstance(contributor_instance, Organization):
                # Organization: ROR, Wikidata, ISNI, Crossref Funder ID
                filtered_vocab = vocabulary.from_collection("Organization")
            else:
                # Fallback: all types
                filtered_vocab = vocabulary

            # Get all available choices
            all_choices = filtered_vocab.choices

            # Filter out already-selected types (unless this is the current instance's type)
            current_type = self.instance.type if self.instance.pk else None
            available_choices = [
                (value, label)
                for value, label in all_choices
                if value == "" or value == current_type or value not in existing_types
            ]

            # Update the choices for the type field
            self.fields["type"].choices = available_choices

    class Meta:
        model = ContributorIdentifier
        fields = ["type", "value"]
        labels = {
            "type": _("Type"),
            "value": _("Value"),
        }


class AffiliationForm(forms.ModelForm):
    """Form for editing organizational affiliations.

    Used in inline formset for managing person's organizational memberships.
    Automatically sets membership type based on organization's existing memberships:
    - PENDING if organization has owners or admins
    - MEMBER if organization has no owners or admins
    """

    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        label=_("Organization"),
        help_text=_("Select an organization."),
        widget=autocomplete.ModelSelect2(url="autocomplete:organization"),
    )

    def save(self, commit=True):
        """Override save to automatically set membership type."""
        instance = super().save(commit=False)

        # Only set type for new memberships (not when editing existing ones)
        if not instance.pk:
            # Check if organization has owners or admins
            from .models import OrganizationMember

            has_managers = instance.organization.memberships.filter(
                type__in=[OrganizationMember.MembershipType.OWNER, OrganizationMember.MembershipType.ADMIN]
            ).exists()

            # Set type based on whether organization has managers
            if has_managers:
                instance.type = OrganizationMember.MembershipType.PENDING
            else:
                instance.type = OrganizationMember.MembershipType.MEMBER

        if commit:
            instance.save()
        return instance

    class Meta:
        model = OrganizationMember
        fields = ["organization", "is_primary", "is_current"]
        labels = {
            "is_primary": _("Primary"),
            "is_current": _("Current"),
        }
        help_texts = {
            "is_primary": _("Your primary affiliation."),
            "is_current": _("Is this affiliation ongoing?"),
        }
