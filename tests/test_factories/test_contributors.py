"""Tests for contributor-related factories (Person, Organization, Contribution).

Also covers integration workflows where contributor factories are combined
with the core model factories (Project, Dataset, Sample, Measurement).
"""

import pytest
from django.test import TestCase

from fairdm.contrib.contributors.models import Contribution, Organization, Person
from fairdm.factories import (
    DatasetFactory,
    MeasurementFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
    SampleFactory,
)
from fairdm.factories.contributors import ContributionFactory, ContributorFactory


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


@pytest.mark.django_db
class TestContributorFactoryCreation:
    """Test PersonFactory and OrganizationFactory instance creation."""

    def test_person_factory_creates_person(self):
        """Test PersonFactory creates a valid Person instance."""
        person = PersonFactory()

        assert isinstance(person, Person)
        assert person.pk is not None
        assert person.name
        assert person.first_name
        assert person.last_name
        assert person.email
        assert "@" in person.email
        assert person.profile

    def test_person_factory_unique_emails(self):
        """Test PersonFactory creates unique emails."""
        person1 = PersonFactory()
        person2 = PersonFactory()

        assert person1.email != person2.email

    def test_person_factory_get_or_create_by_email(self):
        """Test PersonFactory django_get_or_create works for email."""
        email = "test@example.com"
        person1 = PersonFactory(email=email)
        person2 = PersonFactory(email=email)

        assert person1.pk == person2.pk
        assert Person.objects.filter(email=email).count() == 1

    def test_organization_factory_creates_organization(self):
        """Test OrganizationFactory creates a valid Organization instance."""
        org = OrganizationFactory()

        assert isinstance(org, Organization)
        assert org.pk is not None
        assert org.name
        assert org.profile


@pytest.mark.django_db
class TestContributionFactory:
    """Test contribution factory."""

    def test_contribution_factory_with_project(self):
        """Test ContributionFactory can create contributions to projects."""
        person = PersonFactory()
        project = ProjectFactory()

        contribution = ContributionFactory(content_object=project, contributor=person)

        assert isinstance(contribution, Contribution)
        assert contribution.pk is not None
        assert contribution.contributor == person
        assert contribution.content_object == project

    def test_contribution_factory_with_dataset(self):
        """Test ContributionFactory can create contributions to datasets."""
        org = OrganizationFactory()
        dataset = DatasetFactory()

        contribution = ContributionFactory(content_object=dataset, contributor=org)

        assert isinstance(contribution, Contribution)
        assert contribution.pk is not None
        assert contribution.contributor == org
        assert contribution.content_object == dataset


class TestFactoryIntegration(TestCase):
    """Test integration between contributor factories and core factories."""

    def test_complete_research_workflow(self):
        """Test creating a complete research workflow using all factories."""
        # Create contributors
        principal_investigator = PersonFactory(first_name="Dr. Jane", last_name="Smith")
        research_institution = OrganizationFactory(name="University Research Center")

        # Create project with basic info
        project = ProjectFactory(name="Climate Change Research Project")

        # Add contributors to project
        ContributionFactory(contributor=principal_investigator, content_object=project)
        ContributionFactory(contributor=research_institution, content_object=project)

        # Create dataset under the project
        dataset = DatasetFactory(
            project=project, name="Temperature Measurements Dataset"
        )

        # Create samples in the dataset
        samples = SampleFactory.create_batch(3, dataset=dataset)

        # Create measurements for each sample
        measurements = []
        for sample in samples:
            measurement = MeasurementFactory(dataset=dataset, sample=sample)
            measurements.append(measurement)

        # Verify the complete structure
        self.assertEqual(project.name, "Climate Change Research Project")
        self.assertEqual(dataset.project, project)
        self.assertEqual(len(samples), 3)
        self.assertEqual(len(measurements), 3)

        # Verify contributors
        project_contributions = Contribution.objects.filter(
            content_type__model="project", object_id=project.pk
        )
        self.assertEqual(project_contributions.count(), 2)

        # Verify all relationships are properly connected
        for sample in samples:
            self.assertEqual(sample.dataset, dataset)

        for measurement in measurements:
            self.assertIn(measurement.sample, samples)
            self.assertEqual(measurement.dataset, dataset)

    def test_project_with_multiple_datasets_and_samples(self):
        """Test project with complex structure."""
        project = ProjectFactory()

        # Create multiple datasets
        datasets = DatasetFactory.create_batch(2, project=project)

        # Create samples for each dataset
        all_samples = []
        for dataset in datasets:
            samples = SampleFactory.create_batch(2, dataset=dataset)
            all_samples.extend(samples)

        # Create measurements
        all_measurements = []
        for sample in all_samples:
            measurements = MeasurementFactory.create_batch(
                2, dataset=sample.dataset, sample=sample
            )
            all_measurements.extend(measurements)

        # Verify structure
        self.assertEqual(len(datasets), 2)
        self.assertEqual(len(all_samples), 4)  # 2 datasets x 2 samples each
        self.assertEqual(len(all_measurements), 8)  # 4 samples x 2 measurements each

        # Verify all datasets belong to project
        for dataset in datasets:
            self.assertEqual(dataset.project, project)

        # Verify all samples belong to correct datasets
        for sample in all_samples:
            self.assertIn(sample.dataset, datasets)

        # Verify all measurements belong to correct samples and datasets
        for measurement in all_measurements:
            self.assertIn(measurement.sample, all_samples)
            self.assertEqual(measurement.dataset, measurement.sample.dataset)

    def test_contributor_project_relationships(self):
        """Test various contributor-project relationships."""
        # Create different types of contributors
        person = PersonFactory()
        organization = OrganizationFactory()
        contributor_as_person = ContributorFactory()  # Creates Person by default

        # Create project
        project = ProjectFactory()

        # Add all contributors to project
        contributions = [
            ContributionFactory(contributor=person, content_object=project),
            ContributionFactory(contributor=organization, content_object=project),
            ContributionFactory(
                contributor=contributor_as_person, content_object=project
            ),
        ]

        # Verify all contributions are linked to project
        for contribution in contributions:
            self.assertEqual(contribution.content_object, project)

        # Verify we have 3 contributors
        project_contributions = Contribution.objects.filter(
            content_type__model="project", object_id=project.pk
        )
        self.assertEqual(project_contributions.count(), 3)

    def test_sample_measurement_contributor_workflow(self):
        """Test adding contributors at sample and measurement levels."""
        # Create the hierarchy
        dataset = DatasetFactory()
        sample = SampleFactory(dataset=dataset)
        measurement = MeasurementFactory(dataset=dataset, sample=sample)

        # Create contributors
        sample_collector = PersonFactory(first_name="Field", last_name="Collector")
        lab_analyst = PersonFactory(first_name="Lab", last_name="Analyst")

        # Add contributors at different levels
        sample_contribution = ContributionFactory(
            contributor=sample_collector, content_object=sample
        )
        measurement_contribution = ContributionFactory(
            contributor=lab_analyst, content_object=measurement
        )

        # Verify contributions
        self.assertEqual(sample_contribution.content_object, sample)
        self.assertEqual(measurement_contribution.content_object, measurement)

        # Verify contributors are different people
        self.assertNotEqual(sample_collector, lab_analyst)

    def test_factory_build_vs_create(self):
        """Test difference between build() and create() methods."""
        # Build instances (not saved to database)
        project_built = ProjectFactory.build()
        person_built = PersonFactory.build()

        # Create instances (saved to database)
        project_created = ProjectFactory()
        person_created = PersonFactory()

        # Built instances should not have PKs
        self.assertIsNone(project_built.pk)
        self.assertIsNone(person_built.pk)

        # Created instances should have PKs
        self.assertIsNotNone(project_created.pk)
        self.assertIsNotNone(person_created.pk)

    def test_factory_custom_parameters(self):
        """Test creating instances with custom parameters."""
        # Create project with specific parameters
        custom_project = ProjectFactory(
            name="Custom Project Name",
            funding=[{"funderName": "Custom Agency"}],
        )

        # Create person with specific parameters
        custom_person = PersonFactory(
            first_name="John", last_name="Doe", email="john.doe@example.org"
        )

        # Verify custom values
        self.assertEqual(custom_project.name, "Custom Project Name")
        self.assertEqual(custom_project.funding[0]["funderName"], "Custom Agency")
        self.assertEqual(custom_person.first_name, "John")
        self.assertEqual(custom_person.email, "john.doe@example.org")

    def test_related_factory_relationships(self):
        """Test that related factories create proper relationships."""
        # Create a project with explicit opt-in for descriptions and dates
        project = ProjectFactory(descriptions=2, dates=1)

        # Verify related objects were created
        self.assertTrue(project.descriptions.exists())
        self.assertTrue(project.dates.exists())

        # Verify we have the expected number
        self.assertEqual(project.descriptions.count(), 2)
        self.assertEqual(project.dates.count(), 1)

    def test_factory_batch_creation_performance(self):
        """Test batch creation of related factories."""
        # Create multiple projects with all related objects (opt-in)
        projects = ProjectFactory.create_batch(5, descriptions=2, dates=1)

        # Verify all projects have related objects
        for project in projects:
            self.assertTrue(project.descriptions.exists())
            self.assertTrue(project.dates.exists())

        # Create batch of samples with shared dataset
        dataset = DatasetFactory()
        samples = SampleFactory.create_batch(10, dataset=dataset)

        # Verify all samples belong to the same dataset
        for sample in samples:
            self.assertEqual(sample.dataset, dataset)

    def test_polymorphic_contributor_behavior(self):
        """Test polymorphic behavior of contributors."""
        # Create different contributor types
        person = PersonFactory()
        organization = OrganizationFactory()

        # Both should be contributors but different types
        from fairdm.contrib.contributors.models import Contributor

        self.assertIsInstance(person, Contributor)
        self.assertIsInstance(organization, Contributor)
        self.assertIsInstance(person, Person)
        self.assertIsInstance(organization, Organization)

        # They should have different polymorphic types
        self.assertNotEqual(person.polymorphic_ctype, organization.polymorphic_ctype)
