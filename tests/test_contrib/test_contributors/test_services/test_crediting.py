"""Tests for ``Crediting``, the one place a record's contributors are changed."""

import pytest
from django.core.exceptions import ValidationError
from research_vocabs.models import Concept

from fairdm.contrib.contributors.access import RecordAccess
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Contribution
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.core.project.models import Project
from fairdm.factories import OrganizationFactory, PersonFactory

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
