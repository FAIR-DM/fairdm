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

# Specify different license
cc0 = License.objects.get(name="CC0 1.0")
dataset = DatasetFactory(license=cc0)
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
- specs/004-core-datasets/quickstart.md
"""

import factory

from fairdm.factories import MeasurementFactory, SampleFactory

# Import dataset-specific factories from core
from .models import (
    CustomParentSample,
    CustomSample,
    ExampleMeasurement,
    RockSample,
    WaterSample,
)

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
    weight_grams = factory.Faker(
        "pyfloat",
        left_digits=3,
        right_digits=2,
        positive=True,
        min_value=10,
        max_value=999,
    )
    collection_date = factory.Faker("date_between", start_date="-2y", end_date="today")
    hardness_mohs = factory.Faker(
        "pydecimal",
        left_digits=1,
        right_digits=1,
        positive=True,
        min_value=1,
        max_value=10,
    )

    class Meta:
        model = RockSample


class WaterSampleFactory(SampleFactory):
    """
    Factory for WaterSample demonstrating water quality measurement patterns.

    This factory creates water samples with realistic environmental monitoring
    data. Used in Feature 007 tests and for generating demo datasets.

    See: Developer Guide > Testing > Sample Factories
    """

    water_source = factory.Faker(
        "random_element",
        elements=["river", "lake", "groundwater", "ocean", "stream", "pond"],
    )
    temperature_celsius = factory.Faker("pyfloat", left_digits=2, right_digits=1, min_value=0.1, max_value=35)
    ph_level = factory.Faker("pydecimal", left_digits=1, right_digits=2, min_value=4, max_value=10)
    turbidity_ntu = factory.Faker("pyfloat", left_digits=2, right_digits=1, min_value=0.1, max_value=100)
    dissolved_oxygen_mg_l = factory.Faker("pyfloat", left_digits=2, right_digits=2, min_value=0.1, max_value=15)
    conductivity_us_cm = factory.Faker("pyfloat", left_digits=4, right_digits=1, min_value=10, max_value=2000)

    class Meta:
        model = WaterSample


# ============================================================================
# Example 4: Contributor Factories (Feature 009)
# ============================================================================


class PersonFactory(factory.django.DjangoModelFactory):
    """
    Factory for Person (AUTH_USER_MODEL) demonstrating claimed/unclaimed patterns.

    FairDM uses Person as AUTH_USER_MODEL. There are two patterns:
    1. Claimed users (email + password) for interactive portal access
    2. Unclaimed contributors (name-only) for provenance tracking

    See: docs/portal-development/contributors.md
    """

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttribute(lambda obj: f"{obj.first_name.lower()}.{obj.last_name.lower()}@example.com")
    is_active = True  # Claimed users are active by default

    class Meta:
        from fairdm.contrib.contributors.models import Person

        model = Person

    @factory.post_generation
    def set_password(obj, create, extracted, **kwargs):
        """Set a usable password for claimed users."""
        if not create:
            return
        # For claimed users, set a default password
        obj.set_password("password123")
        obj.save()


class UnclaimedPersonFactory(factory.django.DjangoModelFactory):
    """
    Factory for unclaimed Person instances (provenance-only records).

    Unclaimed persons have:
    - No email address (email=None)
    - No usable password
    - is_active=False

    These are used when attributing work to someone without creating
    their portal account.
    """

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = None
    is_active = False

    class Meta:
        from fairdm.contrib.contributors.models import Person

        model = Person


class OrganizationFactory(factory.django.DjangoModelFactory):
    """
    Factory for Organization demonstrating organizational structures.

    Organizations can have:
    - ROR identifiers for institutional lookup
    - Parent-child hierarchies
    - Member affiliations with type-based permissions

    See: docs/portal-development/contributors.md#organizations
    """

    name = factory.Faker("company")
    location = factory.Faker("city")

    class Meta:
        from fairdm.contrib.contributors.models import Organization

        model = Organization


class AffiliationFactory(factory.django.DjangoModelFactory):
    """
    Factory for Affiliation demonstrating membership patterns.

    Affiliation type field determines permissions:
    - PENDING (0): Awaiting verification
    - MEMBER (1): Regular member
    - ADMIN (2): Administrative access
    - OWNER (3): Full control + manage_organization permission

    Example usage:
        # Create regular member
        affiliation = AffiliationFactory(type=Affiliation.MembershipType.MEMBER)

        # Create organization owner
        owner_affiliation = AffiliationFactory(
            type=Affiliation.MembershipType.OWNER,
            is_primary=True
        )
    """

    person = factory.SubFactory(PersonFactory)
    organization = factory.SubFactory(OrganizationFactory)
    type = 1  # MembershipType.MEMBER by default
    is_primary = False

    class Meta:
        from fairdm.contrib.contributors.models import Affiliation

        model = Affiliation
