"""Tests for the plugin base classes the core record pages share."""

import pytest

from fairdm.contrib.contributors.models import Organization, Person
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.core.plugins import RecordOverviewPlugin
from fairdm.factories import (
    AffiliationFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    SampleIdentifierFactory,
)


def _plugin_for(record):
    plugin = RecordOverviewPlugin()
    plugin.base_object = record
    return plugin


@pytest.mark.django_db
class TestRecordOverviewPluginIdentifiers:
    def test_a_doi_links_to_doi_org(self):
        project = ProjectFactory()
        ProjectIdentifierFactory(related=project, type="DOI", value="10.1234/abc")

        [identifier] = _plugin_for(project).get_identifiers()

        assert identifier["type"] == "DOI"
        assert identifier["value"] == "10.1234/abc"
        assert identifier["link"] == "https://doi.org/10.1234/abc"

    def test_an_igsn_links_to_doi_org(self):
        from demo.models import RockSample

        sample = RockSample.objects.create(
            name="Core",
            dataset=DatasetFactory(),
            rock_type="igneous",
            collection_date="2024-01-15",
        )
        SampleIdentifierFactory(related=sample, type="IGSN", value="10.60516/AU1101")

        [identifier] = _plugin_for(sample).get_identifiers()

        assert identifier["link"] == "https://doi.org/10.60516/AU1101"

    def test_a_legacy_igsn_handle_that_doi_org_cannot_resolve_is_not_linked(self):
        from demo.models import RockSample

        sample = RockSample.objects.create(
            name="Core",
            dataset=DatasetFactory(),
            rock_type="igneous",
            collection_date="2024-01-15",
        )
        SampleIdentifierFactory(related=sample, type="IGSN", value="AU1101")

        [identifier] = _plugin_for(sample).get_identifiers()

        assert identifier["link"] is None

    def test_an_identifier_of_another_type_is_not_linked(self):
        project = ProjectFactory()
        ProjectIdentifierFactory(
            related=project, type="GRANT_NUMBER", value="GRANT-2024-001"
        )

        [identifier] = _plugin_for(project).get_identifiers()

        assert identifier["link"] is None

    def test_a_grant_number_that_looks_like_a_doi_is_not_linked(self):
        project = ProjectFactory()
        ProjectIdentifierFactory(
            related=project, type="GRANT_NUMBER", value="10.13039/501100001659"
        )

        [identifier] = _plugin_for(project).get_identifiers()

        assert identifier["link"] is None

    def test_a_record_with_no_identifiers_gives_an_empty_list(self):
        assert _plugin_for(ProjectFactory()).get_identifiers() == []


@pytest.mark.django_db
class TestRecordOverviewPluginCredits:
    @pytest.fixture
    def credited(self):
        project = ProjectFactory()
        person = PersonFactory(is_active=True)
        organisation = OrganizationFactory()
        project.add_contributor(person, with_roles=["Creator", "ContactPerson"])
        project.add_contributor(organisation, with_roles=["Other"])
        return project, person, organisation

    def test_each_credit_carries_its_contributor_as_its_own_subtype(self, credited):
        project, person, organisation = credited

        contributions = _plugin_for(project).get_contributions()

        assert {type(c.contributor) for c in contributions} == {Person, Organization}
        assert {c.contributor.pk: c.is_person() for c in contributions} == {
            person.pk: True,
            organisation.pk: False,
        }

    def test_a_credit_names_the_roles_it_holds(self, credited):
        project, person, _ = credited
        plugin = _plugin_for(project)

        credit = next(
            c for c in plugin.get_contributions() if c.contributor.pk == person.pk
        )

        assert plugin.get_role_names(credit) == {"Creator", "ContactPerson"}

    def test_the_contributors_holding_a_role_are_picked_out_of_the_credits(
        self, credited
    ):
        project, person, _ = credited
        plugin = _plugin_for(project)

        entries = plugin.get_credits()

        assert [
            c.pk for c in plugin.get_contributors_with_role(entries, "Creator")
        ] == [person.pk]
        assert plugin.get_contributors_with_role(entries, "Editor") == []


@pytest.mark.django_db
class TestRecordOverviewPluginOrder:
    @pytest.fixture
    def reordered(self):
        """A project credited organization, person, organization, person, then reordered."""
        project = ProjectFactory()
        first_org, second_org = OrganizationFactory(), OrganizationFactory()
        first_person, second_person = PersonFactory(), PersonFactory()
        for contributor in (first_org, first_person, second_org, second_person):
            project.add_contributor(contributor)
        crediting = Crediting(project)
        crediting.move(project.contributors.get(contributor=second_person), "up")
        crediting.move(project.contributors.get(contributor=first_org), "down")
        return project, [second_person, first_person], [second_org, first_org]

    def test_people_come_first_in_order_then_organizations_in_order(self, reordered):
        project, people, organizations = reordered

        contributions = _plugin_for(project).get_contributions()

        assert [c.contributor.pk for c in contributions] == [
            contributor.pk for contributor in (*people, *organizations)
        ]

    def test_the_credits_follow_the_same_order(self, reordered):
        project, people, organizations = reordered

        entries = _plugin_for(project).get_credits()

        assert [e["contributor"].pk for e in entries] == [
            contributor.pk for contributor in (*people, *organizations)
        ]

    def test_the_people_card_follows_the_same_order(self, reordered):
        project, people, organizations = reordered

        shown = _plugin_for(project).get_people()["shown"]

        assert [c.pk for c in shown] == [
            contributor.pk for contributor in (*people, *organizations)
        ]


@pytest.mark.django_db
class TestRecordOverviewPluginAffiliation:
    @pytest.fixture
    def person(self):
        person = PersonFactory(is_active=True)
        AffiliationFactory(person=person, is_primary=True)
        return person

    def test_a_person_credited_with_no_organization_is_shown_with_none(self, person):
        project = ProjectFactory()
        Crediting(project).add(person)

        (entry,) = _plugin_for(project).get_credits()

        assert entry["affiliation"] is None

    def test_a_person_credited_from_an_organization_is_shown_with_it(self, person):
        project = ProjectFactory()
        organization = OrganizationFactory()
        Crediting(project).add(person, organization=organization)

        entries = _plugin_for(project).get_credits()

        assert {e["contributor"].pk: e["affiliation"] for e in entries}[
            person.pk
        ] == organization
