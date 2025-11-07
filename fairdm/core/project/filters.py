"""Filters for the Project app."""

from fairdm.core.filters import BaseListFilter

from .models import Project


class ProjectFilter(BaseListFilter):
    """Filter for Project list views with name and status filtering."""

    class Meta:
        model = Project
        fields = {
            "name": ["icontains"],
            "status": ["exact"],
        }
