"""Factories for the models defined in tests/registry_models."""

import factory
from factory.django import DjangoModelFactory

from fairdm.contrib.import_export.models import ImportJob, ImportRow
from fairdm.factories import DatasetFactory
from tests.registry_models.models import ConcreteMeasurement, ConcreteSample


class ConcreteSampleFactory(DjangoModelFactory):
    """Build a ConcreteSample. Vary it by overriding fields at the call site."""

    class Meta:
        model = ConcreteSample

    name = factory.Sequence(lambda n: f"concrete-sample-{n}")


class ConcreteMeasurementFactory(DjangoModelFactory):
    """Build a ConcreteMeasurement."""

    class Meta:
        model = ConcreteMeasurement

    reading = factory.Sequence(lambda n: float(n))


class ImportJobFactory(DjangoModelFactory):
    """Build a checked ImportJob of rock samples. Vary it by overriding fields.

    No file is stored unless a test asks for one: ``ImportJobFactory(with_file=True)``.
    """

    class Meta:
        model = ImportJob

    class Params:
        with_file = factory.Trait(
            file=factory.django.FileField(filename="rocks.csv", data=b"name\nA\n"),
        )

    dataset = factory.SubFactory(DatasetFactory)
    definition_name = "rocksample"
    filename = "rocks.csv"
    file_format = "csv"
    status = ImportJob.Status.CHECKED


class ImportRowFactory(DjangoModelFactory):
    """Build one ImportRow of a job, numbered in the order the rows are built."""

    class Meta:
        model = ImportRow

    job = factory.SubFactory(ImportJobFactory)
    number = factory.Sequence(lambda n: n + 1)
    line = factory.LazyAttribute(lambda row: row.number + 1)
    outcome = ImportRow.Outcome.NEW
