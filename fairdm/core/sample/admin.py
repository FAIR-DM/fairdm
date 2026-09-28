"""Django admin configuration for samples."""

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
    Sample,
    SampleDate,
    SampleDescription,
    SampleIdentifier,
    SampleRelation,
)


class SampleDatasetListFilter(admin.RelatedFieldListFilter):
    """A ``dataset`` list filter offering every dataset, private ones included.

    The stock filter reads through ``Dataset``'s privacy-first default manager, so for a portal
    whose datasets are still private it would offer no choices and never render.
    """

    def field_choices(self, field, request, model_admin):
        """List every dataset as a choice, using ``all_objects`` to include private ones."""
        from fairdm.core.dataset.models import Dataset

        # `order_by()` with no arguments clears the model's default ordering, so an empty
        # `ordering` must be left unapplied.
        ordering = self.field_admin_ordering(field, request, model_admin)
        queryset = (
            Dataset.all_objects.order_by(*ordering)
            if ordering
            else Dataset.all_objects.all()
        )
        return [(dataset.pk, str(dataset)) for dataset in queryset]


class SampleDescriptionInline(admin.StackedInline):
    """Inline admin for sample descriptions, capped at one row per vocabulary type."""

    model = SampleDescription
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Cap the formset at the number of description types."""
        formset = super().get_formset(request, obj, **kwargs)
        formset.max_num = len(SampleDescription.VOCABULARY.values)
        return formset


class SampleDateInline(admin.StackedInline):
    """Inline admin for sample dates, capped at one row per vocabulary type."""

    model = SampleDate
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Cap the formset at the number of date types."""
        formset = super().get_formset(request, obj, **kwargs)
        formset.max_num = len(SampleDate.VOCABULARY.values)
        return formset


class SampleIdentifierInline(admin.StackedInline):
    """Inline admin for sample identifiers, capped at one row per vocabulary type."""

    model = SampleIdentifier
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Cap the formset at the number of identifier types."""
        formset = super().get_formset(request, obj, **kwargs)
        formset.max_num = len(SampleIdentifier.VOCABULARY.values)
        return formset


class SampleContributionInline(GenericTabularInline):
    """Inline admin for sample contributions."""

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


class SampleRelationInline(admin.TabularInline):
    """Inline admin for sample-to-sample relationships."""

    model = SampleRelation
    fk_name = "source"
    extra = 0
    fields = ["type", "target"]


class SampleChildAdmin(PolymorphicChildModelAdmin):
    """Base admin for sample child models, with inlines for their related records.

    Subclass it for each sample type and set ``base_model``. Declare ``base_fieldsets`` rather
    than ``fieldsets`` so the polymorphic admin can add the subclass's own fields.
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
        """Offer every dataset, not only the public ones."""
        # The default choices are privacy-first, so a sample in a private dataset could be opened
        # but not saved: its own dataset was not among the choices.
        if db_field.name == "dataset":
            from fairdm.core.dataset.models import Dataset

            kwargs["queryset"] = Dataset.all_objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
        """Return the verbose name of the sample's concrete class."""
        return obj.get_real_instance_class()._meta.verbose_name

    sample_type.short_description = "Sample Type"  # type: ignore[attr-defined]


@admin.register(Sample)
class SampleParentAdmin(PolymorphicParentModelAdmin):
    """Polymorphic parent admin registered for ``Sample``.

    It offers the type selection when adding a sample and routes to the child admin of each
    registered subclass for editing.
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
        """Return the verbose name of the sample's concrete class."""
        return obj.get_real_instance_class()._meta.verbose_name

    sample_type.short_description = "Sample Type"  # type: ignore[attr-defined]

    def get_child_models(self):
        """Return every registered Sample subclass."""
        from fairdm.registry import registry

        return registry.samples
