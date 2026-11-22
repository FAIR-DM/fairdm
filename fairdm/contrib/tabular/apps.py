"""Importing and exporting a dataset's samples and measurements as spreadsheets (prototype)."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TabularConfig(AppConfig):
    name = "fairdm.contrib.tabular"
    label = "tabular"
    verbose_name = _("Spreadsheet import and export")
    default_auto_field = "django.db.models.BigAutoField"
