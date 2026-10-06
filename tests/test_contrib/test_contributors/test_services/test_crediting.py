"""Tests for ``Crediting``, the one place a record's contributors are changed."""

import pytest
from django.core.exceptions import ValidationError
from research_vocabs.models import Concept

from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Contribution
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.core.project.models import Project
from fairdm.factories import AffiliationFactory, OrganizationFactory, PersonFactory

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
        elsewhere = Concept.objects.filter(
            vocabulary__name="fairdm-roles"
        ).exclude(name__in=Project.CONTRIBUTOR_ROLES.values)[0]

        with pytest.raises(ValidationError) as refused:
            Crediting(record_chain.project).update(contribution, roles=[elsewhere])

        assert refused.value.code == "role_not_offered"
        assert not contribution.roles.exists()

    def test_changing_the_roles_leaves_the_level_alone(
        self, record_chain, somebody, grant
    ):
        contribution = grant(record_chain.project, somebody, ContributionLevel.MANAGE)

        Crediting(record_chain.project).update(
            contribution, roles=[role("Creator")]
        )

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

    def test_the_organization_is_listed_on_the_record_once(self, record_chain, somebody):
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
