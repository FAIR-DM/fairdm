"""Concrete Sample and Measurement subclasses for the registry test suite."""

from django.db import models

from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.db.fields import QuantityField


class ConcreteSample(Sample):
    """A concrete Sample subclass, the shape a portal actually registers."""

    rock_type = models.CharField(max_length=100, blank=True)

    class Meta:
        app_label = "registry_models"
        verbose_name = "concrete sample"


class ConcreteMeasurement(Measurement):
    """A concrete Measurement subclass, the shape a portal actually registers."""

    reading = models.FloatField(null=True, blank=True)
    depth = QuantityField("m", unit_choices=["km"], null=True, blank=True)

    class Meta:
        app_label = "registry_models"
        verbose_name = "concrete measurement"
