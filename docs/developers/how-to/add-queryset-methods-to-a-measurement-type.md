# How to add queryset methods to a measurement type

A queryset method gives a query you repeat a name, such as "the laser diffraction results". You add one to a measurement type's manager, and it chains with the filters and loaders that every measurement queryset has.

## Before you start

You need a measurement type. This guide uses `GrainSizeMeasurement` from [How to add a measurement type](add-a-measurement-type.md).

## Steps

1. Subclass `MeasurementQuerySet` and add your methods. Each method returns a queryset.

   ```python
   # sediments/models.py
   from fairdm.core.measurement.managers import MeasurementQuerySet


   class GrainSizeQuerySet(MeasurementQuerySet):
       def by_method(self, method):
           return self.filter(method__iexact=method)

       def with_uncertainty(self):
           return self.exclude(uncertainty__isnull=True)
   ```

   Subclassing `MeasurementQuerySet`, not `QuerySet`, keeps `with_related()`, `with_metadata()`, the location lookups and the visibility methods. They are listed on [Measurement model](../reference/measurement-model.md#queryset).

2. Attach the queryset to the model as its manager. Define the queryset above the model.

   ```python
   class GrainSizeMeasurement(Measurement):
       # ... fields ...

       objects = GrainSizeQuerySet.as_manager()
   ```

   FairDM turns the manager into a polymorphic one, so a query on the type still returns the right subclass.

3. Chain your methods with the built-in ones.

   ```python
   GrainSizeMeasurement.objects.by_method("laser diffraction").with_uncertainty().with_related()
   ```

## The result

`GrainSizeMeasurement.objects` has your methods and the methods of `MeasurementQuerySet`. A queryset method adds no column, so it needs no migration.

Load related records with `with_related()` on a list, so each row does not cost extra queries. Use `with_metadata()` where the page shows descriptions, dates or identifiers.
