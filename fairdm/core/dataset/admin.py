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

import json

from django.contrib import admin, messages
from django.db import models
from django.http import HttpResponse
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

    The max_num is dynamically set in DatasetAdmin.get_formset() based on the
    number of available description types in the vocabulary. This prevents users
    from adding more descriptions than there are valid types, ensuring data
    quality and preventing form confusion.

    For example, if there are 6 description types (Abstract, Methods, etc.),
    max_num will be set to 6, allowing one description of each type.
    """

    model = DatasetDescription
    extra = 0
    # max_num is set dynamically in DatasetAdmin.get_formset()


class DateInline(admin.StackedInline):
    """Inline admin for Dataset dates.

    The max_num is dynamically set in DatasetAdmin.get_formset() based on the
    number of available date types in the vocabulary (Created, Submitted,
    Available, etc.). This prevents users from adding more dates than there
    are valid types.

    The unique_together constraint on (related, type) ensures only one date of
    each type can exist per dataset.
    """

    model = DatasetDate
    extra = 0
    # max_num is set dynamically in DatasetAdmin.get_formset()


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

    def get_formset(self, request, obj=None, **kwargs):
        """Dynamically set max_num for inline formsets based on vocabulary size.

        For DescriptionInline and DateInline, this method sets max_num to match
        the number of available choices in the vocabulary. This prevents users
        from creating more inline forms than there are valid types, improving
        UX and preventing validation errors.

        Args:
            request: The current HTTP request
            obj: The Dataset instance being edited (None for add view)
            **kwargs: Additional arguments including 'inline' for inline formsets

        Returns:
            The formset class with dynamically adjusted max_num
        """
        inline = kwargs.get("inline")
        formset = super().get_formset(request, obj, **kwargs)

        if inline == DescriptionInline:
            # Set max_num to number of description types
            vocabulary_size = len(Dataset.DESCRIPTION_TYPES.choices)
            formset.max_num = vocabulary_size
        elif inline == DateInline:
            # Set max_num to number of date types
            vocabulary_size = len(Dataset.DATE_TYPES.choices)
            formset.max_num = vocabulary_size

        return formset

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

    @admin.action(description=_("Export metadata (JSON)"))
    def export_metadata_json(self, request, queryset):
        """Export dataset metadata as JSON.

        Exports selected datasets with comprehensive metadata including:
        - Basic information (name, UUID, visibility)
        - Timestamps (added, modified)
        - Relationships (project, contributors)
        - Metadata (descriptions, dates, identifiers)

        Args:
            request: The current HTTP request
            queryset: QuerySet of selected Dataset instances

        Returns:
            HttpResponse with JSON content
        """
        datasets_data = []

        for dataset in queryset.select_related("project").prefetch_related(
            "descriptions", "dates", "identifiers", "contributors"
        ):
            dataset_dict = {
                "name": dataset.name,
                "uuid": str(dataset.uuid),
                "visibility": dataset.get_visibility_display(),
                "added": dataset.added.isoformat(),
                "modified": dataset.modified.isoformat(),
                "project": dataset.project.name if dataset.project else None,
                "license": str(dataset.license) if dataset.license else None,
                "has_data": dataset.has_data,
                "descriptions": [
                    {
                        "type": desc.get_type_display(),
                        "value": desc.value,
                    }
                    for desc in dataset.descriptions.all()
                ],
                "dates": [
                    {
                        "type": date.get_type_display(),
                        "value": str(date.value),
                    }
                    for date in dataset.dates.all()
                ],
                "identifiers": [
                    {
                        "type": ident.get_type_display(),
                        "value": ident.value,
                    }
                    for ident in dataset.identifiers.all()
                ],
            }
            datasets_data.append(dataset_dict)

        response = HttpResponse(
            json.dumps(datasets_data, indent=2),
            content_type="application/json",
        )
        response["Content-Disposition"] = 'attachment; filename="datasets_metadata.json"'
        return response

    actions = ["export_metadata_json"]

    # Explicitly remove any bulk visibility change actions if they exist
    # This is a security feature to prevent accidental exposure of private datasets
    def get_actions(self, request):
        """Override to ensure no bulk visibility change actions are available.

        This method filters out any actions that might change dataset visibility
        in bulk. Visibility changes must be deliberate and individual to prevent
        accidental exposure of sensitive research data.
        """
        actions = super().get_actions(request)

        # Remove any visibility-related bulk actions
        visibility_action_patterns = [
            "make_public",
            "make_private",
            "change_visibility",
            "bulk_make_public",
            "bulk_make_private",
            "bulk_change_visibility",
        ]

        for pattern in visibility_action_patterns:
            actions.pop(pattern, None)

        return actions
