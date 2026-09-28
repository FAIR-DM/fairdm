"""Tests for the core FairDM factories (Project, Dataset, Sample, Measurement)."""

import factory
import pytest

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
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


@pytest.mark.django_db
class TestCoreFactoriesBasic:
    def test_project_factory_creates_instance(self):
        project = ProjectFactory(descriptions=2, dates=1)

        assert isinstance(project, Project)
        assert project.pk is not None
        assert project.name is not None

        descriptions = ProjectDescription.objects.filter(related=project)
        dates = ProjectDate.objects.filter(related=project)
        assert descriptions.count() == 2
        assert dates.count() == 1

    def test_dataset_factory_creates_instance(self):
        dataset = DatasetFactory(descriptions=2, dates=1)

        assert isinstance(dataset, Dataset)
        assert dataset.pk is not None
        assert dataset.name is not None
        assert dataset.project is not None

        descriptions = DatasetDescription.objects.filter(related=dataset)
        dates = DatasetDate.objects.filter(related=dataset)
        assert descriptions.count() == 2
        assert dates.count() == 1

    def test_sample_factory_creates_instance(self):
        sample = RockSampleFactory(descriptions=2, dates=1)

        assert isinstance(sample, Sample)
        assert sample.pk is not None
        assert sample.name is not None
        assert sample.dataset is not None

        descriptions = SampleDescription.objects.filter(related=sample)
        dates = SampleDate.objects.filter(related=sample)
        assert descriptions.count() == 2
        assert dates.count() == 1

    def test_measurement_factory_creates_instance(self):
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(), descriptions=2, dates=1
        )

        assert isinstance(measurement, Measurement)
        assert measurement.pk is not None
        assert measurement.name is not None
        assert measurement.dataset is not None
        assert measurement.sample is not None

        descriptions = MeasurementDescription.objects.filter(related=measurement)
        dates = MeasurementDate.objects.filter(related=measurement)
        assert descriptions.count() == 2
        assert dates.count() == 1

    def test_description_factories_with_related_objects(self):
        project = ProjectFactory()
        dataset = DatasetFactory()
        sample = RockSampleFactory()
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        project_desc = ProjectDescriptionFactory(related=project)
        dataset_desc = DatasetDescriptionFactory(related=dataset)
        sample_desc = SampleDescriptionFactory(related=sample)
        measurement_desc = MeasurementDescriptionFactory(related=measurement)

        assert project_desc.related == project
        assert dataset_desc.related == dataset
        assert sample_desc.related == sample
        assert measurement_desc.related == measurement

        assert project_desc.type == "Abstract"
        assert dataset_desc.type == "Abstract"
        # "Abstract" is not a member of the sample description vocabulary, so the factory default is
        # "SampleCollection", a real member.
        assert sample_desc.type == "SampleCollection"
        # "Abstract" is not a member of the measurement description vocabulary, so the factory default
        # is "MeasurementConditions", a real member.
        assert measurement_desc.type == "MeasurementConditions"

    def test_date_factories_with_related_objects(self):
        project = ProjectFactory()
        dataset = DatasetFactory()
        sample = RockSampleFactory()
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        project_date = ProjectDateFactory(related=project)
        dataset_date = DatasetDateFactory(related=dataset)
        sample_date = SampleDateFactory(related=sample)
        measurement_date = MeasurementDateFactory(related=measurement)

        assert project_date.related == project
        assert dataset_date.related == dataset
        assert sample_date.related == sample
        assert measurement_date.related == measurement

        assert project_date.type == "Start"
        # "Created" is not a member of the dataset date vocabulary, so the factory default is
        # "Available", a real member.
        assert dataset_date.type == "Available"
        assert sample_date.type == "Created"
        # "Created" is not a member of the measurement date vocabulary, so the factory default is
        # "Setup", a real member.
        assert measurement_date.type == "Setup"

    def test_factories_support_build_mode(self):
        project = ProjectFactory.build()
        dataset = DatasetFactory.build()
        sample = RockSampleFactory.build()
        measurement = ExampleMeasurementFactory.build()

        assert project.pk is None
        assert dataset.pk is None
        assert sample.pk is None
        assert measurement.pk is None

        assert project.name is not None
        assert dataset.name is not None
        assert sample.name is not None
        assert measurement.name is not None

    def test_factories_support_custom_parameters(self):
        custom_project_name = "Custom Project"
        custom_dataset_name = "Custom Dataset"

        project = ProjectFactory(name=custom_project_name)
        dataset = DatasetFactory(name=custom_dataset_name, project=project)

        assert project.name == custom_project_name
        assert dataset.name == custom_dataset_name
        assert dataset.project == project

    def test_factory_relationships_hierarchy(self):
        project = ProjectFactory()
        dataset = DatasetFactory(project=project)
        sample = RockSampleFactory(dataset=dataset)
        measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)

        assert dataset.project == project
        assert sample.dataset == dataset
        assert measurement.dataset == dataset
        assert measurement.sample == sample

    def test_batch_creation_works(self):
        projects = ProjectFactory.create_batch(3, descriptions=2, dates=1)
        datasets = DatasetFactory.create_batch(3, descriptions=2, dates=1)

        assert len(projects) == 3
        assert len(datasets) == 3

        for project in projects:
            assert ProjectDescription.objects.filter(related=project).count() == 2
            assert ProjectDate.objects.filter(related=project).count() == 1

        for dataset in datasets:
            assert DatasetDescription.objects.filter(related=dataset).count() == 2
            assert DatasetDate.objects.filter(related=dataset).count() == 1

    def test_sample_factory_specific_features(self):
        sample = RockSampleFactory()

        assert sample.local_id is not None
        assert sample.local_id.startswith("SAMPLE-")
        assert sample.status == "unknown"
        assert sample.location is None

    def test_dataset_factory_license_handling(self):
        dataset = DatasetFactory()

        assert dataset.license is not None
        assert dataset.license.name == "CC BY 4.0"

    def test_project_factory_funding_structure(self):
        project = ProjectFactory()

        assert project.funding is not None
        assert isinstance(project.funding, list)
        assert len(project.funding) == 1
        reference = project.funding[0]
        assert "funderName" in reference
        assert "awardNumber" in reference

    def test_factories_respect_database_constraints(self):
        projects = ProjectFactory.create_batch(3)
        datasets = DatasetFactory.create_batch(3)
        samples = RockSampleFactory.create_batch(3)
        measurements = ExampleMeasurementFactory.create_batch(
            3, sample=RockSampleFactory()
        )

        project_pks = [p.pk for p in projects]
        dataset_pks = [d.pk for d in datasets]
        sample_pks = [s.pk for s in samples]
        measurement_pks = [m.pk for m in measurements]

        assert len(set(project_pks)) == 3
        assert len(set(dataset_pks)) == 3
        assert len(set(sample_pks)) == 3
        assert len(set(measurement_pks)) == 3


@pytest.mark.django_db
class TestFactoryVocabularyValidation:
    def test_project_factory_rejects_invalid_description_types(self):
        with pytest.raises(ValueError) as cm:
            ProjectFactory(descriptions=1, descriptions__types=["InvalidType"])

        assert "InvalidType" in str(cm.value)

    def test_project_factory_rejects_invalid_date_types(self):
        with pytest.raises(ValueError) as cm:
            ProjectFactory(dates=1, dates__types=["InvalidType"])

        assert "InvalidType" in str(cm.value)

    def test_dataset_factory_rejects_invalid_description_types(self):
        with pytest.raises(ValueError) as cm:
            DatasetFactory(descriptions=1, descriptions__types=["InvalidType"])

    def test_sample_factory_rejects_invalid_description_types(self):
        with pytest.raises(ValueError) as cm:
            RockSampleFactory(descriptions=1, descriptions__types=["InvalidType"])

    def test_measurement_factory_rejects_invalid_description_types(self):
        with pytest.raises(ValueError) as cm:
            ExampleMeasurementFactory(
                sample=RockSampleFactory(),
                descriptions=1,
                descriptions__types=["InvalidType"],
            )

    def test_factories_accept_valid_vocabulary_types(self):
        project = ProjectFactory(
            descriptions=2, descriptions__types=["Abstract", "Introduction"]
        )
        dataset = DatasetFactory(
            descriptions=2, descriptions__types=["Abstract", "Methods"]
        )

        assert ProjectDescription.objects.filter(related=project).count() == 2
        assert DatasetDescription.objects.filter(related=dataset).count() == 2

        desc_types = list(
            ProjectDescription.objects.filter(related=project).values_list(
                "type", flat=True
            )
        )
        assert "Abstract" in desc_types
        assert "Introduction" in desc_types

    def test_factories_use_vocabulary_defaults(self):
        project = ProjectFactory(descriptions=2)

        descriptions = ProjectDescription.objects.filter(related=project)
        assert descriptions.count() == 2

        desc_types = list(descriptions.values_list("type", flat=True))
        vocab_values = ProjectDescription.VOCABULARY.values

        for dtype in desc_types:
            assert dtype in vocab_values


@pytest.mark.django_db
class TestProjectFactories:
    def test_project_factory_creates_project(self):
        project = ProjectFactory()

        assert isinstance(project, Project)
        assert project.pk is not None
        assert project.name
        assert project.visibility is not None
        assert project.status is not None
        assert project.funding
        assert project.funding[0]["funderName"]

    def test_project_factory_no_auto_descriptions(self):
        project = ProjectFactory()

        assert project.descriptions.count() == 0

    def test_project_factory_no_auto_dates(self):
        project = ProjectFactory()

        assert project.dates.count() == 0

    def test_project_factory_no_auto_contributors(self):
        project = ProjectFactory()

        assert project.contributors.count() == 0

    def test_project_factory_no_auto_image(self):
        # A default factory sets no image. Generating one on every call left files under MEDIA_ROOT (#323).
        project = ProjectFactory()

        assert not project.image

    def test_project_factory_with_owner(self):
        org = OrganizationFactory()
        project = ProjectFactory(owner=org)

        assert project.owner == org

    def test_project_description_factory(self):
        project = ProjectFactory()
        description = ProjectDescriptionFactory(related=project, type="Abstract")

        assert isinstance(description, ProjectDescription)
        assert description.pk is not None
        assert description.related == project
        assert description.type == "Abstract"
        assert description.value

    def test_project_date_factory(self):
        project = ProjectFactory()
        date = ProjectDateFactory(related=project, type="Created")

        assert isinstance(date, ProjectDate)
        assert date.pk is not None
        assert date.related == project
        assert date.type == "Created"
        assert date.value

    def test_project_factory_image_stays_under_media_root(self, tmp_path):
        # MEDIA_ROOT was once a fixed path shared by every run, and nothing removed what landed there (#323).
        from pathlib import Path

        from django.conf import settings

        project = ProjectFactory(with_image=True)

        assert Path(settings.MEDIA_ROOT) == tmp_path / "media"
        assert tmp_path in Path(project.image.path).parents


@pytest.mark.django_db
class TestDatasetFactories:
    def test_dataset_factory_creates_dataset(self):
        dataset = DatasetFactory()

        assert isinstance(dataset, Dataset)
        assert dataset.pk is not None
        assert dataset.name
        assert dataset.visibility is not None
        assert dataset.project is not None
        assert dataset.license is not None

    def test_dataset_factory_with_existing_project(self):
        project = ProjectFactory()
        dataset = DatasetFactory(project=project)

        assert dataset.project == project

    def test_dataset_factory_no_auto_descriptions(self):
        dataset = DatasetFactory()

        assert dataset.descriptions.count() == 0

    def test_dataset_factory_no_auto_dates(self):
        dataset = DatasetFactory()

        assert dataset.dates.count() == 0

    def test_dataset_factory_no_auto_contributors(self):
        dataset = DatasetFactory()

        assert dataset.contributors.count() == 0

    def test_dataset_factory_no_auto_image(self):
        dataset = DatasetFactory()

        assert not dataset.image

    def test_dataset_factory_with_image_generates_one(self):
        dataset = DatasetFactory(with_image=True)

        assert dataset.image

    def test_dataset_description_factory(self):
        dataset = DatasetFactory()
        description = DatasetDescriptionFactory(related=dataset, type="Methods")

        assert isinstance(description, DatasetDescription)
        assert description.pk is not None
        assert description.related == dataset
        assert description.type == "Methods"
        assert description.value

    def test_dataset_date_factory(self):
        dataset = DatasetFactory()
        date = DatasetDateFactory(related=dataset, type="Available")

        assert isinstance(date, DatasetDate)
        assert date.pk is not None
        assert date.related == dataset
        assert date.type == "Available"
        assert date.value


@pytest.mark.django_db
class TestSampleFactories:
    def test_sample_factory_creates_sample(self):
        sample = RockSampleFactory()

        assert isinstance(sample, Sample)
        assert sample.pk is not None
        assert sample.name
        assert sample.local_id
        assert sample.status
        assert sample.dataset is not None

    def test_sample_factory_with_existing_dataset(self):
        dataset = DatasetFactory()
        sample = RockSampleFactory(dataset=dataset)

        assert sample.dataset == dataset

    def test_sample_factory_no_auto_descriptions(self):
        sample = RockSampleFactory()

        assert sample.descriptions.count() == 0

    def test_sample_factory_no_auto_dates(self):
        sample = RockSampleFactory()

        assert sample.dates.count() == 0

    def test_sample_description_factory(self):
        sample = RockSampleFactory()
        description = SampleDescriptionFactory(related=sample, type="Technical Info")

        assert isinstance(description, SampleDescription)
        assert description.pk is not None
        assert description.related == sample
        assert description.type == "Technical Info"
        assert description.value

    def test_sample_date_factory(self):
        sample = RockSampleFactory()
        date = SampleDateFactory(related=sample, type="Collected")

        assert isinstance(date, SampleDate)
        assert date.pk is not None
        assert date.related == sample
        assert date.type == "Collected"
        assert date.value


@pytest.mark.django_db
class TestMeasurementFactories:
    def test_measurement_factory_is_abstract_and_its_concrete_subclass_creates_measurement(
        self,
    ):
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
        dataset = DatasetFactory()
        measurement = ExampleMeasurementFactory(
            sample=RockSampleFactory(dataset=dataset), dataset=dataset
        )

        assert measurement.dataset == dataset
        assert measurement.sample.dataset == dataset

    def test_measurement_factory_with_sample(self):
        dataset = DatasetFactory()
        sample = RockSampleFactory(dataset=dataset)
        measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)

        assert measurement.sample == sample
        assert measurement.dataset == dataset

    def test_measurement_factory_no_auto_descriptions(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        assert measurement.descriptions.count() == 0

    def test_measurement_factory_no_auto_dates(self):
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        assert measurement.dates.count() == 0

    def test_measurement_description_factory(self):
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
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())
        date = MeasurementDateFactory(related=measurement, type="Setup")

        assert isinstance(date, MeasurementDate)
        assert date.pk is not None
        assert date.related == measurement
        assert date.type == "Setup"
        assert date.value


@pytest.mark.django_db
class TestFactoryIntegration:
    def test_create_full_project_hierarchy(self):
        person = PersonFactory()
        org = OrganizationFactory()

        project = ProjectFactory(owner=org)
        ProjectDescriptionFactory(related=project, type="Abstract")
        ProjectDateFactory(related=project, type="Created")
        ContributionFactory(content_object=project, contributor=person)
        ContributionFactory(content_object=project, contributor=org)

        # Public: the subject is factory wiring, not visibility. `project.datasets` uses the privacy-first
        # default manager, so a private dataset would be missing from it though the relation is wired.
        dataset = DatasetFactory(
            project=project, visibility=Dataset.VISIBILITY_CHOICES.PUBLIC
        )
        DatasetDescriptionFactory(related=dataset, type="Methods")
        DatasetDateFactory(related=dataset, type="Available")
        ContributionFactory(content_object=dataset, contributor=person)

        sample1 = RockSampleFactory(dataset=dataset)
        sample2 = RockSampleFactory(dataset=dataset)
        SampleDescriptionFactory(related=sample1)
        SampleDateFactory(related=sample1)

        measurement1 = ExampleMeasurementFactory(dataset=dataset, sample=sample1)
        ExampleMeasurementFactory(dataset=dataset, sample=sample2)
        MeasurementDescriptionFactory(related=measurement1)
        MeasurementDateFactory(related=measurement1)

        assert project.datasets.count() == 1
        assert dataset.samples.count() == 2
        assert dataset.measurements.count() == 2
        assert project.contributors.count() == 2
        assert dataset.contributors.count() == 1
        assert sample1.descriptions.count() == 1
        assert measurement1.descriptions.count() == 1

    def test_multiple_datasets_share_project(self):
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
        people = PersonFactory.create_batch(5)
        assert len(people) == 5
        assert all(isinstance(p, Person) for p in people)

        projects = ProjectFactory.create_batch(3)
        assert len(projects) == 3
        assert all(isinstance(p, Project) for p in projects)


@pytest.mark.django_db
class TestBasicFactoryFunctionality:
    def test_all_factories_can_create_instances(self):
        with pytest.raises(factory.errors.FactoryError):
            MeasurementFactory(sample=RockSampleFactory())

        project = ProjectFactory()
        dataset = DatasetFactory()
        sample = RockSampleFactory()
        measurement = ExampleMeasurementFactory(sample=RockSampleFactory())

        person = PersonFactory()
        contributor = ContributorFactory()

        assert project.pk is not None
        assert dataset.pk is not None
        assert sample.pk is not None
        assert measurement.pk is not None
        assert person.pk is not None
        assert contributor.pk is not None

    def test_all_factories_can_build_instances(self):
        with pytest.raises(factory.errors.FactoryError):
            MeasurementFactory.build()

        project = ProjectFactory.build()
        dataset = DatasetFactory.build()
        sample = RockSampleFactory.build()
        measurement = ExampleMeasurementFactory.build()

        person = PersonFactory.build()
        contributor = ContributorFactory.build()

        assert project.pk is None
        assert dataset.pk is None
        assert sample.pk is None
        assert measurement.pk is None
        assert person.pk is None
        assert contributor.pk is None

    def test_factory_batch_creation(self):
        projects = ProjectFactory.create_batch(2)
        people = PersonFactory.create_batch(2)

        assert len(projects) == 2
        assert len(people) == 2

        assert projects[0].pk != projects[1].pk
        assert people[0].pk != people[1].pk

    def test_factory_custom_parameters(self):
        custom_name = "Test Project"
        project = ProjectFactory(name=custom_name)
        assert project.name == custom_name

        custom_first_name = "John"
        person = PersonFactory(first_name=custom_first_name)
        assert person.first_name == custom_first_name

    def test_factory_relationships(self):
        project = ProjectFactory()
        dataset = DatasetFactory(project=project)
        sample = RockSampleFactory(dataset=dataset)
        measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)

        assert dataset.project == project
        assert sample.dataset == dataset
        assert measurement.dataset == dataset
        assert measurement.sample == sample
