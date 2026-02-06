import django_filters as df
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Contributor


class PersonFilter(df.FilterSet):
    is_active = df.BooleanFilter(
        label=_("Active Only"),
        initial=False,
    )
    is_staff = df.BooleanFilter(
        label=_("Portal Administrators"),
        initial=False,
    )
    name = df.CharFilter(
        label=_("Contributor Name"),
        lookup_expr="icontains",
    )
    city = df.CharFilter(label=_("City"), field_name="affiliations__city", lookup_expr="icontains")
    country = df.CharFilter(label=_("Country"), field_name="affiliations__country", lookup_expr="icontains")
    affiliation = df.CharFilter(
        label=_("Affiliation"),
        field_name="affiliations__organization__name",
        lookup_expr="icontains",
    )

    class Meta:
        model = Contributor
        fields = ["is_active", "is_staff", "name", "city", "country"]


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

    class Meta:
        model = Contributor
        fields = ["name", "city", "country"]


class ContributorFilter(df.FilterSet):
    name = df.CharFilter(
        lookup_expr="icontains",
        widget=forms.TextInput(attrs={"placeholder": "Find a contributor..."}),
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
        fields = ["name", "type"]

    def filter_type(self, queryset, name, value):
        if value == "active":
            return queryset.active()
        elif value == "persons":
            return queryset.persons()
        elif value == "organizations":
            return queryset.organizations()
        return queryset
