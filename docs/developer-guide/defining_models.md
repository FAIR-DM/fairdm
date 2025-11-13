# Defining a model

Declare fields and validators for your database tables in a familiar, easy-to-understand syntax according to the exact specifications required by your research community. With FairDM, the most important data structures are defined by you so there is no need to adapt your requirements to fit a structure defined by somebody else. FairDM provides a base `Measurement` class that you can extend to define your own data structures. This class allows you to leverage the full power of Django's model layer while also providing necessary metadata to properly describe your measuremenet. 

Unlike text-based, NoSQL alternatives, all fields listed in your measurement classes will directly alter your database schema, allowing you to harness the full capabilities of your underlying PostgreSQL database. Additionally, you can use Django's built-in ORM to interact with your database tables, making it easy to query, filter, and manipulate your data.


## Additional Fields

In addition to Django's standard database fields, FairDM provides custom fields that are particularly useful for reasearch data:

- `QuantityField`: A numeric field that also stores basic units of measurement (e.g. meters, seconds, etc.) alongside the value and allows you to perform unit conversions.
- `ConceptField`: A field that stores a concept from a controlled vocabulary.
- `TaggableConcepts`: A generic relationship that allows you to tag any model with concepts from a controlled vocabulary. Great for keyword tagging.
- `PartialDateField`: A field that stores a date with an associated level of uncertainty.

See [Special Fields](special_fields.md) for detailed information on using these fields.

## Sample Models

Sample models represent physical or digital objects that are part of a dataset. They inherit from the base `Sample` class:

```python
from fairdm.core.sample.models import Sample
from django.db import models

class WaterSample(Sample):
    location = models.CharField(max_length=200)
    ph_level = models.FloatField()
    temperature = models.FloatField()
    collected_at = models.DateTimeField()
    
    class Meta:
        verbose_name = "Water Sample"
        verbose_name_plural = "Water Samples"
```

## Measurement Models  

Measurement models represent observations or calculations made on samples. They inherit from the base `Measurement` class:

```python
from fairdm.core.measurement.models import Measurement
from django.db import models

class TemperatureMeasurement(Measurement):
    value = models.FloatField()
    unit = models.CharField(max_length=50, default="celsius")
    uncertainty = models.FloatField(null=True, blank=True)
    method = models.CharField(max_length=100)
    equipment = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = "Temperature Measurement"
        verbose_name_plural = "Temperature Measurements"
```

## Next Steps

After defining your models, you'll need to register them with FairDM to make them available in the interface. See [Model Configuration](model_configuration.md) for detailed instructions on how to register your Sample and Measurement models with auto-generated forms, tables, filters, and API endpoints.