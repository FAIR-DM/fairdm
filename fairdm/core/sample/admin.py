"""Admin configuration for the Sample app."""

from django.contrib import admin

from fairdm.contrib.contributors.admin import ContributionInline, IdentifierInline
from fairdm.core.admin import DateInline, DescriptionInline

from .models import SampleRelation


class SampleRelationInline(admin.TabularInline):
    """Inline admin for sample-to-sample relationships."""

    model = SampleRelation
    fk_name = "source"
    extra = 0
    fields = ["type", "target"]


class SampleAdmin(admin.ModelAdmin):
    """Base admin interface for Sample model and subclasses.

    This class is designed to be inherited by domain-specific sample admin classes.
    It provides a standard interface for managing samples with related objects
    (descriptions, dates, identifiers, contributors, and relationships).

    Note:
        This admin is NOT registered directly - it should be inherited by
        custom sample admin classes or registered via the FairDM registry system.
    """

    list_display = ["name", "dataset", "status", "location", "added"]
    list_filter = ["status", "added"]
    search_fields = ["name", "local_id", "uuid"]
    readonly_fields = ["uuid", "added", "modified"]

    inlines = [
        DescriptionInline,
        DateInline,
        IdentifierInline,
        ContributionInline,
        SampleRelationInline,
    ]

    fieldsets = [
        (
            None,
            {
                "fields": [
                    "name",
                    "dataset",
                    "local_id",
                    "status",
                    "location",
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
