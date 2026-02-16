# Quickstart: Core Measurement Enhancement

**Feature**: 006-core-measurements | **Date**: February 16, 2026

## Overview

This feature enhances the existing `fairdm.core.measurement` app to match the architecture and quality level of `fairdm.core.sample`. No new database models are added — the work consists of fixing vocabulary bugs, adding missing components (queryset, permissions, admin, forms, filters), and establishing reusable base classes for portal developers.

## What Changes

### Bug Fixes

- Fix `MeasurementDescription.VOCABULARY` and `MeasurementDate.VOCABULARY` — currently using Sample vocabulary, corrected to Measurement vocabulary
- Fix `plugins.py` inline model references — currently using `SampleDescription`/`SampleDate`, corrected to `MeasurementDescription`/`MeasurementDate`
- Fix `MeasurementForm` — currently excludes non-existent fields
- Fix `get_absolute_url()` — currently delegates to sample, changed to measurement URL pattern

### New Components

- `MeasurementQuerySet` with `with_related()` and `with_metadata()` optimization methods
- `MeasurementPermissionBackend` inheriting permissions from parent Dataset
- `MeasurementFormMixin` with autocomplete widgets and dataset-scoped sample filtering
- `MeasurementFilterMixin` and rich `MeasurementFilter` with search, type, and cross-relationship filters
- `MeasurementChildAdmin` and `MeasurementParentAdmin` (polymorphic admin pattern)
- `BaseMeasurementConfiguration` for registry integration
- Complete test suite mirroring sample test coverage

### New Files

| File | Purpose |
|------|---------|
| `fairdm/core/measurement/managers.py` | MeasurementQuerySet |
| `fairdm/core/measurement/permissions.py` | MeasurementPermissionBackend |
| `fairdm/core/measurement/config.py` | BaseMeasurementConfiguration |
| `tests/test_core/test_measurement/conftest.py` | Test fixtures |
| `tests/test_core/test_measurement/test_models.py` | Model tests |
| `tests/test_core/test_measurement/test_admin.py` | Admin tests |
| `tests/test_core/test_measurement/test_forms.py` | Form tests |
| `tests/test_core/test_measurement/test_filters.py` | Filter tests |
| `tests/test_core/test_measurement/test_permissions.py` | Permission tests |
| `tests/test_core/test_measurement/test_registry.py` | Registry tests |

### Modified Files

| File | Changes |
|------|---------|
| `fairdm/core/measurement/models.py` | Vocabulary fixes, custom manager |
| `fairdm/core/measurement/admin.py` | Full polymorphic admin rewrite |
| `fairdm/core/measurement/forms.py` | Mixin pattern rewrite |
| `fairdm/core/measurement/filters.py` | Rich filter rewrite |
| `fairdm/core/measurement/plugins.py` | Fix inline model references |
| `fairdm/core/admin.py` | Remove old measurement admin (moved) |
| `fairdm_demo/admin.py` | Add measurement child admins |
| `fairdm_demo/config.py` | Use BaseMeasurementConfiguration |

## Developer Impact

### For Portal Developers

**Defining custom measurement types** (unchanged workflow):

```python
# models.py
from fairdm.core.models import Measurement

class XRFMeasurement(Measurement):
    element = models.CharField(max_length=10)
    concentration_ppm = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        verbose_name = "XRF Measurement"
```

**Registering with the registry** (now with BaseMeasurementConfiguration available):

```python
# config.py
from fairdm.registry import register
from fairdm.core.measurement.config import BaseMeasurementConfiguration
from .models import XRFMeasurement

@register
class XRFMeasurementConfig(BaseMeasurementConfiguration):
    model = XRFMeasurement
    fields = ["name", "dataset", "sample", "element", "concentration_ppm"]
```

**Custom admin** (now following polymorphic pattern):

```python
# admin.py
from fairdm.core.measurement.admin import MeasurementChildAdmin

class XRFMeasurementAdmin(MeasurementChildAdmin):
    base_fieldsets = (
        (None, {"fields": ["name", "dataset", "sample", "element", "concentration_ppm"]}),
        ("Metadata", {"fields": ["uuid", "added", "modified"], "classes": ["collapse"]}),
    )
```

### Deployment Steps

**No database migrations required** — all changes are code-only:

1. Deploy code changes (models, forms, admin, filters, managers, permissions)
2. Run data audit: `python manage.py shell` to check existing `MeasurementDescription.type` and `MeasurementDate.type` values against `from_collection("Measurement")`
3. Fix any invalid vocabulary values before users attempt to edit measurements (model `.clean()` will reject invalid types)
4. Verify admin interface displays correctly with polymorphic parent/child pattern
5. Test filtered sample selection in measurement creation forms

**Note**: Vocabulary changes do not create migrations because `Abstract*` base classes do not set database-level `choices` on CharField.

### Documentation Requirements

All new components require documentation per FairDM Constitution Principle VI:

- **Portal Development Guide**: Custom measurement type tutorial with complete example
- **Admin Guide**: Polymorphic admin usage for portal administrators
- **API Reference**: Sphinx autodoc for all new classes (QuerySet, forms, filters, admin)
- **Overview Documentation**: Data model flows and cross-dataset relationships
- **Deployment Guide**: Data audit procedures for vocabulary validation

Documentation is considered part of the implementation and must be completed before feature is marked as done.
