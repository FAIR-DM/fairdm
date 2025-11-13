from django.test import TestCase

from fairdm.contrib.contributors.models import Contribution, Organization, Person
from fairdm.factories import (
    OrganizationFactory,
    PersonFactory,
)
from fairdm.factories.contributors import ContributionFactory


class TestContributorFactories(TestCase):
    """Test contributor factory functionality."""

    def test_person_factory_creates_valid_person(self):
        """Test PersonFactory creates a valid Person instance."""
        person = PersonFactory()

        self.assertIsInstance(person, Person)
        self.assertIsNotNone(person.pk)
        self.assertIsNotNone(person.name)

    def test_organization_factory_creates_valid_organization(self):
        """Test OrganizationFactory creates a valid Organization instance."""
        organization = OrganizationFactory()

        self.assertIsInstance(organization, Organization)
        self.assertIsNotNone(organization.pk)
        self.assertIsNotNone(organization.name)

    def test_contribution_factory_creates_valid_contribution(self):
        """Test ContributionFactory creates a valid Contribution instance."""
        contribution = ContributionFactory()

        self.assertIsInstance(contribution, Contribution)
        self.assertIsNotNone(contribution.pk)
        self.assertIsNotNone(contribution.contributor)
