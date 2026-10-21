"""Tests for the person creation form and the contribution form."""

import pytest
from mvp_forms.widgets import TomSelectMultiple
from research_vocabs.models import Concept

from fairdm.contrib.autocomplete.fields import OrganizationChoiceField
from fairdm.contrib.contributors.forms.contribution import (
    PersonCreateForm,
    UpdateContributionForm,
)
from fairdm.contrib.contributors.models import Contribution, Person
from fairdm.factories import (
    ContributionFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
)


@pytest.mark.django_db
class TestPersonCreateForm:
    def test_the_affiliation_is_chosen_with_the_organization_field(self):
        field = PersonCreateForm().fields["affiliations"]

        assert isinstance(field, OrganizationChoiceField)

    def test_the_person_is_saved_with_the_chosen_affiliation(self, in_request):
        organization = OrganizationFactory()
        in_request(PersonFactory())
        form = PersonCreateForm(
            {
                "action": "from_form",
                "name": "Dana Smith",
                "first_name": "Dana",
                "last_name": "Smith",
                "affiliations": organization.pk,
                "is_primary": "on",
            }
        )

        assert form.is_valid(), form.errors
        person = form.save()

        affiliation = Person.objects.get(pk=person.pk).affiliations.get()
        assert affiliation.organization == organization
        assert affiliation.is_primary is True

    def test_an_affiliation_is_required_when_adding_manually(self, in_request):
        in_request(PersonFactory())
        form = PersonCreateForm(
            {
                "action": "from_form",
                "name": "Dana Smith",
                "first_name": "Dana",
                "last_name": "Smith",
            }
        )

        assert form.has_error("affiliations")


@pytest.mark.django_db
class TestUpdateContributionForm:
    def test_the_roles_are_chosen_with_a_counted_tom_select(self):
        project = ProjectFactory()
        contribution = ContributionFactory(content_object=project)

        form = UpdateContributionForm(instance=contribution, base_object=project)

        widget = form.fields["roles"].widget
        assert isinstance(widget, TomSelectMultiple)
        assert widget.counted is True

    def test_the_chosen_roles_are_saved(self):
        project = ProjectFactory()
        contribution = ContributionFactory(content_object=project)
        allowed = Concept.objects.filter(name__in=project.CONTRIBUTOR_ROLES.values)
        role = allowed.first()
        form = UpdateContributionForm(
            {"roles": [role.pk]}, instance=contribution, base_object=project
        )

        assert form.is_valid(), form.errors
        form.save()

        assert list(Contribution.objects.get(pk=contribution.pk).roles.all()) == [role]
