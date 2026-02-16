# Deployment Guide: Feature 006 - Core Measurements

**Feature**: Core Measurement Model Enhancement
**Date**: February 16, 2026
**Breaking Changes**: ⚠️ YES - Vocabulary validation changes
**Database Migrations**: ✅ None required (code-only changes)

## Overview

This feature enhances the `fairdm.core.measurement` app with improved admin, forms, filters, querysets, and permissions. All changes are code-only with no database schema modifications required.

**Key Point**: Vocabulary validation for `MeasurementDescription` and `MeasurementDate` changes from `Sample` collection to `Measurement` collection. This is a **breaking change** for existing portals with measurement data.

## Pre-Deployment Checklist

### 1. Data Audit (CRITICAL)

Before deploying, audit existing measurement metadata to identify invalid vocabulary values:

```python
# Run in Django shell: python manage.py shell
from fairdm.core.measurement.models import MeasurementDescription, MeasurementDate
from research_vocabs.vocabularies import from_collection

# Get valid measurement vocabularies
valid_desc_types = [v.id for v in from_collection("Measurement")]
valid_date_types = [v.id for v in from_collection("Measurement")]

# Check for invalid description types
invalid_descriptions = MeasurementDescription.objects.exclude(type__in=valid_desc_types)
print(f"Invalid description types: {invalid_descriptions.count()}")
for desc in invalid_descriptions:
    print(f"  - Measurement: {desc.content_object.name}, Type: {desc.type}")

# Check for invalid date types
invalid_dates = MeasurementDate.objects.exclude(type__in=valid_date_types)
print(f"Invalid date types: {invalid_dates.count()}")
for date in invalid_dates:
    print(f"  - Measurement: {date.content_object.name}, Type: {date.type}")
```

**Expected Results:**

- New portals: Should find 0 invalid records
- Existing portals: May find records with Sample-specific vocabulary types that need migration

### 2. Fix Invalid Vocabulary Values

If the audit finds invalid records, fix them before deployment:

```python
# Map old Sample vocabulary types to Measurement equivalents
VOCABULARY_MIGRATION = {
    # Sample-specific types that need mapping:
    # "collected": "collected",  # Already valid
    # "available": "available",  # Already valid
    # "created": "created",      # Already valid
    # Add any custom mappings here based on your portal's vocabulary
}

# Update invalid descriptions
for desc in invalid_descriptions:
    old_type = desc.type
    new_type = VOCABULARY_MIGRATION.get(old_type, "other")
    desc.type = new_type
    desc.save()
    print(f"Updated description: {old_type} → {new_type}")

# Update invalid dates
for date in invalid_dates:
    old_type = date.type
    new_type = VOCABULARY_MIGRATION.get(old_type, "created")
    date.type = new_type
    date.save()
    print(f"Updated date: {old_type} → {new_type}")
```

**Note**: Modify `VOCABULARY_MIGRATION` based on your portal's actual vocabulary values.

### 3. Backup Database

Even though there are no schema migrations, backup your database before deployment:

```bash
# PostgreSQL backup
pg_dump -U your_user -d your_database > backup_pre_feature006.sql

# Or use Django dbbackup (if installed)
poetry run python manage.py dbbackup
poetry run python manage.py mediabackup
```

### 4. Review Custom Measurement Types

If your portal has custom measurement types, verify they:

1. **Inherit from correct base**: `from fairdm.core import Measurement`
2. **Have get_value() method**: Returns string representation for admin list display
3. **Are registered**: Using `@register` decorator or manual registry.register()
4. **Use BaseMeasurementConfiguration**: If using registry auto-generation

## Deployment Steps

### Step 1: Deploy Code

```bash
# Pull latest code
git fetch origin
git checkout 006-core-measurements

# Update dependencies (if any changed)
poetry install

# Collect static files
poetry run python manage.py collectstatic --noinput
```

### Step 2: Verify No Migrations

Confirm that no database migrations are pending:

```bash
poetry run python manage.py showmigrations

# Should show no new migrations for core.measurement
# If migrations appear, STOP and investigate - this feature should be migration-free
```

### Step 3: Restart Application

```bash
# Docker deployment
docker-compose restart web

# Or systemd service
sudo systemctl restart fairdm

# Or gunicorn with systemd
sudo systemctl restart gunicorn
```

### Step 4: Verify Admin Interface

1. Navigate to `/admin/`
2. Go to **CORE** → **Measurements**
3. Verify type selection page appears with all registered measurement types
4. Click on a specific measurement type (e.g., **XRF Measurements**)
5. Verify list view displays correctly with polymorphic admin
6. Click **Add XRF Measurement**
7. Verify form loads with sample dropdown filtered by accessible datasets
8. Create a test measurement and verify it saves correctly

### Step 5: Test Metadata Editing

1. Edit an existing measurement
2. Add a description (verify type dropdown shows Measurement vocabularies)
3. Add a date (verify type dropdown shows Measurement vocabularies)
4. Save and verify no validation errors

### Step 6: Verify Permissions (If Applicable)

If using object-level permissions:

1. Test that measurement permissions respect dataset permissions
2. Verify cross-dataset measurements (measurement in Dataset B for sample in Dataset A)
3. Confirm permission checks work correctly

## Vocabulary Validation Approach

### How It Works

**Before Feature 006:**

- `MeasurementDescription` incorrectly used `from_collection("Sample")`
- `MeasurementDate` incorrectly used `from_collection("Sample")`
- This allowed Sample-specific vocabulary types on measurements (bug)

**After Feature 006:**

- Both use `from_collection("Measurement")` (correct)
- Only Measurement-specific vocabulary types are valid
- Validation happens at model level via `.clean()` method

### Code-Only Validation (No Database Enforcement)

**Why no database migrations?**

FairDM's vocabulary design intentionally avoids database-level `choices`:

```python
# AbstractDescription base class (fairdm/core/abstract.py)
class AbstractDescription(models.Model):
    type = models.CharField(max_length=50)  # NO choices parameter
    # Vocabularies defined at subclass level, not enforced by database
```

**Validation layers:**

1. **Form rendering**: Dropdown shows only valid vocabulary types from collection
2. **Model clean()**: Validates value is in vocabulary collection before save
3. **Admin interface**: Uses vocabulary-aware widgets that prevent invalid selection

**Benefit**: Vocabulary updates don't require database migrations

**Trade-off**: Existing invalid data won't be caught until user attempts to edit record

## Breaking Changes & Backward Compatibility

### Breaking Changes

⚠️ **Vocabulary Collection Change**

- **Breaking**: `MeasurementDescription.VOCABULARY` changed from `Sample` to `Measurement`
- **Breaking**: `MeasurementDate.VOCABULARY` changed from `Sample` to `Measurement`
- **Impact**: Existing measurements with Sample-specific vocabulary types will fail validation on edit
- **Mitigation**: Run data audit (see Pre-Deployment Checklist) and migrate invalid values

⚠️ **Admin Interface Changes**

- **Breaking**: Old `MeasurementAdmin` removed from `fairdm/core/admin.py`
- **Breaking**: Polymorphic parent/child admin pattern now required
- **Impact**: Custom measurement type admins must inherit from `MeasurementChildAdmin`
- **Mitigation**: Update custom admins to use new base class:

```python
# Before
from django.contrib import admin
class MyMeasurementAdmin(admin.ModelAdmin):
    pass

# After
from fairdm.core.measurement.admin import MeasurementChildAdmin
class MyMeasurementAdmin(MeasurementChildAdmin):
    pass
```

### Backward Compatible Changes

✅ **Model interface unchanged**: All public model methods work the same

✅ **QuerySet API additive**: New methods added (`with_related()`, `with_metadata()`), existing queries still work

✅ **Registration optional**: Registry auto-generation is opt-in; manual forms/tables/filters still work

✅ **Permissions additive**: New `MeasurementPermissionBackend` is additive; existing permissions unchanged

## Common Deployment Issues

### Issue 1: Validation Errors on Existing Measurements

**Symptom**: Admin forms show validation errors: "Select a valid choice. X is not one of the available choices."

**Cause**: Existing metadata uses Sample vocabulary types instead of Measurement types

**Solution**: Run data audit and fix invalid vocabulary values (see Pre-Deployment Checklist)

### Issue 2: Type Dropdown Empty

**Symptom**: When clicking "Add Measurement", type selection page is empty

**Cause**: No measurement types are registered

**Solution**: Verify registration in your app's `config.py`:

```python
# myapp/config.py
from fairdm.registry import register
from fairdm.registry.config import ModelConfiguration
from myapp.models import MyMeasurement

@register
class MyMeasurementConfig(ModelConfiguration):
    model = MyMeasurement
    fields = ["name", "sample", "dataset", "value"]
```

And ensure it's imported in `apps.py`:

```python
# myapp/apps.py
class MyAppConfig(AppConfig):
    name = 'myapp'

    def ready(self):
        import myapp.config  # Trigger registration
```

### Issue 3: Admin Shows Wrong Fields

**Symptom**: Admin edit page shows fields from wrong measurement type

**Cause**: Custom admin doesn't inherit from `MeasurementChildAdmin`

**Solution**: Update admin base class:

```python
from fairdm.core.measurement.admin import MeasurementChildAdmin

class MyMeasurementAdmin(MeasurementChildAdmin):
    base_model = MyMeasurement  # Specify the model
    list_display = ["name", "sample", "value", "dataset"]
```

### Issue 4: Sample Dropdown Empty in Forms

**Symptom**: Sample selection dropdown is empty when creating measurements

**Cause**: User doesn't have view permission for any datasets with samples

**Solution**: Grant appropriate dataset permissions to the user

### Issue 5: N+1 Query Problems in Admin List

**Symptom**: Admin list page is slow with many database queries

**Cause**: Not using optimized querysets

**Solution**: Override `get_queryset` in custom admin:

```python
class MyMeasurementAdmin(MeasurementChildAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.with_related()  # Loads sample and dataset in one query
```

### Issue 6: Migrations Appear Unexpectedly

**Symptom**: Running `makemigrations` shows new migrations for measurement models

**Cause**: Likely unrelated changes or Django version differences

**Solution**:

1. Review the migration content carefully
2. Verify it's not related to vocabulary changes (which should never generate migrations)
3. If it's an unrelated model change, that's OK
4. If it IS vocabulary-related, something is wrong - investigate before deploying

## Post-Deployment Verification

### Smoke Tests

Run these checks after deployment:

1. ✅ Admin loads without errors: `/admin/`
2. ✅ Measurement type selection works: `/admin/core/measurement/add/`
3. ✅ List view displays measurements: `/admin/core/xrfmeasurement/` (or your type)
4. ✅ Create new measurement: Fill form, save, verify success
5. ✅ Edit existing measurement: Metadata editing works, vocabularies correct
6. ✅ Delete measurement: Deletion works without errors
7. ✅ Permissions respected: Non-permitted users cannot access measurements

### Full Regression Test

If using pytest test suite:

```bash
# Run all measurement tests
poetry run pytest tests/test_core/test_measurement/ -v

# Run integration tests specifically
poetry run pytest tests/test_core/test_measurement/test_integration.py -v
```

Expected: All tests pass

## Rollback Procedure

If deployment fails and you need to rollback:

### Step 1: Restore Previous Code

```bash
# Checkout previous stable branch/tag
git checkout main  # or previous stable version

# Restart application
docker-compose restart web
# or
sudo systemctl restart fairdm
```

### Step 2: Verify Application Works

Navigate to admin and verify basic functionality works

### Step 3: Restore Database (If Needed)

Only needed if you applied vocabulary migrations during pre-deployment:

```bash
# Restore from backup
psql -U your_user -d your_database < backup_pre_feature006.sql

# Or use Django dbbackup
poetry run python manage.py dbrestore
```

### Step 4: Report Issues

Document the failure and report to development team:

- What error occurred
- When it occurred (during deployment, after, specific user action)
- Error messages and stack traces
- Steps to reproduce

## Support & Troubleshooting

### Debug Mode

Enable Django debug logging to diagnose issues:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'fairdm.core.measurement': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Useful Management Commands

```bash
# Check for invalid vocabulary values
poetry run python manage.py shell < check_vocab_audit.py

# View all registered measurement types
poetry run python manage.py shell
>>> from fairdm.registry import registry
>>> for model in registry.measurements:
...     print(model.__name__)

# Check permissions
poetry run python manage.py shell
>>> from django.contrib.auth.models import User
>>> user = User.objects.get(username='testuser')
>>> user.get_all_permissions()
```

### Common Log Messages

**If you see:**

```
ValidationError: Select a valid choice. 'collected' is not one of the available choices.
```

**Action**: Run vocabulary audit, some metadata has old Sample vocabulary types

**If you see:**

```
AttributeError: 'Measurement' object has no attribute 'get_value'
```

**Action**: Custom measurement type missing `get_value()` method - add it to your model

**If you see:**

```
ValueError: Cannot query "MeasurementDescription": Must be "Measurement" instance.
```

**Action**: Likely a relationship query issue - check your model definitions

## Additional Resources

- **Feature Spec**: [specs/006-core-measurements/spec.md](spec.md)
- **Developer Quickstart**: [specs/006-core-measurements/quickstart.md](quickstart.md)
- **Research & Decisions**: [specs/006-core-measurements/research.md](research.md)
- **Portal Development Guide**: [docs/portal-development/measurements.md](../../docs/portal-development/measurements.md)
- **Admin Guide**: [docs/portal-administration/managing-measurements.md](../../docs/portal-administration/managing-measurements.md)
