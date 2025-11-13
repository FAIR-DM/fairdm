"""Filters for the Sample app."""

from django import forms
from django.utils.translation import gettext_lazy as _

from fairdm.core.filters import BaseListFilter, GenericSearchFilter

from .models import Sample


class SampleFilter(BaseListFilter):
    """Filter for Sample list views with search and status filtering."""

    search = GenericSearchFilter(
        search_fields=["name", "uuid"],
        widget=forms.TextInput(attrs={"placeholder": _("Search samples...")}),
        label=_("Search"),
    )

    class Meta:
        model = Sample
        fields = ["status"]
