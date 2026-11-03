"""Concrete Sample and Measurement subclasses for the registry test suite."""

from django.db import models
from polymorphic.managers import PolymorphicManager

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


class ProxyMeasurementManager(PolymorphicManager):
    """Reach every record of the proxied type, as a proxy's own manager does in a portal."""

    def get_queryset(self):
        """Leave out polymorphic's filter to records saved through the proxy itself."""
        return self.queryset_class(self.model, using=self._db)


class ProxyMeasurement(ConcreteMeasurement):
    """A proxy of a registered measurement type."""

    objects = ProxyMeasurementManager()

    class Meta:
        proxy = True
        app_label = "registry_models"
        verbose_name = "proxy measurement"


class PlainProxyMeasurement(ConcreteMeasurement):
    """A proxy on polymorphic's own manager, which reaches only records saved through it."""

    class Meta:
        proxy = True
        app_label = "registry_models"
        verbose_name = "plain proxy measurement"
