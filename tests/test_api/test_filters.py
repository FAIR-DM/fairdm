"""Visibility filter tests for FairDM API (Feature 011 â€” US4)."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility
from tests.test_api.conftest import make_token_client


@pytest.mark.django_db
class TestVisibilityFilterProjects:
    def test_public_project_visible_to_anonymous(self):
        proj = ProjectFactory(visibility=Visibility.PUBLIC)
        resp = APIClient().get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in resp.json()["results"]]
        assert str(proj.uuid) in uuids

    def test_private_project_hidden_from_anonymous(self):
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        resp = APIClient().get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in resp.json()["results"]]
        assert str(proj.uuid) not in uuids

    def test_private_project_hidden_from_authenticated_without_perm(self):
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        resp = make_token_client(UserFactory()).get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in resp.json()["results"]]
        assert str(proj.uuid) not in uuids

    def test_private_project_visible_to_user_with_view_perm(self):
        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        ContributionFactory(
            content_object=proj, contributor=user, level=ContributionLevel.VIEW
        )
        resp = make_token_client(user).get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in resp.json()["results"]]
        assert str(proj.uuid) in uuids

    def test_a_stored_guardian_row_alone_does_not_list_a_private_project(self):
        from fairdm.core.utils import assign_perm

        user = UserFactory()
        proj = ProjectFactory(visibility=Visibility.PRIVATE)
        assign_perm("view_project", user, proj)
        resp = make_token_client(user).get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in resp.json()["results"]]
        assert str(proj.uuid) not in uuids

    def test_mixed_queryset_no_duplicates(self):
        user = UserFactory()
        pub = ProjectFactory(visibility=Visibility.PUBLIC)
        priv = ProjectFactory(visibility=Visibility.PRIVATE)
        # Grant view on the public project via guardian too (both filter branches apply)
        ContributionFactory(
            content_object=pub, contributor=user, level=ContributionLevel.VIEW
        )
        ContributionFactory(
            content_object=priv, contributor=user, level=ContributionLevel.VIEW
        )

        resp = make_token_client(user).get(reverse("api:project-list"))
        results = resp.json()["results"]
        all_uuids = [p["uuid"] for p in results]
        assert len(all_uuids) == len(set(all_uuids))
        assert str(pub.uuid) in all_uuids
        assert str(priv.uuid) in all_uuids

    def test_anonymous_sees_multiple_public_projects(self):
        proj1 = ProjectFactory(visibility=Visibility.PUBLIC)
        proj2 = ProjectFactory(visibility=Visibility.PUBLIC)
        resp = APIClient().get(reverse("api:project-list"))
        uuids = [p["uuid"] for p in resp.json()["results"]]
        assert str(proj1.uuid) in uuids
        assert str(proj2.uuid) in uuids


@pytest.mark.django_db
class TestVisibilityFilterDatasets:
    def test_public_dataset_visible_to_anonymous(self):
        pub_proj = ProjectFactory(visibility=Visibility.PUBLIC)
        ds = DatasetFactory(
            project=pub_proj, visibility=Visibility.PUBLIC, published=True
        )
        resp = APIClient().get(reverse("api:dataset-list"))
        uuids = [d["uuid"] for d in resp.json()["results"]]
        assert str(ds.uuid) in uuids

    def test_a_level_on_the_project_above_lists_its_private_dataset(self):
        user = UserFactory()
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        ds = DatasetFactory(project=project, visibility=Visibility.PRIVATE)
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.VIEW
        )
        resp = make_token_client(user).get(reverse("api:dataset-list"))
        uuids = [d["uuid"] for d in resp.json()["results"]]
        assert str(ds.uuid) in uuids

    def test_private_dataset_hidden_without_perm(self):
        pub_proj = ProjectFactory(visibility=Visibility.PUBLIC)
        ds = DatasetFactory(project=pub_proj, visibility=Visibility.PRIVATE)
        resp = make_token_client(UserFactory()).get(reverse("api:dataset-list"))
        uuids = [d["uuid"] for d in resp.json()["results"]]
        assert str(ds.uuid) not in uuids

    def test_private_dataset_visible_with_perm(self):
        user = UserFactory()
        pub_proj = ProjectFactory(visibility=Visibility.PUBLIC)
        ds = DatasetFactory(project=pub_proj, visibility=Visibility.PRIVATE)
        ContributionFactory(
            content_object=ds, contributor=user, level=ContributionLevel.VIEW
        )
        resp = make_token_client(user).get(reverse("api:dataset-list"))
        uuids = [d["uuid"] for d in resp.json()["results"]]
        assert str(ds.uuid) in uuids


@pytest.mark.django_db
class TestVisibilityFilterContributors:
    ROUTES = ("api:person-list", "api:organization-list")

    @pytest.mark.parametrize("route", ROUTES)
    def test_all_contributors_visible_to_anonymous(self, route):
        resp = APIClient().get(reverse(route))
        assert resp.status_code == 200

    @pytest.mark.parametrize("route", ROUTES)
    def test_contributor_list_returns_200_for_authenticated(self, route):
        resp = make_token_client(UserFactory()).get(reverse(route))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestVisibilityOfSamplesAndMeasurements:
    @pytest.fixture(params=["sample", "measurement"])
    def case(self, request, make_record, url_of):
        """A public and a private record of a kind, with the address of their list."""
        from types import SimpleNamespace

        from demo.models import ExampleMeasurement, RockSample

        model = RockSample if request.param == "sample" else ExampleMeasurement
        private = DatasetFactory(visibility=Visibility.PRIVATE)
        public = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        return SimpleNamespace(
            private_dataset=private,
            hidden=make_record(model, private),
            shown=make_record(model, public),
            address=url_of(model, "list"),
        )

    @staticmethod
    def listed_by(client, address):
        data = client.get(address).json()
        return {row["uuid"] for row in data["results"]}, data["count"]

    def test_a_person_with_a_level_on_the_dataset_receives_its_records(self, case):
        from rest_framework.test import APIClient

        viewer = UserFactory()
        ContributionFactory(
            content_object=case.private_dataset,
            contributor=viewer,
            level=ContributionLevel.VIEW,
        )
        client = APIClient()
        client.force_authenticate(viewer)

        listed, count = self.listed_by(client, case.address)

        assert listed == {case.hidden.uuid, case.shown.uuid}
        assert count == 2

    def test_a_signed_in_person_with_no_level_receives_only_public_records(self, case):
        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(UserFactory())

        listed, count = self.listed_by(client, case.address)

        assert listed == {case.shown.uuid}
        assert count == 1

    def test_a_visitor_receives_only_public_records(self, case):
        from rest_framework.test import APIClient

        listed, count = self.listed_by(APIClient(), case.address)

        assert listed == {case.shown.uuid}
        assert count == 1


@pytest.mark.django_db
class TestUnpublishedDataset:
    @pytest.fixture(params=["sample", "measurement"])
    def case(self, request, make_record, url_of):
        """A record of a kind in a public dataset that is not published, with its addresses."""
        from types import SimpleNamespace

        from demo.models import ExampleMeasurement, RockSample

        model = RockSample if request.param == "sample" else ExampleMeasurement
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        record = make_record(model, dataset)
        return SimpleNamespace(
            kind=request.param,
            dataset=dataset,
            record=record,
            list_address=url_of(model, "list"),
            address=url_of(record),
            model=model,
        )

    @pytest.fixture(params=["visitor", "outsider"])
    def client(self, request, signed_in):
        """A visitor, and a signed-in person with no level on anything."""
        from fairdm.factories import PersonFactory

        if request.param == "visitor":
            return APIClient()
        return signed_in(PersonFactory(is_active=True, is_claimed=True))

    def test_the_list_leaves_the_record_out(self, client, case):
        data = client.get(case.list_address).json()

        assert data["results"] == []
        assert data["count"] == 0

    def test_the_record_is_not_found(self, client, case):
        assert client.get(case.address).status_code == 404

    def test_a_write_by_a_signed_in_person_with_no_level_is_not_found(
        self, signed_in, case
    ):
        from fairdm.factories import PersonFactory

        client = signed_in(PersonFactory(is_active=True, is_claimed=True))

        assert (
            client.patch(case.address, {"name": "x"}, format="json").status_code == 404
        )
        assert client.delete(case.address).status_code == 404

    def test_a_person_with_a_level_on_the_dataset_reads_the_record(
        self, signed_in, member_at, case
    ):
        client = signed_in(member_at(case.dataset, ContributionLevel.VIEW))

        listed = client.get(case.list_address).json()
        found = client.get(case.address)

        assert [row["uuid"] for row in listed["results"]] == [str(case.record.uuid)]
        assert found.status_code == 200

    def test_the_dataset_itself_stays_readable(self, client, case):
        response = client.get(
            reverse("api:dataset-detail", kwargs={"uuid": case.dataset.uuid})
        )

        assert response.status_code == 200

    def test_a_reference_to_a_sample_of_the_dataset_reads_null(
        self, client, make_record
    ):
        from demo.factories import RockSampleFactory
        from demo.models import ExampleMeasurement

        sample = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        )
        measurement = make_record(
            ExampleMeasurement,
            DatasetFactory(visibility=Visibility.PUBLIC, published=True),
            sample=sample,
        )

        response = client.get(
            reverse(
                "api:measurements-example-measurements-detail",
                kwargs={"uuid": measurement.uuid},
            )
        )

        assert response.status_code == 200
        assert response.json()["sample"] is None


@pytest.mark.django_db
class TestPeopleFilters:
    @staticmethod
    def found(client, **query):
        response = client.get(reverse("api:person-list"), query)
        assert response.status_code == 200, response.content
        return {row["uuid"] for row in response.json()["results"]}

    def test_organization_returns_people_with_a_verified_affiliation_that_has_not_ended(
        self,
    ):
        from fairdm.contrib.contributors.models import Affiliation
        from fairdm.factories import AffiliationFactory, OrganizationFactory

        institute = OrganizationFactory()
        member = AffiliationFactory(
            organization=institute, type=Affiliation.MembershipType.MEMBER
        ).person
        admin = AffiliationFactory(
            organization=institute, type=Affiliation.MembershipType.ADMIN
        ).person
        pending = AffiliationFactory(
            organization=institute, type=Affiliation.MembershipType.PENDING
        ).person
        ended = AffiliationFactory(
            organization=institute, start_date="2015", end_date="2018"
        ).person
        elsewhere = AffiliationFactory(organization=OrganizationFactory()).person
        unaffiliated = PersonFactory()

        found = self.found(APIClient(), organization=institute.uuid)

        assert found == {member.uuid, admin.uuid}
        assert {pending.uuid, ended.uuid, elsewhere.uuid, unaffiliated.uuid}.isdisjoint(
            found
        )

    def test_a_person_with_a_past_and_a_current_affiliation_is_found_once(self):
        from fairdm.factories import AffiliationFactory, OrganizationFactory

        institute = OrganizationFactory()
        person = AffiliationFactory(organization=institute).person
        AffiliationFactory(
            person=person,
            organization=OrganizationFactory(),
            start_date="2010",
            end_date="2012",
        )

        response = APIClient().get(
            reverse("api:person-list"), {"organization": institute.uuid}
        )

        assert [row["uuid"] for row in response.json()["results"]] == [person.uuid]

    def test_a_database_number_for_organization_is_refused(self):
        from fairdm.factories import OrganizationFactory

        institute = OrganizationFactory()

        response = APIClient().get(
            reverse("api:person-list"), {"organization": institute.pk}
        )

        assert response.status_code == 400
        assert "organization" in response.json()

    def test_an_identifier_nobody_holds_in_organization_is_refused_not_listed(self):
        response = APIClient().get(
            reverse("api:person-list"), {"organization": "u" * 23}
        )

        assert response.status_code == 400

    def test_identifier_returns_the_one_holder_given_the_bare_value(self):
        from fairdm.factories import ContributorIdentifierFactory

        holder = PersonFactory()
        other = PersonFactory()
        ContributorIdentifierFactory(
            related=holder, type="ORCID", value="0000-0002-1825-0097"
        )
        ContributorIdentifierFactory(related=other, type="ORCID")

        found = self.found(APIClient(), identifier="0000-0002-1825-0097")

        assert found == {holder.uuid}

    @pytest.mark.parametrize(
        "sent",
        [
            "https://orcid.org/0000-0002-1825-0097",
            "http://orcid.org/0000-0002-1825-0097",
            "https://orcid.org/0000-0002-1825-0097/",
            "  0000-0002-1825-0097  ",
        ],
    )
    def test_identifier_returns_the_holder_given_the_full_address(self, sent):
        from fairdm.factories import ContributorIdentifierFactory

        holder = PersonFactory()
        ContributorIdentifierFactory(
            related=holder, type="ORCID", value="0000-0002-1825-0097"
        )
        PersonFactory()

        found = self.found(APIClient(), identifier=sent)

        assert found == {holder.uuid}

    def test_identifier_finds_a_value_stored_without_the_spaces_it_is_written_with(
        self,
    ):
        from fairdm.factories import ContributorIdentifierFactory

        holder = PersonFactory()
        ContributorIdentifierFactory(
            related=holder, type="ISNI", value="0000000121032683"
        )

        found = self.found(APIClient(), identifier="0000 0001 2103 2683")

        assert found == {holder.uuid}

    def test_identifier_returns_an_empty_list_for_a_value_nobody_holds(self):
        PersonFactory()

        found = self.found(APIClient(), identifier="0000-0000-0000-0000")

        assert found == set()

    def test_identifier_returns_an_empty_list_for_one_a_superuser_holds(self):
        from fairdm.factories import ContributorIdentifierFactory

        administrator = PersonFactory(is_superuser=True, is_staff=True)
        ContributorIdentifierFactory(
            related=administrator, type="ORCID", value="0000-0003-1415-9265"
        )
        PersonFactory()

        found = self.found(APIClient(), identifier="0000-0003-1415-9265")

        assert found == set()

    def test_the_filters_combine_with_each_other(self):
        from fairdm.factories import (
            AffiliationFactory,
            ContributorIdentifierFactory,
            OrganizationFactory,
        )

        institute = OrganizationFactory()
        holder = AffiliationFactory(organization=institute).person
        ContributorIdentifierFactory(
            related=holder, type="ORCID", value="0000-0002-1825-0097"
        )
        outsider = PersonFactory()
        ContributorIdentifierFactory(
            related=outsider, type="ORCID", value="0000-0001-5109-3700"
        )

        found = self.found(
            APIClient(), organization=institute.uuid, identifier="0000-0001-5109-3700"
        )

        assert found == set()


@pytest.mark.django_db
class TestOrganizationFilters:
    @staticmethod
    def found(client, **query):
        response = client.get(reverse("api:organization-list"), query)
        assert response.status_code == 200, response.content
        return {row["uuid"] for row in response.json()["results"]}

    def test_type_returns_only_organizations_of_that_stored_code(self):
        from fairdm.contrib.contributors.choices import OrganizationType
        from fairdm.factories import OrganizationFactory

        university = OrganizationFactory(type=OrganizationType.EDUCATION)
        company = OrganizationFactory(type=OrganizationType.COMPANY)
        untyped = OrganizationFactory(type=None)

        found = self.found(APIClient(), type="education")

        assert found == {university.uuid}
        assert {company.uuid, untyped.uuid}.isdisjoint(found)

    def test_country_returns_only_organizations_in_that_country(self):
        from fairdm.factories import OrganizationFactory

        australian = OrganizationFactory(country="AU")
        german = OrganizationFactory(country="DE")
        unplaced = OrganizationFactory(country=None)

        found = self.found(APIClient(), country="AU")

        assert found == {australian.uuid}
        assert {german.uuid, unplaced.uuid}.isdisjoint(found)

    def test_parent_returns_the_organizations_that_are_part_of_it(self):
        from fairdm.factories import OrganizationFactory

        university = OrganizationFactory()
        physics = OrganizationFactory(parent=university)
        chemistry = OrganizationFactory(parent=university)
        elsewhere = OrganizationFactory(parent=OrganizationFactory())

        found = self.found(APIClient(), parent=university.uuid)

        assert found == {physics.uuid, chemistry.uuid}
        assert {university.uuid, elsewhere.uuid}.isdisjoint(found)

    def test_a_database_number_for_parent_is_refused(self):
        from fairdm.factories import OrganizationFactory

        university = OrganizationFactory()
        OrganizationFactory(parent=university)

        response = APIClient().get(
            reverse("api:organization-list"), {"parent": university.pk}
        )

        assert response.status_code == 400
        assert "parent" in response.json()

    def test_an_identifier_nobody_holds_in_parent_is_refused_not_listed(self):
        response = APIClient().get(
            reverse("api:organization-list"), {"parent": "u" * 23}
        )

        assert response.status_code == 400

    def test_top_level_true_returns_organizations_with_no_parent(self):
        from fairdm.factories import OrganizationFactory

        university = OrganizationFactory()
        department = OrganizationFactory(parent=university)
        standalone = OrganizationFactory()

        found = self.found(APIClient(), top_level="true")

        assert {university.uuid, standalone.uuid} <= found
        assert department.uuid not in found

    def test_top_level_false_returns_organizations_with_a_parent(self):
        from fairdm.factories import OrganizationFactory

        university = OrganizationFactory()
        department = OrganizationFactory(parent=university)

        found = self.found(APIClient(), top_level="false")

        assert department.uuid in found
        assert university.uuid not in found

    def test_identifier_returns_the_one_holder_given_the_bare_value(self):
        from fairdm.factories import ContributorIdentifierFactory, OrganizationFactory

        holder = OrganizationFactory()
        other = OrganizationFactory()
        ContributorIdentifierFactory(related=holder, type="ROR", value="03yrm5c26")
        ContributorIdentifierFactory(related=other, type="ROR", value="05gq02987")

        found = self.found(APIClient(), identifier="03yrm5c26")

        assert found == {holder.uuid}

    @pytest.mark.parametrize(
        "sent",
        [
            "https://ror.org/03yrm5c26",
            "http://ror.org/03yrm5c26",
            "https://ror.org/03yrm5c26/",
            "  03yrm5c26  ",
        ],
    )
    def test_identifier_returns_the_holder_given_the_full_address(self, sent):
        from fairdm.factories import ContributorIdentifierFactory, OrganizationFactory

        holder = OrganizationFactory()
        ContributorIdentifierFactory(related=holder, type="ROR", value="03yrm5c26")
        OrganizationFactory()

        found = self.found(APIClient(), identifier=sent)

        assert found == {holder.uuid}

    def test_identifier_returns_an_empty_list_for_a_value_nobody_holds(self):
        from fairdm.factories import OrganizationFactory

        OrganizationFactory()

        found = self.found(APIClient(), identifier="05gq02987")

        assert found == set()

    def test_the_filters_combine_with_each_other(self):
        from fairdm.factories import ContributorIdentifierFactory, OrganizationFactory

        university = OrganizationFactory()
        australian = OrganizationFactory(parent=university, country="AU")
        german = OrganizationFactory(parent=university, country="DE")
        ContributorIdentifierFactory(related=german, type="ROR", value="03yrm5c26")

        by_parent_and_country = self.found(
            APIClient(), parent=university.uuid, country="AU"
        )
        by_country_and_identifier = self.found(
            APIClient(), country="AU", identifier="03yrm5c26"
        )

        assert by_parent_and_country == {australian.uuid}
        assert by_country_and_identifier == set()
