"""Filtersets for the literature listing."""

import django_filters as df
from django.utils.translation import gettext_lazy as _
from literature.models import LiteratureItem


class LiteratureFilterset(df.FilterSet):
    """Filter literature items by title, author, year, journal, DOI and publisher."""

    title = df.CharFilter(label=_("Title"), lookup_expr="icontains")
    author = df.CharFilter(
        field_name="item__author", lookup_expr="icontains", label=_("Author")
    )
    issued = df.CharFilter(label=_("Year"))
    journal = df.CharFilter(
        field_name="item__container-title", lookup_expr="icontains", label=_("Journal")
    )
    doi = df.CharFilter(field_name="item__DOI", lookup_expr="icontains", label=_("DOI"))
    publisher = df.CharFilter(
        field_name="item__publisher", lookup_expr="icontains", label=_("Publisher")
    )

    class Meta:
        model = LiteratureItem
        fields = [
            "type",
            "doi",
            "title",
            "author",
        ]
