# import django_filters as df
from django_filters import rest_framework as df

from .models import Measurement, Sample


class BaseListFilter(df.FilterSet):
    """Filter that includes a title and ordering field which can be used to filter a list. These two filters are
    displayed at the top of the list itself and will not be displayed in the sidebar. A second form helper is used to
    render the top filters. This class should be used as a base class for all list filters in the project.
    """


class SampleFilter(BaseListFilter):
    class Meta:
        model = Sample
        fields = ["status"]


class MeasurementFilter(BaseListFilter):
    class Meta:
        fields = []
        model = Measurement
