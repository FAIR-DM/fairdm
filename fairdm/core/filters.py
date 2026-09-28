"""Base filter set shared by the core list pages."""

import django_filters
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as df


class BaseListFilter(df.FilterSet):
    """Base filter set for the core list pages, adding a "has image" filter."""

    image = django_filters.BooleanFilter(
        field_name="image",
        lookup_expr="isnull",
        exclude=True,
        label=_("Has image"),
    )
