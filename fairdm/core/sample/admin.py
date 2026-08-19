"""Admin configuration for the Sample app."""

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from polymorphic.admin import (
    PolymorphicChildModelAdmin,
    PolymorphicChildModelFilter,
    PolymorphicParentModelAdmin,
)

from fairdm.contrib.contributors.models import Contribution

from .models import (
    Sample,
    SampleDate,
    SampleDescription,
    SampleIdentifier,
    SampleRelation,
)


class SampleDatasetListFilter(admin.RelatedFieldListFilter):
    """The ``dataset`` list filter (FR-039, T082), listing every dataset rather than
    only the ones visible through ``Dataset``'s privacy-first default manager.

    The stock ``RelatedFieldListFilter`` populates its choices from
    ``field.get_choices()``, which reads through ``Dataset._default_manager`` - the
    same privacy-first manager ``DatasetAdmin.get_queryset()`` works around
    (`fairdm/core/dataset/admin.py`). Since ``PRIVATE`` is a dataset's default
    visibility, an unmodified filter would offer no choices - and therefore never
    render at all - for the common case of a portal whose datasets have not yet been
    published.
    """

    def field_choices(self, field, request, model_admin):
        from fairdm.core.dataset.models import Dataset

        # `order_by()` with no arguments clears the model's default ordering rather than
        # leaving it in place (F9), so an empty `ordering` - what `field_admin_ordering`
        # returns whenever nothing declares admin-level ordering, the common case - must be
        # left unapplied instead of passed through.
        ordering = self.field_admin_ordering(field, request, model_admin)
        queryset = (
            Dataset.all_objects.order_by(*ordering)
            if ordering
            else Dataset.all_objects.all()
        )
        return [(dataset.pk, str(dataset)) for dataset in queryset]


class SampleDescriptionInline(admin.StackedInline):
    """Inline admin for sample descriptions.

    ``max_num`` is derived from ``SampleDescription.VOCABULARY`` (T084) rather than
    hardcoded, the same dynamic-limit pattern as `DescriptionInline` in
    `fairdm/core/dataset/admin.py` - a specimen cannot carry more descriptions than
    there are description types to give them.
    """

    model = SampleDescription
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Set ``max_num`` to the current size of the description vocabulary."""
        formset = super().get_formset(request, obj, **kwargs)
        formset.max_num = len(SampleDescription.VOCABULARY.values)
        return formset


class SampleDateInline(admin.StackedInline):
    """Inline admin for sample dates.

    ``max_num`` is derived from ``SampleDate.VOCABULARY`` (T084), matching
    `SampleDescriptionInline` above.
    """

    model = SampleDate
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Set ``max_num`` to the current size of the date vocabulary."""
        formset = super().get_formset(request, obj, **kwargs)
        formset.max_num = len(SampleDate.VOCABULARY.values)
        return formset


class SampleIdentifierInline(admin.StackedInline):
    """Inline admin for sample identifiers.

    ``max_num`` is derived from ``SampleIdentifier.VOCABULARY`` (T084), matching
    `SampleDescriptionInline` above.
    """

    model = SampleIdentifier
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Set ``max_num`` to the current size of the identifier vocabulary."""
        formset = super().get_formset(request, obj, **kwargs)
        formset.max_num = len(SampleIdentifier.VOCABULARY.values)
        return formset


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

    list_display = [
        "name",
        "dataset",
        "status",
        "sample_type",
        "location",
        "added",
        "modified",
    ]
    list_filter = [("dataset", SampleDatasetListFilter), "status", "added"]
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Offer every dataset, not only the public ones.

        The dataset field's choices default to `Dataset._default_manager`,
        which is privacy-first, so a specimen belonging to a private dataset
        could be opened but not saved: its own dataset was not among the
        choices and validation rejected it. The administrative interface is
        where a portal is repaired, so it has to reach the records that need
        repairing — the same reason `DatasetAdmin.get_queryset()` reads
        through `all_objects`, and the same reason `SampleDatasetListFilter`
        above does.
        """
        if db_field.name == "dataset":
            from fairdm.core.dataset.models import Dataset

            kwargs["queryset"] = Dataset.all_objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
    list_display = [
        "name",
        "dataset",
        "status",
        "sample_type",
        "location",
        "added",
        "modified",
    ]
    list_filter = [
        PolymorphicChildModelFilter,
        ("dataset", SampleDatasetListFilter),
        "status",
        "added",
    ]
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
