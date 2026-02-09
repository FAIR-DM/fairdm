"""Core model factories for FairDM testing.

This module provides factory_boy factories for creating test instances of FairDM's
core models: Project, Dataset, Sample, and Measurement. These factories follow an
**opt-in pattern** for creating related metadata objects (descriptions and dates).

Key Features
------------

1. **Minimal by Default**: Factories create only required fields unless explicitly requested.
2. **Opt-In Relationships**: Use keyword arguments to create descriptions/dates:

   .. code-block:: python

      # No descriptions or dates created
      project = ProjectFactory()

      # Create 2 descriptions
      project = ProjectFactory(descriptions=2)

      # Create specific description types
      project = ProjectFactory(descriptions=2, descriptions__types=["Abstract", "Methods"])

3. **Vocabulary Validation**: All description/date types are validated against model
   VOCABULARY attributes. Invalid types raise ValueError.

4. **Controlled Vocabularies**: Default types come from the model's VOCABULARY (e.g.,
   ``ProjectDescription.VOCABULARY.values``), ensuring factories create valid test data.

Factories Available
-------------------

- ``ProjectFactory`` - Create Project instances with optional descriptions/dates
- ``DatasetFactory`` - Create Dataset instances with optional descriptions/dates
- ``SampleFactory`` - Create Sample instances with optional descriptions/dates/identifiers
- ``MeasurementFactory`` - Create Measurement instances with optional descriptions/dates

Metadata Factories
------------------

- ``ProjectDescriptionFactory``, ``DatasetDescriptionFactory``, etc.
- ``ProjectDateFactory``, ``DatasetDateFactory``, etc.
- ``SampleIdentifierFactory``, ``SampleRelationFactory``

Usage Examples
--------------

Basic creation::

    project = ProjectFactory()
    dataset = DatasetFactory(project=project)
    sample = SampleFactory(dataset=dataset)

With metadata (opt-in)::

    project = ProjectFactory(
        descriptions=2,  # Create 2 descriptions
        dates=1,  # Create 1 date
    )

Custom types::

    project = ProjectFactory(
        descriptions=3, descriptions__types=["Abstract", "Introduction", "Objectives"]
    )

Batch creation::

    projects = ProjectFactory.create_batch(5, descriptions=2, dates=1)

Type validation::

    # Raises ValueError - "InvalidType" not in ProjectDescription.VOCABULARY
    project = ProjectFactory(descriptions=1, descriptions__types=["InvalidType"])

For more details, see:
- Portal developers: docs/portal-development/testing-portal-projects.md
- Framework contributors: docs/contributing/testing/
"""

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
from fairdm.core.sample.models import SampleDate, SampleDescription, SampleIdentifier, SampleRelation

from . import utils  # noqa: F401 # Ensure utils is imported for the custom Provider
from .contributors import OrganizationFactory  # Import OrganizationFactory for Project.owner


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

    To create descriptions/dates:
        ProjectFactory(descriptions=2)  # Creates 2 descriptions with default types
        ProjectFactory(descriptions=2, descriptions__types=["Abstract", "Methods"])  # Specify types
        ProjectFactory(dates=1)  # Creates 1 date with default type
        ProjectFactory(dates=2, dates__types=["Created", "Updated"])  # Specify types
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

    # Relations - owner required for Project (Organization, not Person)
    owner = SubFactory(OrganizationFactory)

    @factory.post_generation
    def descriptions(obj, create, extracted, **kwargs):
        """Create descriptions.

        Args:
            extracted: Number of descriptions to create (int), or False/None to skip
            **kwargs: Additional parameters:
                - types: List of description types to use

        Examples:
            ProjectFactory(descriptions=2)  # 2 descriptions with default types from model VOCABULARY
            ProjectFactory(descriptions=3, descriptions__types=["Abstract", "Methods", "Objectives"])
        """
        if not create or not extracted:
            return

        if not isinstance(extracted, int):
            raise TypeError(f"descriptions must be an int, got {type(extracted).__name__}")

        # Get types from kwargs or use defaults from model VOCABULARY
        valid_types = ProjectDescription.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        # Validate user-provided types
        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(f"Invalid description types: {invalid_types}. Valid types are: {valid_types}")

        if extracted > len(types):
            raise ValueError(
                f"Cannot create {extracted} descriptions with only {len(types)} types provided. "
                f"Pass descriptions__types=[...] with at least {extracted} types."
            )

        for i in range(extracted):
            ProjectDescriptionFactory(related=obj, type=types[i])

    @factory.post_generation
    def dates(obj, create, extracted, **kwargs):
        """Create dates.

        Args:
            extracted: Number of dates to create (int), or False/None to skip
            **kwargs: Additional parameters:
                - types: List of date types to use

        Examples:
            ProjectFactory(dates=1)  # 1 date with default type from model VOCABULARY
            ProjectFactory(dates=2, dates__types=["Start", "End"])
        """
        if not create or not extracted:
            return

        if not isinstance(extracted, int):
            raise TypeError(f"dates must be an int, got {type(extracted).__name__}")

        # Get types from kwargs or use defaults from model VOCABULARY
        valid_types = ProjectDate.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        # Validate user-provided types
        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(f"Invalid date types: {invalid_types}. Valid types are: {valid_types}")

        if extracted > len(types):
            raise ValueError(
                f"Cannot create {extracted} dates with only {len(types)} types provided. "
                f"Pass dates__types=[...] with at least {extracted} types."
            )

        for i in range(extracted):
            ProjectDateFactory(related=obj, type=types[i])


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
    Project is auto-created unless provided.

    To create descriptions/dates:
        DatasetFactory(descriptions=2)  # Creates 2 descriptions
        DatasetFactory(descriptions=2, descriptions__types=["Abstract", "Methods"])
        DatasetFactory(dates=1)  # Creates 1 date
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

    @factory.post_generation
    def descriptions(obj, create, extracted, **kwargs):
        """Create descriptions. Pass count as int and optionally types via descriptions__types."""
        if not create or not extracted:
            return

        if not isinstance(extracted, int):
            raise TypeError(f"descriptions must be an int, got {type(extracted).__name__}")

        # Get types from kwargs or use defaults from model VOCABULARY
        valid_types = DatasetDescription.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        # Validate user-provided types
        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(f"Invalid description types: {invalid_types}. Valid types are: {valid_types}")

        if extracted > len(types):
            raise ValueError(
                f"Cannot create {extracted} descriptions with only {len(types)} types provided. "
                f"Pass descriptions__types=[...] with at least {extracted} types."
            )

        for i in range(extracted):
            DatasetDescriptionFactory(related=obj, type=types[i])

    @factory.post_generation
    def dates(obj, create, extracted, **kwargs):
        """Create dates. Pass count as int and optionally types via dates__types."""
        if not create or not extracted:
            return

        if not isinstance(extracted, int):
            raise TypeError(f"dates must be an int, got {type(extracted).__name__}")

        # Get types from kwargs or use defaults from model VOCABULARY
        valid_types = DatasetDate.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        # Validate user-provided types
        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(f"Invalid date types: {invalid_types}. Valid types are: {valid_types}")

        if extracted > len(types):
            raise ValueError(
                f"Cannot create {extracted} dates with only {len(types)} types provided. "
                f"Pass dates__types=[...] with at least {extracted} types."
            )

        for i in range(extracted):
            DatasetDateFactory(related=obj, type=types[i])


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


class SampleIdentifierFactory(DjangoModelFactory):
    """Factory for creating SampleIdentifier instances."""

    class Meta:
        model = SampleIdentifier

    type = "DOI"  # Default identifier type
    value = Faker("bothify", text="10.####/sample-?????")
    # related field will be set by the caller


class SampleFactory(DjangoModelFactory):
    """Factory for creating Sample instances.

    By default, creates a minimal Sample with only required fields.
    Dataset is auto-created unless provided.

    To create descriptions/dates:
        SampleFactory(descriptions=2)
        SampleFactory(dates=1)
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

    @factory.post_generation
    def descriptions(obj, create, extracted, **kwargs):
        """Create descriptions. Pass count as int and optionally types via descriptions__types."""
        if not create or not extracted:
            return

        if not isinstance(extracted, int):
            raise TypeError(f"descriptions must be an int, got {type(extracted).__name__}")

        # Get types from kwargs or use defaults from model VOCABULARY
        valid_types = SampleDescription.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        # Validate user-provided types
        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(f"Invalid description types: {invalid_types}. Valid types are: {valid_types}")

        if extracted > len(types):
            raise ValueError(
                f"Cannot create {extracted} descriptions with only {len(types)} types provided. "
                f"Pass descriptions__types=[...] with at least {extracted} types."
            )

        for i in range(extracted):
            SampleDescriptionFactory(related=obj, type=types[i])

    @factory.post_generation
    def dates(obj, create, extracted, **kwargs):
        """Create dates. Pass count as int and optionally types via dates__types."""
        if not create or not extracted:
            return

        if not isinstance(extracted, int):
            raise TypeError(f"dates must be an int, got {type(extracted).__name__}")

        # Get types from kwargs or use defaults from model VOCABULARY
        valid_types = SampleDate.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        # Validate user-provided types
        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(f"Invalid date types: {invalid_types}. Valid types are: {valid_types}")

        if extracted > len(types):
            raise ValueError(
                f"Cannot create {extracted} dates with only {len(types)} types provided. "
                f"Pass dates__types=[...] with at least {extracted} types."
            )

        for i in range(extracted):
            SampleDateFactory(related=obj, type=types[i])


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
    Dataset and sample are auto-created if not provided.
    The sample will be created in the same dataset as the measurement.

    To create descriptions/dates:
        MeasurementFactory(descriptions=2)
        MeasurementFactory(dates=1)
    """

    class Meta:
        model = Measurement

    # Basic fields
    name = Faker("word")

    # Relations - both dataset and sample are required
    # Create dataset first, then create sample in that dataset
    dataset = SubFactory(DatasetFactory)
    sample = SubFactory(SampleFactory, dataset=LazyAttribute(lambda o: o.factory_parent.dataset))

    @factory.post_generation
    def descriptions(obj, create, extracted, **kwargs):
        """Create descriptions. Pass count as int and optionally types via descriptions__types."""
        if not create or not extracted:
            return

        if not isinstance(extracted, int):
            raise TypeError(f"descriptions must be an int, got {type(extracted).__name__}")

        # Get types from kwargs or use defaults from model VOCABULARY
        valid_types = MeasurementDescription.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        # Validate user-provided types
        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(f"Invalid description types: {invalid_types}. Valid types are: {valid_types}")

        if extracted > len(types):
            raise ValueError(
                f"Cannot create {extracted} descriptions with only {len(types)} types provided. "
                f"Pass descriptions__types=[...] with at least {extracted} types."
            )

        for i in range(extracted):
            MeasurementDescriptionFactory(related=obj, type=types[i])

    @factory.post_generation
    def dates(obj, create, extracted, **kwargs):
        """Create dates. Pass count as int and optionally types via dates__types."""
        if not create or not extracted:
            return

        if not isinstance(extracted, int):
            raise TypeError(f"dates must be an int, got {type(extracted).__name__}")

        # Get types from kwargs or use defaults from model VOCABULARY
        valid_types = MeasurementDate.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        # Validate user-provided types
        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(f"Invalid date types: {invalid_types}. Valid types are: {valid_types}")

        if extracted > len(types):
            raise ValueError(
                f"Cannot create {extracted} dates with only {len(types)} types provided. "
                f"Pass dates__types=[...] with at least {extracted} types."
            )

        for i in range(extracted):
            MeasurementDateFactory(related=obj, type=types[i])


class SampleRelationFactory(DjangoModelFactory):
    """Factory for creating SampleRelation instances.

    Creates a typed relationship between two samples.
    Both source and target samples must be provided or will be auto-created.
    """

    class Meta:
        model = SampleRelation

    type = "child_of"  # Default relationship type
    source = SubFactory(SampleFactory)
    target = SubFactory(SampleFactory)
