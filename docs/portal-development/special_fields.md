# Special Fields

In addition to Django's standard database fields, FairDM provides custom fields that are particularly useful for research data. These fields extend Django's capabilities to handle scientific data types and research-specific requirements.

## QuantityField

The `QuantityField` stores numeric values alongside units of measurement and enables unit conversions.

```python
from fairdm.db import models

class TemperatureMeasurement(Measurement):
    temperature = models.QuantityField(
        "degC",
        unit_choices=["degF", "K"],
        help_text="Temperature reading with units"
    )
    
    # Example usage:
    # measurement.temperature = Quantity(25.5, 'degC')
    # converted = measurement.temperature.to('degF')
```

### Features
- Stores value and unit together
- Automatic unit validation
- Unit conversion capabilities
- Integration with scientific libraries

### Editing a quantity

On a form, a quantity field is a number box with a unit list beside it. The list offers the
field's base units and every unit in `unit_choices`. A value entered in any of them is converted
and stored in the base units, and an edit form shows the stored value in the base units, so a
form saved without changes keeps the value it had.

The model fields pick their form field themselves: `fairdm.forms.fields.QuantityFormField`,
`IntegerQuantityFormField` or `DecimalQuantityFormField`. Each is django-pint's form field of the
same name, changed only in how it shows a stored value. That change is
`fairdm.forms.fields.QuantityFormFieldMixin`, which a form field built on another of
django-pint's quantity form fields can mix in for the same behaviour.

## ConceptField

The `ConceptField` links to controlled vocabulary concepts, ensuring data consistency and enabling semantic search.

```python
from research_vocabs.fields import ConceptField
from fairdm.core.vocabularies import SampleTypes

class WaterSample(Sample):
    sample_type = ConceptField(
        vocabulary=SampleTypes,
        help_text="Type of water sample"
    )
```

### Features
- Links to controlled vocabularies
- Ensures data consistency
- Enables semantic queries
- Supports hierarchical vocabularies

## TaggableConcepts

A generic relationship that allows tagging any model with concepts from controlled vocabularies.

```python
from fairdm.db import models

class Sample(BaseModel):
    # Generic relation for tagging
    concepts = models.TaggableConcepts()
    
    # Usage:
    # sample.concepts.add(concept1, concept2)
    # sample.concepts.filter(vocabulary='keywords')
```

### Features
- Generic tagging system
- Multiple vocabulary support
- Flexible keyword management
- Queryable relationships

## PartialDateField  

The `PartialDateField` stores dates with associated uncertainty levels, useful for historical or estimated dates.

```python
from fairdm.db.fields import PartialDateField

class HistoricalSample(Sample):
    collection_date = PartialDateField(
        help_text="Approximate collection date"
    )
    
    # Example usage:
    # sample.collection_date = PartialDate(
    #     date=datetime.date(2020, 6, 15),
    #     precision='month'  # day, month, year, decade, century
    # )
```

### Features
- Stores date with precision indicator
- Handles uncertain/approximate dates
- Useful for historical data
- Queryable by precision level

## Custom Field Usage in Registration

When using special fields in your models, they work seamlessly with the registration system:

```python
from fairdm.core.sample.models import Sample
from fairdm.db import models
from research_vocabs.fields import ConceptField

class AdvancedSample(Sample):
    temperature = models.QuantityField("degC")
    sample_type = ConceptField(vocabulary="sample_types")
    collection_date = models.PartialDateField()

@fairdm.register
class AdvancedSampleConfig(fairdm.SampleConfig):
    model = AdvancedSample
    list_fields = ["name", "temperature", "sample_type", "collection_date"]
    detail_fields = ["name", "temperature", "sample_type", "collection_date", "location"]
    filter_fields = ["sample_type", "collection_date"]
```

`location` is a field every sample already has: the point where it was taken, with
`location_elevation` and `location_uncertainty` beside it. It is not one of the special fields
this page covers, so a sample type does not declare it. See [Locations](locations.md).

The registration system automatically:
- Generates appropriate form widgets for special fields
- Creates filters that understand field semantics
- Handles display formatting in tables
- Provides proper serialization for APIs

## Field Considerations

### Performance
- ConceptFields create database relationships - consider indexing
- QuantityFields store structured data - may impact query performance
- TaggableConcepts create many-to-many relationships

### Validation
- Special fields include built-in validation
- ConceptFields validate against vocabularies
- QuantityFields validate units
- PartialDateFields validate precision levels

### Import/Export
- Special fields have custom serialization
- Import templates handle field-specific formats
- Export includes field metadata
- Unit conversions preserved during import/export

### API Integration
- REST API endpoints handle special field serialization
- GraphQL schema includes field-specific types
- OpenAPI documentation describes field constraints
- Client libraries understand field semantics