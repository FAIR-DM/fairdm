"""Tests for the contributor managers."""

import pytest

from fairdm.contrib.contributors.choices import AccountState
from fairdm.contrib.contributors.models import Affiliation, Contribution, Person
from fairdm.contrib.contributors.tasks import detect_duplicate_contributors


class TestPersonQuerysets:
    @pytest.mark.django_db
    def test_claimed_queryset(self, person):
        unclaimed = Person.objects.create_unclaimed(
            first_name="Unclaimed",
            last_name="Test",
        )

        claimed_persons = Person.objects.claimed()

        assert person in claimed_persons
        assert unclaimed not in claimed_persons

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

    @pytest.mark.django_db
    def test_claimed_excludes_inactive_with_email(self):
        inactive = Person.objects.create(
            email="inactive@example.com",
            first_name="Inactive",
            last_name="User",
            is_active=False,
        )

        claimed_persons = Person.objects.claimed()

        assert inactive not in claimed_persons


class TestAccountStateFilters:
    @pytest.mark.django_db
    @pytest.mark.parametrize("filter_name", ["ghost", "invited", "claimed", "inactive"])
    def test_filter_returns_exactly_the_matching_population_member(
        self, contributor_population, filter_name
    ):
        pop = contributor_population
        by_state = {
            "ghost": pop.ghost,
            "invited": pop.invited,
            "claimed": pop.claimed,
            "inactive": pop.inactive,
        }
        expected = by_state.pop(filter_name)
        result = getattr(Person.objects, filter_name)()

        assert expected in result
        for other in by_state.values():
            assert other not in result

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
        from research_vocabs.models import Concept, Vocabulary

        vocab, _ = Vocabulary.objects.get_or_create(name="fairdm-roles")
        role, _ = Concept.objects.get_or_create(
            vocabulary=vocab,
            name="TestRole",
        )

        contribution.roles.add(role)
        contribution.save()

        qs = Contribution.objects.by_role("TestRole")

        assert qs.count() > 0
        assert contribution in qs

    @pytest.mark.django_db
    def test_by_role_excludes_non_matching(self, contribution):
        qs = Contribution.objects.by_role("NonExistentRole")

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

    @pytest.mark.django_db
    def test_for_entity_returns_empty_for_new_object(self, organization):
        from fairdm.factories import ProjectFactory

        new_project = ProjectFactory(owner=organization)

        new_project.contributors.all().delete()

        qs = Contribution.objects.for_entity(new_project)

        assert qs.count() == 0


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

    @pytest.mark.django_db
    def test_affiliation_current_and_past_mutually_exclusive(self, db):
        from fairdm.factories import (
            AffiliationFactory,
            OrganizationFactory,
            PersonFactory,
        )

        person = PersonFactory()
        org1 = OrganizationFactory(name="Org 1")
        org2 = OrganizationFactory(name="Org 2")
        org3 = OrganizationFactory(name="Org 3")

        AffiliationFactory(
            person=person,
            organization=org1,
            end_date=None,
        )
        AffiliationFactory(
            person=person,
            organization=org2,
            end_date=None,
        )

        AffiliationFactory(
            person=person,
            organization=org3,
            end_date="2020",
        )

        current = person.affiliations.current()
        past = person.affiliations.past()

        assert current.count() == 2
        assert past.count() == 1

        assert set(current) & set(past) == set()


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


class TestQuerysetManagerParity:
    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "method_name",
        ["real", "active", "claimed", "unclaimed", "ghost", "invited"],
    )
    def test_person_query_matches_between_queryset_and_manager(
        self, contributor_population, method_name
    ):
        from_manager = set(getattr(Person.objects, method_name)())
        from_queryset = set(getattr(Person.objects.all(), method_name)())

        assert from_manager == from_queryset
        assert from_manager

    @pytest.mark.django_db
    @pytest.mark.parametrize("method_name", ["current", "past"])
    def test_membership_query_matches_between_queryset_and_manager(
        self, contributor_population, method_name
    ):
        from_manager = set(getattr(Affiliation.objects, method_name)())
        from_queryset = set(getattr(Affiliation.objects.all(), method_name)())

        assert from_manager == from_queryset
        assert from_manager

    @pytest.mark.django_db
    def test_credit_by_role_query_matches_between_queryset_and_manager(
        self, contributor_population
    ):
        role_name = contributor_population.creator_role.name

        from_manager = set(Contribution.objects.by_role(role_name))
        from_queryset = set(Contribution.objects.all().by_role(role_name))

        assert from_manager == from_queryset
        assert from_manager


@pytest.mark.django_db
class TestPersonQuerySetForCards:
    def test_reading_a_card_costs_no_query_after_the_fetch(self, django_assert_num_queries):
        from allauth.socialaccount.models import SocialAccount

        from fairdm.factories import (
            AffiliationFactory,
            ContributorIdentifierFactory,
            PersonFactory,
        )

        person = PersonFactory()
        identifier = ContributorIdentifierFactory(related=person)
        SocialAccount.objects.create(user=person, provider="orcid", uid=identifier.value)
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

    def test_the_kind_is_decided_in_the_query(self, credited, django_assert_num_queries):
        dataset, *_ = credited
        Contribution.objects.for_entity(dataset)

        with django_assert_num_queries(1):
            list(Contribution.objects.for_entity(dataset).people())
        with django_assert_num_queries(1):
            list(Contribution.objects.for_entity(dataset).organizations())
