"""Filters for the dataset list page."""

import django_filters
from django.utils.translation import gettext_lazy as _
from mvp.filters import SearchFilter, SortFilter

from fairdm.core.filters import BaseListFilter

from .models import Dataset


class DatasetFilter(BaseListFilter):
    """Filter for the dataset list, by licence, project, description type and date type.

    The project choices are the public projects plus any the requester holds at least the view
    level on. An anonymous visitor gets the public projects. A filterset built without a request
    offers every project. All filters combine with AND.

    The search matches the name, uuid, identifiers, descriptions and keywords. The sort
    offers date created, last update and name.

    Args:
        *args: Positional arguments passed to ``FilterSet``.
        **kwargs: Keyword arguments passed to ``FilterSet``.

    Attributes:
        q: Match any word against the fields above.
        o: Order the list.
        project: Filter by the dataset's project.
        description_type: Filter by the type of a description the dataset carries.
        date_type: Filter by the type of a date the dataset carries.

    Example:
        ```python
        filterset = DatasetFilter(
            data={"license": license_id, "project": project.id},
            queryset=Dataset.objects.all(),
        )
        ```
    """

    q = SearchFilter(
        fields=[
            "name",
            "uuid",
            "identifiers__value",
            "descriptions__value",
            "keywords__name",
        ]
    )

    o = SortFilter(
        options=[
            ("-added", _("Date created (newest first)"), "-added"),
            ("added", _("Date created (oldest first)"), "added"),
            ("-modified", _("Recently Updated"), "-modified"),
            ("name", _("Name A-Z"), "name"),
            ("-name", _("Name Z-A"), "-name"),
        ]
    )

    project = django_filters.ModelChoiceFilter(
        field_name="project",
        queryset=None,
        label="Project",
        help_text="Filter by associated project",
        empty_label="All projects",
    )

    description_type = django_filters.CharFilter(
        field_name="descriptions__type",
        lookup_expr="exact",
        label="Description Type",
        help_text="Filter by description type (e.g., ABSTRACT, METHODS)",
        distinct=True,  # Prevent duplicate results from joins
    )

    date_type = django_filters.CharFilter(
        field_name="dates__type",
        lookup_expr="exact",
        label="Date Type",
        help_text="Filter by date type (e.g., COLLECTED, PUBLISHED)",
        distinct=True,
    )

    class Meta:
        model = Dataset
        fields = {
            "license": ["exact"],
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from fairdm.contrib.contributors.choices import ContributionLevel
        from fairdm.core.models import Project

        if self.request and hasattr(self.request, "user"):
            queryset = Project.objects.get_visible()
            if self.request.user.is_authenticated:
                permitted = Project.objects.accessible_to(
                    self.request.user, ContributionLevel.VIEW
                )
                queryset = (queryset | permitted).distinct()
        else:
            queryset = Project.objects.all()

        self.filters["project"].queryset = queryset
