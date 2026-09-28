"""Tests for the contributor template tags."""

import pytest
from research_vocabs.models import Concept, Vocabulary

from fairdm.contrib.contributors.models import Contribution
from fairdm.contrib.contributors.templatetags.contributor_tags import by_role, has_role


@pytest.fixture
def role():
    vocab, _ = Vocabulary.objects.get_or_create(name="fairdm-roles")
    role_concept, _ = Concept.objects.get_or_create(vocabulary=vocab, name="TestRole")
    return role_concept


@pytest.fixture
def contribution(project_for_contributions, person, role):
    contribution = Contribution.objects.create(
        content_object=project_for_contributions,
        contributor=person,
    )
    contribution.roles.add(role)
    return contribution


class TestByRoleFilter:
    @pytest.mark.django_db
    def test_by_role_filters_contributions(self, contribution, role):
        contributions = Contribution.objects.all()

        filtered = by_role(contributions, role.name)

        assert contribution in filtered

    @pytest.mark.django_db
    def test_by_role_with_multiple_roles(self, contribution, role):
        contributions = Contribution.objects.all()

        role_names = f"{role.name},NonExistentRole"
        filtered = by_role(contributions, role_names)

        assert contribution in filtered

    @pytest.mark.django_db
    def test_by_role_excludes_non_matching(self, contribution):
        contributions = Contribution.objects.all()

        filtered = by_role(contributions, "NonExistentRole")

        assert contribution not in filtered

    @pytest.mark.django_db
    def test_by_role_returns_all_when_no_role_specified(self, contribution):
        contributions = Contribution.objects.all()

        filtered = by_role(contributions, None)

        assert filtered.count() == contributions.count()
        assert contribution in filtered

    @pytest.mark.django_db
    def test_by_role_with_empty_string(self, contribution):
        contributions = Contribution.objects.all()

        filtered = by_role(contributions, "")

        assert filtered.count() == contributions.count()


class TestHasRoleFilter:
    @pytest.mark.django_db
    def test_has_role_returns_true_for_matching_role(self, contribution, role):
        result = has_role(contribution, role.name)

        assert result is True

    @pytest.mark.django_db
    def test_has_role_returns_false_for_non_matching_role(self, contribution):
        result = has_role(contribution, "NonExistentRole")

        assert result is False

    @pytest.mark.django_db
    def test_has_role_with_multiple_roles(self, contribution, role):
        role_names = f"{role.name},AnotherRole"
        result = has_role(contribution, role_names)

        assert result is True

    @pytest.mark.django_db
    def test_has_role_with_no_matching_roles(self, contribution):
        result = has_role(contribution, "NonExistentRole1,NonExistentRole2")

        assert result is False

    @pytest.mark.django_db
    def test_has_role_returns_contribution_when_no_role_specified(self, contribution):
        result = has_role(contribution, None)

        assert result == contribution

    @pytest.mark.django_db
    def test_has_role_with_empty_string(self, contribution):
        result = has_role(contribution, "")

        assert result == contribution
