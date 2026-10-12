"""Tests for the ``seed_contributors`` command: the development data behind the Contributors tab."""

import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, override_settings

from demo.seed.contributors import PROJECT, STEP_IN
from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Contribution, Person
from fairdm.contrib.plugins import reverse
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.management.commands.create_dev_accounts import (
    DEV_ACCOUNT_PASSWORD,
    DEV_ACCOUNTS,
)
from fairdm.portal_roles import PortalRoles
from fairdm.utils.choices import Visibility

CURATOR = next(a["email"] for a in DEV_ACCOUNTS if a["role"] == "Data Curator")


def seed(*options):
    call_command("seed_contributors", *options, verbosity=0)


def addresses():
    """The address of every record seeded before the curator's, to compare before and after."""
    records = [
        *Project.objects.filter(name=PROJECT),
        *Dataset.all_objects.filter(project__name=PROJECT),
        *Dataset.all_objects.filter(project=None).exclude(name=STEP_IN),
    ]
    return sorted(reverse(record, "contribution-list") for record in records)


def stepping_in_record():
    return Dataset.all_objects.get(name=STEP_IN)


@pytest.mark.django_db
class TestSeedContributorsRefusesOutsideDevelopment:
    @override_settings(DJANGO_ENV="production")
    def test_it_refuses_and_creates_nothing(self):
        with pytest.raises(CommandError):
            seed()

        assert not Dataset.all_objects.filter(name=STEP_IN).exists()


@pytest.mark.django_db
class TestDataCuratorRecord:
    def test_the_data_curator_account_holds_the_role(self):
        seed()

        curator = Person.objects.get(email=CURATOR)
        assert curator.groups.filter(name=PortalRoles.DATA_CURATOR.name).exists()
        assert curator.check_password(DEV_ACCOUNT_PASSWORD)

    def test_the_record_is_private_and_the_curator_is_not_listed_on_it(self):
        seed()

        record = stepping_in_record()
        assert record.visibility == Visibility.PRIVATE
        assert not record.contributors.filter(contributor_id=Person.objects.get(email=CURATOR).pk).exists()

    def test_nobody_on_the_record_counts_as_able_to_manage_it(self):
        seed()

        record = stepping_in_record()
        assert record.contributors.filter(level=ContributionLevel.MANAGE).exists()
        assert RecordAccess(record).managers() == set()

    def test_the_record_has_a_person_to_raise_and_an_organization_they_are_credited_from(
        self,
    ):
        seed()

        record = stepping_in_record()
        raised = record.contributors.get(level=ContributionLevel.VIEW)
        assert raised.affiliation_id is not None
        assert record.contributors.filter(contributor=raised.affiliation).exists()

    def test_the_curator_opens_its_tab_and_the_curator_may_manage_it(self):
        seed()
        browser = Client()
        browser.force_login(Person.objects.get(email=CURATOR))

        response = browser.get(reverse(stepping_in_record(), "contribution-list"))

        assert response.status_code == 200
        assert RecordAccess(stepping_in_record()).can_manage(response.wsgi_request.user)

    def test_running_it_again_replaces_the_record_and_adds_no_second(self):
        seed()
        seed()

        assert Dataset.all_objects.filter(name=STEP_IN).count() == 1


@pytest.mark.django_db
class TestKeepRecords:
    def test_it_adds_the_record_to_a_database_seeded_before_it_existed(self):
        seed()
        stepping_in_record().delete()
        Group.objects.get(name=PortalRoles.DATA_CURATOR.name).user_set.clear()
        before = addresses()

        seed("--keep-records")

        assert addresses() == before
        assert Person.objects.get(email=CURATOR).groups.exists()
        assert stepping_in_record().contributors.filter(
            level=ContributionLevel.MANAGE
        ).exists()

    def test_it_changes_no_existing_address_and_is_safe_to_repeat(self):
        seed()
        before = addresses()
        contributions = Contribution.objects.count()

        seed("--keep-records")
        seed("--keep-records")

        assert addresses() == before
        assert Contribution.objects.count() == contributions
        assert Dataset.all_objects.filter(name=STEP_IN).count() == 1
