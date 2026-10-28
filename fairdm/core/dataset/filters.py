"""Filters for the dataset list page."""

import django_filters
from django.utils.translation import gettext_lazy as _
from mvp.filters import SearchFilter, SortFilter

from fairdm.contrib.autocomplete.fields import ProjectMultipleChoiceField
from fairdm.contrib.autocomplete.filters import RecordMultipleFilter
from fairdm.core.filters import BaseListFilter

from .models import Dataset


class DatasetFilter(BaseListFilter):
    """Filter for the dataset list, by licence, project, description type and date type.

    The project filter is a ``RecordMultipleFilter`` at public scope, so everyone is offered the
    same public projects. Ticking several keeps the datasets of any of them. All filters combine
    with AND.

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
            "keywords__search_text",
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

    project = RecordMultipleFilter(
        ProjectMultipleChoiceField,
        field_name="project",
        help_text=_("Filter by associated project"),
    )

    description_type = django_filters.CharFilter(
        field_name="descriptions__type",
        lookup_expr="exact",
        label="Description Type",
        help_text="Filter by the address of a description type",
        distinct=True,  # Prevent duplicate results from joins
    )

    date_type = django_filters.CharFilter(
        field_name="dates__type",
        lookup_expr="exact",
        label="Date Type",
        help_text="Filter by the address of a date type",
        distinct=True,
    )

    class Meta:
        model = Dataset
        fields = {
            "license": ["exact"],
        }
