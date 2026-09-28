"""Admin registration for the test-only concrete models."""

from django.contrib import admin

from fairdm.core.measurement.admin import MeasurementChildAdmin
from fairdm.core.sample.admin import SampleChildAdmin

from .models import ConcreteMeasurement, ConcreteSample


@admin.register(ConcreteSample)
class ConcreteSampleAdmin(SampleChildAdmin):
    base_model = ConcreteSample


@admin.register(ConcreteMeasurement)
class ConcreteMeasurementAdmin(MeasurementChildAdmin):
    base_model = ConcreteMeasurement
