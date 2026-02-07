"""Admin configuration for the Sample app."""

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from polymorphic.admin import PolymorphicChildModelAdmin, PolymorphicChildModelFilter, PolymorphicParentModelAdmin

from fairdm.contrib.contributors.models import Contribution

from .models import Sample, SampleDate, SampleDescription, SampleIdentifier, SampleRelation


class SampleDescriptionInline(admin.StackedInline):
    """Inline admin for sample descriptions."""

    model = SampleDescription
    extra = 0
    max_num = 6


class SampleDateInline(admin.StackedInline):
    """Inline admin for sample dates."""

    model = SampleDate
    extra = 0
    max_num = 6


class SampleIdentifierInline(admin.StackedInline):
    """Inline admin for sample identifiers."""

    model = SampleIdentifier
    extra = 0
    max_num = 3


class SampleContributionInline(GenericTabularInline):
    """Inline admin for sample contributions."""

    model = Contribution
    extra = 0
    ct_field = "content_type"
    ct_fk_field = "object_id"


class SampleRelationInline(admin.TabularInline):
    """Inline admin for sample-to-sample relationships."""

    model = SampleRelation
    fk_name = "source"
    extra = 0
    fields = ["type", "target"]


class SampleChildAdmin(PolymorphicChildModelAdmin):
    """Base admin interface for Sample child models.

    This class is designed to be inherited by domain-specific sample admin classes.
    It provides a standard interface for managing samples with related objects
    (descriptions, dates, identifiers, contributors, and relationships).

    All child sample models should inherit from this class and set their base_model
    attribute to enable proper polymorphic admin functionality.

    Note:
        Child models inherit from PolymorphicChildModelAdmin to work properly
        with the polymorphic parent admin interface.

        Use base_fieldsets instead of fieldsets to allow polymorphic admin
        to automatically add subclass-specific fields.
    """

    list_display = ["name", "dataset", "status", "sample_type", "location", "added", "modified"]
    list_filter = ["status", "added"]
    search_fields = ["name", "local_id", "uuid"]
    readonly_fields = ["uuid", "added", "modified"]
    autocomplete_fields = ["dataset", "location"]

    inlines = [
        SampleDescriptionInline,
        SampleDateInline,
        SampleIdentifierInline,
        SampleContributionInline,
        SampleRelationInline,
    ]

    # Use base_fieldsets (tuple) instead of fieldsets (list) for polymorphic admin
    # This allows polymorphic admin to automatically add subclass-specific fields
    base_fieldsets = (
        (
            None,
            {
                "fields": [
                    "name",
                    "dataset",
                    "local_id",
                    "status",
                    "location",
                ]
            },
        ),
        (
            "Metadata",
            {
                "fields": [
                    "uuid",
                    "added",
                    "modified",
                ],
                "classes": ["collapse"],
            },
        ),
    )

    def sample_type(self, obj):
        """Display the polymorphic type of the sample."""
        return obj.get_real_instance_class()._meta.verbose_name

    sample_type.short_description = "Sample Type"  # type: ignore[attr-defined]


@admin.register(Sample)
class SampleParentAdmin(PolymorphicParentModelAdmin):
    """Polymorphic parent admin for the Sample model.

    This admin handles the type selection when creating new samples and
    routes to the appropriate child admin for editing existing samples.
    It automatically discovers all registered Sample subclasses.

    Features:
        - Type selection interface when adding new samples
        - Automatic routing to correct child admin for editing
        - List filtering by polymorphic type
        - Display of sample type in list view

    Note:
        This is the admin that gets registered with admin.site for the Sample model.
        Individual child models are registered separately with their own child admins.
    """

    base_model = Sample
    list_display = ["name", "dataset", "status", "sample_type", "location", "added", "modified"]
    list_filter = [PolymorphicChildModelFilter, "status", "added"]
    search_fields = ["name", "local_id", "uuid"]

    def sample_type(self, obj):
        """Display the polymorphic type of the sample."""
        return obj.get_real_instance_class()._meta.verbose_name

    sample_type.short_description = "Sample Type"  # type: ignore[attr-defined]

    def get_child_models(self):
        """Dynamically get all registered Sample subclasses."""
        from fairdm.registry import registry

        # return Sample.__subclasses__()
        return registry.samples
