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

      # Create specific description types, named by address
      project = ProjectFactory(
          descriptions=2,
          descriptions__types=[ABSTRACT, f"{DESCRIPTION_TYPES}/introduction"],
      )

3. **Vocabulary Validation**: All description/date types are validated against the collection
   the model's ``type`` field offers. Invalid types raise ValueError.

4. **Controlled Vocabularies**: Default types come from that collection (e.g.,
   ``ProjectDescription.get_type_concepts()``), ensuring factories create valid test data. The
   vocabularies must be loaded, as the test suite does once per session.

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
        descriptions=2,
        descriptions__types=[ABSTRACT, f"{DESCRIPTION_TYPES}/objectives"],
    )

Batch creation::

    projects = ProjectFactory.create_batch(5, descriptions=2, dates=1)

Type validation::

    # Raises ValueError - the address is not in the project description types
    project = ProjectFactory(
        descriptions=1, descriptions__types=[f"{DESCRIPTION_TYPES}/invalid"]
    )

For more details, see:
- Portal developers: docs/developers/how-to/test-a-portal-with-fairdm-factories.md
- Framework contributors: docs/contributing/testing/
"""

import factory
from django.conf import settings
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
from fairdm.core.vocabularies import (
    ABSTRACT,
    DATE_TYPES,
    DESCRIPTION_TYPES,
    DOI,
    PROJECT_START,
)

from .contributors import (
    OrganizationFactory,
)
from .utils import ConceptFieldFactory


class ProjectDescriptionFactory(ConceptFieldFactory):
    """Factory for creating ProjectDescription instances."""

    class Meta:
        model = ProjectDescription

    type = ABSTRACT
    value = Faker("text", max_nb_chars=300)


class ProjectDateFactory(ConceptFieldFactory):
    """Factory for creating ProjectDate instances."""

    class Meta:
        model = ProjectDate

    type = PROJECT_START
    value = Faker("partial_date")


class ProjectIdentifierFactory(ConceptFieldFactory):
    """Factory for creating ProjectIdentifier instances."""

    class Meta:
        model = ProjectIdentifier

    type = DOI
    value = Faker("bothify", text="10.####/project-?????")


class ProjectFactory(DjangoModelFactory):
    """Factory for creating Project instances.

    By default, creates a minimal Project with only required fields.

    To create descriptions/dates:
        ProjectFactory(descriptions=2)  # Creates 2 descriptions with default types
        ProjectFactory(descriptions=2, descriptions__types=[ABSTRACT, f"{DESCRIPTION_TYPES}/objectives"])
        ProjectFactory(dates=1)  # Creates 1 date with default type
        ProjectFactory(dates=2, dates__types=[PROJECT_START, PROJECT_END])

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

        valid_types = [
            concept.uri for concept in ProjectDescription.get_type_concepts()
        ]
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

        valid_types = [concept.uri for concept in ProjectDate.get_type_concepts()]
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


class DatasetDescriptionFactory(ConceptFieldFactory):
    """Factory for creating DatasetDescription instances."""

    class Meta:
        model = DatasetDescription

    type = ABSTRACT
    value = Faker("text", max_nb_chars=300)


class DatasetDateFactory(ConceptFieldFactory):
    """Factory for creating DatasetDate instances."""

    class Meta:
        model = DatasetDate

    type = f"{DATE_TYPES}/available"
    value = Faker("partial_date")


class DatasetIdentifierFactory(ConceptFieldFactory):
    """Factory for creating DatasetIdentifier instances."""

    class Meta:
        model = DatasetIdentifier

    type = DOI
    value = factory.Sequence(lambda n: f"10.{1000 + n}/dataset-{n}")


class LiteratureItemFactory(DjangoModelFactory):
    """Factory for creating literature.Item instances.

    The item is built from a CSL JSON dictionary with ``literature.converters.from_csl_json``,
    so the DOI, the issued year and the authors are stored as the package stores them.

    Args:
        citation_key: The reference's key. A unique sequence by default.
        title: The title. Derived from the citation key by default.
        type: The CSL item type. ``article-journal`` by default.
        doi: A DOI to store as an identifier.
        year: The year of the issued date.
        authors: ``(family, given)`` pairs, in order.
    """

    class Meta:
        model = "literature.Item"

    citation_key = factory.Sequence(lambda n: f"literature-item-{n}")
    type = "article-journal"
    title = factory.LazyAttribute(lambda o: f"Test Literature Item {o.citation_key}")
    doi = None
    year = None
    authors = ()

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Store the item through ``from_csl_json`` rather than ``Item.objects.create``."""
        from literature.converters import from_csl_json

        csl = {
            "id": kwargs["citation_key"],
            "type": kwargs["type"],
            "title": kwargs["title"],
        }
        if kwargs["doi"]:
            csl["DOI"] = kwargs["doi"]
        if kwargs["year"]:
            csl["issued"] = {"date-parts": [[kwargs["year"]]]}
        if kwargs["authors"]:
            csl["author"] = [
                {"family": family, "given": given}
                for family, given in kwargs["authors"]
            ]
        return from_csl_json(csl)


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
        DatasetFactory(descriptions=2, descriptions__types=[ABSTRACT, f"{DESCRIPTION_TYPES}/methods"])
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
        """Use the portal's default licence, creating it when it does not exist yet.

        Never the first licence by name: where "CC0 1.0" sorts against "CC BY 4.0" depends on
        the database's collation.
        """
        from licensing.models import License

        name = getattr(settings, "FAIRDM_DEFAULT_LICENSE", "CC BY 4.0")
        license_obj, _ = License.objects.get_or_create(name=name)
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

        valid_types = [
            concept.uri for concept in DatasetDescription.get_type_concepts()
        ]
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

        valid_types = [concept.uri for concept in DatasetDate.get_type_concepts()]
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


class SampleDescriptionFactory(ConceptFieldFactory):
    """Factory for creating SampleDescription instances."""

    class Meta:
        model = SampleDescription

    type = f"{DESCRIPTION_TYPES}/sample-collection"
    value = Faker("text", max_nb_chars=300)


class SampleDateFactory(ConceptFieldFactory):
    """Factory for creating SampleDate instances."""

    class Meta:
        model = SampleDate

    type = f"{DATE_TYPES}/created"
    value = Faker("partial_date")


class SampleIdentifierFactory(ConceptFieldFactory):
    """Factory for creating SampleIdentifier instances."""

    class Meta:
        model = SampleIdentifier

    type = DOI
    # AbstractIdentifier.value is unique across every record that carries identifiers.
    value = factory.Sequence(lambda n: f"10.{2000 + n}/sample-{n}")


class SampleFactory(ConceptFieldFactory):
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

        valid_types = [concept.uri for concept in SampleDescription.get_type_concepts()]
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

        valid_types = [concept.uri for concept in SampleDate.get_type_concepts()]
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


class MeasurementDescriptionFactory(ConceptFieldFactory):
    """Factory for creating MeasurementDescription instances."""

    class Meta:
        model = MeasurementDescription

    type = f"{DESCRIPTION_TYPES}/measurement-conditions"
    value = Faker("text", max_nb_chars=300)


class MeasurementDateFactory(ConceptFieldFactory):
    """Factory for creating MeasurementDate instances."""

    class Meta:
        model = MeasurementDate

    type = f"{DATE_TYPES}/setup"
    value = Faker("partial_date")


class MeasurementIdentifierFactory(ConceptFieldFactory):
    """Factory for creating MeasurementIdentifier instances."""

    class Meta:
        model = MeasurementIdentifier

    type = DOI
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

        valid_types = [
            concept.uri for concept in MeasurementDescription.get_type_concepts()
        ]
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

        valid_types = [concept.uri for concept in MeasurementDate.get_type_concepts()]
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
