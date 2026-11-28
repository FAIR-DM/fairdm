"""Tests for the contributor managers."""

import pytest

from fairdm.contrib.contributors.choices import AccountState
from fairdm.contrib.contributors.models import Affiliation, Contribution, Person
from fairdm.contrib.contributors.tasks import detect_duplicate_contributors
from fairdm.core.vocabularies import CONTRIBUTOR_ROLES


class TestPersonQuerysets:
    @pytest.mark.django_db
    def test_unclaimed_queryset(self, unclaimed_person):
        claimed = Person.objects.create(
            email="claimed@example.com",
            first_name="Claimed",
            last_name="Test",
            is_active=True,
            is_claimed=True,
        )
        claimed.set_password("testpass123")
        claimed.save()

        unclaimed_persons = Person.objects.unclaimed()

        assert unclaimed_person in unclaimed_persons
        assert claimed not in unclaimed_persons


class TestAccountStateFilters:
    @pytest.mark.django_db
    def test_filters_partition_the_whole_table_exactly_once(
        self, contributor_population
    ):
        state_to_queryset = {
            AccountState.GHOST: Person.objects.ghost(),
            AccountState.INVITED: Person.objects.invited(),
            AccountState.CLAIMED: Person.objects.claimed(),
            AccountState.INACTIVE: Person.objects.inactive(),
        }

        all_people = list(Person.objects.all())
        assert all_people

        for person in all_people:
            matching_states = [
                state for state, qs in state_to_queryset.items() if person in qs
            ]
            assert matching_states == [person.account_state]


class TestPersonManagerCreation:
    @pytest.mark.django_db
    def test_create_user_normalises_email_and_sets_usable_password(self):
        person = Person.objects.create_user(
            email="New.Person@EXAMPLE.com",
            password="s3cret-pass",
            first_name="New",
            last_name="Person",
        )

        assert person.pk is not None
        assert person.email == "New.Person@example.com"
        assert person.has_usable_password() is True
        assert person.check_password("s3cret-pass") is True
        assert person.is_staff is False
        assert person.is_superuser is False

    @pytest.mark.django_db
    def test_create_user_without_password_sets_unusable_password(self):
        person = Person.objects.create_user(
            email="nopassword@example.com", first_name="No", last_name="Password"
        )

        assert person.has_usable_password() is False

    @pytest.mark.django_db
    def test_create_superuser_sets_staff_and_superuser_flags(self):
        superuser = Person.objects.create_superuser(
            email="admin@example.com",
            password="s3cret-pass",
            first_name="Admin",
            last_name="User",
        )

        assert superuser.is_staff is True
        assert superuser.is_superuser is True
        assert superuser.has_usable_password() is True

    @pytest.mark.django_db
    def test_create_superuser_refuses_is_staff_false(self):
        with pytest.raises(ValueError):
            Person.objects.create_superuser(
                email="notstaff@example.com", password="s3cret-pass", is_staff=False
            )

    @pytest.mark.django_db
    def test_create_unclaimed_produces_attribution_only_shape(self):
        person = Person.objects.create_unclaimed(first_name="Ghost", last_name="Person")

        assert person.pk is not None
        assert person.email is None
        assert person.is_claimed is False
        assert person.is_active is True
        assert person.has_usable_password() is False


class TestContributionByRole:
    @pytest.mark.django_db
    def test_by_role_filters_correctly(self, contribution):
        from controlled_vocabularies.models import Record

        role = Record.objects.get(uri=f"{CONTRIBUTOR_ROLES}/editor")
        contribution.roles.add(role)
        contribution.save()

        qs = Contribution.objects.by_role(role.uri)

        assert contribution in qs

    @pytest.mark.django_db
    def test_by_role_excludes_non_matching(self, contribution):
        qs = Contribution.objects.by_role(f"{CONTRIBUTOR_ROLES}/no-such-role")

        assert contribution not in qs


class TestContributionForEntity:
    @pytest.mark.django_db
    def test_for_entity_filters_by_object(
        self, contribution, project_for_contributions, organization
    ):
        from fairdm.factories import ProjectFactory

        other_project = ProjectFactory(owner=organization)

        qs = Contribution.objects.for_entity(project_for_contributions)

        assert contribution in qs

        other_qs = Contribution.objects.for_entity(other_project)
        assert contribution not in other_qs


class TestDuplicateDetection:
    @pytest.mark.django_db
    def test_detect_duplicate_contributors(self):
        Person.objects.create_unclaimed(
            first_name="John",
            last_name="Smith",
        )
        Person.objects.create_unclaimed(
            first_name="John",
            last_name="Smith",
        )

        result = detect_duplicate_contributors()

        assert result["groups_found"] > 0
        assert result["total_duplicates"] >= 2

    @pytest.mark.django_db
    def test_no_duplicates_when_names_differ(self):
        Person.objects.create_unclaimed(
            first_name="Alice",
            last_name="Johnson",
        )
        Person.objects.create_unclaimed(
            first_name="Bob",
            last_name="Williams",
        )

        result = detect_duplicate_contributors()

        assert result["total_duplicates"] == 0


class TestAffiliationQuerysetMethods:
    @pytest.mark.django_db
    def test_affiliation_primary_method(self, db):
        from fairdm.factories import (
            AffiliationFactory,
            OrganizationFactory,
            PersonFactory,
        )

        person = PersonFactory()
        org1 = OrganizationFactory(name="Org 1")
        org2 = OrganizationFactory(name="Org 2")

        aff1 = AffiliationFactory(
            person=person,
            organization=org1,
            is_primary=False,
        )

        aff2 = AffiliationFactory(
            person=person,
            organization=org2,
            is_primary=True,
        )

        primary = person.affiliations.primary()
        assert primary == aff2
        assert primary.is_primary is True

    @pytest.mark.django_db
    def test_affiliation_primary_returns_none_when_no_primary(self, db):
        from fairdm.factories import (
            AffiliationFactory,
            OrganizationFactory,
            PersonFactory,
        )

        person = PersonFactory()
        org = OrganizationFactory()

        AffiliationFactory(
            person=person,
            organization=org,
            is_primary=False,
        )

        primary = person.affiliations.primary()
        assert primary is None

    @pytest.mark.django_db
    def test_affiliation_current_method(self, db):
        from fairdm.factories import (
            AffiliationFactory,
            OrganizationFactory,
            PersonFactory,
        )

        person = PersonFactory()
        org1 = OrganizationFactory(name="Current Org")
        org2 = OrganizationFactory(name="Past Org")

        current_aff = AffiliationFactory(
            person=person,
            organization=org1,
            start_date="2020",
            end_date=None,
        )

        past_aff = AffiliationFactory(
            person=person,
            organization=org2,
            start_date="2015",
            end_date="2019",
        )

        current_affiliations = person.affiliations.current()
        assert current_affiliations.count() == 1
        assert current_aff in current_affiliations
        assert past_aff not in current_affiliations

    @pytest.mark.django_db
    def test_affiliation_past_method(self, db):
        from fairdm.factories import (
            AffiliationFactory,
            OrganizationFactory,
            PersonFactory,
        )

        person = PersonFactory()
        org1 = OrganizationFactory(name="Current Org")
        org2 = OrganizationFactory(name="Past Org")

        current_aff = AffiliationFactory(
            person=person,
            organization=org1,
            start_date="2020",
            end_date=None,
        )

        past_aff = AffiliationFactory(
            person=person,
            organization=org2,
            start_date="2015",
            end_date="2019",
        )

        past_affiliations = person.affiliations.past()
        assert past_affiliations.count() == 1
        assert past_aff in past_affiliations
        assert current_aff not in past_affiliations


class TestAffiliationOwnersMethod:
    @pytest.mark.django_db
    def test_owners_excludes_an_owner_affiliation_that_has_ended(self, db):
        from fairdm.factories import (
            AffiliationFactory,
            OrganizationFactory,
            PersonFactory,
        )

        org = OrganizationFactory(name="Ended Owner Org")
        ended_owner = AffiliationFactory(
            person=PersonFactory(),
            organization=org,
            type=Affiliation.MembershipType.OWNER,
            end_date="2020",
        )

        owners = org.affiliations.owners()

        assert owners.count() == 0
        assert ended_owner not in owners

    @pytest.mark.django_db
    def test_owners_returns_a_current_owner_affiliation(self, db):
        from fairdm.factories import (
            AffiliationFactory,
            OrganizationFactory,
            PersonFactory,
        )

        org = OrganizationFactory(name="Current Owner Org")
        current_owner = AffiliationFactory(
            person=PersonFactory(),
            organization=org,
            type=Affiliation.MembershipType.OWNER,
            end_date=None,
        )

        owners = org.affiliations.owners()

        assert owners.count() == 1
        assert current_owner in owners

    @pytest.mark.django_db
    def test_owners_excludes_current_non_owner_types(self, db):
        from fairdm.factories import (
            AffiliationFactory,
            OrganizationFactory,
            PersonFactory,
        )

        org = OrganizationFactory(name="Members Org")
        AffiliationFactory(
            person=PersonFactory(),
            organization=org,
            type=Affiliation.MembershipType.MEMBER,
            end_date=None,
        )
        AffiliationFactory(
            person=PersonFactory(),
            organization=org,
            type=Affiliation.MembershipType.ADMIN,
            end_date=None,
        )

        assert org.affiliations.owners().count() == 0


class TestRealContributors:
    @pytest.mark.django_db
    def test_excludes_superusers_and_the_anonymous_placeholder(
        self, contributor_population
    ):
        real = Person.objects.real()

        assert contributor_population.superuser not in real
        assert contributor_population.anonymous not in real

    @pytest.mark.django_db
    def test_keeps_every_other_account_state(self, contributor_population):
        real = Person.objects.real()

        assert contributor_population.ghost in real
        assert contributor_population.invited in real
        assert contributor_population.claimed in real
        assert contributor_population.inactive in real


class TestActiveAccounts:
    @pytest.mark.django_db
    def test_returns_only_active_people(self, contributor_population):
        active = Person.objects.active()

        assert contributor_population.ghost in active
        assert contributor_population.invited in active
        assert contributor_population.claimed in active
        assert contributor_population.inactive not in active


@pytest.mark.django_db
class TestPersonQuerySetForCards:
    def test_reading_a_card_costs_no_query_after_the_fetch(
        self, django_assert_num_queries
    ):
        from allauth.socialaccount.models import SocialAccount

        from fairdm.factories import (
            AffiliationFactory,
            ContributorIdentifierFactory,
            PersonFactory,
        )

        person = PersonFactory()
        identifier = ContributorIdentifierFactory(related=person)
        SocialAccount.objects.create(
            user=person, provider="orcid", uid=identifier.value
        )
        AffiliationFactory(person=person, is_primary=True)
        fetched = Person.objects.for_cards().get(pk=person.pk)

        with django_assert_num_queries(0):
            assert fetched.get_default_identifier() == identifier
            assert fetched.orcid_is_authenticated
            assert fetched.primary_organization is not None
            assert fetched.portal_roles == []


@pytest.mark.django_db
class TestContributionKinds:
    @pytest.fixture
    def credited(self):
        from fairdm.factories import (
            ContributionFactory,
            DatasetFactory,
            OrganizationFactory,
            PersonFactory,
        )

        dataset = DatasetFactory()
        Contribution.objects.filter(
            content_type__model="dataset", object_id=dataset.pk
        ).delete()
        organization = ContributionFactory(
            content_object=dataset, contributor=OrganizationFactory(), level=None
        )
        first = ContributionFactory(content_object=dataset, contributor=PersonFactory())
        second = ContributionFactory(
            content_object=dataset, contributor=PersonFactory()
        )
        return dataset, organization, first, second

    def test_people_are_the_contributions_of_a_person(self, credited):
        dataset, organization, first, second = credited

        people = Contribution.objects.for_entity(dataset).people()

        assert organization not in people
        assert set(people) == {first, second}

    def test_organizations_are_the_contributions_of_an_organization(self, credited):
        dataset, organization, first, second = credited

        organizations = Contribution.objects.for_entity(dataset).organizations()

        assert list(organizations) == [organization]

    def test_each_is_ordered_by_order_then_pk(self, credited):
        dataset, organization, first, second = credited
        scoped = Contribution.objects.for_entity(dataset)
        Contribution.objects.filter(pk__in=[first.pk, second.pk]).update(order=7)

        assert list(scoped.people()) == [first, second]

        Contribution.objects.filter(pk=first.pk).update(order=9)

        assert list(scoped.people()) == [second, first]

    def test_the_kind_is_decided_in_the_query(
        self, credited, django_assert_num_queries
    ):
        dataset, *_ = credited
        Contribution.objects.for_entity(dataset)

        with django_assert_num_queries(1):
            list(Contribution.objects.for_entity(dataset).people())
        with django_assert_num_queries(1):
            list(Contribution.objects.for_entity(dataset).organizations())
