# Demo App Preparation: Configuration & Admin

**Feature**: 006-core-datasets
**Purpose**: Prepare fairdm_demo configuration and admin for updated Dataset functionality
**Files**: `fairdm_demo/config.py`, `fairdm_demo/admin.py`

---

## Option A: Registry Configuration (config.py)

**Recommended approach** using FairDM's registry system.

### Create/Update fairdm_demo/config.py

```python
"""
Demo app registry configuration.

Demonstrates FairDM registry patterns for custom models.
"""

from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration

from .models import RockSample, XRFMeasurement, GeologicalDataset


@register
class RockSampleConfig(ModelConfiguration):
    """
    Registry configuration for RockSample model.

    Demonstrates:
    - Basic field configuration
    - Table columns for list views
    - Filter configuration
    - Form field customization
    """
    model = RockSample

    # Fields for auto-generated components
    fields = [
        'name',
        'rock_type',
        'weight_grams',
        'collection_location',
        'collection_date',
    ]

    # Customize table display
    table_fields = [
        'name',
        'rock_type',
        'weight_grams',
        'collection_location',
        'collection_date',
    ]

    # Enable filtering
    filterset_fields = [
        'rock_type',
        'collection_location',
        'collection_date',
    ]

    # Display metadata
    display_name = "Rock Sample"
    description = "Geological rock samples with metadata"


@register
class XRFMeasurementConfig(ModelConfiguration):
    """
    Registry configuration for XRFMeasurement model.

    Demonstrates:
    - Scientific measurement fields
    - Decimal number handling
    - Related sample filtering
    """
    model = XRFMeasurement

    fields = [
        'sample',
        'element',
        'concentration_ppm',
        'detection_limit_ppm',
        'measurement_date',
        'instrument',
    ]

    table_fields = [
        'sample',
        'element',
        'concentration_ppm',
        'measurement_date',
    ]

    filterset_fields = [
        'element',
        'sample',
        'measurement_date',
    ]

    display_name = "XRF Measurement"
    description = "X-ray fluorescence analysis measurements"


@register
class GeologicalDatasetConfig(ModelConfiguration):
    """
    Registry configuration for GeologicalDataset model.

    Demonstrates:
    - Dataset subclass configuration
    - Inheriting base Dataset functionality
    - Adding domain-specific fields
    """
    model = GeologicalDataset

    # Combine base Dataset fields + custom fields
    fields = [
        'name',
        'project',
        'description',
        'image',
        'license',
        'visibility',
        'region',
        'geological_age',
        'survey_type',
    ]

    table_fields = [
        'name',
        'project',
        'region',
        'geological_age',
        'survey_type',
        'visibility',
    ]

    filterset_fields = [
        'project',
        'region',
        'geological_age',
        'survey_type',
        'visibility',
        'license',
    ]

    display_name = "Geological Dataset"
    description = "Datasets for geological research projects"
```

---

## Option B: Django Admin (admin.py)

**Alternative approach** using standard Django admin (if not using registry).

### Create/Update fairdm_demo/admin.py

```python
"""
Demo app admin configuration.

Demonstrates Django admin patterns for custom FairDM models.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import RockSample, XRFMeasurement, GeologicalDataset


@admin.register(RockSample)
class RockSampleAdmin(admin.ModelAdmin):
    """
    Admin interface for RockSample.

    Demonstrates:
    - Search configuration
    - List display customization
    - Filtering options
    - Date hierarchy
    """
    list_display = [
        'name',
        'rock_type',
        'weight_grams',
        'collection_location',
        'collection_date',
    ]

    list_filter = [
        'rock_type',
        'collection_date',
    ]

    search_fields = [
        'name',
        'collection_location',
        'rock_type',
    ]

    date_hierarchy = 'collection_date'

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'rock_type')
        }),
        (_('Physical Properties'), {
            'fields': ('weight_grams',)
        }),
        (_('Collection Details'), {
            'fields': ('collection_location', 'collection_date')
        }),
    )


@admin.register(XRFMeasurement)
class XRFMeasurementAdmin(admin.ModelAdmin):
    """
    Admin interface for XRFMeasurement.

    Demonstrates:
    - Related object autocomplete
    - Decimal field handling
    - Inline measurements (optional)
    """
    list_display = [
        'sample',
        'element',
        'concentration_ppm',
        'detection_limit_ppm',
        'measurement_date',
    ]

    list_filter = [
        'element',
        'measurement_date',
    ]

    search_fields = [
        'sample__name',
        'element',
        'instrument',
    ]

    autocomplete_fields = ['sample']

    date_hierarchy = 'measurement_date'

    fieldsets = (
        (_('Measurement Details'), {
            'fields': ('sample', 'element', 'measurement_date')
        }),
        (_('Results'), {
            'fields': ('concentration_ppm', 'detection_limit_ppm')
        }),
        (_('Equipment'), {
            'fields': ('instrument',),
            'classes': ('collapse',)
        }),
    )


class XRFMeasurementInline(admin.TabularInline):
    """
    Inline editor for measurements on Sample admin.

    Allows adding measurements directly from sample edit page.
    """
    model = XRFMeasurement
    extra = 1
    fields = ['element', 'concentration_ppm', 'detection_limit_ppm', 'measurement_date']


# Add inline to RockSampleAdmin if using Option B
# RockSampleAdmin.inlines = [XRFMeasurementInline]


@admin.register(GeologicalDataset)
class GeologicalDatasetAdmin(admin.ModelAdmin):
    """
    Admin interface for GeologicalDataset.

    Demonstrates:
    - Dataset subclass admin
    - Combining base + custom fields
    - Advanced filtering
    """
    list_display = [
        'name',
        'project',
        'region',
        'geological_age',
        'survey_type',
        'visibility',
        'has_data',
    ]

    list_filter = [
        'survey_type',
        'geological_age',
        'visibility',
        'license',
    ]

    search_fields = [
        'name',
        'uuid',
        'region',
        'geological_age',
    ]

    autocomplete_fields = [
        'project',
        'related_literature',
    ]

    readonly_fields = [
        'uuid',
        'added',
        'modified',
    ]

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'project', 'description')
        }),
        (_('Geological Details'), {
            'fields': ('region', 'geological_age', 'survey_type')
        }),
        (_('Media & Licensing'), {
            'fields': ('image', 'license')
        }),
        (_('Access Control'), {
            'fields': ('visibility',)
        }),
        (_('System Information'), {
            'fields': ('uuid', 'added', 'modified'),
            'classes': ('collapse',)
        }),
    )

    def has_data(self, obj):
        """Display indicator if dataset has samples/measurements."""
        return obj.has_data
    has_data.boolean = True
    has_data.short_description = _('Has Data')
```

---

## Recommendation: Use Both

**Best practice**: Use registry (config.py) for frontend + Option B admin for advanced admin features.

```python
# config.py - For auto-generated forms, filters, tables
@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = [...]

# admin.py - For advanced admin features
@admin.register(RockSample)
class RockSampleAdmin(admin.ModelAdmin):
    # Advanced admin customizations
    inlines = [XRFMeasurementInline]
    actions = ['export_to_csv']
```

Registry handles:

- Frontend forms
- List/table views
- Basic filtering
- API serializers (if enabled)

Admin handles:

- Advanced search
- Bulk actions
- Inline editing
- Custom admin views

---

## Testing Configuration

### Test Registry Configuration

```python
# In fairdm_demo/tests/test_config.py

import pytest
from fairdm.registry import registry
from fairdm_demo.models import RockSample, GeologicalDataset


def test_rock_sample_registered():
    """RockSample is registered in FairDM registry."""
    assert registry.is_registered(RockSample)


def test_rock_sample_config():
    """RockSample configuration has expected fields."""
    config = registry.get_for_model(RockSample)

    assert 'name' in config.fields
    assert 'rock_type' in config.fields
    assert 'weight_grams' in config.fields


def test_geological_dataset_registered():
    """GeologicalDataset is registered in registry."""
    assert registry.is_registered(GeologicalDataset)


def test_geological_dataset_inherits_dataset_config():
    """GeologicalDataset config includes base Dataset fields."""
    config = registry.get_for_model(GeologicalDataset)

    # Base Dataset fields
    assert 'name' in config.fields
    assert 'project' in config.fields
    assert 'license' in config.fields

    # Custom fields
    assert 'region' in config.fields
    assert 'geological_age' in config.fields
```

### Test Admin Configuration

```python
# In fairdm_demo/tests/test_admin.py

import pytest
from django.contrib.admin.sites import AdminSite
from fairdm_demo.admin import RockSampleAdmin, XRFMeasurementAdmin
from fairdm_demo.models import RockSample, XRFMeasurement


@pytest.mark.django_db
def test_rock_sample_admin_registered():
    """RockSampleAdmin is registered."""
    site = AdminSite()
    assert RockSample in site._registry or admin.site.is_registered(RockSample)


@pytest.mark.django_db
def test_xrf_measurement_inline():
    """XRFMeasurement can be edited inline on RockSample."""
    admin_instance = RockSampleAdmin(RockSample, AdminSite())

    # Check if inline is configured
    inline_models = [inline.model for inline in admin_instance.inlines]
    assert XRFMeasurement in inline_models


@pytest.mark.django_db
def test_geological_dataset_search_fields():
    """GeologicalDataset admin has correct search fields."""
    from fairdm_demo.admin import GeologicalDatasetAdmin

    admin_instance = GeologicalDatasetAdmin(GeologicalDataset, AdminSite())

    assert 'name' in admin_instance.search_fields
    assert 'region' in admin_instance.search_fields
    assert 'geological_age' in admin_instance.search_fields
```

---

## Migration Notes

No database migrations required for configuration changes.

If adding custom admin actions:

1. Document in docstrings
2. Add permissions checks
3. Test with factory-created data

---

## Documentation Comments

Add comprehensive module-level docstrings:

```python
"""
FairDM Demo App Configuration.

This module demonstrates best practices for configuring custom FairDM models
using the registry system. It shows how to:

1. Register custom Sample types (RockSample)
2. Register custom Measurement types (XRFMeasurement)
3. Register Dataset subclasses (GeologicalDataset)
4. Configure auto-generated components (forms, filters, tables)
5. Customize display metadata

For Django Admin customization, see admin.py.

Registry Benefits:
    - Automatic form generation
    - Consistent filtering across models
    - API serializer generation (if enabled)
    - Less boilerplate code

Usage:
    The registry is automatically loaded when Django starts.
    No manual registration calls needed.

Examples:
    >>> from fairdm.registry import registry
    >>> config = registry.get_for_model(RockSample)
    >>> form_class = config.form
    >>> table_class = config.table

See Also:
    - :mod:`fairdm.registry`: Core registry system
    - :class:`fairdm.registry.config.ModelConfiguration`: Base configuration class
    - Developer Guide: Registry Configuration
"""
```

---

## Next Steps

After configuration:

1. Test auto-generated forms
2. Verify admin interface
3. Check API endpoints (if enabled)
4. Update demo app documentation
5. Add usage examples to quickstart.md
