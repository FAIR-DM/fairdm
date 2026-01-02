"""Filters for the Measurement app."""

from fairdm.core.filters import BaseListFilter

from .models import Measurement


class MeasurementFilter(BaseListFilter):
    """Filter for Measurement list views with search filtering."""

    class Meta:
        fields = []
        model = Measurement
