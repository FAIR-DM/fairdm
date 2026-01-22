from django.contrib import admin
from polymorphic.admin import PolymorphicChildModelAdmin, PolymorphicChildModelFilter, PolymorphicParentModelAdmin

from fairdm.core.models import Measurement
from fairdm.utils.utils import get_subclasses

from .dataset.models import DatasetDate, DatasetDescription


class DescriptionInline(admin.StackedInline):
    model = DatasetDescription
    extra = 0
    max_num = 6


class DateInline(admin.StackedInline):
    model = DatasetDate
    extra = 0
    max_num = 6


# @admin.register(Measurement)
class MeasurementParentAdmin(PolymorphicParentModelAdmin):
    model = Measurement
    child_models = get_subclasses(Measurement)
    list_filter = (PolymorphicChildModelFilter,)


class MeasurementAdmin(PolymorphicChildModelAdmin):
    show_in_index = True
    base_model = Measurement
