"""Tests for fairdm/contrib/contributors/receivers.py.

FR-036, SC-012, design review RECON-002: Contribution.remove_user_perms is a
django-lifecycle AFTER_DELETE hook, which only runs from the model instance's own
delete(). QuerySet.delete() bypasses that entirely, so the withdrawal never fired for a
credit removed in bulk. withdraw_rights_on_credit_deletion is a genuine Django
post_delete signal receiver, which Django's deletion collector sends for every collected
row regardless of which delete path removed it.
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction

from fairdm.contrib.contributors.models import Contribution
from fairdm.core.utils import assign_perm


@pytest.mark.django_db
class TestWithdrawRightsOnCreditDeletion:
    def test_queryset_delete_withdraws_the_right(self, person, project_for_contributions):
        assign_perm("change_project", person, project_for_contributions)
        assert person.has_perm("project.change_project", project_for_contributions) is True

        contribution = Contribution.add_to(person, project_for_contributions)

        Contribution.objects.filter(pk=contribution.pk).delete()

        assert (
            person.has_perm("project.change_project", project_for_contributions)
            is False
        )

    def test_instance_delete_still_withdraws_the_right(
        self, person, project_for_contributions
    ):
        """The receiver also fires for an ordinary instance delete - it does not depend
        on the lifecycle hook remaining in place to cover that path."""
        assign_perm("view_project", person, project_for_contributions)
        assert person.has_perm("project.view_project", project_for_contributions) is True

        contribution = Contribution.add_to(person, project_for_contributions)
        contribution.delete()

        assert (
            person.has_perm("project.view_project", project_for_contributions) is False
        )

    def test_deleting_an_organizations_credit_does_not_error(
        self, organization, project_for_contributions
    ):
        """Organizations do not hold user-level object permissions, so the receiver must
        not try to withdraw any."""
        contribution = Contribution.add_to(organization, project_for_contributions)

        Contribution.objects.filter(pk=contribution.pk).delete()

    def test_deleting_the_credited_object_does_not_error(
        self, person, project_for_contributions
    ):
        """Deleting a project cascades to the credits recorded against it, and the
        project row is gone by the time those credits raise post_delete. The credited
        object is therefore unresolvable, and the receiver has nothing to withdraw a
        right over - it must not treat that as a right to withdraw from nothing.

        Every project and dataset created through the portal credits its creator, so
        this is the ordinary delete path rather than an edge case.
        """
        assign_perm("change_project", person, project_for_contributions)
        Contribution.add_to(person, project_for_contributions)

        project_for_contributions.delete()

        assert not Contribution.objects.exists()


@pytest.mark.django_db
class TestRefuseOffVocabularyRole:
    """FR-032, design review SPEC-001: a credit's roles are drawn from the framework's
    controlled roles vocabulary (``fairdm-roles``). Nothing that writes a role calls
    ``full_clean()``, so the rule has to live where the write actually happens -
    ``refuse_off_vocabulary_role``, an ``m2m_changed`` receiver on
    ``Contribution.roles.through``.

    ``roles.add()``/``roles.set()`` raise from inside their own
    ``transaction.atomic(savepoint=False)`` block. Each test that inspects state after
    the raise wraps the call in its own ``transaction.atomic()`` first, exactly as any
    caller nested inside a wider transaction already has to - Django's own docs describe
    this as the way to keep using the connection after an exception raised inside
    ``atomic()``.
    """

    def test_add_with_an_off_vocabulary_role_raises_and_the_relation_stays_empty(
        self, contribution, off_vocabulary_role
    ):
        with transaction.atomic(), pytest.raises(
            ValidationError, match="roles vocabulary"
        ):
            contribution.roles.add(off_vocabulary_role)

        assert contribution.roles.count() == 0

    def test_set_with_an_off_vocabulary_role_raises_and_leaves_roles_unchanged(
        self, contribution, contribution_roles, off_vocabulary_role
    ):
        genuine_role = contribution_roles.first()
        contribution.roles.add(genuine_role)

        with transaction.atomic(), pytest.raises(
            ValidationError, match="roles vocabulary"
        ):
            contribution.roles.set([off_vocabulary_role])

        assert list(contribution.roles.all()) == [genuine_role]

    def test_adding_several_roles_where_one_is_off_vocabulary_stores_none_of_them(
        self, contribution, contribution_roles, off_vocabulary_role
    ):
        genuine_role = contribution_roles.first()

        with transaction.atomic(), pytest.raises(
            ValidationError, match="roles vocabulary"
        ):
            contribution.roles.add(genuine_role, off_vocabulary_role)

        assert contribution.roles.count() == 0

    def test_a_genuine_role_still_adds(self, contribution, contribution_roles):
        genuine_role = contribution_roles.first()

        contribution.roles.add(genuine_role)

        assert list(contribution.roles.all()) == [genuine_role]

    def test_a_genuine_role_still_sets(self, contribution, contribution_roles):
        genuine_role = contribution_roles.first()

        contribution.roles.set([genuine_role])

        assert list(contribution.roles.all()) == [genuine_role]


@pytest.mark.django_db
class TestProductionWritePathsRefuseOffVocabularyRoles:
    """Contribution.add_to, Contributor.add_to and BaseModel.add_contributor are the
    three production entry points that credit a contributor - the reason
    refuse_off_vocabulary_role exists (see the receivers.py module docstring). Each
    returns an ordinary Contribution, and its ``.roles`` relation must refuse an
    off-vocabulary concept exactly as one built any other way does - the write path
    used to create the credit must not carry some exemption from the rule.
    """

    def test_contribution_add_to_returns_a_contribution_whose_roles_still_refuse(
        self, person, project_for_contributions, off_vocabulary_role
    ):
        contribution = Contribution.add_to(person, project_for_contributions)

        with transaction.atomic(), pytest.raises(
            ValidationError, match="roles vocabulary"
        ):
            contribution.roles.add(off_vocabulary_role)

        assert contribution.roles.count() == 0

    def test_contributor_add_to_returns_a_contribution_whose_roles_still_refuse(
        self, person, project_for_contributions, off_vocabulary_role
    ):
        contribution = person.add_to(project_for_contributions)

        with transaction.atomic(), pytest.raises(
            ValidationError, match="roles vocabulary"
        ):
            contribution.roles.add(off_vocabulary_role)

        assert contribution.roles.count() == 0

    def test_add_contributor_returns_a_contribution_whose_roles_still_refuse(
        self, person, project_for_contributions, off_vocabulary_role
    ):
        contribution = project_for_contributions.add_contributor(person)

        with transaction.atomic(), pytest.raises(
            ValidationError, match="roles vocabulary"
        ):
            contribution.roles.add(off_vocabulary_role)

        assert contribution.roles.count() == 0
