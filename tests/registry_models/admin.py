"""Admin registration for the test-only concrete models.

`MeasurementParentAdmin.child_models` is built from `get_subclasses(Measurement)`
at import time, so these models appear in the polymorphic parent admin whether or
not they are registered with the FairDM registry. Registering them here gives the
`registry_models` app an admin URL, without which the parent admin's add page
cannot reverse `app_list` for them.
"""

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
