"""Tests for the visibility rules samples and measurements share."""

import pytest
from django.contrib.auth.models import AnonymousUser

from demo.factories import RockSampleFactory, XRFMeasurementFactory
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.core.utils import assign_perm
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.utils.choices import Visibility

VIEW, EDIT, MANAGE = (
    ContributionLevel.VIEW,
    ContributionLevel.EDIT,
    ContributionLevel.MANAGE,
)


def _sample(dataset):
    return RockSampleFactory(dataset=dataset)


def _measurement(dataset):
    return XRFMeasurementFactory(dataset=dataset, sample=_sample(dataset))


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("model", "make"), [(Sample, _sample), (Measurement, _measurement)]
)
class TestRecordVisibilityMixin:
    """Both querysets decide by the record's own dataset."""

    def test_a_visitor_sees_only_records_in_public_published_datasets(
        self, model, make
    ):
        released = make(DatasetFactory(visibility=Visibility.PUBLIC, published=True))
        make(DatasetFactory(visibility=Visibility.PUBLIC, published=False))

        assert set(model.objects.visible_to(AnonymousUser())) == {released}

    def test_a_team_member_also_sees_their_datasets_records(self, model, make):
        held = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        mine = make(held)
        make(DatasetFactory(visibility=Visibility.PRIVATE, published=False))
        user = PersonFactory(is_active=True)
        ContributionFactory(content_object=held, contributor=user, level=VIEW)

        assert set(model.objects.visible_to(user)) == {mine}

    def test_a_level_on_the_project_above_the_dataset_shows_its_records(
        self, model, make
    ):
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        held = DatasetFactory(
            project=project, visibility=Visibility.PRIVATE, published=False
        )
        mine = make(held)
        make(DatasetFactory(visibility=Visibility.PRIVATE, published=False))
        user = PersonFactory(is_active=True)
        ContributionFactory(content_object=project, contributor=user, level=VIEW)

        assert set(model.objects.visible_to(user)) == {mine}

    def test_a_person_listed_only_on_one_record_sees_it_and_not_its_siblings(
        self, model, make
    ):
        dataset = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        mine = make(dataset)
        make(dataset)
        user = PersonFactory(is_active=True)
        ContributionFactory(content_object=mine, contributor=user, level=VIEW)

        assert set(model.objects.visible_to(user)) == {mine}

    def test_a_person_with_no_level_sees_nothing_private(self, model, make):
        make(DatasetFactory(visibility=Visibility.PRIVATE, published=False))
        user = PersonFactory(is_active=True)

        assert not model.objects.visible_to(user).exists()

    def test_a_stored_guardian_row_alone_shows_nothing(self, model, make):
        held = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        make(held)
        user = PersonFactory(is_active=True)
        assign_perm("view_dataset", user, held)
        assign_perm("change_dataset", user, held)

        assert not model.objects.visible_to(user).exists()

    def test_a_listing_with_no_level_shows_nothing_private(self, model, make):
        held = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        make(held)
        user = PersonFactory(is_active=True)
        ContributionFactory(content_object=held, contributor=user, level=None)

        assert not model.objects.visible_to(user).exists()

    def test_published_keeps_the_records_of_published_datasets(self, model, make):
        kept = make(DatasetFactory(published=True))
        make(DatasetFactory(published=False))

        assert set(model.objects.published()) == {kept}


@pytest.fixture
def tree(db):
    """A private project with a dataset holding a sample and a measurement, and another dataset."""
    project = ProjectFactory(visibility=Visibility.PRIVATE)
    dataset = DatasetFactory(project=project, visibility=Visibility.PRIVATE)
    other = DatasetFactory(project=project, visibility=Visibility.PRIVATE)
    sample = _sample(dataset)
    return {
        "project": project,
        "dataset": dataset,
        "other_dataset": other,
        "sample": sample,
        "sibling": _sample(dataset),
        "measurement": XRFMeasurementFactory(dataset=other, sample=sample),
        "loose": DatasetFactory(project=None, visibility=Visibility.PRIVATE),
    }


@pytest.fixture
def holder(db):
    return PersonFactory(is_active=True, is_claimed=True, password="x")


def listed(model, user, level):
    manager = getattr(model, "all_objects", model.objects)
    return {record.pk for record in manager.with_level(user, level)}


@pytest.mark.django_db
class TestWithLevel:
    def test_a_level_on_a_project_is_held_on_the_project(self, tree, holder):
        ContributionFactory(
            content_object=tree["project"], contributor=holder, level=EDIT
        )

        assert listed(Project, holder, EDIT) == {tree["project"].pk}

    def test_a_level_on_a_dataset_is_held_on_it_and_not_on_the_project(
        self, tree, holder
    ):
        ContributionFactory(
            content_object=tree["dataset"], contributor=holder, level=VIEW
        )

        assert listed(Dataset, holder, VIEW) == {tree["dataset"].pk}
        assert listed(Project, holder, VIEW) == set()

    def test_a_level_on_a_project_reaches_every_dataset_in_it_and_not_others(
        self, tree, holder
    ):
        ContributionFactory(
            content_object=tree["project"], contributor=holder, level=VIEW
        )

        assert listed(Dataset, holder, VIEW) == {
            tree["dataset"].pk,
            tree["other_dataset"].pk,
        }

    def test_a_level_on_a_project_reaches_the_samples_and_measurements_beneath(
        self, tree, holder
    ):
        ContributionFactory(
            content_object=tree["project"], contributor=holder, level=VIEW
        )

        assert listed(Sample, holder, VIEW) == {
            tree["sample"].pk,
            tree["sibling"].pk,
        }
        assert listed(Measurement, holder, VIEW) == {tree["measurement"].pk}

    def test_a_level_on_a_dataset_reaches_its_samples_and_measurements(
        self, tree, holder
    ):
        ContributionFactory(
            content_object=tree["dataset"], contributor=holder, level=EDIT
        )

        assert listed(Sample, holder, EDIT) == {tree["sample"].pk, tree["sibling"].pk}
        assert listed(Measurement, holder, EDIT) == set()

    def test_a_measurement_follows_its_own_dataset_not_its_samples(self, tree, holder):
        ContributionFactory(
            content_object=tree["other_dataset"], contributor=holder, level=EDIT
        )

        assert listed(Measurement, holder, EDIT) == {tree["measurement"].pk}
        assert listed(Sample, holder, EDIT) == set()

    def test_a_person_listed_on_one_sample_holds_it_and_not_its_sibling(
        self, tree, holder
    ):
        ContributionFactory(
            content_object=tree["sample"], contributor=holder, level=VIEW
        )

        assert listed(Sample, holder, VIEW) == {tree["sample"].pk}
        assert listed(Dataset, holder, VIEW) == set()

    def test_a_person_listed_on_one_measurement_holds_it_alone(self, tree, holder):
        ContributionFactory(
            content_object=tree["measurement"], contributor=holder, level=MANAGE
        )

        assert listed(Measurement, holder, MANAGE) == {tree["measurement"].pk}

    def test_a_dataset_with_no_project_holds_its_own_levels(self, tree, holder):
        ContributionFactory(
            content_object=tree["loose"], contributor=holder, level=VIEW
        )

        assert listed(Dataset, holder, VIEW) == {tree["loose"].pk}

    def test_only_levels_at_least_the_one_asked_for_count(self, tree, holder):
        ContributionFactory(
            content_object=tree["dataset"], contributor=holder, level=VIEW
        )
        ContributionFactory(
            content_object=tree["other_dataset"], contributor=holder, level=EDIT
        )

        assert listed(Dataset, holder, VIEW) == {
            tree["dataset"].pk,
            tree["other_dataset"].pk,
        }
        assert listed(Dataset, holder, EDIT) == {tree["other_dataset"].pk}
        assert listed(Dataset, holder, MANAGE) == set()

    def test_another_persons_level_is_not_held(self, tree, holder):
        ContributionFactory(content_object=tree["dataset"], level=MANAGE)

        assert listed(Dataset, holder, VIEW) == set()

    def test_a_listing_with_no_level_holds_nothing(self, tree, holder):
        ContributionFactory(
            content_object=tree["dataset"], contributor=holder, level=None
        )

        assert listed(Dataset, holder, VIEW) == set()

    def test_a_stored_guardian_row_holds_nothing(self, tree, holder):
        assign_perm("change_dataset", holder, tree["dataset"])

        assert listed(Dataset, holder, VIEW) == set()
        assert listed(Sample, holder, VIEW) == set()

    def test_a_visitor_and_an_inactive_user_hold_nothing(self, tree, holder):
        ContributionFactory(
            content_object=tree["project"], contributor=holder, level=MANAGE
        )
        holder.is_active = False
        holder.save()

        assert listed(Dataset, AnonymousUser(), VIEW) == set()
        assert listed(Dataset, None, VIEW) == set()
        assert listed(Dataset, holder, VIEW) == set()
