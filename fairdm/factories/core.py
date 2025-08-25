import factory
from factory.declarations import LazyAttribute, RelatedFactoryList, SubFactory
from factory.django import DjangoModelFactory
from factory.faker import Faker
from factory.fuzzy import FuzzyChoice

from fairdm.core.choices import ProjectStatus
from fairdm.core.dataset.models import DatasetDate, DatasetDescription
from fairdm.core.measurement.models import MeasurementDate, MeasurementDescription
from fairdm.core.models import Dataset, Measurement, Project, Sample
from fairdm.core.project.models import ProjectDate, ProjectDescription
from fairdm.core.sample.models import SampleDate, SampleDescription
from fairdm.utils.choices import Visibility

from . import utils  # noqa: F401 # Ensure utils is imported for the custom Provider


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
    """Factory for creating Project instances."""

    class Meta:
        model = Project

    # Basic fields
    name = Faker("sentence", nb_words=4, variable_nb_words=True)
    image = factory.django.ImageField(width=800, height=600)
    visibility = FuzzyChoice(Visibility.values)
    status = FuzzyChoice(ProjectStatus.values)

    # JSON fields - simplified approach
    funding = LazyAttribute(lambda obj: {"agency": "Sample Agency", "grant_number": "GRANT-2024-001", "amount": 50000})

    # Related objects using RelatedFactoryList
    descriptions = RelatedFactoryList("fairdm.factories.core.ProjectDescriptionFactory", "related", size=2)
    dates = RelatedFactoryList("fairdm.factories.core.ProjectDateFactory", "related", size=1)

    # Relations - owner will be set via contributors
    owner = None

    # Add contributors
    contributors = RelatedFactoryList(
        "fairdm.factories.contributors.ContributionFactory",
        factory_related_name="content_object",
        size=2,
    )


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
    """Factory for creating Dataset instances."""

    class Meta:
        model = Dataset

    # Basic fields
    name = Faker("sentence", nb_words=3, variable_nb_words=True)
    image = factory.django.ImageField(width=800, height=600)
    visibility = FuzzyChoice(Visibility.values)

    # Relations
    project = SubFactory(ProjectFactory)

    # Related objects using RelatedFactoryList
    descriptions = RelatedFactoryList("fairdm.factories.core.DatasetDescriptionFactory", "related", size=2)
    dates = RelatedFactoryList("fairdm.factories.core.DatasetDateFactory", "related", size=1)

    # Simplified license handling
    @LazyAttribute
    def license(self):
        from licensing.models import License

        # Try to get the first existing license, or create a simple one
        existing_license = License.objects.first()
        if existing_license:
            return existing_license

        # Create a minimal license with only the required fields
        license_obj, created = License.objects.get_or_create(
            name="CC BY 4.0"
            # Remove the 'url' field since it doesn't exist on the License model
        )
        return license_obj

    # Add contributors
    contributors = RelatedFactoryList(
        "fairdm.factories.contributors.ContributionFactory",
        factory_related_name="content_object",
        size=1,
    )


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
    """Factory for creating Sample instances."""

    class Meta:
        model = Sample

    # Basic fields
    name = Faker("word")
    local_id = Faker("bothify", text="SAMPLE-####")
    status = "unknown"  # Default from the model

    # Relations
    dataset = SubFactory(DatasetFactory)
    location = None  # Optional field

    # Related objects using RelatedFactoryList
    descriptions = RelatedFactoryList("fairdm.factories.core.SampleDescriptionFactory", "related", size=2)
    dates = RelatedFactoryList("fairdm.factories.core.SampleDateFactory", "related", size=1)


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
    """Factory for creating Measurement instances."""

    class Meta:
        model = Measurement

    # Basic fields
    name = Faker("word")

    # Relations
    dataset = SubFactory(DatasetFactory)
    sample = SubFactory(SampleFactory)

    # Related objects using RelatedFactoryList
    descriptions = RelatedFactoryList("fairdm.factories.core.MeasurementDescriptionFactory", "related", size=2)
    dates = RelatedFactoryList("fairdm.factories.core.MeasurementDateFactory", "related", size=1)
