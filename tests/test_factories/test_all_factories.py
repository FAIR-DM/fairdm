"""Tests for factory_boy factories.

This module tests all factories to ensure they can create valid model instances
without errors and that relationships work as expected.
"""

import pytest

from fairdm.contrib.contributors.models import Contribution, Organization, Person
from fairdm.core.dataset.models import DatasetDate, DatasetDescription
from fairdm.core.measurement.models import MeasurementDate, MeasurementDescription
from fairdm.core.models import Dataset, Measurement, Project, Sample
from fairdm.core.project.models import ProjectDate, ProjectDescription
from fairdm.core.sample.models import SampleDate, SampleDescription
from fairdm.factories import (
    DatasetFactory,
    MeasurementFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
    SampleFactory,
)
from fairdm.factories.contributors import ContributionFactory
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


@pytest.mark.django_db
class TestContributorFactories:
    """Test contributor-related factories."""

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
        date = DatasetDateFactory(related=dataset, type="Issued")

        assert isinstance(date, DatasetDate)
        assert date.pk is not None
        assert date.related == dataset
        assert date.type == "Issued"
        assert date.value


@pytest.mark.django_db
class TestSampleFactories:
    """Test sample-related factories."""

    def test_sample_factory_creates_sample(self):
        """Test SampleFactory creates a valid Sample instance."""
        sample = SampleFactory()

        assert isinstance(sample, Sample)
        assert sample.pk is not None
        assert sample.name
        assert sample.local_id
        assert sample.status
        assert sample.dataset is not None

    def test_sample_factory_with_existing_dataset(self):
        """Test SampleFactory can use an existing dataset."""
        dataset = DatasetFactory()
        sample = SampleFactory(dataset=dataset)

        assert sample.dataset == dataset

    def test_sample_factory_no_auto_descriptions(self):
        """Test SampleFactory doesn't auto-create descriptions."""
        sample = SampleFactory()

        assert sample.descriptions.count() == 0

    def test_sample_factory_no_auto_dates(self):
        """Test SampleFactory doesn't auto-create dates."""
        sample = SampleFactory()

        assert sample.dates.count() == 0

    def test_sample_description_factory(self):
        """Test SampleDescriptionFactory creates valid descriptions."""
        sample = SampleFactory()
        description = SampleDescriptionFactory(related=sample, type="Technical Info")

        assert isinstance(description, SampleDescription)
        assert description.pk is not None
        assert description.related == sample
        assert description.type == "Technical Info"
        assert description.value

    def test_sample_date_factory(self):
        """Test SampleDateFactory creates valid dates."""
        sample = SampleFactory()
        date = SampleDateFactory(related=sample, type="Collected")

        assert isinstance(date, SampleDate)
        assert date.pk is not None
        assert date.related == sample
        assert date.type == "Collected"
        assert date.value


@pytest.mark.django_db
class TestMeasurementFactories:
    """Test measurement-related factories."""

    def test_measurement_factory_creates_measurement(self):
        """Test MeasurementFactory creates a valid Measurement instance."""
        measurement = MeasurementFactory()

        assert isinstance(measurement, Measurement)
        assert measurement.pk is not None
        assert measurement.name
        assert measurement.dataset is not None
        assert measurement.sample is not None
        assert measurement.sample.dataset == measurement.dataset

    def test_measurement_factory_with_existing_dataset(self):
        """Test MeasurementFactory can use an existing dataset."""
        dataset = DatasetFactory()
        measurement = MeasurementFactory(dataset=dataset)

        assert measurement.dataset == dataset
        assert measurement.sample.dataset == dataset

    def test_measurement_factory_with_sample(self):
        """Test MeasurementFactory can link to a specific sample."""
        dataset = DatasetFactory()
        sample = SampleFactory(dataset=dataset)
        measurement = MeasurementFactory(dataset=dataset, sample=sample)

        assert measurement.sample == sample
        assert measurement.dataset == dataset

    def test_measurement_factory_no_auto_descriptions(self):
        """Test MeasurementFactory doesn't auto-create descriptions."""
        measurement = MeasurementFactory()

        assert measurement.descriptions.count() == 0

    def test_measurement_factory_no_auto_dates(self):
        """Test MeasurementFactory doesn't auto-create dates."""
        measurement = MeasurementFactory()

        assert measurement.dates.count() == 0

    def test_measurement_description_factory(self):
        """Test MeasurementDescriptionFactory creates valid descriptions."""
        measurement = MeasurementFactory()
        description = MeasurementDescriptionFactory(related=measurement, type="Abstract")

        assert isinstance(description, MeasurementDescription)
        assert description.pk is not None
        assert description.related == measurement
        assert description.type == "Abstract"
        assert description.value

    def test_measurement_date_factory(self):
        """Test MeasurementDateFactory creates valid dates."""
        measurement = MeasurementFactory()
        date = MeasurementDateFactory(related=measurement, type="Created")

        assert isinstance(date, MeasurementDate)
        assert date.pk is not None
        assert date.related == measurement
        assert date.type == "Created"
        assert date.value


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

        # Create dataset
        dataset = DatasetFactory(project=project)
        DatasetDescriptionFactory(related=dataset, type="Methods")
        DatasetDateFactory(related=dataset, type="Issued")
        ContributionFactory(content_object=dataset, contributor=person)

        # Create samples
        sample1 = SampleFactory(dataset=dataset)
        sample2 = SampleFactory(dataset=dataset)
        SampleDescriptionFactory(related=sample1)
        SampleDateFactory(related=sample1)

        # Create measurements
        measurement1 = MeasurementFactory(dataset=dataset, sample=sample1)
        MeasurementFactory(dataset=dataset, sample=sample2)
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
        project = ProjectFactory()
        dataset1 = DatasetFactory(project=project)
        dataset2 = DatasetFactory(project=project)

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
