"""Tests for the ``seed_profiles`` command: the development data behind the contributor pages."""

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from fairdm.contrib.contributors.choices import AccountState
from fairdm.contrib.contributors.models import Affiliation, Organization, Person
from fairdm.management.commands.create_dev_accounts import DEV_ACCOUNT_PASSWORD
from fairdm.factories import PersonFactory

REGULAR_USER = "regular.user@example.com"
ADMIN_USER = "admin.user@example.com"
MEMBER_USER = "member.user@example.com"
FORMER_ADMIN_USER = "former-admin.user@example.com"


def _seed():
    call_command("seed_profiles", verbosity=0)


def _seeded_people():
    return list(Person.objects.filter(config__seed="profiles"))


def _is_non_latin(name):
    """Whether the name holds a character outside the Latin scripts."""
    return any(ord(character) > 0x24F for character in name)


def _seeded_organizations():
    return list(Organization.objects.filter(config__seed="profiles"))


@pytest.fixture
def seeded(db):
    _seed()
    return _seeded_people()


@pytest.fixture
def seeded_organizations(db):
    _seed()
    return _seeded_organizations()


@pytest.mark.django_db
class TestSeedProfilesRefusesOutsideDevelopment:
    @override_settings(DJANGO_ENV="production")
    def test_it_refuses_in_production(self):
        with pytest.raises(CommandError):
            _seed()

    @override_settings(DJANGO_ENV="production")
    def test_a_refusal_creates_no_record(self):
        with pytest.raises(CommandError):
            _seed()

        assert _seeded_people() == []
        assert not Person.objects.filter(email=REGULAR_USER).exists()


@pytest.mark.django_db
class TestSeedProfilesStates:
    def test_a_complete_profile_exists(self, seeded):
        complete = [
            p
            for p in seeded
            if p.orcid_is_authenticated
            and all(p.get_profile_completeness().values())
        ]

        assert complete

    def test_the_signed_in_users_own_profile_is_incomplete(self, seeded):
        me = Person.objects.get(email=REGULAR_USER)

        assert me in seeded
        assert me.account_state == AccountState.CLAIMED
        assert not all(me.get_profile_completeness().values())

    def test_an_unclaimed_profile_exists(self, seeded):
        states = {p.account_state for p in seeded}

        assert states & {AccountState.GHOST, AccountState.INVITED}

    def test_an_inactive_account_exists(self, seeded):
        assert AccountState.INACTIVE in {p.account_state for p in seeded}

    def test_a_person_credited_on_nothing_exists(self, seeded):
        assert [p for p in seeded if not p.contributions.exists()]

    def test_a_very_long_name_exists(self, seeded):
        assert max(len(p.name) for p in seeded) >= 40

    def test_a_name_in_a_non_latin_script_exists(self, seeded):
        assert [p for p in seeded if _is_non_latin(p.name)]

    def test_every_seeded_page_answers_for_a_visitor(self, seeded, client):
        for person in seeded:
            response = client.get(person.get_absolute_url())

            assert response.status_code == 200, person

    def test_the_signed_in_users_own_page_answers_for_them(self, seeded, client):
        me = Person.objects.get(email=REGULAR_USER)
        client.login(email=REGULAR_USER, password=DEV_ACCOUNT_PASSWORD)

        response = client.get(me.get_absolute_url())

        assert response.status_code == 200


@pytest.mark.django_db
class TestSeedProfilesOrganizationStates:
    def test_an_organization_with_everything_recorded_exists(self, seeded_organizations):
        complete = [
            o
            for o in seeded_organizations
            if all(o.get_record_completeness().values())
            and o.location_id
            and o.parent_id
            and o.sub_organizations.exists()
            and o.get_current_memberships()
            and o.get_public_projects().filter(owner=o).exists()
        ]

        assert complete

    def test_one_the_signed_in_user_owns_exists(self, seeded_organizations):
        me = Person.objects.get(email=REGULAR_USER)

        owned = [
            o
            for o in seeded_organizations
            if o.affiliations.filter(
                person=me, type=Affiliation.MembershipType.OWNER, end_date__isnull=True
            ).exists()
        ]

        assert owned
        assert all(o.is_managed_by(me) for o in owned)

    def test_one_with_nothing_recorded_exists(self, seeded_organizations):
        bare = [
            o
            for o in seeded_organizations
            if not any(o.get_record_completeness().values())
            and not o.location_id
            and not o.parent_id
            and not o.sub_organizations.exists()
            and not o.affiliations.exists()
            and not o.contributions.exists()
            and not o.owned_projects.exists()
            and not o.links
        ]

        assert bare

    def test_every_seeded_organization_page_answers_for_a_visitor(
        self, seeded_organizations, client
    ):
        for organization in seeded_organizations:
            response = client.get(organization.get_absolute_url())

            assert response.status_code == 200, organization

    def test_every_organization_page_answers_for_the_signed_in_user_and_shows_the_checklist_only_to_the_owner(
        self, seeded_organizations, client
    ):
        me = Person.objects.get(email=REGULAR_USER)
        client.login(email=REGULAR_USER, password=DEV_ACCOUNT_PASSWORD)

        for organization in seeded_organizations:
            response = client.get(organization.get_absolute_url())

            assert response.status_code == 200, organization
            assert ("readiness" in response.context) is organization.is_managed_by(me)


@pytest.mark.django_db
class TestSeedProfilesIsSafeToRunAgain:
    def test_a_second_run_leaves_the_same_number_of_people(self, seeded):
        _seed()

        assert len(_seeded_people()) == len(seeded)

    def test_a_person_it_did_not_create_survives_a_run(self, db):
        bystander = PersonFactory(email="bystander@example.org")

        _seed()
        _seed()

        assert Person.objects.filter(pk=bystander.pk).exists()


def _owned_organization():
    me = Person.objects.get(email=REGULAR_USER)
    return Organization.objects.get(
        affiliations__person=me,
        affiliations__type=Affiliation.MembershipType.OWNER,
        affiliations__end_date__isnull=True,
    )


@pytest.fixture
def owned_organization(db):
    """The organization the regular user owns, once the profiles are seeded."""
    _seed()
    return _owned_organization()


def _affiliation(organization, email):
    return organization.affiliations.get(person__email=email)


@pytest.mark.django_db
class TestSeedProfilesKeepersOfTheOwnedOrganization:
    def test_an_administrator_is_a_current_administrator_of_it(self, owned_organization):
        affiliation = _affiliation(owned_organization, ADMIN_USER)

        assert affiliation.type == Affiliation.MembershipType.ADMIN
        assert affiliation.end_date is None

    def test_an_ordinary_member_is_a_current_member_of_it(self, owned_organization):
        affiliation = _affiliation(owned_organization, MEMBER_USER)

        assert affiliation.type == Affiliation.MembershipType.MEMBER
        assert affiliation.end_date is None

    def test_an_administrator_whose_affiliation_has_ended_was_one_of_it(
        self, owned_organization
    ):
        affiliation = _affiliation(owned_organization, FORMER_ADMIN_USER)

        assert affiliation.type == Affiliation.MembershipType.ADMIN
        assert affiliation.end_date is not None

    def test_only_the_owner_and_the_administrator_may_edit_it(self, owned_organization):
        who = {
            email: Person.objects.get(email=email)
            for email in (REGULAR_USER, ADMIN_USER, MEMBER_USER, FORMER_ADMIN_USER)
        }

        allowed = {
            email
            for email, person in who.items()
            if owned_organization.is_editable_by(person)
        }

        assert allowed == {REGULAR_USER, ADMIN_USER}

    @pytest.mark.parametrize("email", [ADMIN_USER, MEMBER_USER, FORMER_ADMIN_USER])
    def test_each_account_signs_in_with_the_shared_password(
        self, owned_organization, client, email
    ):
        assert client.login(email=email, password=DEV_ACCOUNT_PASSWORD)

    @pytest.mark.parametrize("email", [ADMIN_USER, MEMBER_USER, FORMER_ADMIN_USER])
    def test_each_account_is_an_active_claimed_profile(self, owned_organization, email):
        person = Person.objects.get(email=email)

        assert person.account_state == AccountState.CLAIMED

    def test_the_administrator_reaches_the_editing_page_and_the_member_does_not(
        self, owned_organization, client
    ):
        url = owned_organization.get_update_url()

        client.login(email=ADMIN_USER, password=DEV_ACCOUNT_PASSWORD)
        as_admin = client.get(url).status_code
        client.login(email=MEMBER_USER, password=DEV_ACCOUNT_PASSWORD)
        as_member = client.get(url).status_code

        assert (as_admin, as_member) == (200, 403)

    def test_a_second_run_leaves_each_account_and_affiliation_once(
        self, owned_organization
    ):
        _seed()

        organization = _owned_organization()
        for email in (ADMIN_USER, MEMBER_USER, FORMER_ADMIN_USER):
            assert Person.objects.filter(email=email).count() == 1
            assert organization.affiliations.filter(person__email=email).count() == 1
