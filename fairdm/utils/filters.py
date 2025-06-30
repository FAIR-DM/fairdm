import django_filters as df
from django.utils.translation import gettext_lazy as _
from literature.models import LiteratureItem


class LiteratureFilterset(df.FilterSet):
    o = df.OrderingFilter(
        fields=(
            ("title", "title"),
            ("issued", "issued"),
            ("created", "created"),
        ),
        field_labels={
            "title": _("Title"),
            "issued": _("Year published"),
            "created": _("Date added"),
        },
    )

    title = df.CharFilter(label=_("Title"), lookup_expr="icontains")
    author = df.CharFilter(field_name="item__author", lookup_expr="icontains", label=_("Author"))
    issued = df.CharFilter(label=_("Year"))
    journal = df.CharFilter(field_name="item__container-title", lookup_expr="icontains", label=_("Journal"))
    doi = df.CharFilter(field_name="item__DOI", lookup_expr="icontains", label=_("DOI"))
    publisher = df.CharFilter(field_name="item__publisher", lookup_expr="icontains", label=_("Publisher"))
    # keywords = df.ModelMultipleChoiceFilter(to_field_name="name", queryset=Tag.objects.all(), label=_("Keywords"))

    class Meta:
        model = LiteratureItem
        fields = [
            "o",
            "type",
            "doi",
            "title",
            "author",
        ]
