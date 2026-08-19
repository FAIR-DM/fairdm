from django.contrib import admin

from .dataset.models import DatasetDate, DatasetDescription


class DescriptionInline(admin.StackedInline):
    model = DatasetDescription
    extra = 0
    max_num = 6


class DateInline(admin.StackedInline):
    model = DatasetDate
    extra = 0
    max_num = 6
