"""Admin configuration for the Measurement app."""

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from polymorphic.admin import (
    PolymorphicChildModelAdmin,
    PolymorphicChildModelFilter,
    PolymorphicParentModelAdmin,
)

from fairdm.contrib.contributors.models import Contribution

from .models import (
    Measurement,
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)


class MeasurementDatasetListFilter(admin.RelatedFieldListFilter):
    """A `dataset` list filter offering every dataset, private ones included.

    `Dataset`'s default manager excludes private datasets (FR-019, see
    `fairdm.core.dataset.models.DatasetManager`), and the built-in related
    field filter draws its choices from that manager - so without this
    override, filtering by a private dataset (the model's own default, see
    `tests/test_core/test_measurement/conftest.py`) would silently be
    unavailable. The administrative interface is where a portal is repaired
    and needs to see everything, the same reasoning `DatasetAdmin.get_queryset`
    already applies (FR-019a).
    """

    def field_choices(self, field, request, model_admin):
        ordering = self.field_admin_ordering(field, request, model_admin)
        return [
            (obj.pk, str(obj))
            for obj in field.remote_field.model.all_objects.order_by(*ordering)
        ]


class MeasurementDescriptionInline(admin.StackedInline):
    """Inline admin for measurement descriptions.

    Capped to the number of members its vocabulary carries: a description's
    type is drawn from `MeasurementDescription.VOCABULARY`, so no measurement
    can ever need more rows than that vocabulary has types.
    """

    model = MeasurementDescription
    extra = 0
    max_num = len(MeasurementDescription.VOCABULARY.values)


class MeasurementDateInline(admin.StackedInline):
    """Inline admin for measurement dates.

    Capped to the number of members its vocabulary carries, for the same
    reason as `MeasurementDescriptionInline`.
    """

    model = MeasurementDate
    extra = 0
    max_num = len(MeasurementDate.VOCABULARY.values)


class MeasurementIdentifierInline(admin.StackedInline):
    """Inline admin for measurement identifiers.

    Capped to the number of members its vocabulary carries, for the same
    reason as `MeasurementDescriptionInline`.
    """

    model = MeasurementIdentifier
    extra = 0
    max_num = len(MeasurementIdentifier.VOCABULARY.values)


class MeasurementContributionInline(GenericTabularInline):
    """Inline admin for measurement contributions.

    Deliberately uncapped: a contribution credits a person or organisation,
    not a vocabulary member, and a measurement may credit any number of
    contributors, one row each (design review correction).
    """

    model = Contribution
    extra = 0
    ct_field = "content_type"
    ct_fk_field = "object_id"


class MeasurementChildAdmin(PolymorphicChildModelAdmin):
    """Base admin interface for Measurement child models.

    This class is designed to be inherited by domain-specific measurement admin classes.
    It provides a standard interface for managing measurements with related objects
    (descriptions, dates, identifiers, and contributors).

    All child measurement models should inherit from this class and set their base_model
    attribute to enable proper polymorphic admin functionality.

    See Also:
        - Developer Guide: docs/portal-development/measurements.md#step-3-create-custom-admin
        - Admin Guide (Portal Administrators): docs/portal-administration/managing-measurements.md
        - Registry Guide: docs/portal-development/using_the_registry.md#polymorphic-admin-validation-rules

    Note:
        Child models inherit from PolymorphicChildModelAdmin to work properly
        with the polymorphic parent admin interface.

        Use base_fieldsets instead of fieldsets to allow polymorphic admin
        to automatically add subclass-specific fields.
    """

    list_display = [
        "name",
        "sample",
        "dataset",
        "measurement_type",
        "added",
        "modified",
    ]
    list_filter = [("dataset", MeasurementDatasetListFilter), "sample", "added"]
    search_fields = ["name", "uuid"]
    readonly_fields = ["uuid", "added", "modified"]
    autocomplete_fields = ["dataset", "sample"]

    inlines = [
        MeasurementDescriptionInline,
        MeasurementDateInline,
        MeasurementIdentifierInline,
        MeasurementContributionInline,
    ]

    # Use base_fieldsets (tuple) instead of fieldsets (list) for polymorphic admin
    # This allows polymorphic admin to automatically add subclass-specific fields
    base_fieldsets = (
        (
            None,
            {
                "fields": [
                    "name",
                    "sample",
                    "dataset",
                    "image",
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

    def measurement_type(self, obj):
        """Display the polymorphic type of the measurement."""
        return obj.get_real_instance_class()._meta.verbose_name

    measurement_type.short_description = "Measurement Type"  # type: ignore[attr-defined]


@admin.register(Measurement)
class MeasurementParentAdmin(PolymorphicParentModelAdmin):
    """Polymorphic parent admin for the Measurement model.

    This admin handles the type selection when creating new measurements and
    routes to the appropriate child admin for editing existing measurements.
    It automatically discovers all registered Measurement subclasses.

    Features:
        - Type selection interface when adding new measurements
        - Automatic routing to correct child admin for editing
        - List filtering by polymorphic type
        - Display of measurement type in list view

    See Also:
        - Admin Guide (Portal Administrators): docs/portal-administration/managing-measurements.md#understanding-the-type-selection-interface
        - Registry Guide: docs/portal-development/using_the_registry.md#polymorphic-admin-validation-rules

    Note:
        This is the admin that gets registered with admin.site for the Measurement model.
        Individual child models are registered separately with their own child admins.
    """

    base_model = Measurement
    list_display = [
        "name",
        "sample",
        "dataset",
        "measurement_type",
        "added",
        "modified",
    ]
    list_filter = [
        PolymorphicChildModelFilter,
        ("dataset", MeasurementDatasetListFilter),
        "sample",
        "added",
    ]
    search_fields = ["name", "uuid"]

    def measurement_type(self, obj):
        """Display the polymorphic type of the measurement."""
        return obj.get_real_instance_class()._meta.verbose_name

    measurement_type.short_description = "Measurement Type"  # type: ignore[attr-defined]

    def get_child_models(self):
        """Dynamically get all registered Measurement subclasses."""
        from fairdm.registry import registry

        return registry.measurements
