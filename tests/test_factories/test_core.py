"""Tests for the core FairDM factories (Project, Dataset, Sample, Measurement).

Covers basic instance creation, relationship wiring, opt-in description/date
generation, vocabulary validation, and integration workflows across the core
model hierarchy.
"""

import factory
import pytest
from django.test import TestCase

from fairdm.contrib.contributors.models import Person
from fairdm.core.dataset.models import Dataset, DatasetDate, DatasetDescription
from fairdm.core.measurement.models import (
    Measurement,
    MeasurementDate,
    MeasurementDescription,
)
from fairdm.core.project.models import Project, ProjectDate, ProjectDescription
from fairdm.core.sample.models import Sample, SampleDate, SampleDescription
from fairdm.factories import (
    DatasetFactory,
    MeasurementFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.factories.contributors import ContributionFactory, ContributorFactory
from fairdm.factories.core import (
    DatasetDateFactory,
    DatasetDescriptionFactory,
    MeasurementDateFactory,
    MeasurementDescriptionFactory,
    ProjectDateFactory,
    ProjectDescriptionFactory,
    SampleDateFactory,
    SampleDescriptionFactory,
)
from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory


class TestCoreFactoriesBasic(TestCase):
    """Test basic functionality of all core factories."""

    def test_project_factory_creates_instance(self):
        """Test ProjectFactory creates valid instances with relationships."""
        project = ProjectFactory(descriptions=2, dates=1)

        self.assertIsInstance(project, Project)
        self.assertIsNotNone(project.pk)
        self.assertIsNotNone(project.name)

        # Check that descriptions and dates are created
        descriptions = ProjectDescription.objects.filter(related=project)
        dates = ProjectDate.objects.filter(related=project)
        self.assertEqual(descriptions.count(), 2)
        self.assertEqual(dates.count(), 1)

    def test_dataset_factory_creates_instance(self):
        """Test DatasetFactory creates valid instances with relationships."""
        dataset = DatasetFactory(descriptions=2, dates=1)

        self.assertIsInstance(dataset, Dataset)
        self.assertIsNotNone(dataset.pk)
        self.assertIsNotNone(dataset.name)
        self.assertIsNotNone(dataset.project)

        # Check that descriptions and dates are created
        descriptions = DatasetDescription.objects.filter(related=dataset)
        dates = DatasetDate.objects.filter(related=dataset)
        self.assertEqual(descriptions.count(), 2)
        self.assertEqual(dates.count(), 1)

    def test_sample_factory_creates_instance(self):
        """Test SampleFactory creates valid instances with relationships."""
        sample = RockSampleFactory(descriptions=2, dates=1)

        self.assertIsInstance(sample, Sample)
        self.assertIsNotNone(sample.pk)
        self.assertIsNotNone(sample.name)
        self.assertIsNotNone(sample.dataset)

        # Check that descriptions and dates are created
        descriptions = SampleDescription.objects.filter(related=sample)
        dates = SampleDate.objects.filter(related=sample)
        self.assertEqual(descriptions.count(), 2)
        self.assertEqual(dates.count(), 1)

    def test_measurement_factory_creates_instance(self):
        """Test a concrete measurement factory creates valid instances with relationships.

        MeasurementFactory itself is abstract (FR-011 forbids the bare Measurement
        record - see TestMeasurementFactories below for that assertion); this test
        exercises its concrete demo subclass, the same way test_sample_factory_creates_instance
        above exercises RockSampleFactory rather than the abstract SampleFactory.
        """
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(), descriptions=2, dates=1
        )

        self.assertIsInstance(measurement, Measurement)
        self.assertIsNotNone(measurement.pk)
        self.assertIsNotNone(measurement.name)
        self.assertIsNotNone(measurement.dataset)
        self.assertIsNotNone(measurement.sample)

        # Check that descriptions and dates are created
        descriptions = MeasurementDescription.objects.filter(related=measurement)
        dates = MeasurementDate.objects.filter(related=measurement)
        self.assertEqual(descriptions.count(), 2)
        self.assertEqual(dates.count(), 1)

    def test_description_factories_with_related_objects(self):
        """Test description factories work when provided with related objects."""
        project = ProjectFactory()
        dataset = DatasetFactory()
        sample = RockSampleFactory()
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        # Test description factories
        project_desc = ProjectDescriptionFactory(related=project)
        dataset_desc = DatasetDescriptionFactory(related=dataset)
        sample_desc = SampleDescriptionFactory(related=sample)
        measurement_desc = MeasurementDescriptionFactory(related=measurement)

        self.assertEqual(project_desc.related, project)
        self.assertEqual(dataset_desc.related, dataset)
        self.assertEqual(sample_desc.related, sample)
        self.assertEqual(measurement_desc.related, measurement)

        # Check default types
        self.assertEqual(project_desc.type, "Abstract")
        self.assertEqual(dataset_desc.type, "Abstract")
        # "Abstract" is not a member of the sample description vocabulary (005-core-samples
        # T005) - SampleDescriptionFactory's default was corrected to "SampleCollection", a
        # real member, so the assertion here tracks that.
        self.assertEqual(sample_desc.type, "SampleCollection")
        # "Abstract" is not a member of the measurement description vocabulary
        # (006-core-measurements T001) - MeasurementDescriptionFactory's default was
        # corrected to "MeasurementConditions", a real member, so the assertion here
        # tracks that.
        self.assertEqual(measurement_desc.type, "MeasurementConditions")

    def test_date_factories_with_related_objects(self):
        """Test date factories work when provided with related objects."""
        project = ProjectFactory()
        dataset = DatasetFactory()
        sample = RockSampleFactory()
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        # Test date factories
        project_date = ProjectDateFactory(related=project)
        dataset_date = DatasetDateFactory(related=dataset)
        sample_date = SampleDateFactory(related=sample)
        measurement_date = MeasurementDateFactory(related=measurement)

        self.assertEqual(project_date.related, project)
        self.assertEqual(dataset_date.related, dataset)
        self.assertEqual(sample_date.related, sample)
        self.assertEqual(measurement_date.related, measurement)

        # Check default types
        self.assertEqual(project_date.type, "Start")
        # "Created" is not a member of the dataset date vocabulary (D-008, D-012;
        # 004-core-datasets R3) - DatasetDateFactory's default was corrected to
        # "Available", a real member, so the assertion here tracks that.
        self.assertEqual(dataset_date.type, "Available")
        self.assertEqual(sample_date.type, "Created")
        # "Created" is not a member of the measurement date vocabulary
        # (006-core-measurements T001) - MeasurementDateFactory's default was
        # corrected to "Setup", a real member, so the assertion here tracks that.
        self.assertEqual(measurement_date.type, "Setup")

    def test_factories_support_build_mode(self):
        """Test that all factories support build mode (without saving to database)."""
        project = ProjectFactory.build()
        dataset = DatasetFactory.build()
        sample = RockSampleFactory.build()
        measurement = ExampleMeasurementFactory.build()

        # Built instances should not have PKs
        self.assertIsNone(project.pk)
        self.assertIsNone(dataset.pk)
        self.assertIsNone(sample.pk)
        self.assertIsNone(measurement.pk)

        # But should have required fields
        self.assertIsNotNone(project.name)
        self.assertIsNotNone(dataset.name)
        self.assertIsNotNone(sample.name)
        self.assertIsNotNone(measurement.name)

    def test_factories_support_custom_parameters(self):
        """Test that factories accept custom parameters."""
        custom_project_name = "Custom Project"
        custom_dataset_name = "Custom Dataset"

        project = ProjectFactory(name=custom_project_name)
        dataset = DatasetFactory(name=custom_dataset_name, project=project)

        self.assertEqual(project.name, custom_project_name)
        self.assertEqual(dataset.name, custom_dataset_name)
        self.assertEqual(dataset.project, project)

    def test_factory_relationships_hierarchy(self):
        """Test that factories create proper relationships in hierarchy."""
        # Create a complete hierarchy
        project = ProjectFactory()
        dataset = DatasetFactory(project=project)
        sample = RockSampleFactory(dataset=dataset)
        measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)

        # Verify relationships
        self.assertEqual(dataset.project, project)
        self.assertEqual(sample.dataset, dataset)
        self.assertEqual(measurement.dataset, dataset)
        self.assertEqual(measurement.sample, sample)

    def test_batch_creation_works(self):
        """Test that factories support batch creation."""
        projects = ProjectFactory.create_batch(3, descriptions=2, dates=1)
        datasets = DatasetFactory.create_batch(3, descriptions=2, dates=1)

        self.assertEqual(len(projects), 3)
        self.assertEqual(len(datasets), 3)

        # Check each has the expected descriptions and dates
        for project in projects:
            self.assertEqual(
                ProjectDescription.objects.filter(related=project).count(), 2
            )
            self.assertEqual(ProjectDate.objects.filter(related=project).count(), 1)

        for dataset in datasets:
            self.assertEqual(
                DatasetDescription.objects.filter(related=dataset).count(), 2
            )
            self.assertEqual(DatasetDate.objects.filter(related=dataset).count(), 1)

    def test_sample_factory_specific_features(self):
        """Test Sample-specific factory features."""
        sample = RockSampleFactory()

        self.assertIsNotNone(sample.local_id)
        self.assertTrue(sample.local_id.startswith("SAMPLE-"))
        self.assertEqual(sample.status, "unknown")
        self.assertIsNone(sample.location)  # Optional field

    def test_dataset_factory_license_handling(self):
        """Test Dataset factory license creation."""
        dataset = DatasetFactory()

        self.assertIsNotNone(dataset.license)
        self.assertEqual(dataset.license.name, "CC BY 4.0")

    def test_project_factory_funding_structure(self):
        """Test Project factory funding JSON field.

        Requirement: FR-015 - funding is stored as a list of DataCite
        funding references.
        """
        project = ProjectFactory()

        self.assertIsNotNone(project.funding)
        self.assertIsInstance(project.funding, list)
        self.assertEqual(len(project.funding), 1)
        reference = project.funding[0]
        self.assertIn("funderName", reference)
        self.assertIn("awardNumber", reference)

    @pytest.mark.django_db
    def test_factories_respect_database_constraints(self):
        """Test that factories respect database constraints."""
        # Create multiple objects to test uniqueness constraints
        projects = ProjectFactory.create_batch(3)
        datasets = DatasetFactory.create_batch(3)
        samples = RockSampleFactory.create_batch(3)
        measurements = ExampleMeasurementFactory.create_batch(
            3, sample=RockSampleFactory()
        )

        # Verify all have unique PKs
        project_pks = [p.pk for p in projects]
        dataset_pks = [d.pk for d in datasets]
        sample_pks = [s.pk for s in samples]
        measurement_pks = [m.pk for m in measurements]

        self.assertEqual(len(set(project_pks)), 3)
        self.assertEqual(len(set(dataset_pks)), 3)
        self.assertEqual(len(set(sample_pks)), 3)
        self.assertEqual(len(set(measurement_pks)), 3)


class TestFactoryVocabularyValidation(TestCase):
    """Test that factories validate types against model VOCABULARY."""

    def test_project_factory_rejects_invalid_description_types(self):
        """Test ProjectFactory raises error for invalid description types."""
        with self.assertRaises(ValueError) as cm:
            ProjectFactory(descriptions=1, descriptions__types=["InvalidType"])

        self.assertIn("Invalid description types", str(cm.exception))
        self.assertIn("InvalidType", str(cm.exception))

    def test_project_factory_rejects_invalid_date_types(self):
        """Test ProjectFactory raises error for invalid date types."""
        with self.assertRaises(ValueError) as cm:
            ProjectFactory(dates=1, dates__types=["InvalidType"])

        self.assertIn("Invalid date types", str(cm.exception))
        self.assertIn("InvalidType", str(cm.exception))

    def test_dataset_factory_rejects_invalid_description_types(self):
        """Test DatasetFactory raises error for invalid description types."""
        with self.assertRaises(ValueError) as cm:
            DatasetFactory(descriptions=1, descriptions__types=["InvalidType"])

        self.assertIn("Invalid description types", str(cm.exception))

    def test_sample_factory_rejects_invalid_description_types(self):
        """Test SampleFactory raises error for invalid description types."""
        with self.assertRaises(ValueError) as cm:
            RockSampleFactory(descriptions=1, descriptions__types=["InvalidType"])

        self.assertIn("Invalid description types", str(cm.exception))

    def test_measurement_factory_rejects_invalid_description_types(self):
        """Test a concrete measurement factory raises error for invalid description types."""
        with self.assertRaises(ValueError) as cm:
            ExampleMeasurementFactory(
                sample=RockSampleFactory(),
                descriptions=1,
                descriptions__types=["InvalidType"],
            )

        self.assertIn("Invalid description types", str(cm.exception))

    def test_factories_accept_valid_vocabulary_types(self):
        """Test factories accept all valid types from VOCABULARY."""
        # Test with valid types from vocabularies
        project = ProjectFactory(
            descriptions=2, descriptions__types=["Abstract", "Introduction"]
        )
        dataset = DatasetFactory(
            descriptions=2, descriptions__types=["Abstract", "Methods"]
        )

        self.assertEqual(ProjectDescription.objects.filter(related=project).count(), 2)
        self.assertEqual(DatasetDescription.objects.filter(related=dataset).count(), 2)

        # Verify the types were used
        desc_types = list(
            ProjectDescription.objects.filter(related=project).values_list(
                "type", flat=True
            )
        )
        self.assertIn("Abstract", desc_types)
        self.assertIn("Introduction", desc_types)

    def test_factories_use_vocabulary_defaults(self):
        """Test factories use defaults from model VOCABULARY when no types specified."""
        project = ProjectFactory(descriptions=2)

        # Should create 2 descriptions with first 2 types from VOCABULARY
        descriptions = ProjectDescription.objects.filter(related=project)
        self.assertEqual(descriptions.count(), 2)

        # Types should be from the model's VOCABULARY
        desc_types = list(descriptions.values_list("type", flat=True))
        vocab_values = ProjectDescription.VOCABULARY.values

        # The created types should be in the vocabulary
        for dtype in desc_types:
            self.assertIn(dtype, vocab_values)


@pytest.mark.django_db
class TestProjectFactories:
    """Test project-related factories."""

    def test_project_factory_creates_project(self):
        """Test ProjectFactory creates a valid Project instance."""
        project = ProjectFactory()

        assert isinstance(project, Project)
        assert project.pk is not None
        assert project.name
        assert project.visibility is not None
        assert project.status is not None
        assert project.funding
        assert project.funding[0]["funderName"]

    def test_project_factory_no_auto_descriptions(self):
        """Test ProjectFactory doesn't auto-create descriptions."""
        project = ProjectFactory()

        assert project.descriptions.count() == 0

    def test_project_factory_no_auto_dates(self):
        """Test ProjectFactory doesn't auto-create dates."""
        project = ProjectFactory()

        assert project.dates.count() == 0

    def test_project_factory_no_auto_contributors(self):
        """Test ProjectFactory doesn't auto-create contributors."""
        project = ProjectFactory()

        assert project.contributors.count() == 0

    def test_project_factory_with_owner(self):
        """Test ProjectFactory can set an owner (must be Organization)."""
        org = OrganizationFactory()
        project = ProjectFactory(owner=org)

        assert project.owner == org

    def test_project_description_factory(self):
        """Test ProjectDescriptionFactory creates valid descriptions."""
        project = ProjectFactory()
        description = ProjectDescriptionFactory(related=project, type="Abstract")

        assert isinstance(description, ProjectDescription)
        assert description.pk is not None
        assert description.related == project
        assert description.type == "Abstract"
        assert description.value

    def test_project_date_factory(self):
        """Test ProjectDateFactory creates valid dates."""
        project = ProjectFactory()
        date = ProjectDateFactory(related=project, type="Created")

        assert isinstance(date, ProjectDate)
        assert date.pk is not None
        assert date.related == project
        assert date.type == "Created"
        assert date.value


@pytest.mark.django_db
class TestDatasetFactories:
    """Test dataset-related factories."""

    def test_dataset_factory_creates_dataset(self):
        """Test DatasetFactory creates a valid Dataset instance."""
        dataset = DatasetFactory()

        assert isinstance(dataset, Dataset)
        assert dataset.pk is not None
        assert dataset.name
        assert dataset.visibility is not None
        assert dataset.project is not None
        assert dataset.license is not None

    def test_dataset_factory_with_existing_project(self):
        """Test DatasetFactory can use an existing project."""
        project = ProjectFactory()
        dataset = DatasetFactory(project=project)

        assert dataset.project == project

    def test_dataset_factory_no_auto_descriptions(self):
        """Test DatasetFactory doesn't auto-create descriptions."""
        dataset = DatasetFactory()

        assert dataset.descriptions.count() == 0

    def test_dataset_factory_no_auto_dates(self):
        """Test DatasetFactory doesn't auto-create dates."""
        dataset = DatasetFactory()

        assert dataset.dates.count() == 0

    def test_dataset_factory_no_auto_contributors(self):
        """Test DatasetFactory doesn't auto-create contributors."""
        dataset = DatasetFactory()

        assert dataset.contributors.count() == 0

    def test_dataset_description_factory(self):
        """Test DatasetDescriptionFactory creates valid descriptions."""
        dataset = DatasetFactory()
        description = DatasetDescriptionFactory(related=dataset, type="Methods")

        assert isinstance(description, DatasetDescription)
        assert description.pk is not None
        assert description.related == dataset
        assert description.type == "Methods"
        assert description.value

    def test_dataset_date_factory(self):
        """Test DatasetDateFactory creates valid dates."""
        dataset = DatasetFactory()
        date = DatasetDateFactory(related=dataset, type="Available")

        assert isinstance(date, DatasetDate)
        assert date.pk is not None
        assert date.related == dataset
        assert date.type == "Available"
        assert date.value


@pytest.mark.django_db
class TestSampleFactories:
    """Test sample-related factories."""

    def test_sample_factory_creates_sample(self):
        """Test SampleFactory creates a valid Sample instance."""
        sample = RockSampleFactory()

        assert isinstance(sample, Sample)
        assert sample.pk is not None
        assert sample.name
        assert sample.local_id
        assert sample.status
        assert sample.dataset is not None

    def test_sample_factory_with_existing_dataset(self):
        """Test SampleFactory can use an existing dataset."""
        dataset = DatasetFactory()
        sample = RockSampleFactory(dataset=dataset)

        assert sample.dataset == dataset

    def test_sample_factory_no_auto_descriptions(self):
        """Test SampleFactory doesn't auto-create descriptions."""
        sample = RockSampleFactory()

        assert sample.descriptions.count() == 0

    def test_sample_factory_no_auto_dates(self):
        """Test SampleFactory doesn't auto-create dates."""
        sample = RockSampleFactory()

        assert sample.dates.count() == 0

    def test_sample_description_factory(self):
        """Test SampleDescriptionFactory creates valid descriptions."""
        sample = RockSampleFactory()
        description = SampleDescriptionFactory(related=sample, type="Technical Info")

        assert isinstance(description, SampleDescription)
        assert description.pk is not None
        assert description.related == sample
        assert description.type == "Technical Info"
        assert description.value

    def test_sample_date_factory(self):
        """Test SampleDateFactory creates valid dates."""
        sample = RockSampleFactory()
        date = SampleDateFactory(related=sample, type="Collected")

        assert isinstance(date, SampleDate)
        assert date.pk is not None
        assert date.related == sample
        assert date.type == "Collected"
        assert date.value


@pytest.mark.django_db
class TestMeasurementFactories:
    """Test measurement-related factories."""

    def test_measurement_factory_is_abstract_and_its_concrete_subclass_creates_measurement(
        self,
    ):
        """Test MeasurementFactory itself is abstract and refuses (FR-011 forbids the
        bare Measurement record), and that its concrete demo subclass creates a valid
        instance.

        Rewritten from an earlier version of this test that asserted "MeasurementFactory
        creates a valid Measurement instance" - that claim is exactly what FR-011 now
        forbids (006-core-measurements T002), so the test's meaning changed along with
        the call site rather than just the call site.
        """
        dataset = DatasetFactory()
        sample = RockSampleFactory(dataset=dataset)

        with pytest.raises(factory.errors.FactoryError):
            MeasurementFactory(dataset=dataset, sample=sample)

        measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)

        assert isinstance(measurement, Measurement)
        assert measurement.pk is not None
        assert measurement.name
        assert measurement.dataset is not None
        assert measurement.sample is not None
        assert measurement.sample.dataset == measurement.dataset

    def test_measurement_factory_with_existing_dataset(self):
        """Test a concrete measurement factory can use an existing dataset."""
        dataset = DatasetFactory()
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(dataset=dataset), dataset=dataset
        )

        assert measurement.dataset == dataset
        assert measurement.sample.dataset == dataset

    def test_measurement_factory_with_sample(self):
        """Test a concrete measurement factory can link to a specific sample."""
        dataset = DatasetFactory()
        sample = RockSampleFactory(dataset=dataset)
        measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)

        assert measurement.sample == sample
        assert measurement.dataset == dataset

    def test_measurement_factory_no_auto_descriptions(self):
        """Test a concrete measurement factory doesn't auto-create descriptions."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        assert measurement.descriptions.count() == 0

    def test_measurement_factory_no_auto_dates(self):
        """Test a concrete measurement factory doesn't auto-create dates."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        assert measurement.dates.count() == 0

    def test_measurement_description_factory(self):
        """Test MeasurementDescriptionFactory creates valid descriptions."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        description = MeasurementDescriptionFactory(
            related=measurement, type="MeasurementConditions"
        )

        assert isinstance(description, MeasurementDescription)
        assert description.pk is not None
        assert description.related == measurement
        assert description.type == "MeasurementConditions"
        assert description.value

    def test_measurement_date_factory(self):
        """Test MeasurementDateFactory creates valid dates."""
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        date = MeasurementDateFactory(related=measurement, type="Setup")

        assert isinstance(date, MeasurementDate)
        assert date.pk is not None
        assert date.related == measurement
        assert date.type == "Setup"
        assert date.value


@pytest.mark.django_db
class TestFactoryIntegration:
    """Test factories work together in realistic scenarios."""

    def test_create_full_project_hierarchy(self):
        """Test creating a complete project with datasets, samples, and measurements."""
        # Create contributors
        person = PersonFactory()
        org = OrganizationFactory()

        # Create project (owner must be organization)
        project = ProjectFactory(owner=org)
        ProjectDescriptionFactory(related=project, type="Abstract")
        ProjectDateFactory(related=project, type="Created")
        ContributionFactory(content_object=project, contributor=person)
        ContributionFactory(content_object=project, contributor=org)

        # Create dataset. Public: the subject here is factory wiring — that a
        # project's reverse `datasets` relation is populated — not visibility.
        # `project.datasets` is a reverse FK manager built from `Dataset`'s
        # default manager, privacy-first since 004-core-datasets FR-019, so a
        # private dataset would not appear in `project.datasets.count()` even
        # though the relation is wired correctly.
        dataset = DatasetFactory(
            project=project, visibility=Dataset.VISIBILITY_CHOICES.PUBLIC
        )
        DatasetDescriptionFactory(related=dataset, type="Methods")
        DatasetDateFactory(related=dataset, type="Available")
        ContributionFactory(content_object=dataset, contributor=person)

        # Create samples
        sample1 = RockSampleFactory(dataset=dataset)
        sample2 = RockSampleFactory(dataset=dataset)
        SampleDescriptionFactory(related=sample1)
        SampleDateFactory(related=sample1)

        # Create measurements
        measurement1 = ExampleMeasurementFactory(dataset=dataset, sample=sample1)
        ExampleMeasurementFactory(dataset=dataset, sample=sample2)
        MeasurementDescriptionFactory(related=measurement1)
        MeasurementDateFactory(related=measurement1)

        # Verify the hierarchy
        assert project.datasets.count() == 1
        assert dataset.samples.count() == 2
        assert dataset.measurements.count() == 2
        assert project.contributors.count() == 2
        assert dataset.contributors.count() == 1
        assert sample1.descriptions.count() == 1
        assert measurement1.descriptions.count() == 1

    def test_multiple_datasets_share_project(self):
        """Test multiple datasets can share the same project."""
        # Public: subject is factory wiring, not visibility (see above).
        project = ProjectFactory()
        dataset1 = DatasetFactory(
            project=project, visibility=Dataset.VISIBILITY_CHOICES.PUBLIC
        )
        dataset2 = DatasetFactory(
            project=project, visibility=Dataset.VISIBILITY_CHOICES.PUBLIC
        )

        assert dataset1.project == dataset2.project
        assert project.datasets.count() == 2

    def test_batch_creation(self):
        """Test creating multiple instances efficiently."""
        # Create multiple people
        people = PersonFactory.create_batch(5)
        assert len(people) == 5
        assert all(isinstance(p, Person) for p in people)

        # Create multiple projects
        projects = ProjectFactory.create_batch(3)
        assert len(projects) == 3
        assert all(isinstance(p, Project) for p in projects)


class TestBasicFactoryFunctionality(TestCase):
    """Test basic functionality of all factories."""

    def test_all_factories_can_create_instances(self):
        """Test that all usable factories can create basic instances without errors,
        and that the abstract MeasurementFactory base refuses to.

        MeasurementFactory itself is abstract (FR-011, 006-core-measurements T002) -
        SampleFactory is treated the same way here (RockSampleFactory, not the abstract
        SampleFactory), so the same substitution now applies to measurement.
        """
        with self.assertRaises(factory.errors.FactoryError):
            MeasurementFactory(sample=RockSampleFactory())

        # Test core factories
        project = ProjectFactory()
        dataset = DatasetFactory()
        sample = RockSampleFactory()
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

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
        """Test that all usable factories can build instances without saving, and
        that the abstract MeasurementFactory base refuses to."""
        with self.assertRaises(factory.errors.FactoryError):
            MeasurementFactory.build()

        # Test core factories
        project = ProjectFactory.build()
        dataset = DatasetFactory.build()
        sample = RockSampleFactory.build()
        measurement = ExampleMeasurementFactory.build()

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
        sample = RockSampleFactory(dataset=dataset)
        measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)

        # Verify relationships
        self.assertEqual(dataset.project, project)
        self.assertEqual(sample.dataset, dataset)
        self.assertEqual(measurement.dataset, dataset)
        self.assertEqual(measurement.sample, sample)
