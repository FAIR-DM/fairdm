"""Inline formsets and forms for identifiers and affiliations."""

from controlled_vocabularies.models import Record
from django import forms
from django.forms.models import BaseInlineFormSet
from django.utils.translation import gettext_lazy as _

from fairdm.contrib.autocomplete.fields import OrganizationChoiceField
from fairdm.core.forms import ConceptSelectField
from fairdm.core.vocabularies import IDENTIFIER_TYPES, collection_members

from ..models import Affiliation, ContributorIdentifier, Organization, Person


class UserIdentifierFormSet(BaseInlineFormSet):
    """Identifier formset that tells each form which types the other identifiers already use."""

    def get_form_kwargs(self, index):
        """Pass the types used by the other identifiers to each form."""
        kwargs = super().get_form_kwargs(index)

        # Forms are not bound yet, so read the types from the queryset.
        existing_types = set()

        current_instance = None
        if (
            self.queryset is not None
            and index is not None
            and index < len(self.queryset)
        ):
            current_instance = self.queryset[index]

        if self.queryset is not None:
            for obj in self.queryset:
                if obj != current_instance:
                    existing_types.add(obj.type_id)

        kwargs["existing_types"] = existing_types
        return kwargs


class UserIdentifierForm(forms.ModelForm):
    """Edit a persistent identifier, offering only types that suit the contributor and are not already used.

    Args:
        *args: Passed to ``ModelForm``.
        **kwargs: Passed to ``ModelForm`` after removing ``contributor_instance``, the
            contributor being edited, and ``existing_types``, the types already in use.
    """

    def __init__(self, *args, **kwargs):
        contributor_instance = kwargs.pop("contributor_instance", None)
        existing_types = kwargs.pop("existing_types", set())
        super().__init__(*args, **kwargs)

        if contributor_instance:
            if isinstance(contributor_instance, Person):
                collection = f"{IDENTIFIER_TYPES}/person"
            elif isinstance(contributor_instance, Organization):
                collection = f"{IDENTIFIER_TYPES}/organization"
            else:
                collection = f"{IDENTIFIER_TYPES}/contributor"

            current_type = self.instance.type_id if self.instance.pk else None
            available = [
                concept.uri
                for concept in collection_members(collection)
                if concept.uri == current_type or concept.uri not in existing_types
            ]
            self.fields["type"].queryset = Record.objects.filter(uri__in=available)

    class Meta:
        model = ContributorIdentifier
        fields = ["type", "value"]
        field_classes = {"type": ConceptSelectField}
        labels = {
            "type": _("Type"),
            "value": _("Value"),
        }


class AffiliationForm(forms.ModelForm):
    """Edit a person's affiliation, setting the type of a new one from the organisation's managers.

    A new affiliation is pending when the organisation has an owner or admin, and a member otherwise.

    Attributes:
        organization: The organisation joined.
    """

    organization = OrganizationChoiceField(
        label=_("Organization"),
        help_text=_("Select an organization."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A form built outside a request serves no person and accepts every organization.
        self.fields["organization"].queryset = Organization.objects.all()

    def save(self, commit=True):
        """Set the type of a new affiliation, then save."""
        instance = super().save(commit=False)

        if not instance.pk:
            has_managers = instance.organization.affiliations.filter(
                type__in=[
                    Affiliation.MembershipType.OWNER,
                    Affiliation.MembershipType.ADMIN,
                ]
            ).exists()

            if has_managers:
                instance.type = Affiliation.MembershipType.PENDING
            else:
                instance.type = Affiliation.MembershipType.MEMBER

        if commit:
            instance.save()
        return instance

    class Meta:
        model = Affiliation
        fields = ["organization", "is_primary"]
        labels = {
            "is_primary": _("Primary"),
            "is_current": _("Current"),
        }
        help_texts = {
            "is_primary": _("Your primary affiliation."),
            "is_current": _("Is this affiliation ongoing?"),
        }
