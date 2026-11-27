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
    Person,
)
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
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


@pytest.mark.slow
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


@pytest.mark.slow
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
