"""Tests for fairdm/contrib/contributors/receivers.py.

FR-036, SC-012, design review RECON-002: Contribution.remove_user_perms is a
django-lifecycle AFTER_DELETE hook, which only runs from the model instance's own
delete(). QuerySet.delete() bypasses that entirely, so the withdrawal never fired for a
credit removed in bulk. withdraw_rights_on_credit_deletion is a genuine Django
post_delete signal receiver, which Django's deletion collector sends for every collected
row regardless of which delete path removed it.
"""

import pytest

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
