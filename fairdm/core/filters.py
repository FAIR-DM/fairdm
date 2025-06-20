# import django_filters as df
from django import forms
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as df

from .models import Dataset, Measurement, Project, Sample


class BaseListFilter(df.FilterSet):
    """Filter that includes a title and ordering field which can be used to filter a list. These two filters are
    displayed at the top of the list itself and will not be displayed in the sidebar. A second form helper is used to
    render the top filters. This class should be used as a base class for all list filters in the project.
    """

    o = df.OrderingFilter(
        fields=(
            ("created", "created"),
            ("modified", "modified"),
        ),
        field_labels={
            "created": _("Created"),
            "modified": _("Modified"),
        },
        widget=forms.Select,
        empty_label=_("Order by"),
    )


class ProjectFilter(BaseListFilter):
    class Meta:
        model = Project
        fields = {
            "name": ["icontains"],
            "status": ["exact"],
        }


class DatasetFilter(BaseListFilter):
    class Meta:
        model = Dataset
        fields = {
            "name": ["icontains"],
            "license": ["exact"],
        }


class SampleFilter(BaseListFilter):
    name = df.CharFilter(lookup_expr="icontains", widget=forms.TextInput(attrs={"placeholder": _("Search...")}))

    class Meta:
        model = Sample
        fields = ["name", "status"]


class MeasurementFilter(BaseListFilter):
    name = df.CharFilter(lookup_expr="icontains", widget=forms.TextInput(attrs={"placeholder": _("Search...")}))

    class Meta:
        fields = ["name"]
        model = Measurement
