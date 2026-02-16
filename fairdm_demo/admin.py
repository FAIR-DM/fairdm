"""
FairDM Demo Portal - Admin Interface Examples

This module demonstrates best practices for customizing Django admin interfaces
in FairDM portals, including:

1. **Dynamic Inline Form Limits**: Vocabulary-based max_num configuration
2. **Bulk Metadata Export**: Custom admin actions for data export
3. **Security Patterns**: Preventing accidental bulk visibility changes
4. **Search & Filtering**: Optimized admin list views
5. **Readonly Fields**: Protecting system-managed data

These examples follow the patterns established in fairdm.core.dataset.admin
and can be adapted for custom Sample and Measurement models.

## Quick Reference

**Dynamic Inline Limits Example**:
```python
def get_formset(self, request, obj=None, **kwargs):
    inline = kwargs.get("inline")
    formset = super().get_formset(request, obj, **kwargs)
    if inline == MyInline:
        formset.max_num = len(MyModel.VOCABULARY.choices)
    return formset
```

**Bulk Export Action Example**:
```python
@admin.action(description="Export as JSON")
def export_json(self, request, queryset):
    data = [{"name": obj.name, "id": str(obj.uuid)} for obj in queryset]
    response = HttpResponse(json.dumps(data, indent=2))
    response["Content-Disposition"] = 'attachment; filename="export.json"'
    return response
```

**Prevent Bulk Visibility Changes**:
```python
def get_actions(self, request):
    actions = super().get_actions(request)
    # Remove visibility-related bulk actions for security
    for pattern in ["make_public", "make_private"]:
        actions.pop(pattern, None)
    return actions
```

## Related Documentation

- **Admin Interface Guide**: `docs/portal-development/admin_interfaces.md`
  - Complete guide to customizing admin interfaces

- **Dataset Admin Reference**: `fairdm/core/dataset/admin.py`
  - Production admin implementation with comprehensive features

- **Security Best Practices**: `docs/portal-administration/security.md`
  - Guidelines for protecting sensitive data

## Integration with FairDM Registry

The admin patterns shown here work seamlessly with FairDM's registry system.
Models registered via `@register` decorator automatically get admin interfaces,
but you can override the default admin classes for custom behavior:

```python
from fairdm.registry import register, ModelConfiguration


@register
class MySampleConfig(ModelConfiguration):
    model = MySample
    admin_class = MySampleAdmin  # Custom admin class
    fields = ["name", "location", "date"]
```

See `docs/portal-development/registry_integration.md` for details.
"""

from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2MultipleWidget, Select2Widget

from fairdm.core.dataset.models import DatasetDescription

# ============================================================================
# Example 1: Dynamic Inline Form Limits Based on Vocabulary Size
# ============================================================================


class RockSampleDescriptionInline(admin.StackedInline):
    """Example inline with dynamic max_num based on vocabulary.

    This inline demonstrates the pattern used in DatasetAdmin where max_num
    is dynamically set based on the number of available choices in a vocabulary.
    This prevents users from creating more forms than there are valid types.

    Benefits:
    - Improved UX (no unnecessary empty forms)
    - Data quality (prevents validation errors)
    - Clear feedback (users know the limit)

    Implementation:
    The get_formset() method in the parent ModelAdmin sets max_num at runtime.
    """

    model = DatasetDescription  # Example - replace with your inline model
    extra = 0
    # max_num set dynamically in parent ModelAdmin.get_formset()

    class Meta:
        verbose_name = "Description"
        verbose_name_plural = "Descriptions"


# Commented out example admin - uncomment and adapt for your models
# @admin.register(RockSample)
class RockSampleAdminExample(admin.ModelAdmin):
    """Example admin showing dynamic inline limits and bulk export.

    This admin class demonstrates:
    1. Dynamic inline max_num based on vocabulary size
    2. Bulk metadata export action
    3. Security controls (no bulk visibility changes)
    4. Comprehensive search and filtering

    Pattern Usage:
    Copy this pattern to your own Sample/Measurement admin classes,
    adjusting the vocabulary references to match your model's fields.
    """

    # inlines = [RockSampleDescriptionInline]
    search_fields = ("name", "uuid")
    list_display = ("name", "added", "modified", "dataset")
    list_filter = ("dataset", "added")
    readonly_fields = ("uuid", "added", "modified")
    # autocomplete_fields = ("dataset", "location")

    # ============================================================================
    # Dynamic Inline Form Limits
    # ============================================================================

    def get_formset(self, request, obj=None, **kwargs):
        """Dynamically set max_num for inline formsets based on vocabulary size.

        This method implements the same pattern as DatasetAdmin.get_formset().
        When a model has a vocabulary-constrained field (e.g., description_type),
        we limit the number of inline forms to match the vocabulary size.

        Example:
        If RockSample has 5 description types (Abstract, Methods, Results, etc.),
        max_num will be set to 5, preventing users from adding a 6th description.

        Args:
            request: The current HTTP request
            obj: The model instance being edited (None for add view)
            **kwargs: Additional arguments including 'inline' for inline formsets

        Returns:
            The formset class with dynamically adjusted max_num
        """
        inline = kwargs.get("inline")
        formset = super().get_formset(request, obj, **kwargs)

        # Example: Adjust max_num for description inline
        # if inline == RockSampleDescriptionInline:
        #     # Get vocabulary size from model
        #     vocabulary_size = len(RockSample.DESCRIPTION_TYPES.choices)
        #     formset.max_num = vocabulary_size

        return formset


# ============================================================================
# Example 2: Measurement Admin with Readonly Calculated Fields
# ============================================================================


# Commented out example - uncomment and adapt for your models
# @admin.register(XRFMeasurement)
class XRFMeasurementAdminExample(admin.ModelAdmin):
    """Example admin for Measurement models with calculated fields.

    This admin demonstrates:
    1. Readonly fields for system-managed data (UUID, timestamps)
    2. Readonly fields for calculated/derived values
    3. Organized fieldsets with collapsible sections
    4. Autocomplete widgets for foreign keys

    Pattern Usage:
    Use this pattern for Measurement models that have calculated fields
    (e.g., ratios, totals, quality scores) that should not be manually edited.
    """

    search_fields = ("name", "uuid")
    list_display = ("name", "dataset", "added", "modified")
    list_filter = ("dataset", "added")
    readonly_fields = (
        "uuid",
        "added",
        "modified",
        # Add calculated fields here
        # "total_concentration",
        # "quality_score",
    )
    # autocomplete_fields = ("dataset", "sample")

    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "name",
                    "uuid",
                    "dataset",
                    # "sample",
                )
            },
        ),
        (
            _("Measurement Data"),
            {
                "fields": (
                    # Add measurement-specific fields
                    # "concentration_ppm",
                    # "uncertainty",
                    # "detection_limit",
                )
            },
        ),
        (
            _("Calculated Values"),
            {
                "fields": (
                    # "total_concentration",
                    # "quality_score",
                ),
                "classes": ("collapse",),
                "description": _("These values are automatically calculated and cannot be edited manually."),
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("added", "modified"),
                "classes": ("collapse",),
            },
        ),
    )

    formfield_overrides = {
        models.ManyToManyField: {"widget": Select2MultipleWidget},
        models.ForeignKey: {"widget": Select2Widget},
        models.OneToOneField: {"widget": Select2Widget},
    }


# ============================================================================
# Best Practices Summary
# ============================================================================

"""
## Admin Interface Best Practices for FairDM Portals

### 1. Dynamic Inline Limits
- Set max_num based on vocabulary size to prevent validation errors
- Document the behavior in inline class docstrings
- Use get_formset() override in parent ModelAdmin

### 2. Bulk Export Actions
- Provide JSON export for metadata exchange
- Use select_related/prefetch_related for performance
- Include comprehensive metadata (not just basic fields)
- Set appropriate Content-Disposition header

### 3. Security Controls
- Never allow bulk visibility changes
- Make visibility changes individual and deliberate
- Document security rationale in docstrings
- Filter out potentially dangerous actions

### 4. Search & Filtering
- Always include UUID in search_fields
- Use list_filter for common query patterns
- Keep list_display concise (5-7 fields maximum)
- Consider custom list_filter classes for complex queries

### 5. Readonly Fields
- Protect UUIDs and timestamps from editing
- Mark calculated/derived fields as readonly
- Use fieldsets with collapse for secondary information
- Add field descriptions for clarity

### 6. Autocomplete Widgets
- Use autocomplete_fields for all ForeignKey/ManyToMany
- Ensure related models have search_fields configured
- Test autocomplete with large datasets
- Consider custom autocomplete views for complex filtering

### 7. Fieldset Organization
- Group related fields logically
- Use descriptive fieldset titles
- Collapse secondary/advanced sections by default
- Add fieldset descriptions when helpful

### 8. Performance Optimization
- Use select_related for ForeignKey relationships
- Use prefetch_related for ManyToMany/reverse ForeignKey
- Add database indexes for commonly filtered fields
- Monitor admin query performance with Django Debug Toolbar

## Testing Your Admin Interface

After customizing admin interfaces, test:
1. Search functionality with various queries
2. Filter combinations (especially complex ones)
3. Inline form limits (try exceeding max_num)
4. Bulk export with large datasets (performance)
5. Autocomplete response time with many records
6. Mobile responsiveness (Django admin is mobile-friendly)

See: `tests/integration/core/dataset/test_admin.py` for comprehensive admin tests.
"""


# ============================================================================
# Demo Sample Admin Classes
# ============================================================================


from fairdm.core.sample.admin import SampleChildAdmin

from .models import RockSample, WaterSample


@admin.register(RockSample)
class RockSampleAdmin(SampleChildAdmin):
    """Admin interface for RockSample model.

    Extends SampleAdmin to add custom fields and filters specific to geological
    rock samples. Demonstrates how to customize the base SampleAdmin for
    domain-specific sample types.

    Custom Features:
        - Additional list display: rock_type, mineral_content
        - Custom filters: rock_type, hardness range
        - Enhanced search: mineral_content
        - Fieldset for geological properties

    See Also:
        - fairdm.core.sample.admin.SampleAdmin: Base admin class
        - docs/portal-development/admin/sample-admin.md: Admin customization guide
    """

    base_model = RockSample
    show_in_index = True  # Show in main admin index

    # Add rock-specific fields to list display
    list_display = [*SampleChildAdmin.list_display, "rock_type", "mineral_content"]

    # Add rock-specific filters
    list_filter = [*SampleChildAdmin.list_filter, "rock_type"]

    # Add rock-specific search fields
    search_fields = [*SampleChildAdmin.search_fields, "mineral_content"]

    # Extend base_fieldsets to include geological properties
    fieldsets = (
        (
            "Geological Properties",
            {
                "fields": [
                    "rock_type",
                    "mineral_content",
                    "weight_grams",
                    "hardness_mohs",
                    "collection_date",
                ],
            },
        ),
    )


@admin.register(WaterSample)
class WaterSampleAdmin(SampleChildAdmin):
    """Admin interface for WaterSample model.

    Extends SampleAdmin to add custom fields and filters specific to water
    quality samples. Demonstrates how to customize the base SampleAdmin for
    environmental monitoring applications.

    Custom Features:
        - Additional list display: water_source, ph_level, temperature
        - Custom filters: water_source, ph range
        - Enhanced search: water_source
        - Fieldset for water quality parameters

    See Also:
        - fairdm.core.sample.admin.SampleAdmin: Base admin class
        - docs/portal-development/admin/sample-admin.md: Admin customization guide
    """

    base_model = WaterSample
    show_in_index = True  # Show in main admin index

    # Add water-specific fields to list display
    list_display = [
        *SampleChildAdmin.list_display,
        "water_source",
        "ph_level",
        "temperature_celsius",
    ]

    # Add water-specific filters
    list_filter = [*SampleChildAdmin.list_filter, "water_source"]

    # Add water-specific search fields
    search_fields = [*SampleChildAdmin.search_fields, "water_source"]

    # Extend base_fieldsets to include water quality parameters
    fieldsets = (
        (
            "Water Quality Parameters",
            {
                "fields": [
                    "water_source",
                    "temperature_celsius",
                    "ph_level",
                    "turbidity_ntu",
                    "dissolved_oxygen_mg_l",
                    "conductivity_us_cm",
                ],
            },
        ),
    )
