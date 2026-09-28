"""Factories for FairDM's core models.

These factory_boy factories create test instances of FairDM's
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
      project = ProjectFactory(
          descriptions=2, descriptions__types=["Abstract", "Methods"]
      )

3. **Vocabulary Validation**: All description/date types are validated against model
   VOCABULARY attributes. Invalid types raise ValueError.

4. **Controlled Vocabularies**: Default types come from the model's VOCABULARY (e.g.,
   ``ProjectDescription.VOCABULARY.values``), ensuring factories create valid test data.

Factories Available
-------------------

- ``ProjectFactory`` - Create Project instances with optional descriptions/dates
- ``DatasetFactory`` - Create Dataset instances with optional descriptions/dates
- ``SampleFactory`` - **Abstract.** The base every specimen factory builds on; it cannot be
  instantiated directly because the ``Sample`` model it declares cannot be created directly
  either. A reference implementation lives in ``demo.factories`` (e.g.
  ``RockSampleFactory``); a portal defines its own alongside its own specimen types.
- ``MeasurementFactory`` - **Abstract.** The base every measurement factory builds on; it cannot
  be instantiated directly because the ``Measurement`` model it declares cannot be created
  directly either. A reference implementation lives in ``demo.factories`` (e.g.
  ``ExampleMeasurementFactory``); a portal defines its own alongside its own measurement types.

Metadata Factories
------------------

- ``ProjectDescriptionFactory``, ``DatasetDescriptionFactory``, etc.
- ``SampleDescriptionFactory``, ``SampleDateFactory``, ``SampleIdentifierFactory``,
  ``SampleRelationFactory``

Usage Examples
--------------

Basic creation::

    project = ProjectFactory()
    dataset = DatasetFactory(project=project)
    from demo.factories import RockSampleFactory

    sample = RockSampleFactory(dataset=dataset)

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
from fairdm.core.dataset.models import (
    DatasetDate,
    DatasetDescription,
    DatasetIdentifier,
    DatasetLiteratureRelation,
)
from fairdm.core.measurement.models import (
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)
from fairdm.core.models import Dataset, Measurement, Project, Sample
from fairdm.core.project.models import (
    ProjectDate,
    ProjectDescription,
    ProjectIdentifier,
)
from fairdm.core.sample.models import (
    SampleDate,
    SampleDescription,
    SampleIdentifier,
    SampleRelation,
)

from . import utils  # noqa: F401 # Ensure utils is imported for the custom Provider
from .contributors import (
    OrganizationFactory,
)


class ProjectDescriptionFactory(DjangoModelFactory):
    """Factory for creating ProjectDescription instances."""

    class Meta:
        model = ProjectDescription

    type = "Abstract"
    value = Faker("text", max_nb_chars=300)


class ProjectDateFactory(DjangoModelFactory):
    """Factory for creating ProjectDate instances."""

    class Meta:
        model = ProjectDate

    type = "Start"
    value = Faker("partial_date")


class ProjectIdentifierFactory(DjangoModelFactory):
    """Factory for creating ProjectIdentifier instances."""

    class Meta:
        model = ProjectIdentifier

    type = "DOI"
    value = Faker("bothify", text="10.####/project-?????")


class ProjectFactory(DjangoModelFactory):
    """Factory for creating Project instances.

    By default, creates a minimal Project with only required fields.

    To create descriptions/dates:
        ProjectFactory(descriptions=2)  # Creates 2 descriptions with default types
        ProjectFactory(descriptions=2, descriptions__types=["Abstract", "Methods"])  # Specify types
        ProjectFactory(dates=1)  # Creates 1 date with default type
        ProjectFactory(dates=2, dates__types=["Created", "Updated"])  # Specify types

    Image (opt-in, issue #323):
        ProjectFactory()  # No image, no file written
        ProjectFactory(with_image=True)  # A generated placeholder JPEG
        ProjectFactory(image=some_file)  # That file used directly
    """

    class Meta:
        model = Project

    class Params:
        # No image unless a test asks for one: an image written on every build left
        # files under MEDIA_ROOT (#323).
        with_image = factory.Trait(
            image=factory.django.ImageField(width=800, height=600),
        )

    name = Faker("sentence", nb_words=4, variable_nb_words=True)
    # visibility defaults to PRIVATE per model definition
    status = FuzzyChoice(ProjectStatus.values)

    # A list of DataCite funding references.
    funding = LazyAttribute(
        lambda obj: [
            {
                "funderName": "Sample Agency",
                "awardNumber": "GRANT-2024-001",
            }
        ]
    )

    owner = SubFactory(OrganizationFactory)

    @factory.post_generation
    def descriptions(obj, create, extracted, **kwargs):
        """Create descriptions. Pass count as int and optionally types via descriptions__types."""
        if not create or not extracted:
            return

        if not isinstance(extracted, int):
            raise TypeError(
                f"descriptions must be an int, got {type(extracted).__name__}"
            )

        valid_types = ProjectDescription.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(
                    f"Invalid description types: {invalid_types}. Valid types are: {valid_types}"
                )

        if extracted > len(types):
            raise ValueError(
                f"Cannot create {extracted} descriptions with only {len(types)} types provided. "
                f"Pass descriptions__types=[...] with at least {extracted} types."
            )

        for i in range(extracted):
            ProjectDescriptionFactory(related=obj, type=types[i])

    @factory.post_generation
    def dates(obj, create, extracted, **kwargs):
        """Create dates. Pass count as int and optionally types via dates__types."""
        if not create or not extracted:
            return

        if not isinstance(extracted, int):
            raise TypeError(f"dates must be an int, got {type(extracted).__name__}")

        valid_types = ProjectDate.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(
                    f"Invalid date types: {invalid_types}. Valid types are: {valid_types}"
                )

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

    type = "Abstract"
    value = Faker("text", max_nb_chars=300)


class DatasetDateFactory(DjangoModelFactory):
    """Factory for creating DatasetDate instances."""

    class Meta:
        model = DatasetDate

    type = "Available"
    value = Faker("partial_date")


class DatasetIdentifierFactory(DjangoModelFactory):
    """Factory for creating DatasetIdentifier instances."""

    class Meta:
        model = DatasetIdentifier

    type = "DOI"
    value = factory.Sequence(lambda n: f"10.{1000 + n}/dataset-{n}")


class LiteratureItemFactory(DjangoModelFactory):
    """Factory for creating literature.LiteratureItem instances.

    ``LiteratureItem.save()`` derives ``type`` and ``title`` from the ``item``
    CSL-JSON blob, and falls back to generating ``citation_key`` from the
    title when one isn't supplied - so an explicit, sequence-guarded
    ``citation_key`` is provided here to satisfy its uniqueness constraint.
    """

    class Meta:
        model = "literature.LiteratureItem"

    citation_key = factory.Sequence(lambda n: f"literature-item-{n}")
    item = factory.LazyAttribute(
        lambda o: {
            "type": "article-journal",
            "title": f"Test Literature Item {o.citation_key}",
        }
    )


class DatasetLiteratureRelationFactory(DjangoModelFactory):
    """Factory for creating DatasetLiteratureRelation instances.

    Relates a dataset to a literature item under a DataCite relationship type.
    """

    class Meta:
        model = DatasetLiteratureRelation

    dataset = SubFactory("fairdm.factories.core.DatasetFactory")
    literature_item = SubFactory("fairdm.factories.core.LiteratureItemFactory")
    relationship_type = "IsCitedBy"


class DatasetFactory(DjangoModelFactory):
    """Factory for creating Dataset instances.

    By default, creates a minimal Dataset with only required fields.
    Project is auto-created unless provided.

    To create descriptions/dates:
        DatasetFactory(descriptions=2)  # Creates 2 descriptions
        DatasetFactory(descriptions=2, descriptions__types=["Abstract", "Methods"])
        DatasetFactory(dates=1)  # Creates 1 date

    Image (opt-in, issue #323): same as ProjectFactory above.
    """

    class Meta:
        model = Dataset

    class Params:
        # No image unless a test asks for one (#323).
        with_image = factory.Trait(
            image=factory.django.ImageField(width=800, height=600),
        )

    name = Faker("sentence", nb_words=3, variable_nb_words=True)
    # visibility defaults to PRIVATE per model definition

    project = SubFactory(ProjectFactory)

    @LazyAttribute
    def license(self):
        """Use the first existing license, creating "CC BY 4.0" when there is none."""
        from licensing.models import License

        existing_license = License.objects.first()
        if existing_license:
            return existing_license

        license_obj, _ = License.objects.get_or_create(name="CC BY 4.0")
        return license_obj

    @factory.post_generation
    def descriptions(obj, create, extracted, **kwargs):
        """Create descriptions. Pass count as int and optionally types via descriptions__types."""
        if not create or not extracted:
            return

        if not isinstance(extracted, int):
            raise TypeError(
                f"descriptions must be an int, got {type(extracted).__name__}"
            )

        valid_types = DatasetDescription.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(
                    f"Invalid description types: {invalid_types}. Valid types are: {valid_types}"
                )

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

        valid_types = DatasetDate.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(
                    f"Invalid date types: {invalid_types}. Valid types are: {valid_types}"
                )

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

    type = "SampleCollection"
    value = Faker("text", max_nb_chars=300)


class SampleDateFactory(DjangoModelFactory):
    """Factory for creating SampleDate instances."""

    class Meta:
        model = SampleDate

    type = "Created"
    value = Faker("partial_date")


class SampleIdentifierFactory(DjangoModelFactory):
    """Factory for creating SampleIdentifier instances."""

    class Meta:
        model = SampleIdentifier

    type = "DOI"
    # AbstractIdentifier.value is unique across every record that carries identifiers.
    value = factory.Sequence(lambda n: f"10.{2000 + n}/sample-{n}")


class SampleFactory(DjangoModelFactory):
    """Abstract factory for creating Sample instances.

    ``Sample`` is a polymorphic base that cannot be created directly (only a registered
    specimen type can be) - see ``fairdm.core.sample.models.Sample``'s ``pre_save`` guard. This
    factory declares the fields every specimen shares and is meant to be subclassed, never
    instantiated on its own. The framework's reference implementation supplies concrete
    subclasses in ``demo.factories`` (``RockSampleFactory``, ``WaterSampleFactory``,
    ``SoilSampleFactory``, ...); a portal defines its own alongside its own specimen types.

    To create descriptions/dates on a concrete subclass:
        RockSampleFactory(descriptions=2)
        RockSampleFactory(dates=1)
    """

    class Meta:
        model = Sample
        abstract = True

    name = Faker("word")
    local_id = Faker("bothify", text="SAMPLE-####")
    status = "unknown"

    dataset = SubFactory(DatasetFactory)
    location = None

    @factory.post_generation
    def descriptions(obj, create, extracted, **kwargs):
        """Create descriptions. Pass count as int and optionally types via descriptions__types."""
        if not create or not extracted:
            return

        if not isinstance(extracted, int):
            raise TypeError(
                f"descriptions must be an int, got {type(extracted).__name__}"
            )

        valid_types = SampleDescription.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(
                    f"Invalid description types: {invalid_types}. Valid types are: {valid_types}"
                )

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

        valid_types = SampleDate.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(
                    f"Invalid date types: {invalid_types}. Valid types are: {valid_types}"
                )

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

    type = "MeasurementConditions"
    value = Faker("text", max_nb_chars=300)


class MeasurementDateFactory(DjangoModelFactory):
    """Factory for creating MeasurementDate instances."""

    class Meta:
        model = MeasurementDate

    type = "Setup"
    value = Faker("partial_date")


class MeasurementIdentifierFactory(DjangoModelFactory):
    """Factory for creating MeasurementIdentifier instances."""

    class Meta:
        model = MeasurementIdentifier

    type = "DOI"
    value = factory.Sequence(lambda n: f"10.{4000 + n}/measurement-{n}")


class MeasurementFactory(DjangoModelFactory):
    """Abstract factory for creating Measurement instances.

    ``Measurement`` is a polymorphic base that cannot be created directly (only a registered
    measurement type can be) - see ``fairdm.core.measurement.models.Measurement``'s ``clean``
    guard. This factory declares the fields every measurement shares and is meant to be
    subclassed, never instantiated on its own. The framework's reference implementation
    supplies concrete subclasses in ``demo.factories`` (``ExampleMeasurementFactory``,
    ``XRFMeasurementFactory``, ``ICP_MS_MeasurementFactory``, ...); a portal defines its own
    alongside its own measurement types.

    By default, creates a minimal Measurement with only required fields. Dataset is
    auto-created if not provided, but ``sample`` has no default and must always be passed
    explicitly: ``Sample`` is a polymorphic base that cannot be created directly, and this
    factory has no concrete specimen type of its own to fall back on (see ``SampleFactory``).
    Pass a concrete specimen instance, e.g.
    ``XRFMeasurementFactory(sample=RockSampleFactory())``.

    To create descriptions/dates on a concrete subclass:
        ExampleMeasurementFactory(sample=some_sample, descriptions=2)
        ExampleMeasurementFactory(sample=some_sample, dates=1)
    """

    class Meta:
        model = Measurement
        abstract = True

    name = Faker("word")

    dataset = SubFactory(DatasetFactory)

    @factory.post_generation
    def descriptions(obj, create, extracted, **kwargs):
        """Create descriptions. Pass count as int and optionally types via descriptions__types."""
        if not create or not extracted:
            return

        if not isinstance(extracted, int):
            raise TypeError(
                f"descriptions must be an int, got {type(extracted).__name__}"
            )

        valid_types = MeasurementDescription.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(
                    f"Invalid description types: {invalid_types}. Valid types are: {valid_types}"
                )

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

        valid_types = MeasurementDate.VOCABULARY.values
        types = kwargs.get("types", valid_types)

        if "types" in kwargs:
            invalid_types = [t for t in types if t not in valid_types]
            if invalid_types:
                raise ValueError(
                    f"Invalid date types: {invalid_types}. Valid types are: {valid_types}"
                )

        if extracted > len(types):
            raise ValueError(
                f"Cannot create {extracted} dates with only {len(types)} types provided. "
                f"Pass dates__types=[...] with at least {extracted} types."
            )

        for i in range(extracted):
            MeasurementDateFactory(related=obj, type=types[i])


class SampleRelationFactory(DjangoModelFactory):
    """Factory for creating SampleRelation instances.

    Creates a typed relationship between two samples. ``source`` and ``target`` have no
    default and must always be provided - both are concrete specimens, and ``Sample`` (the
    class ``SampleFactory`` declares) cannot be created directly. Pass concrete specimen
    instances, e.g. ``SampleRelationFactory(source=RockSampleFactory(), target=parent)``.
    """

    class Meta:
        model = SampleRelation

    type = "child_of"


class PointFactory(DjangoModelFactory):
    """Factory for creating Point (location) instances.

    A location has no uuid; it is identified by its coordinate pair, which is why the plugin
    machinery had to stop assuming one.
    """

    class Meta:
        model = "fairdm_location.Point"
        django_get_or_create = ("x", "y")

    x = Faker("pydecimal", left_digits=2, right_digits=6, positive=True)
    y = Faker("pydecimal", left_digits=2, right_digits=6, positive=True)
