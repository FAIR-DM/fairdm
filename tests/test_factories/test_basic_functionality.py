from django.test import TestCase

from fairdm.factories import (
    DatasetFactory,
    MeasurementFactory,
    ProjectFactory,
    SampleFactory,
)
from fairdm.factories.contributors import ContributorFactory, PersonFactory


class TestBasicFactoryFunctionality(TestCase):
    """Test basic functionality of all factories."""

    def test_all_factories_can_create_instances(self):
        """Test that all factories can create basic instances without errors."""
        # Test core factories
        project = ProjectFactory()
        dataset = DatasetFactory()
        sample = SampleFactory()
        measurement = MeasurementFactory()

        # Test contributor factories
        person = PersonFactory()
        contributor = ContributorFactory()

        # Basic assertions to ensure objects were created
        self.assertIsNotNone(project.pk)
        self.assertIsNotNone(dataset.pk)
        self.assertIsNotNone(sample.pk)
        self.assertIsNotNone(measurement.pk)
        self.assertIsNotNone(person.pk)
        self.assertIsNotNone(contributor.pk)

    def test_all_factories_can_build_instances(self):
        """Test that all factories can build instances without saving."""
        # Test core factories
        project = ProjectFactory.build()
        dataset = DatasetFactory.build()
        sample = SampleFactory.build()
        measurement = MeasurementFactory.build()

        # Test contributor factories
        person = PersonFactory.build()
        contributor = ContributorFactory.build()

        # Built instances should not have PKs
        self.assertIsNone(project.pk)
        self.assertIsNone(dataset.pk)
        self.assertIsNone(sample.pk)
        self.assertIsNone(measurement.pk)
        self.assertIsNone(person.pk)
        self.assertIsNone(contributor.pk)

    def test_factory_batch_creation(self):
        """Test that all factories support batch creation."""
        # Test batch creation with small numbers
        projects = ProjectFactory.create_batch(2)
        people = PersonFactory.create_batch(2)

        self.assertEqual(len(projects), 2)
        self.assertEqual(len(people), 2)

        # Ensure all have different PKs
        self.assertNotEqual(projects[0].pk, projects[1].pk)
        self.assertNotEqual(people[0].pk, people[1].pk)

    def test_factory_custom_parameters(self):
        """Test that factories accept custom parameters."""
        custom_name = "Test Project"
        project = ProjectFactory(name=custom_name)
        self.assertEqual(project.name, custom_name)

        custom_first_name = "John"
        person = PersonFactory(first_name=custom_first_name)
        self.assertEqual(person.first_name, custom_first_name)

    def test_factory_relationships(self):
        """Test that factories create proper relationships."""
        # Create related objects
        project = ProjectFactory()
        dataset = DatasetFactory(project=project)
        sample = SampleFactory(dataset=dataset)
        measurement = MeasurementFactory(dataset=dataset, sample=sample)

        # Verify relationships
        self.assertEqual(dataset.project, project)
        self.assertEqual(sample.dataset, dataset)
        self.assertEqual(measurement.dataset, dataset)
        self.assertEqual(measurement.sample, sample)
