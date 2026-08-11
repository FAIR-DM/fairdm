# import django_filters as df
import django_filters
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as df


class BaseListFilter(df.FilterSet):
    """Filter that includes a title and ordering field which can be used to filter a list. These two filters are
    displayed at the top of the list itself and will not be displayed in the sidebar. A second form helper is used to
    render the top filters. This class should be used as a base class for all list filters in the project.
    """

    image = django_filters.BooleanFilter(
        field_name="images",
        lookup_expr="isnull",
        exclude=True,
        label=_("Has image"),
    )
