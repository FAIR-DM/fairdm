"""Django admin configuration for Dataset models (US-6).

This module registers `DatasetAdmin`, which provides:
- Search by name, generated identifier (UUID), external identifier and
  project (FR-023).
- Filtering by project, licence and visibility (FR-023).
- Inline editing for descriptions, dates and identifiers, each bounded to
  the number of types its vocabulary carries (FR-024).
- List columns reporting whether a dataset carries an abstract and whether
  it carries a DOI, computed in the list query rather than per row
  (FR-025).
- No bulk action that changes more than one dataset's visibility at a time
  (FR-026) - `DatasetAdmin` declares none of its own, so the only action
  available is Django's own `delete_selected`.
- Readonly generated identifier and timestamps (FR-027).
- A warning when the licence of a dataset carrying a DOI is changed
  (FR-028).

The admin interface follows FAIR data principles and enforces deliberate,
individual visibility changes to prevent accidental exposure of private
datasets.
"""

from django.contrib import admin, messages
from django.db import models
from django.db.models import Exists, OuterRef
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2MultipleWidget, Select2Widget
from literature.models import LiteratureItem

from ..formsets import date_ordering_formset
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


DateInlineFormSet = date_ordering_formset(
    DatasetDate.START_TYPE,
    DatasetDate.END_TYPE,
    _(
        "The dataset's collection end date (%(end)s) cannot be "
        "before its collection start date (%(start)s)."
    ),
)


class DateInline(admin.StackedInline):
    """Inline admin for Dataset dates.

    The max_num is dynamically set based on the number of available date types
    in the vocabulary (Available, CollectionStart, CollectionEnd, Submitted,
    Published, Withdrawn). This prevents users from adding more dates than
    there are valid types.

    The unique_together constraint on (related, type) ensures only one date of
    each type can exist per dataset. `DateInlineFormSet` additionally refuses
    a backwards CollectionStart/CollectionEnd pair across the whole formset
    (FR-011).
    """

    model = DatasetDate
    fk_name = "related"
    formset = DateInlineFormSet
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Dynamically set max_num based on vocabulary size."""
        formset = super().get_formset(request, obj, **kwargs)
        vocabulary_size = len(Dataset.DATE_TYPES.choices)
        formset.max_num = vocabulary_size
        return formset


class IdentifierInline(admin.TabularInline):
    """Inline admin for Dataset identifiers (T078, T085).

    The max_num is dynamically set based on the number of available
    identifier types in the dataset identifier vocabulary - currently
    `DOI` alone (D-003, research.md R3) - the same dynamic-limit pattern
    `DescriptionInline` and `DateInline` above use.
    """

    model = DatasetIdentifier
    fk_name = "related"
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        """Dynamically set max_num based on vocabulary size."""
        formset = super().get_formset(request, obj, **kwargs)
        formset.max_num = len(Dataset.IDENTIFIER_TYPES)
        return formset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    """Admin interface for Dataset model with comprehensive FAIR data management.

    **Search & Filtering:**
    - Search by name, generated identifier (UUID, full or partial), any
      external identifier attached to the dataset, and project name
      (FR-023).
    - Filter by project, license, visibility (FR-023).

    **List Display:**
    - Name, added timestamp, modified timestamp, has_data indicator, and
      whether the dataset carries an abstract and a DOI (FR-025).

    **Inline Editing:**
    - DatasetDescription: Dynamic limit based on vocabulary size
    - DatasetDate: Dynamic limit based on vocabulary size
    - DatasetIdentifier: Dynamic limit based on vocabulary size

    **Bulk Operations:**
    - Change visibility - DISABLED for security. `DatasetAdmin` declares no
      actions of its own, so the only action available on the changelist is
      Django's own `delete_selected`, which removes whole records rather
      than changing `visibility` (FR-026).

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
        """Use `all_objects` rather than the privacy-first default manager,
        and annotate the abstract/DOI flags on the queryset itself.

        `ModelAdmin.get_queryset()` reads through `Dataset._default_manager`
        by default, which would hide PRIVATE datasets from the admin
        changelist. The admin is where a portal is repaired, so it must see
        every dataset regardless of visibility (FR-019a).

        `list_per_page` is 100 by default, and without the annotations below
        `has_abstract`/`has_doi` would each run an `.exists()` query per row
        - `Exists()` subqueries fold both checks into the single query the
        changelist already runs (FR-025, mirrors
        `ProjectAdmin.get_queryset()`, `fairdm/core/project/admin.py`).
        """
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
        """Whether the dataset carries an abstract description (FR-025)."""
        return obj._has_abstract

    @admin.display(boolean=True, description=_("DOI"))
    def has_doi(self, obj):
        """Whether the dataset carries a DOI identifier (FR-025)."""
        return obj._has_doi

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
