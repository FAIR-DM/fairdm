"""Django admin configuration for measurements."""

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from polymorphic.admin import (
    PolymorphicChildModelAdmin,
    PolymorphicChildModelFilter,
    PolymorphicParentModelAdmin,
)
from research_vocabs.models import Concept

from fairdm.contrib.contributors.models import Contribution

from .models import (
    Measurement,
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)


class MeasurementDatasetListFilter(admin.RelatedFieldListFilter):
    """A ``dataset`` list filter offering every dataset, private ones included.

    ``Dataset``'s default manager excludes private datasets and the built-in filter draws its
    choices from it, so filtering by a private dataset would otherwise be unavailable. The admin
    needs to see everything, as in ``DatasetAdmin.get_queryset``.
    """

    def field_choices(self, field, request, model_admin):
        """List every dataset as a choice, using ``all_objects`` to include private ones."""
        ordering = self.field_admin_ordering(field, request, model_admin)
        return [
            (obj.pk, str(obj))
            for obj in field.remote_field.model.all_objects.order_by(*ordering)
        ]


class MeasurementDescriptionInline(admin.StackedInline):
    """Inline admin for measurement descriptions, capped at one row per vocabulary type."""

    model = MeasurementDescription
    extra = 0
    max_num = len(MeasurementDescription.VOCABULARY.values)


class MeasurementDateInline(admin.StackedInline):
    """Inline admin for measurement dates, capped at one row per vocabulary type."""

    model = MeasurementDate
    extra = 0
    max_num = len(MeasurementDate.VOCABULARY.values)


class MeasurementIdentifierInline(admin.StackedInline):
    """Inline admin for measurement identifiers, capped at one row per vocabulary type."""

    model = MeasurementIdentifier
    extra = 0
    max_num = len(MeasurementIdentifier.VOCABULARY.values)


class MeasurementContributionInline(GenericTabularInline):
    """Inline admin for measurement contributions, uncapped because each row credits a contributor."""

    model = Contribution
    extra = 0
    ct_field = "content_type"
    ct_fk_field = "object_id"

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Narrow ``roles`` to the roles vocabulary."""
        # Otherwise the widget offers every Concept, and an off-vocabulary choice is refused
        # by the `m2m_changed` receiver uncaught, which turns a field error into a 500.
        if db_field.name == "roles":
            kwargs["queryset"] = Concept.get_for_vocabulary(
                Contribution.roles_vocab.__class__
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class MeasurementChildAdmin(PolymorphicChildModelAdmin):
    """Base admin for measurement child models, with inlines for their related records.

    Subclass it for each measurement type and set ``base_model``. Declare ``base_fieldsets``
    rather than ``fieldsets`` so the polymorphic admin can add the subclass's own fields. See
    docs/portal-development/measurements.md.
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
        """Return the verbose name of the measurement's concrete class."""
        return obj.get_real_instance_class()._meta.verbose_name

    measurement_type.short_description = "Measurement Type"  # type: ignore[attr-defined]


@admin.register(Measurement)
class MeasurementParentAdmin(PolymorphicParentModelAdmin):
    """Polymorphic parent admin registered for ``Measurement``.

    It offers the type selection when adding a measurement and routes to the child admin of each
    registered subclass for editing. See docs/portal-administration/managing-measurements.md.
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
        """Return the verbose name of the measurement's concrete class."""
        return obj.get_real_instance_class()._meta.verbose_name

    measurement_type.short_description = "Measurement Type"  # type: ignore[attr-defined]

    def get_child_models(self):
        """Return every registered Measurement subclass."""
        from fairdm.registry import registry

        return registry.measurements
