"""Admin inlines for the dataset description and date rows."""

from django.contrib import admin

from .dataset.models import DatasetDate, DatasetDescription


class DescriptionInline(admin.StackedInline):
    """Inline for the descriptions attached to a dataset."""

    model = DatasetDescription
    extra = 0
    max_num = 6


class DateInline(admin.StackedInline):
    """Inline for the dates attached to a dataset."""

    model = DatasetDate
    extra = 0
    max_num = 6
