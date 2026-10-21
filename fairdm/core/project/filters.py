"""Filters for the project list page."""

import django_filters as df
from django import forms
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from mvp.filters import SearchFilter, SortFilter
from mvp_forms.widgets import TomSelectMultiple

from fairdm.contrib.autocomplete.fields import (
    OrganizationMultipleChoiceField,
    PersonMultipleChoiceField,
)
from fairdm.contrib.autocomplete.filters import RecordMultipleFilter
from fairdm.core.filters import BaseListFilter
from fairdm.utils.utils import get_setting

from .models import Project


class ProjectFilter(BaseListFilter):
    """Filter for the project list, by status, owner, tag, contributor and keywords.

    The search matches the name, the uuid and the identifiers. The sort offers name and
    date created. Keyword filters are created from the ``FAIRDM_PROJECT["keywords"]``
    setting.
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

    tags = df.CharFilter(
        field_name="tags__name",
        lookup_expr="iexact",
        label=_("Tag"),
    )

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

        from research_vocabs.models import Concept

        vocabularies = get_setting("PROJECT", "keywords") or []

        if vocabularies:
            for vocab_path in vocabularies:
                vocab_class = import_string(vocab_path)
                vocab_name = vocab_class._meta.name
                field_name = vocab_class.__name__
                filter_name = f"keywords_{field_name}"

                self.filters[filter_name] = df.ModelMultipleChoiceFilter(
                    field_name="keywords",
                    queryset=Concept.objects.filter(
                        vocabulary__name=vocab_name, projects__isnull=False
                    ).distinct(),
                    conjoined=True,
                    label=field_name,
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
                queryset=Concept.objects.filter(projects__isnull=False).distinct(),
                conjoined=True,
                label=_("Keywords"),
                widget=forms.CheckboxSelectMultiple,
            )

    @property
    def form(self):
        """Include the dynamically created keyword filters in the form."""
        if not hasattr(self, "_form"):
            vocabularies = get_setting("PROJECT", "keywords") or []
            if vocabularies:
                vocab_fields = [
                    f"keywords_{import_string(vocab).__name__}"
                    for vocab in vocabularies
                ]
                self._meta.fields = [*list(self._meta.fields), *vocab_fields]
            else:
                self._meta.fields = [*list(self._meta.fields), "keywords"]
            self._form = super().form
        return self._form

    class Meta:
        model = Project
        fields = ["status", "owner", "tags", "contributor"]
