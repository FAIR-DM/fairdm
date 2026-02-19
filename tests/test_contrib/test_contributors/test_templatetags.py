"""
Tests for Template Tags (Phase 12).

This module tests contributor template tags for filtering and display:
- by_role: Filter contributions by role
- has_role: Check if contribution has specific role

Tests correspond to tasks T120-T121.
"""

import pytest
from research_vocabs.models import Concept, Vocabulary

from fairdm.contrib.contributors.models import Contribution
from fairdm.contrib.contributors.templatetags.contributor_tags import by_role, has_role


@pytest.fixture
def role():
    """Create a test role Concept."""
    vocab, _ = Vocabulary.objects.get_or_create(name="fairdm-roles")
    role_concept, _ = Concept.objects.get_or_create(vocabulary=vocab, name="TestRole")
    return role_concept


@pytest.fixture
def contribution(project_for_contributions, person, role):
    """Create a contribution with a role."""
    contribution = Contribution.objects.create(
        content_object=project_for_contributions,
        contributor=person,
    )
    contribution.roles.add(role)
    return contribution


# ── T120: by_role template filter ────────────────────────────────────────────


class TestByRoleFilter:
    """Test by_role template filter."""

    @pytest.mark.django_db
    def test_by_role_filters_contributions(self, contribution, role):
        """by_role filter returns contributions with specified role."""
        # Get all contributions
        contributions = Contribution.objects.all()

        # Filter by role
        filtered = by_role(contributions, role.name)

        # Should include the contribution with that role
        assert contribution in filtered

    @pytest.mark.django_db
    def test_by_role_with_multiple_roles(self, contribution, role):
        """by_role filter accepts comma-separated role names."""
        # Get all contributions
        contributions = Contribution.objects.all()

        # Filter by multiple roles (comma-separated)
        role_names = f"{role.name},NonExistentRole"
        filtered = by_role(contributions, role_names)

        # Should include contributions with any of the specified roles
        assert contribution in filtered

    @pytest.mark.django_db
    def test_by_role_excludes_non_matching(self, contribution):
        """by_role filter excludes contributions without specified role."""
        # Get all contributions
        contributions = Contribution.objects.all()

        # Filter by a role that doesn't exist
        filtered = by_role(contributions, "NonExistentRole")

        # Should not include the contribution
        assert contribution not in filtered

    @pytest.mark.django_db
    def test_by_role_returns_all_when_no_role_specified(self, contribution):
        """by_role filter returns all contributions when role is None."""
        # Get all contributions
        contributions = Contribution.objects.all()

        # Filter without specifying role
        filtered = by_role(contributions, None)

        # Should return all contributions
        assert filtered.count() == contributions.count()
        assert contribution in filtered

    @pytest.mark.django_db
    def test_by_role_with_empty_string(self, contribution):
        """by_role filter returns all contributions when role is empty string."""
        # Get all contributions
        contributions = Contribution.objects.all()

        # Filter with empty string
        filtered = by_role(contributions, "")

        # Should return all contributions
        assert filtered.count() == contributions.count()


# ── T121: has_role template filter ───────────────────────────────────────────


class TestHasRoleFilter:
    """Test has_role template filter."""

    @pytest.mark.django_db
    def test_has_role_returns_true_for_matching_role(self, contribution, role):
        """has_role filter returns True when contribution has the specified role."""
        # Check if contribution has the role
        result = has_role(contribution, role.name)

        # Should return True
        assert result is True

    @pytest.mark.django_db
    def test_has_role_returns_false_for_non_matching_role(self, contribution):
        """has_role filter returns False when contribution doesn't have the role."""
        # Check for a role that doesn't exist
        result = has_role(contribution, "NonExistentRole")

        # Should return False
        assert result is False

    @pytest.mark.django_db
    def test_has_role_with_multiple_roles(self, contribution, role):
        """has_role filter accepts comma-separated role names."""
        # Check if contribution has any of the specified roles
        role_names = f"{role.name},AnotherRole"
        result = has_role(contribution, role_names)

        # Should return True because it has at least one role
        assert result is True

    @pytest.mark.django_db
    def test_has_role_with_no_matching_roles(self, contribution):
        """has_role filter returns False when contribution has none of the specified roles."""
        # Check for multiple roles that don't exist
        result = has_role(contribution, "NonExistentRole1,NonExistentRole2")

        # Should return False
        assert result is False

    @pytest.mark.django_db
    def test_has_role_returns_contribution_when_no_role_specified(self, contribution):
        """has_role filter returns the contribution when role is None."""
        # Check without specifying role
        result = has_role(contribution, None)

        # Should return the contribution itself
        assert result == contribution

    @pytest.mark.django_db
    def test_has_role_with_empty_string(self, contribution):
        """has_role filter returns the contribution when role is empty string."""
        # Check with empty string
        result = has_role(contribution, "")

        # Should return the contribution itself
        assert result == contribution
