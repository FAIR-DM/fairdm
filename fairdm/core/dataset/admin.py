from django.contrib import admin
from django.db import models
from django_select2.forms import Select2MultipleWidget, Select2Widget

from .models import Dataset, DatasetDate, DatasetDescription


class DescriptionInline(admin.StackedInline):
    """Inline admin for Dataset descriptions."""

    model = DatasetDescription
    extra = 0
    max_num = 6


class DateInline(admin.StackedInline):
    """Inline admin for Dataset dates."""

    model = DatasetDate
    extra = 0
    max_num = 6


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    """Admin interface for Dataset model.

    Provides search, filtering, and inline editing through the Django admin interface.
    Uses Select2 widgets for improved UX on foreign key and many-to-many fields.
    """

    inlines = [DescriptionInline, DateInline]
    search_fields = ("uuid", "name")
    list_display = ("name", "added", "modified")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "project",
                    "image",
                    "reference",
                    "visibility",
                    "tags",
                )
            },
        ),
    )
    formfield_overrides = {
        models.ManyToManyField: {"widget": Select2MultipleWidget},
        models.ForeignKey: {"widget": Select2Widget},
        models.OneToOneField: {"widget": Select2Widget},
    }
