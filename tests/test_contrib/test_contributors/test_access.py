"""Tests for ``RecordAccess``, which answers what a person may do on one record.

The level a person holds is read from the contribution that lists them on the record, or on a
record above it. Nothing here goes through a permission backend.
"""

import pytest
from django.contrib.auth.models import AnonymousUser, Permission

from fairdm.contrib.contributors.access import REQUIRED_LEVEL, RecordAccess
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.factories import (
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
)

VIEW, EDIT, MANAGE = (
    ContributionLevel.VIEW,
    ContributionLevel.EDIT,
    ContributionLevel.MANAGE,
)


@pytest.fixture
def signed_in():
    """A person who can sign in."""
    return PersonFactory(is_active=True, is_claimed=True, password="x")


@pytest.mark.django_db
class TestRecordsAbove:
    def test_a_project_has_nothing_above_it(self, record_chain):
        assert RecordAccess(record_chain.project).above == []

    def test_a_dataset_takes_from_its_project(self, record_chain):
        assert RecordAccess(record_chain.dataset).above == [record_chain.project]

    def test_a_dataset_with_no_project_has_nothing_above_it(self):
        dataset = DatasetFactory(project=None)

        assert RecordAccess(dataset).above == []

    def test_a_sample_takes_from_its_dataset_then_the_project(self, record_chain):
        assert RecordAccess(record_chain.sample).above == [
            record_chain.dataset,
            record_chain.project,
        ]

    def test_a_measurement_follows_its_own_dataset_not_its_samples(
        self, record_chain
    ):
        assert RecordAccess(record_chain.measurement).above == [
            record_chain.other_dataset,
            record_chain.project,
        ]


@pytest.mark.django_db
class TestLevelOf:
    def test_a_person_who_is_not_listed_holds_none(self, record_chain, signed_in):
        assert RecordAccess(record_chain.dataset).level_of(signed_in) is None

    def test_a_person_listed_with_no_level_holds_none(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.dataset, signed_in, None)

        assert RecordAccess(record_chain.dataset).level_of(signed_in) is None

    def test_a_person_holds_the_level_they_are_listed_at(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.dataset, signed_in, EDIT)

        assert RecordAccess(record_chain.dataset).level_of(signed_in) == EDIT

    def test_a_level_on_a_dataset_reaches_its_samples(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.dataset, signed_in, EDIT)

        assert RecordAccess(record_chain.sample).level_of(signed_in) == EDIT

    def test_a_level_on_a_dataset_does_not_reach_the_project(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.dataset, signed_in, MANAGE)

        assert RecordAccess(record_chain.project).level_of(signed_in) is None

    def test_a_level_on_a_project_reaches_a_measurement(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.project, signed_in, VIEW)

        assert RecordAccess(record_chain.measurement).level_of(signed_in) == VIEW

    def test_a_level_on_the_samples_dataset_does_not_reach_its_measurement(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.dataset, signed_in, MANAGE)

        assert RecordAccess(record_chain.measurement).level_of(signed_in) is None

    def test_the_higher_of_two_levels_applies(self, record_chain, signed_in, grant):
        grant(record_chain.sample, signed_in, VIEW)
        grant(record_chain.dataset, signed_in, EDIT)

        assert RecordAccess(record_chain.sample).level_of(signed_in) == EDIT

    def test_a_level_on_the_record_beats_a_lower_one_from_above(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.sample, signed_in, MANAGE)
        grant(record_chain.project, signed_in, VIEW)

        assert RecordAccess(record_chain.sample).level_of(signed_in) == MANAGE

    def test_a_visitor_holds_none(self, record_chain):
        assert RecordAccess(record_chain.dataset).level_of(AnonymousUser()) is None

    def test_an_inactive_user_holds_none(self, record_chain, grant):
        gone = PersonFactory(is_active=False, is_claimed=True, password="x")
        grant(record_chain.dataset, gone, MANAGE)

        assert RecordAccess(record_chain.dataset).level_of(gone) is None

    def test_the_chain_is_read_in_one_query(
        self, record_chain, signed_in, grant, django_assert_num_queries
    ):
        grant(record_chain.project, signed_in, VIEW)
        access = RecordAccess(record_chain.measurement)
        access.level_of(signed_in)  # fills Django's content type cache

        with django_assert_num_queries(1):
            access.level_of(signed_in)


@pytest.mark.django_db
class TestLevelParts:
    def test_the_own_level_ignores_what_is_held_from_above(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.project, signed_in, MANAGE)
        grant(record_chain.dataset, signed_in, VIEW)

        assert RecordAccess(record_chain.dataset).own_level(signed_in) == VIEW

    def test_a_person_with_no_own_level_has_none(self, record_chain, signed_in, grant):
        grant(record_chain.project, signed_in, MANAGE)

        assert RecordAccess(record_chain.dataset).own_level(signed_in) is None

    def test_the_level_from_above_names_the_record_it_comes_from(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.project, signed_in, EDIT)

        level, source = RecordAccess(record_chain.sample).level_from_above(signed_in)

        assert (level, source) == (EDIT, record_chain.project)

    def test_the_highest_level_from_above_wins(self, record_chain, signed_in, grant):
        grant(record_chain.project, signed_in, EDIT)
        grant(record_chain.dataset, signed_in, VIEW)

        level, source = RecordAccess(record_chain.sample).level_from_above(signed_in)

        assert (level, source) == (EDIT, record_chain.project)

    def test_nothing_is_held_from_above_by_a_person_with_only_their_own_level(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.sample, signed_in, MANAGE)

        assert RecordAccess(record_chain.sample).level_from_above(signed_in) == (
            None,
            None,
        )


@pytest.mark.django_db
class TestPeopleAbove:
    def test_everyone_holding_a_level_from_above_is_named_with_its_source(
        self, record_chain, grant
    ):
        from_project, from_dataset = PersonFactory(), PersonFactory()
        grant(record_chain.project, from_project, VIEW)
        grant(record_chain.dataset, from_dataset, EDIT)

        found = RecordAccess(record_chain.sample).people_above()

        assert {(person.pk, level, source) for person, level, source in found} == {
            (from_project.pk, VIEW, record_chain.project),
            (from_dataset.pk, EDIT, record_chain.dataset),
        }

    def test_a_person_holding_two_is_named_once_at_the_higher(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.project, signed_in, VIEW)
        grant(record_chain.dataset, signed_in, MANAGE)

        found = RecordAccess(record_chain.sample).people_above()

        assert [(p.pk, level, source) for p, level, source in found] == [
            (signed_in.pk, MANAGE, record_chain.dataset)
        ]

    def test_a_level_on_the_record_itself_is_not_from_above(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.sample, signed_in, MANAGE)

        assert RecordAccess(record_chain.sample).people_above() == []

    def test_an_organization_is_never_named(self, record_chain, grant):
        grant(record_chain.project, OrganizationFactory(), None)

        assert RecordAccess(record_chain.dataset).people_above() == []


@pytest.mark.django_db
class TestManagers:
    def test_a_manager_on_the_record_is_counted(self, record_chain, signed_in, grant):
        grant(record_chain.dataset, signed_in, MANAGE)

        assert RecordAccess(record_chain.dataset).managers() == {signed_in.pk}

    def test_a_manager_on_a_record_above_is_counted(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.project, signed_in, MANAGE)

        assert RecordAccess(record_chain.sample).managers() == {signed_in.pk}

    def test_an_editor_is_not_counted(self, record_chain, signed_in, grant):
        grant(record_chain.dataset, signed_in, EDIT)

        assert RecordAccess(record_chain.dataset).managers() == set()

    def test_a_manager_of_a_record_below_is_not_counted(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.sample, signed_in, MANAGE)

        assert RecordAccess(record_chain.dataset).managers() == set()

    @pytest.mark.parametrize(
        "state",
        [
            {"is_active": False, "is_claimed": True},
            {"is_active": True, "is_claimed": False},
        ],
        ids=["inactive", "never_signed_in"],
    )
    def test_a_person_who_cannot_sign_in_is_left_out(
        self, record_chain, grant, state
    ):
        person = PersonFactory(password="x", **state)
        grant(record_chain.dataset, person, MANAGE)

        assert RecordAccess(record_chain.dataset).managers() == set()


@pytest.mark.django_db
class TestCanManage:
    def test_a_manager_may(self, record_chain, signed_in, grant):
        grant(record_chain.dataset, signed_in, MANAGE)

        assert RecordAccess(record_chain.dataset).can_manage(signed_in) is True

    def test_a_manager_of_the_project_may_manage_its_sample(
        self, record_chain, signed_in, grant
    ):
        grant(record_chain.project, signed_in, MANAGE)

        assert RecordAccess(record_chain.sample).can_manage(signed_in) is True

    def test_an_editor_may_not(self, record_chain, signed_in, grant):
        grant(record_chain.dataset, signed_in, EDIT)

        assert RecordAccess(record_chain.dataset).can_manage(signed_in) is False

    def test_a_person_holding_change_for_the_whole_portal_may(
        self, record_chain, signed_in
    ):
        signed_in.user_permissions.add(Permission.objects.get(codename="change_dataset"))
        signed_in = type(signed_in).objects.get(pk=signed_in.pk)

        assert RecordAccess(record_chain.dataset).can_manage(signed_in) is True

    def test_change_for_datasets_does_not_reach_a_project(
        self, record_chain, signed_in
    ):
        signed_in.user_permissions.add(Permission.objects.get(codename="change_dataset"))
        signed_in = type(signed_in).objects.get(pk=signed_in.pk)

        assert RecordAccess(record_chain.project).can_manage(signed_in) is False

    def test_a_superuser_may(self, record_chain):
        superuser = PersonFactory(is_active=True, is_superuser=True, password="x")

        assert RecordAccess(record_chain.dataset).can_manage(superuser) is True

    def test_a_visitor_may_not(self, record_chain):
        assert RecordAccess(record_chain.dataset).can_manage(AnonymousUser()) is False


@pytest.mark.django_db
class TestRequiredLevel:
    @pytest.mark.parametrize("model", [Project, Dataset, Sample, Measurement])
    def test_every_permission_a_record_type_declares_is_given_a_level(self, model):
        meta = model._meta
        declared = {f"{action}_{meta.model_name}" for action in meta.default_permissions}
        declared |= {codename for codename, _name in meta.permissions}

        assert declared - set(REQUIRED_LEVEL) == set()

    def test_every_level_asked_for_is_one_of_the_three(self):
        assert set(REQUIRED_LEVEL.values()) <= set(ContributionLevel)
