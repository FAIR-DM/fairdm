"""Filters for the Measurement app."""

from django import forms
from django.utils.translation import gettext_lazy as _

from fairdm.core.filters import BaseListFilter, GenericSearchFilter

from .models import Measurement


class MeasurementFilter(BaseListFilter):
    """Filter for Measurement list views with search filtering."""

    search = GenericSearchFilter(
        search_fields=["name", "uuid"],
        widget=forms.TextInput(attrs={"placeholder": _("Search measurements...")}),
        label=_("Search"),
    )

    class Meta:
        fields = []
        model = Measurement
