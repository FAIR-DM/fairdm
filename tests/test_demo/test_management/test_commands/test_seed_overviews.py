"""Tests for the ``seed_overviews`` command: the development data behind the overview pages."""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models import Count
from django.test import override_settings
from django.urls import reverse

from demo.seed.measurements import PROJECT as MEASUREMENT_PROJECT
from demo.seed.projects import EMPTY, SEEDED_NAMES, SHOWCASE
from demo.seed.samples import PROJECT as SAMPLE_PROJECT
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.factories import DatasetFactory, ProjectFactory, UserFactory
from fairdm.management.commands.create_dev_accounts import (
    DEV_ACCOUNT_PASSWORD,
    EXAMPLE_ACCOUNT_EMAILS,
)

Person = get_user_model()

ACCOUNTS = {
    "regular": "regular.user@example.com",
    "staff": "staff.user@example.com",
    "super": "super.user@example.com",
}
EVERY_SEEDED_PROJECT_NAME = [*SEEDED_NAMES, SAMPLE_PROJECT, MEASUREMENT_PROJECT]


def _seed():
    call_command("seed_overviews", verbosity=0)


def _records():
    """What the command leaves behind: project and dataset names, and how many records each holds.

    Sample and measurement names come from a random generator the command does not seed, so
    only their numbers are compared.
    """
    return {
        "projects": sorted(Project.objects.values_list("name", flat=True)),
        "datasets": sorted(Dataset.all_objects.values_list("name", flat=True)),
        "samples per dataset": sorted(
            Dataset.all_objects.annotate(n=Count("samples")).values_list("name", "n")
        ),
        "measurements per dataset": sorted(
            Dataset.all_objects.annotate(n=Count("measurements")).values_list(
                "name", "n"
            )
        ),
    }


def _seeded_projects():
    return Project.objects.filter(name__in=EVERY_SEEDED_PROJECT_NAME)


@pytest.mark.django_db
class TestSeedOverviewsRefusesOutsideDevelopment:
    @override_settings(DJANGO_ENV="production")
    def test_it_refuses_in_production(self):
        with pytest.raises(CommandError):
            _seed()

    @override_settings(DJANGO_ENV="production")
    def test_a_refusal_creates_no_account_and_no_record(self):
        with pytest.raises(CommandError):
            _seed()

        assert not Person.objects.filter(email__in=EXAMPLE_ACCOUNT_EMAILS).exists()
        assert not _seeded_projects().exists()

    def test_it_runs_in_development(self):
        _seed()

        assert _seeded_projects().exists()


@pytest.mark.django_db
class TestSeedOverviewsAccounts:
    def test_it_creates_the_three_example_accounts_when_they_are_missing(self):
        _seed()

        assert set(
            Person.objects.filter(email__in=EXAMPLE_ACCOUNT_EMAILS).values_list(
                "email", flat=True
            )
        ) == set(ACCOUNTS.values())

    def test_each_account_holds_the_published_password(self):
        _seed()

        for email in ACCOUNTS.values():
            assert Person.objects.get(email=email).check_password(DEV_ACCOUNT_PASSWORD)

    def test_only_the_super_user_is_a_superuser(self):
        _seed()

        flags = {
            key: Person.objects.get(email=email).is_superuser
            for key, email in ACCOUNTS.items()
        }
        assert flags == {"regular": False, "staff": False, "super": True}

    def test_each_account_signs_in(self, client):
        _seed()

        for email in ACCOUNTS.values():
            client.logout()
            client.post(
                reverse("account_login"),
                {"login": email, "password": DEV_ACCOUNT_PASSWORD},
            )
            assert "_auth_user_id" in client.session, email

    def test_an_account_that_already_exists_is_left_untouched(self):
        existing = Person.objects.create_user(
            email=ACCOUNTS["staff"],
            password="my own password",
            first_name="Somebody",
            last_name="Else",
        )

        _seed()

        existing.refresh_from_db()
        assert existing.check_password("my own password")
        assert not existing.check_password(DEV_ACCOUNT_PASSWORD)
        assert (existing.first_name, existing.last_name) == ("Somebody", "Else")
        assert existing.is_staff is False

    def test_the_command_still_creates_the_accounts_that_are_missing_beside_one_that_exists(
        self,
    ):
        Person.objects.create_user(email=ACCOUNTS["staff"], password="x")

        _seed()

        assert Person.objects.filter(email__in=EXAMPLE_ACCOUNT_EMAILS).count() == 3


@pytest.mark.django_db
class TestSeedOverviewsTeams:
    def test_the_staff_user_may_change_the_seeded_records_that_have_a_team(self):
        _seed()
        staff = Person.objects.get(email=ACCOUNTS["staff"])

        showcase = Project.objects.get(name=SHOWCASE)
        datasets = Dataset.all_objects.filter(project=showcase)
        assert staff.has_perm("project.change_project", showcase)
        assert datasets.exists()
        for dataset in datasets:
            assert staff.has_perm("dataset.change_dataset", dataset)

    def test_the_staff_user_is_on_the_team_of_the_empty_project(self):
        _seed()
        staff = Person.objects.get(email=ACCOUNTS["staff"])

        empty = Project.objects.get(name=EMPTY)

        assert staff.has_perm("project.change_project", empty)

    def test_the_regular_user_is_on_no_team(self):
        _seed()
        regular = Person.objects.get(email=ACCOUNTS["regular"])

        for project in _seeded_projects():
            assert not regular.has_perm("project.change_project", project)
        for dataset in Dataset.all_objects.filter(project__in=_seeded_projects()):
            assert not regular.has_perm("dataset.change_dataset", dataset)

    def test_the_regular_user_may_not_open_the_private_empty_project(self, client):
        _seed()
        client.login(email=ACCOUNTS["regular"], password=DEV_ACCOUNT_PASSWORD)
        empty = Project.objects.get(name=EMPTY)

        response = client.get(
            reverse("project:overview", kwargs={"uuid": empty.uuid})
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestSeedOverviewsIsSafeToRunAgain:
    def test_a_second_run_leaves_the_same_records(self):
        _seed()
        first = _records()

        _seed()

        assert _records() == first

    def test_a_second_run_leaves_the_same_accounts(self):
        _seed()
        _seed()

        assert Person.objects.filter(email__in=EXAMPLE_ACCOUNT_EMAILS).count() == 3

    def test_a_project_it_did_not_create_survives_a_run_even_when_it_shares_a_seeded_name(
        self,
    ):
        owner = UserFactory()
        foreign = [
            ProjectFactory(name=name, created_by=owner)
            for name in EVERY_SEEDED_PROJECT_NAME
        ]
        foreign_datasets = [DatasetFactory(project=project) for project in foreign]

        _seed()
        _seed()

        assert Project.objects.filter(pk__in=[p.pk for p in foreign]).count() == len(
            foreign
        )
        assert Dataset.all_objects.filter(
            pk__in=[d.pk for d in foreign_datasets]
        ).count() == len(foreign_datasets)

    def test_a_run_replaces_the_records_the_earlier_run_created(self):
        _seed()
        before = set(_seeded_projects().values_list("pk", flat=True))

        _seed()

        after = set(_seeded_projects().values_list("pk", flat=True))
        assert before
        assert not before & after
