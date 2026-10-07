"""Tests for ``Crediting``, the one place a record's contributors are changed."""

from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from research_vocabs.models import Concept

from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Contribution
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.core.project.models import Project
from fairdm.factories import AffiliationFactory, OrganizationFactory, PersonFactory
from fairdm.utils.choices import Visibility

RECORDS = ["project", "dataset", "sample", "measurement"]


def role(name):
    return Concept.objects.get(vocabulary__name="fairdm-roles", name=name)


@pytest.fixture
def somebody(db):
    return PersonFactory(is_active=True, is_claimed=True, password="x")


@pytest.mark.django_db
class TestAdd:
    @pytest.mark.parametrize("kind", RECORDS)
    def test_a_person_is_listed_at_the_view_level(self, record_chain, somebody, kind):
        record = getattr(record_chain, kind)

        contribution = Crediting(record).add(somebody)

        assert contribution in record.contributors.all()
        assert RecordAccess(record).own_level(somebody) == ContributionLevel.VIEW

    def test_an_organization_is_listed_with_no_level(self, record_chain):
        organization = OrganizationFactory()

        contribution = Crediting(record_chain.dataset).add(organization)

        assert contribution.level is None

    def test_a_contributor_is_placed_last(self, record_chain, somebody, grant):
        grant(record_chain.dataset, PersonFactory(), None)
        grant(record_chain.dataset, PersonFactory(), None)

        added = Crediting(record_chain.dataset).add(somebody)

        listed = record_chain.dataset.contributors.order_by("order")
        assert list(listed)[-1] == added

    def test_a_contributor_already_listed_is_refused(
        self, record_chain, somebody, grant
    ):
        grant(record_chain.dataset, somebody, ContributionLevel.EDIT)

        with pytest.raises(ValidationError) as refused:
            Crediting(record_chain.dataset).add(somebody)

        assert refused.value.code == "duplicate"
        assert record_chain.dataset.contributors.count() == 1

    def test_a_refused_duplicate_leaves_the_level_it_held(
        self, record_chain, somebody, grant
    ):
        grant(record_chain.dataset, somebody, ContributionLevel.EDIT)

        with pytest.raises(ValidationError):
            Crediting(record_chain.dataset).add(somebody)

        level = RecordAccess(record_chain.dataset).own_level(somebody)
        assert level == ContributionLevel.EDIT

    def test_a_superuser_is_refused_with_a_validation_error(self, record_chain):
        superuser = PersonFactory(is_active=True, is_superuser=True, password="x")

        with pytest.raises(ValidationError) as refused:
            Crediting(record_chain.dataset).add(superuser)

        assert refused.value.code == "superuser"
        assert not record_chain.dataset.contributors.exists()


@pytest.mark.django_db
class TestOfferedRoles:
    @pytest.mark.parametrize("kind", RECORDS)
    def test_the_roles_are_those_the_vocabulary_groups_for_the_record_type(
        self, record_chain, kind
    ):
        record = getattr(record_chain, kind)

        offered = Crediting(record).offered_roles()

        assert [concept.name for concept in offered] == list(
            record.CONTRIBUTOR_ROLES.values
        )


@pytest.mark.django_db
class TestUpdate:
    def test_the_roles_are_saved(self, record_chain, somebody, grant):
        contribution = grant(record_chain.project, somebody, None)

        Crediting(record_chain.project).update(
            contribution, roles=[role("Creator"), role("ProjectLeader")]
        )

        assert {r.name for r in contribution.roles.all()} == {
            "Creator",
            "ProjectLeader",
        }

    def test_the_roles_replace_those_held(self, record_chain, somebody, grant):
        contribution = grant(record_chain.project, somebody, None)
        contribution.roles.add(role("Creator"))

        Crediting(record_chain.project).update(
            contribution, roles=[role("ProjectMember")]
        )

        assert [r.name for r in contribution.roles.all()] == ["ProjectMember"]

    def test_no_role_is_allowed(self, record_chain, somebody, grant):
        contribution = grant(record_chain.project, somebody, None)
        contribution.roles.add(role("Creator"))

        Crediting(record_chain.project).update(contribution, roles=[])

        assert not contribution.roles.exists()

    def test_a_role_from_another_record_types_group_is_refused(
        self, record_chain, somebody, grant
    ):
        contribution = grant(record_chain.project, somebody, None)
        elsewhere = Concept.objects.filter(vocabulary__name="fairdm-roles").exclude(
            name__in=Project.CONTRIBUTOR_ROLES.values
        )[0]

        with pytest.raises(ValidationError) as refused:
            Crediting(record_chain.project).update(contribution, roles=[elsewhere])

        assert refused.value.code == "role_not_offered"
        assert not contribution.roles.exists()

    def test_changing_the_roles_leaves_the_level_alone(
        self, record_chain, somebody, grant
    ):
        contribution = grant(record_chain.project, somebody, ContributionLevel.MANAGE)

        Crediting(record_chain.project).update(contribution, roles=[role("Creator")])

        contribution.refresh_from_db()
        assert contribution.level == ContributionLevel.MANAGE


@pytest.mark.django_db
class TestUpdateLevel:
    @pytest.mark.parametrize("kind", RECORDS)
    @pytest.mark.parametrize(
        "level",
        [ContributionLevel.VIEW, ContributionLevel.EDIT, ContributionLevel.MANAGE],
    )
    def test_the_level_is_saved(self, record_chain, somebody, grant, kind, level):
        record = getattr(record_chain, kind)
        contribution = grant(record, somebody, ContributionLevel.VIEW)

        Crediting(record).update(contribution, roles=[], level=level)

        assert RecordAccess(record).own_level(somebody) == level

    def test_no_level_given_leaves_it_alone(self, record_chain, somebody, grant):
        contribution = grant(record_chain.dataset, somebody, ContributionLevel.EDIT)

        Crediting(record_chain.dataset).update(contribution, roles=[])

        contribution.refresh_from_db()
        assert contribution.level == ContributionLevel.EDIT

    def test_a_level_below_what_is_held_from_above_is_refused(
        self, record_chain, somebody, grant
    ):
        grant(record_chain.project, somebody, ContributionLevel.EDIT)
        contribution = grant(record_chain.dataset, somebody, ContributionLevel.EDIT)

        with pytest.raises(ValidationError) as refused:
            Crediting(record_chain.dataset).update(
                contribution, roles=[], level=ContributionLevel.VIEW
            )

        assert refused.value.code == "below_inherited"
        contribution.refresh_from_db()
        assert contribution.level == ContributionLevel.EDIT

    def test_the_level_held_from_above_is_allowed(self, record_chain, somebody, grant):
        grant(
            record_chain.dataset,
            PersonFactory(is_active=True, is_claimed=True, password="x"),
            ContributionLevel.MANAGE,
        )
        grant(record_chain.project, somebody, ContributionLevel.EDIT)
        contribution = grant(record_chain.dataset, somebody, ContributionLevel.MANAGE)

        Crediting(record_chain.dataset).update(
            contribution, roles=[], level=ContributionLevel.EDIT
        )

        contribution.refresh_from_db()
        assert contribution.level == ContributionLevel.EDIT

    def test_a_level_held_on_a_record_below_does_not_hold_this_one_up(
        self, record_chain, somebody, grant
    ):
        grant(
            record_chain.project,
            PersonFactory(is_active=True, is_claimed=True, password="x"),
            ContributionLevel.MANAGE,
        )
        grant(record_chain.dataset, somebody, ContributionLevel.MANAGE)
        contribution = grant(record_chain.project, somebody, ContributionLevel.MANAGE)

        Crediting(record_chain.project).update(
            contribution, roles=[], level=ContributionLevel.VIEW
        )

        contribution.refresh_from_db()
        assert contribution.level == ContributionLevel.VIEW

    def test_a_refused_level_saves_no_roles_either(self, record_chain, somebody, grant):
        grant(record_chain.project, somebody, ContributionLevel.MANAGE)
        contribution = grant(record_chain.dataset, somebody, ContributionLevel.MANAGE)

        with pytest.raises(ValidationError):
            Crediting(record_chain.dataset).update(
                contribution,
                roles=[role("Creator")],
                level=ContributionLevel.VIEW,
            )

        assert not contribution.roles.exists()

    def test_a_refused_level_and_a_refused_role_are_both_reported(
        self, record_chain, somebody, grant
    ):
        grant(record_chain.project, somebody, ContributionLevel.MANAGE)
        contribution = grant(record_chain.dataset, somebody, ContributionLevel.MANAGE)
        elsewhere = Concept.objects.filter(vocabulary__name="fairdm-roles").exclude(
            name__in=record_chain.dataset.CONTRIBUTOR_ROLES.values
        )[0]

        with pytest.raises(ValidationError) as refused:
            Crediting(record_chain.dataset).update(
                contribution, roles=[elsewhere], level=ContributionLevel.VIEW
            )

        assert {error.code for error in refused.value.error_list} == {
            "role_not_offered",
            "below_inherited",
        }

    def test_an_organization_is_given_no_level(self, record_chain):
        organization = OrganizationFactory()
        contribution = Crediting(record_chain.dataset).add(organization)

        Crediting(record_chain.dataset).update(
            contribution, roles=[], level=ContributionLevel.MANAGE
        )

        contribution.refresh_from_db()
        assert contribution.level is None


@pytest.mark.django_db
class TestRemove:
    def test_the_contribution_is_gone(self, record_chain, somebody, grant):
        contribution = grant(record_chain.dataset, somebody, ContributionLevel.EDIT)

        Crediting(record_chain.dataset).remove(contribution)

        assert not Contribution.objects.filter(pk=contribution.pk).exists()

    def test_the_level_goes_with_it(self, record_chain, somebody, grant):
        grant(
            record_chain.dataset,
            PersonFactory(is_active=True, is_claimed=True, password="x"),
            ContributionLevel.MANAGE,
        )
        contribution = grant(record_chain.dataset, somebody, ContributionLevel.MANAGE)

        Crediting(record_chain.dataset).remove(contribution)

        assert RecordAccess(record_chain.dataset).own_level(somebody) is None

    def test_a_level_held_from_above_stays(self, record_chain, somebody, grant):
        grant(record_chain.project, somebody, ContributionLevel.EDIT)
        contribution = grant(record_chain.dataset, somebody, ContributionLevel.VIEW)

        Crediting(record_chain.dataset).remove(contribution)

        level = RecordAccess(record_chain.dataset).level_of(somebody)
        assert level == ContributionLevel.EDIT


@pytest.mark.django_db
class TestCreditedFrom:
    @pytest.mark.parametrize("kind", RECORDS)
    def test_a_person_is_added_credited_from_the_organization(
        self, record_chain, somebody, kind
    ):
        record = getattr(record_chain, kind)
        organization = OrganizationFactory()

        contribution = Crediting(record).add(somebody, organization=organization)

        assert contribution.affiliation == organization

    def test_the_organization_is_listed_on_the_record_once(
        self, record_chain, somebody
    ):
        organization = OrganizationFactory()

        Crediting(record_chain.dataset).add(somebody, organization=organization)
        Crediting(record_chain.dataset).add(
            PersonFactory(is_active=True), organization=organization
        )

        listed = record_chain.dataset.contributors.filter(contributor=organization)
        assert listed.count() == 1
        assert listed.get().level is None

    def test_an_organization_already_listed_is_not_listed_again(
        self, record_chain, somebody
    ):
        organization = OrganizationFactory()
        Crediting(record_chain.dataset).add(organization)

        Crediting(record_chain.dataset).add(somebody, organization=organization)

        listed = record_chain.dataset.contributors.filter(contributor=organization)
        assert listed.count() == 1

    def test_a_person_added_with_no_organization_is_credited_from_none(
        self, record_chain, somebody
    ):
        AffiliationFactory(person=somebody, is_primary=True)

        contribution = Crediting(record_chain.dataset).add(somebody)

        assert contribution.affiliation is None
        assert [c.contributor_id for c in record_chain.dataset.contributors.all()] == [
            somebody.pk
        ]

    def test_a_refused_add_lists_no_organization(self, record_chain, somebody, grant):
        grant(record_chain.dataset, somebody, ContributionLevel.EDIT)
        organization = OrganizationFactory()

        with pytest.raises(ValidationError):
            Crediting(record_chain.dataset).add(somebody, organization=organization)

        assert not record_chain.dataset.contributors.filter(
            contributor=organization
        ).exists()

    def test_deleting_the_organization_leaves_the_person_credited_from_none(
        self, record_chain, somebody
    ):
        organization = OrganizationFactory()
        contribution = Crediting(record_chain.dataset).add(
            somebody, organization=organization
        )

        organization.delete()

        contribution.refresh_from_db()
        assert contribution.affiliation is None
        assert record_chain.dataset.contributors.filter(contributor=somebody).exists()

    def test_update_changes_the_organization_and_lists_it(self, record_chain, somebody):
        first, second = OrganizationFactory(), OrganizationFactory()
        crediting = Crediting(record_chain.dataset)
        contribution = crediting.add(somebody, organization=first)

        crediting.update(contribution, roles=[], organization=second)

        contribution.refresh_from_db()
        assert contribution.affiliation == second
        assert record_chain.dataset.contributors.filter(contributor=second).count() == 1

    def test_update_can_set_the_organization_to_none(self, record_chain, somebody):
        crediting = Crediting(record_chain.dataset)
        contribution = crediting.add(somebody, organization=OrganizationFactory())

        crediting.update(contribution, roles=[], organization=None)

        contribution.refresh_from_db()
        assert contribution.affiliation is None

    def test_update_without_an_organization_leaves_it_alone(
        self, record_chain, somebody
    ):
        organization = OrganizationFactory()
        crediting = Crediting(record_chain.dataset)
        contribution = crediting.add(somebody, organization=organization)

        crediting.update(contribution, roles=[role("Creator")])

        contribution.refresh_from_db()
        assert contribution.affiliation == organization

    def test_a_refused_update_changes_no_organization(self, record_chain, somebody):
        first = OrganizationFactory()
        crediting = Crediting(record_chain.project)
        contribution = crediting.add(somebody, organization=first)
        elsewhere = Concept.objects.filter(vocabulary__name="fairdm-roles").exclude(
            name__in=Project.CONTRIBUTOR_ROLES.values
        )[0]
        other = OrganizationFactory()

        with pytest.raises(ValidationError):
            crediting.update(contribution, roles=[elsewhere], organization=other)

        contribution.refresh_from_db()
        assert contribution.affiliation == first
        assert not record_chain.project.contributors.filter(contributor=other).exists()

    def test_the_organization_stays_when_its_last_person_leaves(
        self, record_chain, somebody
    ):
        organization = OrganizationFactory()
        crediting = Crediting(record_chain.dataset)
        contribution = crediting.add(somebody, organization=organization)

        crediting.remove(contribution)

        assert record_chain.dataset.contributors.filter(
            contributor=organization
        ).exists()

    def test_the_organization_stays_when_its_last_person_is_credited_from_elsewhere(
        self, record_chain, somebody
    ):
        first = OrganizationFactory()
        crediting = Crediting(record_chain.dataset)
        contribution = crediting.add(somebody, organization=first)

        crediting.update(contribution, roles=[], organization=OrganizationFactory())

        assert record_chain.dataset.contributors.filter(contributor=first).exists()

    def test_an_organization_nobody_is_credited_from_can_be_removed(
        self, record_chain, somebody
    ):
        organization = OrganizationFactory()
        crediting = Crediting(record_chain.dataset)
        contribution = crediting.add(somebody, organization=organization)
        crediting.remove(contribution)
        listed = record_chain.dataset.contributors.get(contributor=organization)

        crediting.remove(listed)

        assert not Contribution.objects.filter(pk=listed.pk).exists()

    def test_an_organization_people_are_credited_from_cannot_be_removed(
        self, record_chain, somebody
    ):
        organization = OrganizationFactory()
        other = PersonFactory(is_active=True)
        crediting = Crediting(record_chain.dataset)
        crediting.add(somebody, organization=organization)
        crediting.add(other, organization=organization)
        listed = record_chain.dataset.contributors.get(contributor=organization)

        with pytest.raises(ValidationError) as refused:
            crediting.remove(listed)

        assert refused.value.code == "credited_from"
        assert {person.pk for person in refused.value.params["people"]} == {
            somebody.pk,
            other.pk,
        }
        assert Contribution.objects.filter(pk=listed.pk).exists()

    def test_credited_from_maps_each_organization_to_its_people(
        self, record_chain, somebody
    ):
        organization = OrganizationFactory()
        crediting = Crediting(record_chain.dataset)
        crediting.add(somebody, organization=organization)
        crediting.add(PersonFactory(is_active=True))

        found = crediting.credited_from()

        assert {pk: [p.pk for p in people] for pk, people in found.items()} == {
            organization.pk: [somebody.pk]
        }

    def test_credited_from_looks_only_at_this_record(self, record_chain, somebody):
        organization = OrganizationFactory()
        Crediting(record_chain.project).add(somebody, organization=organization)

        assert Crediting(record_chain.dataset).credited_from() == {}


@pytest.mark.django_db
class TestMakeCreator:
    @pytest.mark.parametrize("kind", RECORDS)
    def test_the_creator_is_listed_at_the_manage_level(
        self, record_chain, somebody, kind
    ):
        record = getattr(record_chain, kind)

        contribution = Crediting(record).make_creator(somebody)

        assert contribution in record.contributors.all()
        assert RecordAccess(record).own_level(somebody) == ContributionLevel.MANAGE
        assert somebody.has_perm(f"{kind}.change_{kind}", record)

    def test_the_roles_given_are_held(self, record_chain, somebody):
        contribution = Crediting(record_chain.dataset).make_creator(
            somebody, roles=["Creator", "ContactPerson"]
        )

        assert set(contribution.roles.values_list("name", flat=True)) == {
            "Creator",
            "ContactPerson",
        }

    def test_no_stored_permission_row_is_written(self, record_chain, somebody):
        from guardian.models import UserObjectPermission

        Crediting(record_chain.dataset).make_creator(somebody)

        assert not UserObjectPermission.objects.exists()

    def test_a_superuser_creates_without_being_credited(self, record_chain):
        admin = PersonFactory(is_active=True, is_superuser=True, password="x")

        contribution = Crediting(record_chain.dataset).make_creator(admin)

        assert contribution is None
        assert not record_chain.dataset.contributors.filter(contributor=admin).exists()

    def test_a_creator_already_listed_is_raised_to_manage(self, record_chain, somebody):
        Crediting(record_chain.dataset).add(somebody)

        Crediting(record_chain.dataset).make_creator(somebody)

        level = RecordAccess(record_chain.dataset).own_level(somebody)
        assert level == ContributionLevel.MANAGE
        assert (
            record_chain.dataset.contributors.filter(contributor=somebody).count() == 1
        )


@pytest.fixture
def manager(db):
    return PersonFactory(is_active=True, is_claimed=True, password="x")


@pytest.fixture
def no_account(db):
    return PersonFactory(is_active=True, is_claimed=False)


@pytest.mark.django_db
class TestLastManager:
    def test_removing_the_only_manager_is_refused(self, record_chain, manager, grant):
        contribution = grant(record_chain.dataset, manager, ContributionLevel.MANAGE)

        with pytest.raises(ValidationError) as refused:
            Crediting(record_chain.dataset).remove(contribution)

        assert refused.value.code == "last_manager"
        assert Contribution.objects.filter(pk=contribution.pk).exists()

    def test_lowering_the_only_manager_is_refused_and_nothing_changes(
        self, record_chain, manager, grant
    ):
        contribution = grant(record_chain.dataset, manager, ContributionLevel.MANAGE)
        contribution.roles.set([role("Creator")])

        with pytest.raises(ValidationError) as refused:
            Crediting(record_chain.dataset).update(
                contribution, roles=[], level=ContributionLevel.EDIT
            )

        assert refused.value.code == "last_manager"
        contribution.refresh_from_db()
        assert contribution.level == ContributionLevel.MANAGE
        assert list(contribution.roles.all()) == [role("Creator")]

    def test_a_stale_contribution_is_judged_by_what_is_stored(
        self, record_chain, manager, grant
    ):
        contribution = grant(record_chain.dataset, manager, ContributionLevel.EDIT)
        stale = Contribution.objects.get(pk=contribution.pk)
        Contribution.objects.filter(pk=contribution.pk).update(
            level=ContributionLevel.MANAGE
        )

        with pytest.raises(ValidationError) as refused:
            Crediting(record_chain.dataset).update(
                stale, roles=[], level=ContributionLevel.VIEW
            )

        assert refused.value.code == "last_manager"
        contribution.refresh_from_db()
        assert contribution.level == ContributionLevel.MANAGE

    @pytest.mark.parametrize("kind", RECORDS)
    def test_the_rule_holds_for_every_kind_of_record(
        self, record_chain, manager, grant, kind
    ):
        record = getattr(record_chain, kind)
        contribution = grant(record, manager, ContributionLevel.MANAGE)

        with pytest.raises(ValidationError) as refused:
            Crediting(record).remove(contribution)

        assert refused.value.code == "last_manager"

    def test_with_two_managers_one_can_be_removed(self, record_chain, manager, grant):
        other = PersonFactory(is_active=True, is_claimed=True, password="x")
        grant(record_chain.dataset, other, ContributionLevel.MANAGE)
        contribution = grant(record_chain.dataset, manager, ContributionLevel.MANAGE)

        Crediting(record_chain.dataset).remove(contribution)

        assert RecordAccess(record_chain.dataset).managers() == {other.pk}

    def test_with_two_managers_one_can_be_lowered(self, record_chain, manager, grant):
        other = PersonFactory(is_active=True, is_claimed=True, password="x")
        grant(record_chain.dataset, other, ContributionLevel.MANAGE)
        contribution = grant(record_chain.dataset, manager, ContributionLevel.MANAGE)

        Crediting(record_chain.dataset).update(
            contribution, roles=[], level=ContributionLevel.VIEW
        )

        contribution.refresh_from_db()
        assert contribution.level == ContributionLevel.VIEW

    def test_the_manager_may_keep_the_level_while_changing_roles(
        self, record_chain, manager, grant
    ):
        contribution = grant(record_chain.dataset, manager, ContributionLevel.MANAGE)

        Crediting(record_chain.dataset).update(
            contribution, roles=[role("Creator")], level=ContributionLevel.MANAGE
        )

        assert list(contribution.roles.all()) == [role("Creator")]

    def test_a_manager_through_the_dataset_counts(self, record_chain, manager, grant):
        above = PersonFactory(is_active=True, is_claimed=True, password="x")
        grant(record_chain.dataset, above, ContributionLevel.MANAGE)
        contribution = grant(record_chain.sample, manager, ContributionLevel.MANAGE)

        Crediting(record_chain.sample).remove(contribution)

        assert RecordAccess(record_chain.sample).managers() == {above.pk}

    def test_a_manager_through_the_project_counts_for_a_lowered_level(
        self, record_chain, manager, grant
    ):
        above = PersonFactory(is_active=True, is_claimed=True, password="x")
        grant(record_chain.project, above, ContributionLevel.MANAGE)
        contribution = grant(record_chain.dataset, manager, ContributionLevel.MANAGE)

        Crediting(record_chain.dataset).update(
            contribution, roles=[], level=ContributionLevel.EDIT
        )

        contribution.refresh_from_db()
        assert contribution.level == ContributionLevel.EDIT

    def test_the_manager_who_manages_through_the_dataset_may_leave_the_sample(
        self, record_chain, manager, grant
    ):
        grant(record_chain.dataset, manager, ContributionLevel.MANAGE)
        contribution = grant(record_chain.sample, manager, ContributionLevel.MANAGE)

        Crediting(record_chain.sample).remove(contribution)

        assert RecordAccess(record_chain.sample).managers() == {manager.pk}

    def test_a_person_who_cannot_sign_in_does_not_count(
        self, record_chain, manager, no_account, grant
    ):
        grant(record_chain.dataset, no_account, ContributionLevel.MANAGE)
        contribution = grant(record_chain.dataset, manager, ContributionLevel.MANAGE)

        with pytest.raises(ValidationError) as refused:
            Crediting(record_chain.dataset).remove(contribution)

        assert refused.value.code == "last_manager"

    def test_a_person_who_cannot_sign_in_may_be_removed(
        self, record_chain, manager, no_account, grant
    ):
        grant(record_chain.dataset, manager, ContributionLevel.MANAGE)
        contribution = grant(record_chain.dataset, no_account, ContributionLevel.MANAGE)

        Crediting(record_chain.dataset).remove(contribution)

        assert not Contribution.objects.filter(pk=contribution.pk).exists()

    def test_a_record_with_no_manager_may_lose_anyone(
        self, record_chain, no_account, grant
    ):
        contribution = grant(record_chain.dataset, no_account, ContributionLevel.MANAGE)

        Crediting(record_chain.dataset).update(
            contribution, roles=[], level=ContributionLevel.VIEW
        )
        Crediting(record_chain.dataset).remove(contribution)

        assert not Contribution.objects.filter(pk=contribution.pk).exists()

    def test_raising_someone_on_a_record_with_no_manager_is_allowed(
        self, record_chain, manager, grant
    ):
        contribution = grant(record_chain.dataset, manager, ContributionLevel.EDIT)

        Crediting(record_chain.dataset).update(
            contribution, roles=[], level=ContributionLevel.MANAGE
        )

        assert RecordAccess(record_chain.dataset).managers() == {manager.pk}

    def test_removing_someone_who_is_not_a_manager_is_allowed(
        self, record_chain, manager, grant
    ):
        grant(record_chain.dataset, manager, ContributionLevel.MANAGE)
        editor = PersonFactory(is_active=True, is_claimed=True, password="x")
        contribution = grant(record_chain.dataset, editor, ContributionLevel.EDIT)

        Crediting(record_chain.dataset).remove(contribution)

        assert not Contribution.objects.filter(pk=contribution.pk).exists()

    def test_an_organization_may_be_removed_from_a_record_with_one_manager(
        self, record_chain, manager, grant
    ):
        grant(record_chain.dataset, manager, ContributionLevel.MANAGE)
        organization = Crediting(record_chain.dataset).add(OrganizationFactory())

        Crediting(record_chain.dataset).remove(organization)

        assert not Contribution.objects.filter(pk=organization.pk).exists()

    def test_would_leave_no_manager_answers_without_changing_anything(
        self, record_chain, manager, grant
    ):
        contribution = grant(record_chain.dataset, manager, ContributionLevel.MANAGE)
        crediting = Crediting(record_chain.dataset)

        assert crediting.would_leave_no_manager(contribution)
        assert crediting.would_leave_no_manager(
            contribution, level=ContributionLevel.EDIT
        )
        assert not crediting.would_leave_no_manager(
            contribution, level=ContributionLevel.MANAGE
        )
        contribution.refresh_from_db()
        assert contribution.level == ContributionLevel.MANAGE


@pytest.mark.django_db
class TestMove:
    @pytest.fixture
    def listed(self, record_chain, grant):
        """A dataset with four people and three organizations, listed alternately."""
        dataset = record_chain.dataset
        people, organizations = [], []
        for _ in range(3):
            people.append(grant(dataset, PersonFactory(), ContributionLevel.VIEW))
            organizations.append(grant(dataset, OrganizationFactory(), None))
        people.append(grant(dataset, PersonFactory(), ContributionLevel.VIEW))
        return SimpleNamespace(
            dataset=dataset,
            people=people,
            organizations=organizations,
            crediting=Crediting(dataset),
        )

    @staticmethod
    def placed(dataset):
        return list(Contribution.objects.for_entity(dataset).values_list("pk", "order"))

    @staticmethod
    def named(queryset):
        return [contribution.pk for contribution in queryset]

    def pks(self, items):
        return [item.pk for item in items]

    def test_a_person_moves_later_among_the_people(self, listed):
        first, second, third, fourth = listed.people

        listed.crediting.move(second, "down")

        assert self.named(Contribution.objects.for_entity(listed.dataset).people()) == (
            self.pks([first, third, second, fourth])
        )

    def test_a_person_moves_earlier_among_the_people(self, listed):
        first, second, third, fourth = listed.people

        listed.crediting.move(fourth, "up")

        assert self.named(Contribution.objects.for_entity(listed.dataset).people()) == (
            self.pks([first, second, fourth, third])
        )

    def test_an_organization_moves_among_the_organizations(self, listed):
        first, second, third = listed.organizations

        listed.crediting.move(first, "down")

        assert self.named(
            Contribution.objects.for_entity(listed.dataset).organizations()
        ) == self.pks([second, first, third])

    def test_moving_a_person_leaves_the_organizations_alone(self, listed):
        before = self.named(
            Contribution.objects.for_entity(listed.dataset).organizations()
        )
        orders = dict(
            Contribution.objects.filter(pk__in=before).values_list("pk", "order")
        )

        listed.crediting.move(listed.people[1], "up")

        after = Contribution.objects.filter(pk__in=before).values_list("pk", "order")
        assert dict(after) == orders

    def test_moving_an_organization_leaves_the_people_alone(self, listed):
        orders = dict(
            Contribution.objects.filter(pk__in=self.pks(listed.people)).values_list(
                "pk", "order"
            )
        )

        listed.crediting.move(listed.organizations[1], "down")

        after = Contribution.objects.filter(pk__in=orders).values_list("pk", "order")
        assert dict(after) == orders

    def test_a_move_changes_no_other_record(self, listed, record_chain, grant):
        elsewhere = [
            grant(record_chain.other_dataset, PersonFactory(), ContributionLevel.VIEW)
            for _ in range(2)
        ]
        orders = dict(
            Contribution.objects.filter(pk__in=self.pks(elsewhere)).values_list(
                "pk", "order"
            )
        )

        listed.crediting.move(listed.people[0], "down")

        after = Contribution.objects.filter(pk__in=orders).values_list("pk", "order")
        assert dict(after) == orders

    def test_the_first_person_cannot_move_earlier(self, listed):
        before = self.placed(listed.dataset)

        listed.crediting.move(listed.people[0], "up")

        after = self.placed(listed.dataset)
        assert after == before

    def test_the_last_person_cannot_move_later(self, listed):
        before = self.placed(listed.dataset)

        listed.crediting.move(listed.people[-1], "down")

        after = self.placed(listed.dataset)
        assert after == before

    def test_the_ends_of_the_organizations_do_not_move_either(self, listed):
        before = self.placed(listed.dataset)

        listed.crediting.move(listed.organizations[0], "up")
        listed.crediting.move(listed.organizations[-1], "down")

        after = self.placed(listed.dataset)
        assert after == before

    def test_the_only_one_of_its_kind_stays_put(self, record_chain, grant):
        dataset = record_chain.dataset
        only = grant(dataset, OrganizationFactory(), None)
        grant(dataset, PersonFactory(), ContributionLevel.VIEW)

        Crediting(dataset).move(only, "up")
        Crediting(dataset).move(only, "down")

        only.refresh_from_db()
        assert Contribution.objects.for_entity(dataset).organizations().get() == only

    def test_moving_twice_in_a_direction_goes_two_places(self, listed):
        first, second, third, fourth = listed.people

        listed.crediting.move(first, "down")
        listed.crediting.move(first, "down")

        assert self.named(Contribution.objects.for_entity(listed.dataset).people()) == (
            self.pks([second, third, first, fourth])
        )

    def test_contributions_sharing_an_order_move_deterministically(self, listed):
        first, second, third, fourth = listed.people
        Contribution.objects.filter(pk__in=self.pks(listed.people)).update(order=5)

        listed.crediting.move(second, "up")

        assert self.named(Contribution.objects.for_entity(listed.dataset).people()) == (
            self.pks([second, first, third, fourth])
        )

    def test_an_unknown_direction_is_refused_with_a_code(self, listed):
        with pytest.raises(ValidationError) as raised:
            listed.crediting.move(listed.people[1], "sideways")

        assert raised.value.code == "direction"

    def test_a_new_person_is_last_among_the_people(self, listed, somebody):
        added = listed.crediting.add(somebody)

        people = Contribution.objects.for_entity(listed.dataset).people()
        assert list(people)[-1] == added

    def test_a_new_organization_is_last_among_the_organizations(self, listed):
        added = listed.crediting.add(OrganizationFactory())

        organizations = Contribution.objects.for_entity(listed.dataset).organizations()
        assert list(organizations)[-1] == added

    def test_a_new_person_does_not_join_the_organizations_nor_the_reverse(
        self, listed, somebody
    ):
        person = listed.crediting.add(somebody)
        organization = listed.crediting.add(OrganizationFactory())

        scoped = Contribution.objects.for_entity(listed.dataset)
        assert person not in scoped.organizations()
        assert organization not in scoped.people()

    def test_removing_one_leaves_the_others_in_their_places(self, listed):
        first, second, third, fourth = listed.people

        listed.crediting.remove(second)

        assert self.named(Contribution.objects.for_entity(listed.dataset).people()) == (
            self.pks([first, third, fourth])
        )

    def test_editing_one_leaves_the_others_in_their_places(self, listed):
        first, second, third, fourth = listed.people

        listed.crediting.update(second, roles=[], level=ContributionLevel.EDIT)

        assert self.named(Contribution.objects.for_entity(listed.dataset).people()) == (
            self.pks([first, second, third, fourth])
        )


@pytest.mark.skipif(
    not connection.features.has_select_for_update,
    reason="this database cannot lock rows, so no SELECT ... FOR UPDATE is issued",
)
@pytest.mark.django_db
class TestRecordLock:
    @pytest.fixture
    def changes(self, record_chain, somebody, manager, grant):
        """Each changing method, as a call on a dataset that can take it."""
        dataset = record_chain.dataset
        grant(dataset, manager, ContributionLevel.MANAGE)
        listed = grant(dataset, PersonFactory(), ContributionLevel.EDIT)
        crediting = Crediting(dataset)
        return {
            "add": lambda: crediting.add(somebody),
            "update": lambda: crediting.update(
                listed, roles=[], level=ContributionLevel.VIEW
            ),
            "remove": lambda: crediting.remove(listed),
            "make_creator": lambda: crediting.make_creator(somebody),
            "move": lambda: crediting.move(listed, "up"),
        }

    @pytest.mark.parametrize(
        "method", ["add", "update", "remove", "make_creator", "move"]
    )
    def test_the_records_row_is_locked_before_its_contributors_are_read(
        self, record_chain, changes, method
    ):
        table = record_chain.dataset._meta.db_table

        with CaptureQueriesContext(connection) as captured:
            changes[method]()

        sql = [query["sql"] for query in captured.captured_queries]
        locks = [
            at
            for at, text in enumerate(sql)
            if "FOR UPDATE" in text and f'"{table}"' in text
        ]
        reads = [
            at
            for at, text in enumerate(sql)
            if f'"{Contribution._meta.db_table}"' in text
        ]
        assert locks
        assert locks[0] < reads[0]

    def test_the_lock_does_not_filter_out_a_private_record(
        self, record_chain, somebody
    ):
        dataset = record_chain.dataset
        dataset.visibility = Visibility.PRIVATE
        dataset.save()

        with CaptureQueriesContext(connection) as captured:
            Crediting(dataset).add(somebody)

        locks = [
            query["sql"]
            for query in captured.captured_queries
            if "FOR UPDATE" in query["sql"]
        ]
        assert locks
        assert "visibility" not in locks[0]
