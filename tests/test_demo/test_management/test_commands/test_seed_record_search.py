"""Tests for the ``seed_record_search`` command: the data behind a walkthrough of the search fields."""

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from literature.models import Item

from demo.models import RockSample
from demo.seed.record_search import (
    LARGE_DATASET,
    PRIVATE_DATASETS,
    PRIVATE_PROJECT,
    RecordSearchSeed,
)
from fairdm.contrib.contributors.models import (
    ContributorIdentifier,
    Organization,
    Person,
)
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample, SampleIdentifier
from fairdm.core.vocabularies import IDENTIFIER_TYPES
from fairdm.utils.choices import Visibility


def seed(*options):
    call_command("seed_record_search", *options, verbosity=0)


@pytest.mark.django_db
class TestSeedRecordSearchRefusesOutsideDevelopment:
    @override_settings(DJANGO_ENV="production")
    def test_it_refuses_and_creates_nothing(self):
        with pytest.raises(CommandError):
            seed()

        assert not Project.objects.filter(name=PRIVATE_PROJECT).exists()


@pytest.mark.django_db
class TestSeedRecordSearch:
    def test_the_regular_user_manages_a_private_project_and_two_private_datasets(self):
        seed()

        regular = Person.objects.get(email="regular.user@example.com")
        project = Project.objects.get(name=PRIVATE_PROJECT)
        datasets = Dataset.all_objects.filter(name__in=PRIVATE_DATASETS)
        assert project.visibility == Visibility.PRIVATE
        assert datasets.count() == 2
        assert all(d.visibility == Visibility.PRIVATE for d in datasets)
        assert Dataset.all_objects.accessible_to(regular, 3).count() >= 2

    def test_organizations_carry_a_ror_and_people_an_orcid(self):
        seed()

        assert Organization.objects.filter(
            identifiers__type=f"{IDENTIFIER_TYPES}/ror", identifiers__value="04z8jg394"
        ).exists()
        assert ContributorIdentifier.objects.filter(
            type_id=f"{IDENTIFIER_TYPES}/orcid"
        ).exists()

    def test_two_people_are_left_unclaimed(self):
        seed()

        assert Person.objects.filter(is_claimed=False, email__isnull=True).count() >= 2

    def test_samples_carry_local_ids_and_igsns(self):
        seed()

        assert RockSample.objects.filter(local_id="AS25-001").exists()
        assert (
            SampleIdentifier.objects.filter(type_id=f"{IDENTIFIER_TYPES}/igsn").count()
            == 3
        )

    def test_publications_carry_a_doi(self):
        seed()

        assert Item.objects.filter(
            item_identifiers__type="DOI",
            item_identifiers__value="10.5880/gfz.2024.011",
        ).exists()

    def test_a_second_run_adds_nothing(self):
        seed()
        counts = (
            Project.objects.count(),
            Dataset.all_objects.count(),
            Sample.objects.count(),
            Item.objects.count(),
            Person.objects.count(),
        )

        seed()

        assert counts == (
            Project.objects.count(),
            Dataset.all_objects.count(),
            Sample.objects.count(),
            Item.objects.count(),
            Person.objects.count(),
        )


@pytest.mark.django_db
class TestLargeDataset:
    def test_it_holds_the_samples_asked_for_and_a_second_run_adds_only_the_rest(
        self, capsys
    ):
        import io

        seed_ = RecordSearchSeed(stdout=io.StringIO())
        seed_.handle()

        dataset = seed_.large_dataset(count=120)
        seed_.large_dataset(count=150)

        assert dataset.name == LARGE_DATASET
        samples = RockSample.objects.filter(dataset=dataset)
        assert samples.count() == 150
        assert Sample.objects.filter(dataset=dataset).count() == 150
        assert samples.filter(local_id="LC-000150").exists()
