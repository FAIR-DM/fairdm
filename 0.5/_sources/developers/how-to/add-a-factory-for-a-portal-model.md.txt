# How to add a factory for a portal model

FairDM's `SampleFactory` and `MeasurementFactory` are abstract, because the base `Sample` and `Measurement` cannot be created. You add a factory for each sample or measurement type your portal defines, so tests and development data can create records of it with one call.

## Before you start

- The type exists and is registered. See [How to add a sample type](add-a-sample-type.md) or [How to add a measurement type](add-a-measurement-type.md).
- The examples use a sample type `PlantSample` with the fields `species`, `collected_on` and `dry_weight_g`, and a measurement type `ChlorophyllMeasurement` with a `reading` field. Both are in an app called `plants`. Use your own names.

## Steps

1. Create `plants/factories.py`. Keep it outside `tests/` if you want the `generate_fake_data` command to use it.

2. Subclass `SampleFactory`, name the model in `Meta`, and give a value to each field the model requires. The factory already fills in `name`, `local_id`, `status` and `dataset`.

   ```python
   import factory

   from fairdm.factories import MeasurementFactory, SampleFactory

   from .models import ChlorophyllMeasurement, PlantSample


   class PlantSampleFactory(SampleFactory):
       class Meta:
           model = PlantSample

       species = factory.Faker(
           "random_element",
           elements=["Quercus robur", "Fagus sylvatica", "Pinus sylvestris"],
       )
       collected_on = factory.Faker("date_between", start_date="-2y", end_date="today")
       dry_weight_g = factory.Faker(
           "pyfloat", left_digits=2, right_digits=1, min_value=1, max_value=99
       )
   ```

   A field that has a default, or may be blank or null, can be left out. A required field you leave out makes `create()` fail with the database's error.

3. Subclass `MeasurementFactory` for a measurement type. It gives `sample` no default, so declare one. Build the sample in the same dataset as the measurement.

   ```python
   class ChlorophyllMeasurementFactory(MeasurementFactory):
       class Meta:
           model = ChlorophyllMeasurement

       sample = factory.SubFactory(
           PlantSampleFactory, dataset=factory.SelfAttribute("..dataset")
       )
       reading = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
   ```

   `SelfAttribute("..dataset")` reads `dataset` from the measurement being built. A test that passes its own `dataset` or `sample` replaces the default.

4. Optionally, add a trait for a scenario you test often. A trait switches on with a keyword argument.

   ```python
   class PlantSampleFactory(SampleFactory):
       ...

       class Params:
           heavy = factory.Trait(dry_weight_g=95.0)
   ```

5. Use the factory in a test.

   ```python
   import pytest

   from plants.factories import ChlorophyllMeasurementFactory, PlantSampleFactory


   @pytest.mark.django_db
   def test_a_measurement_is_made_on_a_sample_of_its_dataset():
       measurement = ChlorophyllMeasurementFactory()

       assert measurement.sample.dataset == measurement.dataset


   @pytest.mark.django_db
   def test_a_sample_with_descriptions():
       sample = PlantSampleFactory(heavy=True, descriptions=2)

       assert sample.dry_weight_g == 95.0
       assert sample.descriptions.count() == 2
   ```

6. Optionally, list the factories in the `FAIRDM_FACTORIES` setting so `generate_fake_data` creates records of the type. The setting maps a model label to the dotted path of its factory, and is described in [Settings](../reference/settings.md).

   ```python
   FAIRDM_FACTORIES = {
       "plants.PlantSample": "plants.factories.PlantSampleFactory",
       "plants.ChlorophyllMeasurement": "plants.factories.ChlorophyllMeasurementFactory",
   }
   ```

## The result

`PlantSampleFactory()` creates a saved sample in a new private dataset, and `ChlorophyllMeasurementFactory()` creates a measurement on a sample of its own dataset. Both take the arguments every record factory takes, such as `descriptions=2` and `dates=1`. They are listed in the [factories reference](../reference/factories.md).

[How to test a portal with FairDM factories](test-a-portal-with-fairdm-factories.md) shows the factories in use. The [`generate_fake_data` command](../reference/management-commands.md#generate_fake_data) picks one of the listed factories at random for each sample or measurement it creates.
