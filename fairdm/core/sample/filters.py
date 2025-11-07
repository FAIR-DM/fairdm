"""Filters for the Sample app."""

import django_filters as df
from django import forms
from django.utils.translation import gettext_lazy as _

from fairdm.core.filters import BaseListFilter

from .models import Sample


class SampleFilter(BaseListFilter):
    """Filter for Sample list views.

    Provides filtering by name (case-insensitive contains) and status.
    """

    name = df.CharFilter(lookup_expr="icontains", widget=forms.TextInput(attrs={"placeholder": _("Search...")}))

    class Meta:
        model = Sample
        fields = ["name", "status"]
