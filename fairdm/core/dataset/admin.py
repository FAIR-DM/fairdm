"""Django admin configuration for the Dataset models.

Registers ``DatasetAdmin`` with search, filters, bounded inlines for descriptions, dates and
identifiers, and a warning when the licence of a dataset carrying a DOI changes. It declares no
bulk action of its own, so visibility can only be changed one dataset at a time.
"""

from django.contrib import admin, messages
from django.db import models
from django.db.models import Exists, OuterRef
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2MultipleWidget, Select2Widget
from literature.models import LiteratureItem

from ..formsets import date_ordering_formset
from .models import Dataset, DatasetDate, DatasetDescription, DatasetIdentifier


@admin.register(LiteratureItem)
class LiteratureItemAdmin(admin.ModelAdmin):
    """Minimal admin for LiteratureItem, required by the autocomplete on ``DatasetAdmin.reference``."""

    search_fields = ("title", "authors")
    list_display = ("title",)


class DescriptionInline(admin.StackedInline):
    """Inline admin for dataset descriptions, limited to one row per description type."""

    model = DatasetDescription
    fk_name = "related"
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Cap the formset at the number of description types."""
        formset = super().get_formset(request, obj, **kwargs)
        vocabulary_size = len(Dataset.DESCRIPTION_TYPES.choices)
        formset.max_num = vocabulary_size
        return formset


DateInlineFormSet = date_ordering_formset(
    DatasetDate.START_TYPE,
    DatasetDate.END_TYPE,
    _(
        "The dataset's collection end date (%(end)s) cannot be "
        "before its collection start date (%(start)s)."
    ),
)


class DateInline(admin.StackedInline):
    """Inline admin for dataset dates, limited to one row per date type.

    ``DateInlineFormSet`` also refuses a collection end date before the collection start date.
    """

    model = DatasetDate
    fk_name = "related"
    formset = DateInlineFormSet
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Cap the formset at the number of date types."""
        formset = super().get_formset(request, obj, **kwargs)
        vocabulary_size = len(Dataset.DATE_TYPES.choices)
        formset.max_num = vocabulary_size
        return formset


class IdentifierInline(admin.TabularInline):
    """Inline admin for dataset identifiers, limited to one row per identifier type."""

    model = DatasetIdentifier
    fk_name = "related"
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Cap the formset at the number of identifier types."""
        formset = super().get_formset(request, obj, **kwargs)
        formset.max_num = len(Dataset.IDENTIFIER_TYPES)
        return formset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    """Admin for datasets.

    Bulk visibility changes are deliberately absent, so a private dataset cannot be exposed by
    accident. Changing the licence of a dataset that has a DOI shows a warning, because the
    published DOI metadata may still name the original licence.
    """

    inlines = [DescriptionInline, DateInline, IdentifierInline]
    search_fields = ("name", "uuid", "identifiers__value", "project__name")
    list_display = (
        "name",
        "added",
        "modified",
        "has_data",
        "has_abstract",
        "has_doi",
        "published",
    )
    list_filter = ("project", "license", "visibility", "published")
    readonly_fields = ("uuid", "added", "modified")
    autocomplete_fields = ("project", "reference")

    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "name",
                    "uuid",
                    "project",
                    "visibility",
                    "published",
                )
            },
        ),
        (
            _("Licensing & Attribution"),
            {"fields": ("license",)},
        ),
        (
            _("Literature & References"),
            {"fields": ("reference",)},
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "keywords",
                    "image",
                )
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": (
                    "added",
                    "modified",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    formfield_overrides = {
        models.ManyToManyField: {"widget": Select2MultipleWidget},
        models.ForeignKey: {"widget": Select2Widget},
        models.OneToOneField: {"widget": Select2Widget},
    }

    def get_queryset(self, request):
        """Include private datasets and annotate the abstract and DOI flags."""
        # The default manager hides private datasets, and the admin must see them all.
        # The annotations avoid one `.exists()` query per row for `has_abstract` and `has_doi`.
        return Dataset.all_objects.all().annotate(
            _has_abstract=Exists(
                DatasetDescription.objects.filter(
                    related=OuterRef("pk"), type="Abstract"
                )
            ),
            _has_doi=Exists(
                DatasetIdentifier.objects.filter(related=OuterRef("pk"), type="DOI")
            ),
        )

    @admin.display(boolean=True, description=_("Abstract"))
    def has_abstract(self, obj):
        """Return whether the dataset carries an abstract description."""
        return obj._has_abstract

    @admin.display(boolean=True, description=_("DOI"))
    def has_doi(self, obj):
        """Return whether the dataset carries a DOI identifier."""
        return obj._has_doi

    def save_model(self, request, obj, form, change):
        """Save the dataset, warning when the licence of a dataset with a DOI changes."""
        if change and "license" in form.changed_data:
            has_doi = DatasetIdentifier.objects.filter(related=obj, type="DOI").exists()

            if has_doi:
                messages.warning(
                    request,
                    _(
                        "Warning: This dataset has an assigned DOI. Changing the license "
                        "may require updating the DOI metadata in external registries "
                        "(e.g., DataCite, Crossref). Please ensure all published metadata "
                        "is updated to reflect the new license terms."
                    ),
                )

        super().save_model(request, obj, form, change)
