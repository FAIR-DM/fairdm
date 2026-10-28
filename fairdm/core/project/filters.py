"""Filters for the project list page."""

import django_filters as df
from controlled_vocabularies.models import ConceptScheme, Record
from django import forms
from django.utils.translation import gettext_lazy as _
from mvp.filters import SearchFilter, SortFilter
from mvp_forms.widgets import TomSelectMultiple

from fairdm.contrib.autocomplete.fields import (
    OrganizationMultipleChoiceField,
    PersonMultipleChoiceField,
)
from fairdm.contrib.autocomplete.filters import RecordMultipleFilter, TagFilter
from fairdm.core.filters import BaseListFilter
from fairdm.utils.utils import get_setting

from .models import Project


class ProjectFilter(BaseListFilter):
    """Filter for the project list, by status, owner, tag, contributor and keywords.

    The search matches the name, the uuid and the identifiers. The sort offers name and
    date created. One keyword filter is created for each vocabulary address the
    ``FAIRDM_PROJECT["keywords"]`` setting lists, and a single one over every keyword when it
    lists none.
    """

    q = SearchFilter(fields=["uuid", "name", "identifiers__value"])

    o = SortFilter(
        options=[
            ("name", _("Name (A-Z)"), "name"),
            ("-name", _("Name (Z-A)"), "-name"),
            ("added", _("Date created (oldest first)"), "added"),
            ("-added", _("Date created (newest first)"), "-added"),
        ]
    )

    status = df.MultipleChoiceFilter(
        choices=Project.STATUS_CHOICES,
        label=_("Status"),
    )

    owner = RecordMultipleFilter(
        OrganizationMultipleChoiceField,
        field_name="owner",
        label=_("Owner"),
    )

    tags = TagFilter(field_name="tags__name", label=_("Tag"))

    contributor = RecordMultipleFilter(
        PersonMultipleChoiceField,
        field_name="contributors__contributor",
        label=_("Contributor"),
        distinct=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.queryset is not None:
            self.queryset = self.queryset.get_visible()

        vocabularies = self.keyword_vocabularies()
        if vocabularies:
            names = dict(
                ConceptScheme.objects.filter(uri__in=vocabularies.values()).values_list(
                    "uri", "pref_label"
                )
            )
            for filter_name, uri in vocabularies.items():
                self.filters[filter_name] = df.ModelMultipleChoiceFilter(
                    field_name="keywords",
                    queryset=Record.objects.filter(
                        scheme__uri=uri, projects__isnull=False
                    ).distinct(),
                    conjoined=True,
                    label=names.get(uri) or uri,
                    widget=TomSelectMultiple(
                        counted=True,
                        placeholder=_("Any"),
                        none_text=_("Any"),
                        count_text=_("selected"),
                    ),
                )
        else:
            self.filters["keywords"] = df.ModelMultipleChoiceFilter(
                field_name="keywords",
                queryset=Record.objects.filter(projects__isnull=False).distinct(),
                conjoined=True,
                label=_("Keywords"),
                widget=forms.CheckboxSelectMultiple,
            )

    @staticmethod
    def keyword_vocabularies():
        """Return the keyword filters the ``FAIRDM_PROJECT["keywords"]`` setting asks for.

        Returns:
            The address of each vocabulary the setting names, keyed by the name of its filter:
            ``keywords_`` followed by the last part of the address.
        """
        return {
            f"keywords_{uri.rstrip('/').rsplit('/', 1)[-1]}": uri
            for uri in get_setting("PROJECT", "keywords") or []
        }

    @property
    def form(self):
        """Include the keyword filters in the form."""
        if not hasattr(self, "_form"):
            vocabularies = self.keyword_vocabularies()
            self._meta.fields = [
                *list(self._meta.fields),
                *(vocabularies or ["keywords"]),
            ]
            self._form = super().form
        return self._form

    class Meta:
        model = Project
        fields = ["status", "owner", "tags", "contributor"]
