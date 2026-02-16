"""Filters for the Project app."""

import django_filters as df
from django import forms
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from fairdm.contrib.autocomplete.fields import ConceptMultiSelect
from fairdm.core.filters import BaseListFilter
from fairdm.utils.utils import get_setting

from .models import Project


class ProjectFilter(BaseListFilter):
    """Filter for Project list views with comprehensive filtering options.

    Keyword filters are automatically created based on FAIRDM_PROJECT["keywords"] setting.
    """

    # Project status filter (Concept, Planning, In Progress, Complete)
    status = df.ChoiceFilter(
        choices=Project.STATUS_CHOICES,
        empty_label=_("Any"),
        label=_("Status"),
    )

    # Filter by owner organization
    owner = df.ModelChoiceFilter(
        queryset=None,  # Set dynamically in __init__
        empty_label=_("Any"),
        label=_("Owner"),
    )

    # Filter by tags (free-form)
    tags = df.CharFilter(
        field_name="tags__name",
        lookup_expr="iexact",
        label=_("Tag"),
    )

    # Filter by contributor (person or organization)
    contributor = df.ModelChoiceFilter(
        queryset=None,  # Set dynamically in __init__
        field_name="contributors__contributor",
        empty_label=_("Any"),
        label=_("Contributor"),
        distinct=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter to only show public projects
        if self.queryset is not None:
            self.queryset = self.queryset.get_visible()

        # Dynamically set owner queryset to only organizations that own projects
        from fairdm.contrib.contributors.models import Organization

        self.filters["owner"].queryset = Organization.objects.filter(owned_projects__isnull=False).distinct()

        # Dynamically create keyword filters based on configuration
        from research_vocabs.models import Concept

        # Get vocabulary paths from settings
        vocabularies = get_setting("PROJECT", "keywords") or []

        if vocabularies:
            # Create vocabulary-specific keyword filters
            for vocab_path in vocabularies:
                vocab_class = import_string(vocab_path)
                vocab_name = vocab_class._meta.name
                field_name = vocab_class.__name__
                filter_name = f"keywords_{field_name}"

                # Create the filter using autocomplete field
                self.filters[filter_name] = df.ModelMultipleChoiceFilter(
                    field_name="keywords",
                    queryset=Concept.objects.filter(vocabulary__name=vocab_name, projects__isnull=False).distinct(),
                    conjoined=False,  # OR logic: match ANY selected keyword
                    label=field_name,
                    widget=ConceptMultiSelect(vocabulary=vocab_path, required=False).widget,
                )
        else:
            # Create a generic keywords filter for all vocabularies
            self.filters["keywords"] = df.ModelMultipleChoiceFilter(
                field_name="keywords",
                queryset=Concept.objects.filter(projects__isnull=False).distinct(),
                conjoined=False,
                label=_("Keywords"),
                widget=forms.CheckboxSelectMultiple,
            )

        # Dynamically set contributor queryset to only contributors linked to projects
        from fairdm.contrib.contributors.models import Contributor

        self.filters["contributor"].queryset = Contributor.objects.filter(
            contributions__content_type__model="project"
        ).distinct()

    @property
    def form(self):
        """Override form property to include dynamically created fields."""
        if not hasattr(self, "_form"):
            vocabularies = get_setting("PROJECT", "keywords") or []
            if vocabularies:
                # Add vocabulary filter names to Meta.fields
                vocab_fields = [f"keywords_{import_string(vocab).__name__}" for vocab in vocabularies]
                self._meta.fields = [*list(self._meta.fields), *vocab_fields]
            else:
                # Add generic keywords field
                self._meta.fields = [*list(self._meta.fields), "keywords"]
            self._form = super().form
        return self._form

    class Meta:
        model = Project
        fields = ["status", "owner", "tags", "contributor"]
