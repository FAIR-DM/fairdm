"""Tests for the contributor template tags."""

import pytest
from research_vocabs.models import Concept, Vocabulary

from fairdm.contrib.contributors.models import Contribution
from fairdm.contrib.contributors.templatetags.contributor_tags import (
    as_contributor,
    as_contributors,
    by_role,
    contributor_name,
    has_role,
    split_contributors,
)
from fairdm.factories import OrganizationFactory, PersonFactory


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


@pytest.mark.django_db
class TestAsContributor:
    def test_a_contribution_gives_its_contributor_as_its_concrete_type(self, contribution):
        assert as_contributor(contribution) == contribution.contributor.get_real_instance()
        assert type(as_contributor(contribution)).__name__ == "Person"

    def test_a_contributor_is_returned_as_it_is(self):
        organization = OrganizationFactory()

        assert as_contributor(organization) is organization

    def test_nothing_gives_nothing(self):
        assert as_contributor(None) is None


@pytest.mark.django_db
class TestAsContributors:
    def test_a_mixed_list_becomes_contributors(self, contribution):
        organization = OrganizationFactory()

        result = as_contributors([contribution, organization])

        assert [c.pk for c in result] == [contribution.contributor_id, organization.pk]

    def test_nothing_gives_an_empty_list(self):
        assert as_contributors(None) == []


@pytest.mark.django_db
class TestContributorName:
    def test_the_preferred_name_by_default(self):
        person = PersonFactory(first_name="Ada", last_name="Lovelace", name="Countess Lovelace")

        assert contributor_name(person) == "Countess Lovelace"

    def test_a_citation_format_uses_the_given_and_family_names(self):
        person = PersonFactory(first_name="Ada", last_name="Lovelace", name="Countess Lovelace")

        assert contributor_name(person, "family_given") == "Lovelace, Ada"

    def test_an_organization_ignores_the_format(self):
        organization = OrganizationFactory(name="University of Potsdam")

        assert contributor_name(organization, "family_given") == "University of Potsdam"


class TestSplitContributors:
    def test_past_the_limit_the_rest_are_counted(self):
        group = split_contributors(["a", "b", "c", "d", "e"], limit=2)

        assert group == {"shown": ["a", "b"], "more": 3, "total": 5}

    def test_one_over_the_limit_is_shown_rather_than_counted(self):
        group = split_contributors(["a", "b", "c"], limit=2)

        assert group == {"shown": ["a", "b", "c"], "more": 0, "total": 3}

    def test_a_given_total_counts_contributors_already_cut_off(self):
        group = split_contributors(["a", "b"], limit=2, total=10)

        assert group == {"shown": ["a", "b"], "more": 8, "total": 10}

    def test_no_limit_shows_everyone(self):
        group = split_contributors(["a", "b", "c"], limit=0)

        assert group == {"shown": ["a", "b", "c"], "more": 0, "total": 3}
