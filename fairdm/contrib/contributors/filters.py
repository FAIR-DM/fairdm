import django_filters as df
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Contributor


class PersonFilter(df.FilterSet):
    name = df.CharFilter(lookup_expr="icontains", label=_("Name"))
    city = df.CharFilter(label=_("City"), field_name="affiliations__city", lookup_expr="icontains")
    country = df.CharFilter(label=_("Country"), field_name="affiliations__country", lookup_expr="icontains")

    o = df.OrderingFilter(
        fields=(
            ("created", "created"),
            ("modified", "modified"),
        ),
        field_labels={
            "created": _("Created"),
            "modified": _("Modified"),
        },
        label=_("Sort by"),
        widget=forms.Select,
        empty_label=_("Order by"),
    )

    class Meta:
        model = Contributor
        fields = ["name", "city", "country", "o"]


class OrganizationFilter(df.FilterSet):
    name = df.CharFilter(lookup_expr="icontains", label=_("Name"))

    city = df.CharFilter(
        lookup_expr="icontains",
        label=_("City"),
    )
    country = df.CharFilter(
        lookup_expr="icontains",
        label=_("Country"),
    )

    o = df.OrderingFilter(
        fields=(
            ("created", "created"),
            ("modified", "modified"),
        ),
        field_labels={
            "created": _("Created"),
            "modified": _("Modified"),
        },
        label=_("Sort by"),
        widget=forms.Select,
        empty_label=_("Order by"),
    )

    class Meta:
        model = Contributor
        fields = ["name", "city", "country", "o"]


class ContributorFilter(df.FilterSet):
    name = df.CharFilter(
        lookup_expr="icontains",
        widget=forms.TextInput(attrs={"placeholder": "Find a contributor..."}),
    )

    o = df.OrderingFilter(
        fields=(
            ("created", "created"),
            ("modified", "modified"),
        ),
        field_labels={
            "created": _("Created"),
            "modified": _("Modified"),
        },
        label=_("Sort by"),
        widget=forms.Select,
        empty_label=_("Order by"),
    )

    type = df.ChoiceFilter(
        choices=[
            ("active", "Active"),
            ("persons", "Persons"),
            ("organizations", "Organizations"),
        ],
        label=_("Type"),
        method="filter_type",
        widget=forms.Select,
        empty_label=_("Type"),
    )

    class Meta:
        model = Contributor
        fields = ["name", "o", "type"]

    def filter_type(self, queryset, name, value):
        if value == "active":
            return queryset.active()
        elif value == "persons":
            return queryset.persons()
        elif value == "organizations":
            return queryset.organizations()
        return queryset
