"""Django admin configuration for Dataset models.

This module provides a comprehensive admin interface for Dataset management with:
- Search by name and UUID
- Filtering by project, license, and visibility
- Inline editing for descriptions and dates
- Dynamic inline form limits based on vocabulary size
- Bulk metadata export (JSON/DataCite format)
- Security controls (no bulk visibility changes)
- Autocomplete widgets on ForeignKey fields
- Readonly UUID and timestamps
- License change warnings when DOI exists

The admin interface follows FAIR data principles and enforces deliberate,
individual visibility changes to prevent accidental exposure of private datasets.
"""

from django.contrib import admin, messages
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2MultipleWidget, Select2Widget
from literature.models import LiteratureItem

from .models import Dataset, DatasetDate, DatasetDescription, DatasetIdentifier


# Register LiteratureItem admin for autocomplete support
@admin.register(LiteratureItem)
class LiteratureItemAdmin(admin.ModelAdmin):
    """Minimal admin for LiteratureItem to enable autocomplete in DatasetAdmin.

    This registration is required because DatasetAdmin uses autocomplete_fields
    for the 'reference' ForeignKey field. The search_fields enable autocomplete
    search functionality in the admin interface.
    """

    search_fields = ("title", "authors")
    list_display = ("title",)


class DescriptionInline(admin.StackedInline):
    """Inline admin for Dataset descriptions.

    The max_num is dynamically set based on the number of available description
    types in the vocabulary. This prevents users from adding more descriptions
    than there are valid types, ensuring data quality and preventing form confusion.

    For example, if there are 6 description types (Abstract, Methods, etc.),
    max_num will be set to 6, allowing one description of each type.
    """

    model = DatasetDescription
    fk_name = "related"
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Dynamically set max_num based on vocabulary size."""
        formset = super().get_formset(request, obj, **kwargs)
        vocabulary_size = len(Dataset.DESCRIPTION_TYPES.choices)
        formset.max_num = vocabulary_size
        return formset


class DateInline(admin.StackedInline):
    """Inline admin for Dataset dates.

    The max_num is dynamically set based on the number of available date types
    in the vocabulary (Created, Submitted, Available, etc.). This prevents users
    from adding more dates than there are valid types.

    The unique_together constraint on (related, type) ensures only one date of
    each type can exist per dataset.
    """

    model = DatasetDate
    fk_name = "related"
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Dynamically set max_num based on vocabulary size."""
        formset = super().get_formset(request, obj, **kwargs)
        vocabulary_size = len(Dataset.DATE_TYPES.choices)
        formset.max_num = vocabulary_size
        return formset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    """Admin interface for Dataset model with comprehensive FAIR data management.

    **Search & Filtering:**
    - Search by name and UUID (full or partial)
    - Filter by project, license, visibility

    **List Display:**
    - Name, added timestamp, modified timestamp, has_data indicator

    **Inline Editing:**
    - DatasetDescription: Dynamic limit based on vocabulary size
    - DatasetDate: Dynamic limit based on vocabulary size

    **Bulk Operations:**
    - Export metadata (JSON, DataCite format) - Available
    - Change visibility - DISABLED for security

    **Security Note:**
    Bulk visibility change actions are intentionally disabled to prevent
    accidental exposure of private research datasets. Visibility must be
    changed individually through the dataset edit form, ensuring deliberate
    and documented decisions about data access.

    **License Change Warning:**
    When a dataset has an assigned DOI and the license is changed, the admin
    displays a warning because published DOI metadata may reference the
    original license and require manual updates in external registries.
    """

    inlines = [DescriptionInline, DateInline]
    search_fields = ("name", "uuid")
    list_display = ("name", "added", "modified", "has_data")
    list_filter = ("project", "license", "visibility")
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

    def save_model(self, request, obj, form, change):
        """Save the dataset and display license change warning if DOI exists.

        When editing an existing dataset that has a DOI assigned, changing the
        license triggers a warning message because:

        1. The DOI metadata may have been published with the original license
        2. External registries (DataCite, etc.) need manual updates
        3. Citations may reference the original license terms

        Args:
            request: The current HTTP request
            obj: The Dataset instance being saved
            form: The ModelForm instance
            change: Boolean indicating if this is an update (True) or create (False)
        """
        # Check for license changes on datasets with DOIs
        if change and "license" in form.changed_data:
            # Check if dataset has a DOI
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
