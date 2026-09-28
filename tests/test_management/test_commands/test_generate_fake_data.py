"""Tests for ``fairdm/management/commands/generate_fake_data.py``."""

import pytest

from fairdm.contrib.contributors.models import Contribution
from fairdm.factories import PersonFactory, ProjectFactory
from fairdm.management.commands.generate_fake_data import Command


@pytest.mark.django_db
class TestAddContributors:
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
