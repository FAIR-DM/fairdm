"""Tests for the affiliation form."""

import pytest

from fairdm.contrib.autocomplete.fields import OrganizationChoiceField
from fairdm.contrib.contributors.forms.forms import AffiliationForm
from fairdm.contrib.contributors.models import Affiliation
from fairdm.factories import OrganizationFactory, PersonFactory


@pytest.mark.django_db
class TestAffiliationForm:
    def test_the_organization_is_chosen_with_the_organization_field(self):
        field = AffiliationForm().fields["organization"]

        assert isinstance(field, OrganizationChoiceField)

    def test_the_chosen_organization_is_saved(self, in_request):
        person = PersonFactory()
        organization = OrganizationFactory()
        in_request(person)
        form = AffiliationForm(
            {"organization": organization.pk}, instance=Affiliation(person=person)
        )

        assert form.is_valid(), form.errors
        affiliation = form.save()

        assert Affiliation.objects.get(pk=affiliation.pk).organization == organization

    def test_an_organization_that_does_not_exist_is_refused(self, in_request):
        person = PersonFactory()
        in_request(person)
        form = AffiliationForm({"organization": 0}, instance=Affiliation(person=person))

        assert form.has_error("organization", code="invalid_choice")
