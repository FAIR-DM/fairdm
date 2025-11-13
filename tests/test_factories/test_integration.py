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


class TestFactoryIntegration(TestCase):
    """Test integration between all factory types."""

    def test_complete_research_workflow(self):
        """Test creating a complete research workflow using all factories."""
        # Create contributors
        principal_investigator = PersonFactory(first_name="Dr. Jane", last_name="Smith")
        research_institution = OrganizationFactory(name="University Research Center")

        # Create project with basic info (without automatic contributors)
        project = ProjectFactory(name="Climate Change Research Project", contributors=[])

        # Add contributors to project
        ContributionFactory(contributor=principal_investigator, content_object=project)
        ContributionFactory(contributor=research_institution, content_object=project)

        # Create dataset under the project
        dataset = DatasetFactory(project=project, name="Temperature Measurements Dataset")

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
        project_contributions = Contribution.objects.filter(content_type__model="project", object_id=project.pk)
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
            measurements = MeasurementFactory.create_batch(2, dataset=sample.dataset, sample=sample)
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

        # Create project (without automatic contributors)
        project = ProjectFactory(contributors=[])

        # Add all contributors to project
        contributions = [
            ContributionFactory(contributor=person, content_object=project),
            ContributionFactory(contributor=organization, content_object=project),
            ContributionFactory(contributor=contributor_as_person, content_object=project),
        ]

        # Verify all contributions are linked to project
        for contribution in contributions:
            self.assertEqual(contribution.content_object, project)

        # Verify we have 3 contributors
        project_contributions = Contribution.objects.filter(content_type__model="project", object_id=project.pk)
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
        sample_contribution = ContributionFactory(contributor=sample_collector, content_object=sample)
        measurement_contribution = ContributionFactory(contributor=lab_analyst, content_object=measurement)

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
            name="Custom Project Name", funding={"agency": "Custom Agency", "amount": 100000}
        )

        # Create person with specific parameters
        custom_person = PersonFactory(first_name="John", last_name="Doe", email="john.doe@example.org")

        # Verify custom values
        self.assertEqual(custom_project.name, "Custom Project Name")
        self.assertEqual(custom_project.funding["agency"], "Custom Agency")
        self.assertEqual(custom_person.first_name, "John")
        self.assertEqual(custom_person.email, "john.doe@example.org")

    def test_related_factory_relationships(self):
        """Test that related factories create proper relationships."""
        # Create a project (which should create descriptions and dates)
        project = ProjectFactory()

        # Verify related objects were created
        self.assertTrue(project.descriptions.exists())
        self.assertTrue(project.dates.exists())

        # Verify we have the expected number
        self.assertEqual(project.descriptions.count(), 2)  # As defined in factory
        self.assertEqual(project.dates.count(), 1)  # As defined in factory

    def test_factory_batch_creation_performance(self):
        """Test batch creation of related factories."""
        # Create multiple projects with all related objects
        projects = ProjectFactory.create_batch(5)

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
