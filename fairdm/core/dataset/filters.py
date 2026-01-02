"""Filters for the Dataset app."""

from fairdm.core.filters import BaseListFilter

from .models import Dataset


class DatasetFilter(BaseListFilter):
    """Filter for Dataset list views with name, license, and generic search filtering."""

    class Meta:
        model = Dataset
        fields = {
            "license": ["exact"],
        }
