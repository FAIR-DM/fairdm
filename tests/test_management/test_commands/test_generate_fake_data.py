"""Tests for ``fairdm/management/commands/generate_fake_data.py``."""

import pytest

from fairdm.contrib.contributors.models import Contribution
from fairdm.factories import PersonFactory, ProjectFactory
from fairdm.management.commands.generate_fake_data import Command


@pytest.mark.django_db
class TestAddContributors:
    """The command credits each contributor it is given against the object it is
    building, under one to three randomly chosen roles.

    A contributor holds one credit per object carrying every role they have on it, so
    the command has to record its roles on the credit already there rather than start a
    second one. It shares that rule with the model's own entry points, and it is the
    only caller that can be handed the same contributor twice.
    """

    def test_each_contributor_is_credited_once_with_roles(self):
        project = ProjectFactory()
        people = [PersonFactory(), PersonFactory()]

        Command()._add_contributors(project, people, is_project=True)

        credits = Contribution.objects.filter(object_id=project.pk)
        assert credits.count() == 2
        for credit in credits:
            assert credit.roles.exists()

    def test_the_same_contributor_twice_keeps_one_credit(self):
        project = ProjectFactory()
        person = PersonFactory()

        Command()._add_contributors(project, [person, person], is_project=True)

        credits = Contribution.objects.filter(object_id=project.pk, contributor=person)
        assert credits.count() == 1
        assert credits.get().roles.exists()
