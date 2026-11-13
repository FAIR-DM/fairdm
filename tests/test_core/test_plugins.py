"""Tests for the plugin base classes the core record pages share."""

import pytest

from fairdm.contrib.contributors.models import Organization, Person
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.core.plugins import RecordOverviewPlugin
from fairdm.core.vocabularies import CONTRIBUTOR_ROLES, IDENTIFIER_TYPES
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
        ProjectIdentifierFactory(
            related=project, type_id=f"{IDENTIFIER_TYPES}/doi", value="10.1234/abc"
        )

        [identifier] = _plugin_for(project).get_identifiers()

        assert identifier["type"].uri == f"{IDENTIFIER_TYPES}/doi"
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
        SampleIdentifierFactory(
            related=sample, type_id=f"{IDENTIFIER_TYPES}/igsn", value="10.60516/AU1101"
        )

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
        SampleIdentifierFactory(
            related=sample, type_id=f"{IDENTIFIER_TYPES}/igsn", value="AU1101"
        )

        [identifier] = _plugin_for(sample).get_identifiers()

        assert identifier["link"] is None

    def test_an_identifier_of_another_type_is_not_linked(self):
        project = ProjectFactory()
        ProjectIdentifierFactory(
            related=project,
            type_id=f"{IDENTIFIER_TYPES}/grant-number",
            value="GRANT-2024-001",
        )

        [identifier] = _plugin_for(project).get_identifiers()

        assert identifier["link"] is None

    def test_a_grant_number_that_looks_like_a_doi_is_not_linked(self):
        project = ProjectFactory()
        ProjectIdentifierFactory(
            related=project,
            type_id=f"{IDENTIFIER_TYPES}/grant-number",
            value="10.13039/501100001659",
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
        project.add_contributor(
            person,
            with_roles=[
                f"{CONTRIBUTOR_ROLES}/creator",
                f"{CONTRIBUTOR_ROLES}/contact-person",
            ],
        )
        project.add_contributor(organisation, with_roles=[f"{CONTRIBUTOR_ROLES}/other"])
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

        assert plugin.get_role_uris(credit) == {
            f"{CONTRIBUTOR_ROLES}/creator",
            f"{CONTRIBUTOR_ROLES}/contact-person",
        }

    def test_the_contributors_holding_a_role_are_picked_out_of_the_credits(
        self, credited
    ):
        project, person, _ = credited
        plugin = _plugin_for(project)

        entries = plugin.get_credits()

        assert [
            c.pk
            for c in plugin.get_contributors_with_role(
                entries, f"{CONTRIBUTOR_ROLES}/creator"
            )
        ] == [person.pk]
        assert (
            plugin.get_contributors_with_role(entries, f"{CONTRIBUTOR_ROLES}/editor")
            == []
        )


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

        named = _plugin_for(project).get_people()["named"]

        assert [row["contributor"].pk for row in named] == [
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


@pytest.mark.django_db
class TestRecordOverviewPluginPeople:
    @pytest.fixture
    def plugin(self):
        plugin = _plugin_for(ProjectFactory())
        plugin.people_named = 2
        plugin.people_faces = 3
        return plugin

    @staticmethod
    def entries(n, roles=("Creator",)):
        return [
            {
                "contributor": f"contributor {i}",
                "roles": {f"role-{r}": r for r in roles},
                "affiliation": None,
            }
            for i in range(n)
        ]

    def test_the_first_credits_are_named_then_faces_then_a_count(self, plugin):
        people = plugin.get_people(self.entries(7))

        assert [row["contributor"] for row in people["named"]] == [
            "contributor 0",
            "contributor 1",
        ]
        assert people["faces"] == ["contributor 2", "contributor 3", "contributor 4"]
        assert (people["more"], people["total"]) == (2, 7)

    def test_a_named_credit_shows_two_roles_and_counts_the_rest(self, plugin):
        people = plugin.get_people(self.entries(1, roles=("creator", "editor", "x")))

        [row] = people["named"]
        assert row["roles"] == ["Creator", "Editor"]
        assert row["more_roles"] == 1

    def test_with_nobody_credited_there_is_nothing_to_show(self, plugin):
        assert plugin.get_people([]) == {
            "named": [],
            "faces": [],
            "more": 0,
            "total": 0,
        }


class TestRecordOverviewPluginPrimaryIdentifier:
    def test_the_first_identifier_that_resolves_is_the_primary_one(self):
        identifiers = [
            {"type": "grant", "value": "G-1", "link": None},
            {"type": "doi", "value": "10.1/a", "link": "https://doi.org/10.1/a"},
            {"type": "igsn", "value": "10.2/b", "link": "https://doi.org/10.2/b"},
        ]

        primary = RecordOverviewPlugin.get_primary_identifier(identifiers)

        assert primary["value"] == "10.1/a"

    def test_a_record_with_no_resolving_identifier_has_none(self):
        identifiers = [{"type": "grant", "value": "G-1", "link": None}]

        assert RecordOverviewPlugin.get_primary_identifier(identifiers) is None


@pytest.mark.django_db
class TestRecordOverviewPluginTypeMix:
    def test_samples_and_measurements_are_counted_apart_with_the_largest_count(self):
        from demo.factories import RockSampleFactory, XRFMeasurementFactory
        from fairdm.core.measurement.models import Measurement
        from fairdm.core.sample.models import Sample

        dataset = DatasetFactory()
        rocks = RockSampleFactory.create_batch(3, dataset=dataset)
        XRFMeasurementFactory(sample=rocks[0], dataset=dataset)

        mix = _plugin_for(dataset).get_type_mix(
            Sample.objects.filter(dataset=dataset),
            Measurement.objects.filter(dataset=dataset),
        )

        assert [n for _label, n in mix["samples"]] == [3]
        assert [n for _label, n in mix["measurements"]] == [1]
        assert mix["max"] == 3

    def test_with_no_records_there_is_no_mix(self):
        from fairdm.core.measurement.models import Measurement
        from fairdm.core.sample.models import Sample

        assert (
            _plugin_for(DatasetFactory()).get_type_mix(
                Sample.objects.none(), Measurement.objects.none()
            )
            is None
        )
