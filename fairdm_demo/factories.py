"""
FairDM Demo App - Factory Examples

This module demonstrates best practices for creating test factories in FairDM
portals using factory_boy. These factories are used in tests and for generating
fixture data.

## Factory Patterns

1. **DatasetFactory Usage**: Creating datasets with CC BY 4.0 default license
2. **DatasetIdentifier**: Adding DOIs and other identifiers to datasets
3. **DatasetLiteratureRelation**: Linking datasets with publications
4. **Metadata Creation**: Adding descriptions, dates, and other metadata
5. **Sample/Measurement**: Creating related samples and measurements

## Quick Reference

**Creating a Dataset with License**:
```python
from tests.factories import DatasetFactory
from licensing.models import License

# Uses CC BY 4.0 by default
dataset = DatasetFactory()
assert dataset.license.name == "CC BY 4.0"

# Specify different license
cc0 = License.objects.get(name="CC0 1.0")
dataset = DatasetFactory(license=cc0)
```

**Adding DOI to Dataset**:
```python
from tests.factories import DatasetFactory, DatasetIdentifierFactory

dataset = DatasetFactory()

# Create DOI identifier
doi = DatasetIdentifierFactory(related=dataset, type="DOI", value="10.5061/dryad.12345")

# Access via convenience property
print(dataset.doi)  # "10.5061/dryad.12345"
```

**Linking Literature**:
```python
from tests.factories import (
    DatasetFactory,
    DatasetLiteratureRelationFactory,
    LiteratureItemFactory,
)

dataset = DatasetFactory()
paper = LiteratureItemFactory(title="XRF Analysis Methods", year=2024)

# Link with DataCite relationship type
relation = DatasetLiteratureRelationFactory(
    dataset=dataset, literature_item=paper, relationship_type="IsDocumentedBy"
)
```

## See Also

- Developer Guide > Testing > Factory Best Practices
- Developer Guide > Testing > Fixture Generation
- specs/006-core-datasets/quickstart.md
"""

import factory
from licensing.models import License

from fairdm.factories import MeasurementFactory, SampleFactory

# Import dataset-specific factories from core
from fairdm.factories.core import DatasetDescriptionFactory, DatasetFactory

from .models import CustomParentSample, CustomSample, ExampleMeasurement, RockSample, WaterSample

# ============================================================================
# Example 1: Basic Sample Factory
# ============================================================================


class CustomParentSampleFactory(SampleFactory):
    """
    Basic sample factory demonstrating minimal configuration.

    This is the simplest factory pattern - just specify fake data for
    your custom fields. The parent SampleFactory handles all base fields
    (name, uuid, dataset, project, etc.).
    """

    char_field = factory.Faker("word")

    class Meta:
        model = CustomParentSample


# ============================================================================
# Example 2: Comprehensive Sample Factory with All Field Types
# ============================================================================


class CustomSampleFactory(SampleFactory):
    """
    Comprehensive sample factory showing all common field types.

    This factory demonstrates how to use Faker providers for different
    Django field types. Use this as a reference when creating factories
    for your own sample models.
    """

    char_field = factory.Faker("word")
    text_field = factory.Faker("text")
    integer_field = factory.Faker("random_int")
    big_integer_field = factory.Faker("random_int")
    positive_integer_field = factory.Faker("random_int")
    positive_small_integer_field = factory.Faker("random_int")
    small_integer_field = factory.Faker("random_int")
    boolean_field = factory.Faker("boolean")
    date_field = factory.Faker("date")
    date_time_field = factory.Faker("date_time")
    time_field = factory.Faker("time")
    decimal_field = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    float_field = factory.Faker("random_int")

    class Meta:
        model = CustomSample


# ============================================================================
# Example 3: Measurement Factory
# ============================================================================


class ExampleMeasurementFactory(MeasurementFactory):
    """
    Measurement factory demonstrating measurement-specific patterns.

    Measurement factories inherit from MeasurementFactory which provides
    base fields. Always ensure measurements are linked to samples.
    """

    char_field = factory.Faker("word")
    text_field = factory.Faker("text")
    integer_field = factory.Faker("random_int")
    big_integer_field = factory.Faker("random_int")
    positive_integer_field = factory.Faker("random_int")
    positive_small_integer_field = factory.Faker("random_int")
    small_integer_field = factory.Faker("random_int")
    boolean_field = factory.Faker("boolean")
    date_field = factory.Faker("date")
    date_time_field = factory.Faker("date_time")
    time_field = factory.Faker("time")
    decimal_field = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    float_field = factory.Faker("random_int")

    class Meta:
        model = ExampleMeasurement


# ============================================================================
# Polymorphic Sample Factories (Feature 007)
# ============================================================================


class RockSampleFactory(SampleFactory):
    """
    Factory for RockSample demonstrating geological sample data patterns.

    This factory shows how to create rock samples with realistic test data
    for geological studies. Used in Feature 007 tests and demo data generation.

    See: Developer Guide > Testing > Sample Factories
    """

    rock_type = factory.Faker("random_element", elements=["igneous", "sedimentary", "metamorphic"])
    mineral_content = factory.Faker(
        "random_element",
        elements=[
            "Quartz, Feldspar, Mica",
            "Calcite, Dolomite",
            "Olivine, Pyroxene",
            "Chlorite, Garnet, Staurolite",
        ],
    )
    weight_grams = factory.Faker("pyfloat", left_digits=3, right_digits=2, positive=True, min_value=10, max_value=999)
    collection_date = factory.Faker("date_between", start_date="-2y", end_date="today")
    hardness_mohs = factory.Faker("pydecimal", left_digits=1, right_digits=1, positive=True, min_value=1, max_value=10)

    class Meta:
        model = RockSample


class WaterSampleFactory(SampleFactory):
    """
    Factory for WaterSample demonstrating water quality measurement patterns.

    This factory creates water samples with realistic environmental monitoring
    data. Used in Feature 007 tests and for generating demo datasets.

    See: Developer Guide > Testing > Sample Factories
    """

    water_source = factory.Faker("random_element", elements=["river", "lake", "groundwater", "ocean", "stream", "pond"])
    temperature_celsius = factory.Faker("pyfloat", left_digits=2, right_digits=1, min_value=0.1, max_value=35)
    ph_level = factory.Faker("pydecimal", left_digits=1, right_digits=2, min_value=4, max_value=10)
    turbidity_ntu = factory.Faker("pyfloat", left_digits=2, right_digits=1, min_value=0.1, max_value=100)
    dissolved_oxygen_mg_l = factory.Faker("pyfloat", left_digits=2, right_digits=2, min_value=0.1, max_value=15)
    conductivity_us_cm = factory.Faker("pyfloat", left_digits=4, right_digits=1, min_value=10, max_value=2000)

    class Meta:
        model = WaterSample


# ============================================================================
# Example 4: Dataset Factory Usage Examples (T155)
# ============================================================================


def example_dataset_with_default_license():
    """
    Example: Creating a dataset with CC BY 4.0 default license.

    The DatasetFactory automatically assigns CC BY 4.0 license if not specified.
    This encourages FAIR data principles and open science.
    """
    # Create dataset - automatically gets CC BY 4.0 license
    dataset = DatasetFactory()

    # Verify license
    assert dataset.license is not None
    assert dataset.license.name == "CC BY 4.0"

    return dataset


def example_dataset_with_custom_license():
    """
    Example: Creating a dataset with a different license.

    You can specify any license from the licensing.models.License model.
    Common choices: CC BY 4.0, CC0 1.0, CC BY-SA 4.0, etc.
    """
    # Get different license
    cc0_license = License.objects.get(name="CC0 1.0")

    # Create dataset with custom license
    dataset = DatasetFactory(license=cc0_license)

    assert dataset.license.name == "CC0 1.0"

    return dataset


# ============================================================================
# Example 5: DatasetIdentifier Factory Examples (T156)
# ============================================================================


def example_dataset_with_doi():
    """
    Example: Adding a DOI to a dataset using DatasetIdentifier.

    DOIs should always be created through DatasetIdentifier, not the
    reference field. This allows datasets to have multiple identifiers.
    """
    # Create dataset
    dataset = DatasetFactory()

    # Add DOI identifier
    doi = DatasetIdentifierFactory(related=dataset, type="DOI", value="10.5061/dryad.abc123")

    # Access DOI through convenience property
    assert dataset.doi == "10.5061/dryad.abc123"

    # Query datasets by DOI
    from fairdm.core.dataset.models import Dataset

    found = Dataset.objects.filter(identifiers__type="DOI", identifiers__value="10.5061/dryad.abc123").first()

    assert found == dataset

    return dataset


def example_dataset_with_multiple_identifiers():
    """
    Example: Adding multiple identifiers to a dataset.

    Datasets can have multiple identifiers of different types:
    DOI, ARK, Handle, etc. Each must be globally unique.
    """
    dataset = DatasetFactory()

    # Add DOI
    DatasetIdentifierFactory(related=dataset, type="DOI", value="10.5061/dryad.xyz789")

    # Add ARK
    DatasetIdentifierFactory(related=dataset, type="ARK", value="ark:/12345/fk2abc123")

    # Add Handle
    DatasetIdentifierFactory(related=dataset, type="Handle", value="20.500.12345/abc123")

    assert dataset.identifiers.count() == 3

    return dataset


# ============================================================================
# Example 6: DatasetLiteratureRelation Factory Examples (T157)
# ============================================================================


def example_dataset_with_literature_relation():
    """
    Example: Linking a dataset to a publication using DataCite relationship types.

    Use DatasetLiteratureRelation to create bidirectional links between
    datasets and publications with standardized relationship types.
    """
    from tests.factories import DatasetLiteratureRelationFactory, LiteratureItemFactory

    # Create dataset and publication
    dataset = DatasetFactory(name="XRF Analysis Dataset")

    paper = LiteratureItemFactory(
        title="X-Ray Fluorescence Analysis Methods for Geological Samples",
        authors="Smith, J.; Doe, A.; Johnson, B.",
        year=2024,
        doi="10.1000/journal.2024.123",
    )

    # Link with DataCite relationship type
    relation = DatasetLiteratureRelationFactory(
        dataset=dataset, literature_item=paper, relationship_type="IsDocumentedBy"
    )

    # Access related literature
    assert dataset.related_literature.count() == 1
    assert dataset.related_literature.first() == paper

    return dataset


def example_dataset_with_multiple_literature_relations():
    """
    Example: Linking a dataset to multiple publications with different relationship types.

    Common relationship types (DataCite Metadata Schema 4.4):
    - IsDocumentedBy: Paper describes the dataset
    - IsSupplementTo: Dataset supplements a paper
    - IsDerivedFrom: Dataset derived from another source
    - IsSourceOf: Dataset is source for another work
    """
    from tests.factories import DatasetLiteratureRelationFactory, LiteratureItemFactory

    dataset = DatasetFactory(name="Comprehensive Geological Study")

    # Methods paper
    methods_paper = LiteratureItemFactory(title="Field Collection Methods", year=2023)
    DatasetLiteratureRelationFactory(dataset=dataset, literature_item=methods_paper, relationship_type="IsDocumentedBy")

    # Results paper (dataset supplements this paper)
    results_paper = LiteratureItemFactory(title="Geological Formation Analysis Results", year=2024)
    DatasetLiteratureRelationFactory(dataset=dataset, literature_item=results_paper, relationship_type="IsSupplementTo")

    # Source dataset (this dataset derived from it)
    source_paper = LiteratureItemFactory(title="Original Field Survey Data", year=2022)
    DatasetLiteratureRelationFactory(dataset=dataset, literature_item=source_paper, relationship_type="IsDerivedFrom")

    assert dataset.related_literature.count() == 3

    return dataset


# ============================================================================
# Example 7: Complex Dataset with Complete Metadata
# ============================================================================


def example_complete_dataset():
    """
    Example: Creating a complete dataset with all metadata types.

    This demonstrates a realistic dataset with:
    - License (CC BY 4.0 default)
    - DOI identifier
    - Literature relation
    - Descriptions (abstract, methods)
    - Dates (created, published)
    - Samples and measurements
    """
    from tests.factories import (
        DatasetDateFactory,
        DatasetLiteratureRelationFactory,
        LiteratureItemFactory,
    )

    # Create base dataset
    dataset = DatasetFactory(
        name="Geological Survey 2024: XRF Analysis of Rock Samples",
        visibility=DatasetFactory._meta.model.Visibility.PUBLIC,
    )

    # Add DOI
    DatasetIdentifierFactory(related=dataset, type="DOI", value="10.5061/dryad.geo2024")

    # Add descriptions
    DatasetDescriptionFactory(
        related=dataset, type="Abstract", value="This dataset contains X-ray fluorescence (XRF) measurements..."
    )

    DatasetDescriptionFactory(
        related=dataset, type="Methods", value="Samples were collected using standard field procedures..."
    )

    # Add dates
    DatasetDateFactory(related=dataset, type="Created", value="2024-01-15")

    DatasetDateFactory(related=dataset, type="Published", value="2024-06-01")

    # Link literature
    paper = LiteratureItemFactory(title="XRF Analysis Protocols for Geological Samples", year=2024)
    DatasetLiteratureRelationFactory(dataset=dataset, literature_item=paper, relationship_type="IsDocumentedBy")

    # Add samples and measurements
    sample = CustomSampleFactory(dataset=dataset)
    ExampleMeasurementFactory(sample=sample)

    return dataset
