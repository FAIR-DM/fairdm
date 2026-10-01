"""Tests for the ``seed_profiles`` command: the development data behind the contributor pages."""

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from fairdm.contrib.contributors.choices import AccountState
from fairdm.contrib.contributors.models import Person
from fairdm.management.commands.create_dev_accounts import DEV_ACCOUNT_PASSWORD
from fairdm.factories import PersonFactory

REGULAR_USER = "regular.user@example.com"


def _seed():
    call_command("seed_profiles", verbosity=0)


def _seeded_people():
    return list(Person.objects.filter(config__seed="profiles"))


def _is_non_latin(name):
    """Whether the name holds a character outside the Latin scripts."""
    return any(ord(character) > 0x24F for character in name)


@pytest.fixture
def seeded(db):
    _seed()
    return _seeded_people()


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
class TestSeedProfilesIsSafeToRunAgain:
    def test_a_second_run_leaves_the_same_number_of_people(self, seeded):
        _seed()

        assert len(_seeded_people()) == len(seeded)

    def test_a_person_it_did_not_create_survives_a_run(self, db):
        bystander = PersonFactory(email="bystander@example.org")

        _seed()
        _seed()

        assert Person.objects.filter(pk=bystander.pk).exists()
