from django.contrib import admin
from django.db import models
from django.utils.translation import gettext as _
from django_select2.forms import Select2MultipleWidget, Select2Widget
from import_export.admin import ImportExportActionModelAdmin
from polymorphic.admin import PolymorphicChildModelAdmin, PolymorphicChildModelFilter, PolymorphicParentModelAdmin

from fairdm.core.models import Measurement
from fairdm.utils.utils import get_subclasses

from .dataset.models import DatasetDate, DatasetDescription
from .models import Sample


class DescriptionInline(admin.StackedInline):
    model = DatasetDescription
    extra = 0
    max_num = 6


class DateInline(admin.StackedInline):
    model = DatasetDate
    extra = 0
    max_num = 6


@admin.register(Sample)
class BaseSampleAdmin(PolymorphicParentModelAdmin):
    base_model = Sample
    # child_models = [m["class"] for m in registry.samples]
    child_models = get_subclasses(Sample)
    list_display = ["sample_type", "name", "added"]
    exclude = ["options"]
    list_filter = (PolymorphicChildModelFilter,)

    def sample_type(self, obj):
        return obj._meta.verbose_name

    sample_type.short_description = "Type"


class SampleAdmin(ImportExportActionModelAdmin):
    model = Sample
    base_fieldsets = (
        (
            _("Basic information"),
            {
                "fields": (
                    ("name", "status"),
                    "local_id",
                    "dataset",
                    "keywords",
                    "options",
                )
            },
        ),
    )
    # show_in_index = True
    formfield_overrides = {
        models.ForeignKey: {"widget": Select2Widget},
        models.ManyToManyField: {"widget": Select2MultipleWidget},
    }


@admin.register(Measurement)
class MeasurementParentAdmin(PolymorphicParentModelAdmin):
    model = Measurement
    child_models = get_subclasses(Measurement)
    list_filter = (PolymorphicChildModelFilter,)


class MeasurementAdmin(PolymorphicChildModelAdmin):
    show_in_index = True
    base_model = Measurement
