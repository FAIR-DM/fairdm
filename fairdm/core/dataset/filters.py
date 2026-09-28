"""Filters for the dataset list page."""

import django_filters

from fairdm.core.filters import BaseListFilter

from .models import Dataset


class DatasetFilter(BaseListFilter):
    """Filter for the dataset list, by licence, project, description type and date type.

    The project choices are the public projects plus any the requester holds ``view_project``
    on at record level. This differs from the creation form's contribution-based rule, because an
    anonymous visitor must also get a usable queryset. A filterset built without a request offers
    every project. All filters combine with AND.

    The list's text search is the page's own ``?q=`` control, not a filter on this class.

    Args:
        *args: Positional arguments passed to ``FilterSet``.
        **kwargs: Keyword arguments passed to ``FilterSet``.

    Attributes:
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

        from fairdm.core.models import Project
        from fairdm.core.utils import get_objects_for_user

        if self.request and hasattr(self.request, "user"):
            queryset = Project.objects.get_visible()
            if self.request.user.is_authenticated:
                permitted = get_objects_for_user(
                    self.request.user,
                    "project.view_project",
                    Project.objects.all(),
                )
                queryset = (queryset | permitted).distinct()
        else:
            queryset = Project.objects.all()

        self.filters["project"].queryset = queryset
