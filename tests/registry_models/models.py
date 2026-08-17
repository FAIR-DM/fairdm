"""Concrete Sample and Measurement subclasses for the registry test suite.

These stand in for the types a portal defines itself. They are declared once, in a
real installed app, because a model under an uninstalled label breaks admin and URL
resolution for every later test in the session.
"""

from django.db import models

from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample


class ConcreteSample(Sample):
    """A concrete Sample subclass, the shape a portal actually registers."""

    rock_type = models.CharField(max_length=100, blank=True)

    class Meta:
        app_label = "registry_models"
        verbose_name = "concrete sample"


class ConcreteMeasurement(Measurement):
    """A concrete Measurement subclass, the shape a portal actually registers."""

    reading = models.FloatField(null=True, blank=True)

    class Meta:
        app_label = "registry_models"
        verbose_name = "concrete measurement"
