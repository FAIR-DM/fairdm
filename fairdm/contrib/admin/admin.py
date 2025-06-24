from django.contrib import admin
from waffle.models import Flag, Sample, Switch

__all__ = ["MeasurementAdmin", "SampleAdmin"]


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    """
    Admin interface for Sample model.
    Inherits from SampleAdmin in fairdm.core.admin.
    """

    pass


@admin.register(Flag)
class FlagAdmin(admin.ModelAdmin):
    """
    Admin interface for Flag model.
    Inherits from Django's ModelAdmin.
    """

    pass


@admin.register(Switch)
class SwitchAdmin(admin.ModelAdmin):
    """
    Admin interface for Switch model.
    Inherits from Django's ModelAdmin.
    """

    list_display = ("name", "active")
    list_editable = ("active",)
    search_fields = ("name",)
    list_filter = ("active",)
    ordering = ("name",)
