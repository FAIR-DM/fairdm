"""Filters for the Measurement app."""

import django_filters as df
from django import forms
from django.utils.translation import gettext_lazy as _

from fairdm.core.filters import BaseListFilter

from .models import Measurement


class MeasurementFilter(BaseListFilter):
    """Filter for Measurement list views.

    Provides filtering by name (case-insensitive contains) for measurements.
    """

    name = df.CharFilter(lookup_expr="icontains", widget=forms.TextInput(attrs={"placeholder": _("Search...")}))

    class Meta:
        fields = ["name"]
        model = Measurement
