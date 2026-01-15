import factory
from factory.declarations import LazyAttribute, SubFactory
from factory.django import DjangoModelFactory
from factory.faker import Faker
from factory.fuzzy import FuzzyChoice

from fairdm.core.choices import ProjectStatus
from fairdm.core.dataset.models import DatasetDate, DatasetDescription
from fairdm.core.measurement.models import MeasurementDate, MeasurementDescription
from fairdm.core.models import Dataset, Measurement, Project, Sample
from fairdm.core.project.models import ProjectDate, ProjectDescription
from fairdm.core.sample.models import SampleDate, SampleDescription

from . import utils  # noqa: F401 # Ensure utils is imported for the custom Provider
from .contributors import UserFactory  # Import UserFactory for Project.owner


class ProjectDescriptionFactory(DjangoModelFactory):
    """Factory for creating ProjectDescription instances."""

    class Meta:
        model = ProjectDescription

    type = "Abstract"  # Default description type
    value = Faker("text", max_nb_chars=300)


class ProjectDateFactory(DjangoModelFactory):
    """Factory for creating ProjectDate instances."""

    class Meta:
        model = ProjectDate

    type = "Created"  # Default date type
    value = Faker("partial_date")


class ProjectFactory(DjangoModelFactory):
    """Factory for creating Project instances.

    By default, creates a minimal Project with only required fields.
    Use traits or manual creation for descriptions, dates, and contributors.
    """

    class Meta:
        model = Project

    # Basic fields
    name = Faker("sentence", nb_words=4, variable_nb_words=True)
    image = factory.django.ImageField(width=800, height=600)
    # visibility defaults to PRIVATE per model definition
    status = FuzzyChoice(ProjectStatus.values)

    # JSON fields - simplified approach
    funding = LazyAttribute(lambda obj: {"agency": "Sample Agency", "grant_number": "GRANT-2024-001", "amount": 50000})

    # Relations - owner required for Project
    owner = SubFactory(UserFactory)


class DatasetDescriptionFactory(DjangoModelFactory):
    """Factory for creating DatasetDescription instances."""

    class Meta:
        model = DatasetDescription

    type = "Abstract"  # Default description type
    value = Faker("text", max_nb_chars=300)


class DatasetDateFactory(DjangoModelFactory):
    """Factory for creating DatasetDate instances."""

    class Meta:
        model = DatasetDate

    type = "Created"  # Default date type
    value = Faker("partial_date")


class DatasetFactory(DjangoModelFactory):
    """Factory for creating Dataset instances.

    By default, creates a minimal Dataset with only required fields.
    Use traits or manual creation for descriptions, dates, and contributors.
    Project must be provided or will be auto-created.
    """

    class Meta:
        model = Dataset

    # Basic fields
    name = Faker("sentence", nb_words=3, variable_nb_words=True)
    image = factory.django.ImageField(width=800, height=600)
    # visibility defaults to PRIVATE per model definition

    # Relations - project can be passed in or auto-created
    project = SubFactory(ProjectFactory)

    # Simplified license handling
    @LazyAttribute
    def license(self):
        from licensing.models import License

        # Try to get the first existing license, or create a simple one
        existing_license = License.objects.first()
        if existing_license:
            return existing_license

        # Create a minimal license with only the required fields
        license_obj, _ = License.objects.get_or_create(name="CC BY 4.0")
        return license_obj


class SampleDescriptionFactory(DjangoModelFactory):
    """Factory for creating SampleDescription instances."""

    class Meta:
        model = SampleDescription

    type = "Abstract"  # Default description type
    value = Faker("text", max_nb_chars=300)


class SampleDateFactory(DjangoModelFactory):
    """Factory for creating SampleDate instances."""

    class Meta:
        model = SampleDate

    type = "Created"  # Default date type
    value = Faker("partial_date")


class SampleFactory(DjangoModelFactory):
    """Factory for creating Sample instances.

    By default, creates a minimal Sample with only required fields.
    Dataset must be provided or will be auto-created.
    Use manual creation for descriptions and dates.
    """

    class Meta:
        model = Sample

    # Basic fields
    name = Faker("word")
    local_id = Faker("bothify", text="SAMPLE-####")
    status = "unknown"  # Default from the model

    # Relations - dataset can be passed in or auto-created
    dataset = SubFactory(DatasetFactory)
    location = None  # Optional field


class MeasurementDescriptionFactory(DjangoModelFactory):
    """Factory for creating MeasurementDescription instances."""

    class Meta:
        model = MeasurementDescription

    type = "Abstract"  # Default description type
    value = Faker("text", max_nb_chars=300)


class MeasurementDateFactory(DjangoModelFactory):
    """Factory for creating MeasurementDate instances."""

    class Meta:
        model = MeasurementDate

    type = "Created"  # Default date type
    value = Faker("partial_date")


class MeasurementFactory(DjangoModelFactory):
    """Factory for creating Measurement instances.

    By default, creates a minimal Measurement with only required fields.
    Dataset and sample are both required and will be auto-created if not provided.
    The sample will be created in the same dataset as the measurement.
    Use manual creation for descriptions and dates.
    """

    class Meta:
        model = Measurement

    # Basic fields
    name = Faker("word")

    # Relations - both dataset and sample are required
    # Create dataset first, then create sample in that dataset
    dataset = SubFactory(DatasetFactory)
    sample = SubFactory(SampleFactory, dataset=LazyAttribute(lambda o: o.factory_parent.dataset))
