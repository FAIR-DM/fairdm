"""Tests for the ``seed_record_lists`` command: the development data behind the record tabs."""

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models import Count
from django.test import override_settings

from demo.seed.record_lists import MAIN
from fairdm.contrib.contributors.models import Contribution
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project


REGULAR = "regular.user@example.com"


def seed():
    call_command("seed_record_lists", verbosity=0)


def counts():
    """What the command leaves behind: names, and how many records each dataset holds."""
    return {
        "projects": sorted(Project.objects.values_list("name", flat=True)),
        "datasets": sorted(Dataset.all_objects.values_list("name", flat=True)),
        "samples": sorted(
            Dataset.all_objects.annotate(n=Count("samples")).values_list("name", "n")
        ),
        "measurements": sorted(
            Dataset.all_objects.annotate(n=Count("measurements")).values_list(
                "name", "n"
            )
        ),
        "contributions": Contribution.objects.count(),
    }


@pytest.mark.slow
@pytest.mark.django_db
class TestSeedRecordLists:
    @override_settings(DJANGO_ENV="production")
    def test_it_refuses_outside_development_and_creates_nothing(self):
        with pytest.raises(CommandError):
            seed()

        assert not Project.objects.filter(name=MAIN).exists()

    def test_run_twice_it_creates_each_record_once(self):
        seed()
        first = counts()

        seed()

        assert counts() == first
        assert Project.objects.filter(name=MAIN).count() == 1


