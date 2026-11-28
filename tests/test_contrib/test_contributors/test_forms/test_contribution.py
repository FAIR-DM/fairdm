"""Tests for the person creation form and the contribution form."""

import pytest
from controlled_vocabularies.models import Record

from fairdm.contrib.contributors.choices import SyncStatus
from fairdm.contrib.contributors.forms.contribution import (
    PersonCreateForm,
    UpdateContributionForm,
)
from fairdm.contrib.contributors.models import Contribution, Person
from fairdm.core.vocabularies import ORCID, collection_members
from fairdm.factories import (
    ContributionFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
)


@pytest.mark.django_db
class TestPersonCreateForm:
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

    def test_the_orcid_action_saves_the_person_from_their_orcid_record(
        self, registry_network, recorded
    ):
        registry_network.answer(
            "https://pub.orcid.org/v3.0/0000-0002-1825-0097", recorded("orcid-record")
        )
        form = PersonCreateForm(
            {"action": "from_orcid", "from_orcid": "0000-0002-1825-0097"}
        )
        assert form.is_valid(), form.errors

        person = form.save()

        assert person == Person.objects.get(
            identifiers__value="0000-0002-1825-0097", identifiers__type_id=ORCID
        )

    def test_the_orcid_action_stores_the_full_record_once_the_save_is_committed(
        self, registry_network, recorded, django_capture_on_commit_callbacks
    ):
        registry_network.answer(
            "https://pub.orcid.org/v3.0/0000-0002-1825-0097", recorded("orcid-record")
        )
        form = PersonCreateForm(
            {"action": "from_orcid", "from_orcid": "0000-0002-1825-0097"}
        )
        assert form.is_valid(), form.errors

        with django_capture_on_commit_callbacks(execute=True):
            person = form.save()

        person.refresh_from_db()
        assert person.synced_data == recorded("orcid-record")
        assert person.sync_status == SyncStatus.SUCCEEDED


@pytest.mark.django_db
class TestUpdateContributionForm:
    def test_the_chosen_roles_are_saved(self):
        project = ProjectFactory()
        contribution = ContributionFactory(content_object=project)
        allowed = Record.objects.filter(
            uri__in=[role.uri for role in collection_members(project.CONTRIBUTOR_ROLES)]
        )
        role = allowed.first()
        form = UpdateContributionForm(
            {"roles": [role.uri]}, instance=contribution, base_object=project
        )

        assert form.is_valid(), form.errors
        form.save()

        assert list(Contribution.objects.get(pk=contribution.pk).roles.all()) == [role]
