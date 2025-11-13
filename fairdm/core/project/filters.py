"""Filters for the Project app."""

import django_filters as df
from django import forms
from django.utils.translation import gettext_lazy as _

from fairdm.core.filters import BaseListFilter, GenericSearchFilter

from .models import Project


class ProjectFilter(BaseListFilter):
    """Filter for Project list views with name, status, and generic search filtering."""

    # Override the ordering field to include project-specific options
    o = df.OrderingFilter(
        choices=(
            ("-created", _("Newest First")),
            ("created", _("Oldest First")),
            ("-modified", _("Recently Updated")),
            ("name", _("Name A-Z")),
            ("-name", _("Name Z-A")),
        ),
        widget=forms.Select,
        empty_label=False,
        initial="-created",
    )

    search = GenericSearchFilter(
        search_fields=["name", "uuid", "descriptions__value"],
        widget=forms.TextInput(attrs={"placeholder": _("Search projects...")}),
        label=_("Search"),
    )

    class Meta:
        model = Project
        fields = {
            "status": ["exact"],
        }
