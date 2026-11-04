"""Tests for the ``seed_record_lists`` command: the development data behind the record tabs."""

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction
from django.db.models import Count
from django.test import override_settings

from demo.seed.record_lists import HIDDEN, MAIN, ORGANIZATION, WAITING
from fairdm.contrib.contributors.models import Contribution, Organization, Person
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.utils.choices import Visibility

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


def types_in(model, dataset):
    """Return the distinct types of ``model`` records the dataset holds."""
    return set(
        model.objects.filter(dataset=dataset).values_list(
            "polymorphic_ctype", flat=True
        )
    )


@pytest.fixture(scope="class")
def record_lists_seeded(django_db_setup, django_db_blocker):
    """Run the command once for a test class, the slowest part of these tests."""
    with django_db_blocker.unblock(), transaction.atomic():
        seed()
        yield
        transaction.set_rollback(True)


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


@pytest.mark.django_db
@pytest.mark.usefixtures("record_lists_seeded")
class TestSeedRecordListsStates:
    @pytest.fixture
    def main(self):
        return Project.objects.get(name=MAIN)

    def test_a_dataset_holds_several_sample_and_measurement_types(self, main):
        published = Dataset.all_objects.get(
            project=main, name="Borehole cores, published"
        )

        assert len(types_in(Sample, published)) >= 2
        assert len(types_in(Measurement, published)) >= 2

    def test_a_public_dataset_is_not_published(self, main):
        waiting = Dataset.all_objects.filter(
            project=main, visibility=Visibility.PUBLIC, published=False
        )

        assert waiting.exists()
        assert all(
            Sample.objects.filter(dataset=dataset).exists() for dataset in waiting
        )

    def test_a_dataset_is_empty(self, main):
        empty = [
            dataset
            for dataset in Dataset.all_objects.filter(project=main)
            if not Sample.objects.filter(dataset=dataset).exists()
            and not Measurement.objects.filter(dataset=dataset).exists()
        ]

        assert empty

    def test_a_measurement_is_on_another_datasets_sample(self):
        assert any(
            measurement.dataset_id != measurement.sample.dataset_id
            for measurement in Measurement.objects.select_related("sample")
            if measurement.dataset.project and measurement.dataset.project.name == MAIN
        )

    def test_a_sample_is_measured_in_datasets_a_visitor_may_and_may_not_open(
        self, main
    ):
        core = Sample.objects.get(dataset__project=main, name="BH-1 core, 100 m")
        measurements = Measurement.objects.filter(sample=core)
        datasets = Dataset.all_objects.filter(measurements__in=measurements).distinct()

        assert measurements.values("polymorphic_ctype").distinct().count() >= 2
        assert datasets.exclude(pk=core.dataset_id).filter(published=True).exists()
        assert datasets.filter(published=False).exists()
        assert datasets.filter(visibility=Visibility.PRIVATE).exists()
        assert measurements.filter(dataset=core.dataset).count() > 50

    def test_a_project_has_public_unpublished_and_private_datasets(self, main):
        datasets = Dataset.all_objects.filter(project=main)

        assert datasets.filter(visibility=Visibility.PUBLIC, published=True).exists()
        assert datasets.filter(visibility=Visibility.PUBLIC, published=False).exists()
        assert datasets.filter(visibility=Visibility.PRIVATE).exists()

    def test_a_project_is_private_and_another_has_nothing_published(self):
        assert Project.objects.get(name=HIDDEN).visibility == Visibility.PRIVATE
        waiting = Project.objects.get(name=WAITING)
        assert not Dataset.all_objects.filter(project=waiting, published=True).exists()

    def test_a_person_is_credited_on_a_project_a_dataset_a_sample_and_a_measurement(
        self,
    ):
        person = Person.objects.get(email=REGULAR)
        credited = set(
            Contribution.objects.filter(contributor=person).values_list(
                "content_type", flat=True
            )
        )
        wanted = {
            ContentType.objects.get_for_model(Project).pk,
            ContentType.objects.get_for_model(Dataset).pk,
        }
        assert wanted <= credited
        kinds = {ContentType.objects.get_for_id(pk).model_class() for pk in credited}
        assert any(issubclass(kind, Sample) for kind in kinds)
        assert any(issubclass(kind, Measurement) for kind in kinds)

    def test_an_organization_owns_a_project(self, main):
        assert main.owner == Organization.objects.get(name=ORGANIZATION)
