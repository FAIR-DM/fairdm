"""Filters for the Sample app."""

from fairdm.core.filters import BaseListFilter

from .models import Sample


class SampleFilter(BaseListFilter):
    """Filter for Sample list views with search and status filtering."""

    class Meta:
        model = Sample
        fields = ["status"]
