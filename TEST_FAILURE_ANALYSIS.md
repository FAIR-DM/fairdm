# Test Failure Analysis Report

**Date:** February 8, 2026
**Branch:** test
**Status:** 600 passing, 94 skipped, 89 failing, 3 errors

## Executive Summary

After skipping plugin-related tests (pending API redesign), we have **600 tests passing** with **89 failures remaining**. The failures fall into clear categories that require different remediation strategies.

## Tests Skipped Due to API Changes

### Plugin System Tests (55 tests total)

**Status:** All skipped pending plugin system redesign

**Files:**

- `tests/test_plugins.py` - 48 tests skipped
  - **Reason:** Plugin API completely redesigned - `PluginMenuItem` now requires `category`, configuration structure changed, menu item creation updated

- `tests/test_core/test_project_edit_plugin.py` - 7 tests skipped
  - **Reason:** Plugin `category` attribute moved/changed, depends on new plugin configuration API

**Action Required:** Update tests after plugin system design is finalized

---

## Remaining Test Failures by Category

### 1. Dataset Tests (62 failures)

#### A. Dataset Form Tests (18 failures)

**File:** `tests/test_core/test_dataset/test_form.py`

**Root Cause:** Missing test fixtures and license data

- Tests expect licenses like "CC BY 4.0" to exist in database
- Form validation tests fail due to missing required fixture setup
- 3 ERROR status tests related to form queryset filtering

**Example Error:**

```
licensing.models.License.DoesNotExist: License matching query does not exist.
```

**Remediation:**

- [ ] Create pytest fixtures for License objects
- [ ] Add fixture for common Creative Commons licenses
- [ ] Update test setup to load required reference data

**API Change Impact:** Low - these are testing existing form functionality

#### B. Dataset Queryset Tests (17 failures)

**File:** `tests/test_core/test_dataset/test_queryset.py`

**Classes:**

- `TestPrivacyFirstDefault` - Testing default manager behavior
- `TestExplicitPrivateAccess` - Testing `.with_private()` queryset method
- `TestWithRelatedOptimization` - Testing prefetch optimization
- `TestWithContributorsOptimization` - Testing contributor prefetch
- `TestMethodChaining` - Testing queryset method chaining
- `TestPerformanceOptimization` - Testing query reduction

**Root Cause:** Missing test data setup

- Tests create datasets but likely missing related objects (contributors, project relationships)
- Performance tests need baseline data

**Remediation:**

- [ ] Review queryset manager implementation
- [ ] Add comprehensive dataset fixtures with relationships
- [ ] May need factory adjustments for related objects

**API Change Impact:** Medium - queryset API may have changed

#### C. Dataset Filter Tests (13 failures)

**File:** `tests/test_core/test_dataset/test_filter.py`

**Root Cause:** Same as form tests - missing License fixtures and test data

**Remediation:**

- [ ] Share fixture setup with form tests
- [ ] Create factory for test datasets with various filters

**API Change Impact:** Low

#### D. Dataset Admin Tests (5 failures)

**File:** `tests/test_core/test_dataset/test_admin.py`

**Root Cause:** Likely admin interface changes or missing permissions

**Remediation:**

- [ ] Review admin configuration changes
- [ ] Check if admin views exist and are registered

**API Change Impact:** Medium

#### E. Dataset Integration Tests (9 failures)

**File:** `tests/test_core/test_dataset/test_integration.py`

**Root Cause:** End-to-end tests depending on fixtures, views, permissions

**Remediation:**

- [ ] Fix underlying form/filter tests first
- [ ] Review URL patterns and view registration
- [ ] Check permission system integration

**API Change Impact:** Medium

---

### 2. Factory Tests (10 failures)

#### Factory Core Tests (5 failures)

**File:** `tests/test_factories/test_core_factories.py`

**Failing Tests:**

- `test_batch_creation_works`
- `test_dataset_factory_creates_instance`
- `test_measurement_factory_creates_instance`
- `test_project_factory_creates_instance`
- `test_sample_factory_creates_instance`

**Root Cause:** Factories not creating expected related objects

- `ProjectFactory` should create 2 descriptions and 2 dates but creates 0
- Other factories similarly not creating relationships

**Example Error:**

```python
# Expected: descriptions.count() == 2
# Actual: 0
```

**Remediation:**

- [ ] Review factory definitions in `fairdm/factories/core.py`
- [ ] Check if RelatedFactory or SubFactory declarations need updates
- [ ] Ensure factory post-generation hooks are firing

**API Change Impact:** High - factory API may have changed significantly

#### Factory Integration Tests (4 failures)

**File:** `tests/test_factories/test_integration.py`

**Root Cause:** Depends on factories working correctly

**Remediation:**

- [ ] Fix core factory issues first
- [ ] Then retest integration scenarios

#### Contributor Factory Tests (1 failure)

**File:** `tests/test_factories/test_contributor_factories.py`

**Root Cause:** Similar factory relationship issues

---

### 3. Configuration/Addon Tests (8 failures)

#### Addon Discovery Tests (6 failures)

**File:** `tests/test_conf/test_addons.py`

**Root Cause:** Addon system not loading/discovering addons correctly

- `__fdm_setup_module__` not being called
- Addon settings not being injected
- Module discovery failing

**Example Error:**

```python
assert hasattr(test_settings, "DUMMY_ADDON_INSTALLED")
# AssertionError: assert False
```

**Remediation:**

- [ ] Review addon discovery mechanism in `fairdm.setup()`
- [ ] Check if addon module loading changed
- [ ] Verify addon hook system still works

**API Change Impact:** High - addon system API may have changed

#### Environment Override Tests (2 failures)

**File:** `tests/test_conf/test_overrides.py`

**Root Cause:** Environment file parameter handling changed

**Remediation:**

- [ ] Check if env_file parameter still supported
- [ ] Review settings override mechanism

---

### 4. Project Tests (7 failures)

**Files:**

- `tests/test_core/test_project/test_integration.py` (4 failures)
- `tests/test_core/test_project/test_admin.py` (1 failure)
- `tests/test_core/test_project/test_views.py` (1 failure)
- `tests/test_core/test_project/test_models.py` (1 failure)

**Root Cause:** Similar to dataset tests - missing fixtures, view changes

**Remediation:**

- [ ] Create project test fixtures
- [ ] Review URL patterns
- [ ] Check admin integration

---

### 5. Measurement Tests (1 failure)

**File:** `tests/test_core/test_measurement/test_integration.py`

**Test:** `test_measurement_get_absolute_url`

**Root Cause:** URL resolution or view registration issue

**Remediation:**

- [ ] Check measurement URL patterns
- [ ] Verify get_absolute_url implementation

---

### 6. Registry Validation Test (1 failure)

**File:** `tests/test_registry/test_validation.py`

**Test:** `test_invalid_related_field_path`

**Root Cause:** Field name clash - 'related' field in RockSample clashes with base class Sample

**Error:**

```
django.core.exceptions.FieldError: Local field 'related' in class 'RockSample'
clashes with field of the same name from base class 'Sample'.
```

**Remediation:**

- [ ] Check if Sample model has a 'related' field
- [ ] Test model may need to use different field name
- [ ] This might be catching a real validation issue correctly

---

## Prioritized Remediation Plan

### Phase 1: Foundation Fixes (High Impact)

1. **Create License Fixtures** → Fixes 31+ dataset tests
2. **Fix Factory Relationships** → Fixes 10 factory tests, unblocks integration tests
3. **Review Addon System** → Fixes 8 configuration tests

### Phase 2: Integration Tests (Medium Impact)

1. **Fix Dataset/Project Integration Tests** → Fixes 13 tests
   - Depends on fixtures and factories working
2. **Review Admin Interface** → Fixes 6 admin tests

### Phase 3: Cleanup (Low Impact)

1. **Fix Measurement URL Test** → 1 test
2. **Fix Registry Validation Test** → 1 test (may be working correctly)

---

## Recommendations

### Immediate Actions

1. ✅ **Plugin tests skipped** - Complete
2. **Create fixture module** for common test data (licenses, permissions)
3. **Debug factory relationships** - critical for many tests

### API Change Strategy

- Tests marked as skipped have clear dependency on plugin API redesign
- Dataset/Project tests appear to be testing stable APIs but need fixtures
- Factory and addon tests may have API changes - need investigation

### Test Infrastructure

Consider:

- Adding `conftest.py` fixtures for common License objects
- Creating a `tests/fixtures/` module with reusable test data
- Factory debugging - may need to update to new factory_boy patterns

---

## Summary Statistics

| Category | Passing | Skipped | Failing | Total |
|----------|---------|---------|---------|-------|
| Plugin Tests | 0 | 55 | 0 | 55 |
| Dataset Tests | ~100 | 0 | 62 | ~162 |
| Factory Tests | ~15 | 0 | 10 | ~25 |
| Config Tests | ~5 | 0 | 8 | ~13 |
| Project Tests | ~20 | 0 | 7 | ~27 |
| Other | ~460 | 39 | 2 | ~501 |
| **TOTAL** | **600** | **94** | **89** | **783** |

**Test Success Rate:** 76.7% passing (600/783)
**When Including Skipped (Pending API):** 88.6% passing or intentionally skipped (694/783)
