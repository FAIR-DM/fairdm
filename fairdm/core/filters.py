# import django_filters as df
from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as df

from .models import Measurement, Sample


class GenericSearchFilter(df.CharFilter):
    """
    A reusable search filter that searches across multiple fields specified in search_fields.
    Similar to Django admin's search_fields functionality.

    Usage:
        search = GenericSearchFilter(
            search_fields=['name', 'uuid', 'descriptions__value'],
            widget=forms.TextInput(attrs={"placeholder": _("Search...")})
        )
    """

    def __init__(self, search_fields=None, *args, **kwargs):
        """
        Initialize the generic search filter.

        Args:
            search_fields (list): List of field names to search across.
                                Field names can include relationship lookups (e.g., 'descriptions__value').
        """
        self.search_fields = search_fields or []
        super().__init__(*args, **kwargs)

    def filter(self, queryset, value):
        """
        Filter method that searches across all specified search_fields.

        Args:
            queryset: The queryset to filter
            value: The search term

        Returns:
            Filtered queryset
        """
        if not value or not self.search_fields:
            return queryset

        search_term = str(value).strip()
        if not search_term:
            return queryset

        search_query = Q()

        # Build OR query for all search fields
        for field in self.search_fields:
            search_query |= Q(**{f"{field}__icontains": search_term})

        return queryset.filter(search_query).distinct()


class BaseListFilter(df.FilterSet):
    """Filter that includes a title and ordering field which can be used to filter a list. These two filters are
    displayed at the top of the list itself and will not be displayed in the sidebar. A second form helper is used to
    render the top filters. This class should be used as a base class for all list filters in the project.
    """

    o = df.OrderingFilter(
        choices=(
            ("created", _("Oldest First")),
            ("-created", _("Newest First")),
            ("modified", _("Last Updated")),
            ("-modified", _("Recently Updated")),
        ),
        widget=forms.Select,
        empty_label=False,
        initial="-created",
    )


class SampleFilter(BaseListFilter):
    search = GenericSearchFilter(
        search_fields=["name", "uuid"],
        widget=forms.TextInput(attrs={"placeholder": _("Search samples...")}),
        label=_("Search"),
    )

    class Meta:
        model = Sample
        fields = ["status"]


class MeasurementFilter(BaseListFilter):
    search = GenericSearchFilter(
        search_fields=["name", "uuid"],
        widget=forms.TextInput(attrs={"placeholder": _("Search measurements...")}),
        label=_("Search"),
    )

    class Meta:
        fields = []
        model = Measurement
