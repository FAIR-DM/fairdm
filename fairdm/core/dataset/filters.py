"""Filters for the Dataset app."""

from fairdm.core.filters import BaseListFilter

from .models import Dataset


class DatasetFilter(BaseListFilter):
    """Filter for Dataset list views with name and license filtering."""

    class Meta:
        model = Dataset
        fields = {
            "name": ["icontains"],
            "license": ["exact"],
        }
