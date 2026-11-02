# How to register a sample or measurement type

Registering a type tells FairDM to build the type's form, table, filter set, serializer, resource and administration page, and to add the type to the portal's menus and API. You do it once for each sample or measurement type, after you define its model.

## Before you start

You need a portal app listed in `fairdm.setup(apps=[...])`, with the type's model defined and migrated. See [How to add a sample type](add-a-sample-type.md) or [How to add a measurement type](add-a-measurement-type.md). This guide uses an app named `fieldwork` with these two models:

```python
# fieldwork/models.py
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.db import models


class PlantSample(Sample):
    species = models.CharField(max_length=200)
    collected_on = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Plant Sample"
        verbose_name_plural = "Plant Samples"


class LeafAreaMeasurement(Measurement):
    value = models.FloatField(help_text="Leaf area in square centimetres.")
    uncertainty = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Leaf Area Measurement"
        verbose_name_plural = "Leaf Area Measurements"
```

## Steps

1. Create a module named `config.py` in the app. FairDM imports the module of this name in every installed app when the portal starts, so the name is what makes it found.

2. Declare the configuration. Subclass the base configuration for the kind of type, name the model and list the fields that every component uses. Start from the base list, which keeps the fields every sample or measurement has.

   For a sample type:

   ```python
   # fieldwork/config.py
   from fairdm.core.sample.config import BaseSampleConfiguration
   from fairdm.registry import register

   from .models import PlantSample


   @register
   class PlantSampleConfig(BaseSampleConfiguration):
       model = PlantSample
       fields = [
           *BaseSampleConfiguration.fields,
           "species",
           "collected_on",
           "notes",
       ]
   ```

   For a measurement type:

   ```python
   # fieldwork/config.py
   from fairdm.core.measurement.config import BaseMeasurementConfiguration
   from fairdm.registry import register

   from .models import LeafAreaMeasurement


   @register
   class LeafAreaMeasurementConfig(BaseMeasurementConfiguration):
       model = LeafAreaMeasurement
       fields = [
           *BaseMeasurementConfiguration.fields,
           "value",
           "uncertainty",
       ]
   ```

   A measurement type lists `name`, `sample` and `dataset` too, because its serializer, resource and administration page read only `fields`. The base list holds them.

3. Restart the portal. A registration is checked as the module is imported, and a mistake stops the start with a message that names the model, the option and the name that failed.

4. Check that the registry holds the type.

   ```bash
   python manage.py shell -c "from fairdm.registry import registry; print(registry.is_registered('fieldwork.plantsample'))"
   ```

## The result

The command prints `True`. The portal has these for each type:

- a listing page at `/collections/samples/plantsample/` or `/collections/measurements/leafareameasurement/`, with an entry under **Samples** or **Measurements** in the menu
- a form, a table and a filter set
- an administration page, in the group named after the app
- API endpoints at `/api/v1/samples/plant-samples/` and `/api/v1/measurements/leaf-area-measurements/`

The listing shows records from published datasets only. See [What registering a type produces](../explanation/what-registering-a-type-produces.md).

The options of a configuration are on [Model configuration](../reference/model-configuration.md), and the registry is on [The registry](../reference/registry.md). To change one generated part, see [How to customise a generated component](customise-a-generated-component.md).
