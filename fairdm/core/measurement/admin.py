"""Admin configuration for the Measurement app."""

from django.contrib import admin

from fairdm.contrib.contributors.admin import ContributionInline, IdentifierInline
from fairdm.core.admin import DateInline, DescriptionInline


class MeasurementAdmin(admin.ModelAdmin):
    """Base admin interface for Measurement model and subclasses.

    This class is designed to be inherited by domain-specific measurement admin classes.
    It provides a standard interface for managing measurements with related objects
    (descriptions, dates, identifiers, and contributors).

    Note:
        This admin is NOT registered directly - it should be inherited by
        custom measurement admin classes or registered via the FairDM registry system.
    """

    list_display = ["name", "sample", "dataset", "added"]
    list_filter = ["added", "dataset"]
    search_fields = ["name", "uuid"]
    readonly_fields = ["uuid", "added", "modified"]

    inlines = [
        DescriptionInline,
        DateInline,
        IdentifierInline,
        ContributionInline,
    ]

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "name",
                    "dataset",
                    "sample",
                    "uuid",
                ]
            },
        ),
        (
            "Metadata",
            {
                "fields": [
                    "added",
                    "modified",
                ],
                "classes": ["collapse"],
            },
        ),
    ]
