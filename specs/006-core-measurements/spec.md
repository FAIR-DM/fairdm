# Feature Specification: Core Measurement Model Enhancement

**Feature Branch**: `006-core-measurements`
**Created**: February 16, 2026
**Status**: Draft
**Input**: User description: "The measurements app captures and manages scientific observations and analytical results derived from research samples. Measurements represent the actual data outputs of research—the quantitative and qualitative values obtained when analyzing samples. This feature follows the same enhancement pattern applied to the Sample model (Feature 005). Client-side integration is out of scope."

## Clarifications

### Session 2026-02-16

- Q: Should vocabulary migration from Sample to Measurement collections use backwards compatibility or accept potential data loss? → A: Vocabulary changes are code-only with NO database migration. Abstract* base classes (AbstractDescription, AbstractDate) do not set CharField `choices` at the database level. Validation happens at the model level via `clean()` methods. Existing records with invalid vocabulary types will fail validation on next save, requiring data audit before deployment.
- Q: Should Measurement.get_absolute_url() defer to sample detail view or return placeholder URL for future measurement detail views? → A: Return placeholder URL - measurement detail views will be implemented in future but URL pattern should be defined now
- Q: How should cross-dataset sample selection be implemented when creating measurements? → A: Use filtered queryset limited to samples included in the measurement's dataset. Users must first add samples to their dataset (create new or add from another dataset), then they can create measurements on those samples
- Q: How should polymorphic measurement admin be configured? → A: Use existing PolymorphicParentModelAdmin/PolymorphicChildModelAdmin pattern from Sample app. MeasurementParentAdmin (already defined in fairdm/core/admin.py) handles type selection, individual measurement subtype admins inherit from MeasurementChildAdmin (currently named MeasurementAdmin in fairdm/core/admin.py)
- Q: What should the prefetch strategy be for QuerySet optimization methods? → A: Balanced prefetching - with_related() prefetches direct relationships (sample, dataset, contributors), with_metadata() prefetches descriptions/dates/identifiers, deep nested relationships left to specific views

## User Scenarios & Testing

### User Story 1 - Measurement Model Polymorphism & Registry Integration (Priority: P1)

As a portal developer using FairDM, I want the Measurement model to support polymorphic inheritance and seamlessly integrate with the FairDM registry (Feature 002) so that I can define domain-specific measurement types (e.g., XRF analysis, water quality parameters) that automatically get forms, filters, tables, and admin interfaces without manual coding.

**Why this priority**: Polymorphic measurement support and registry integration are the foundation of FairDM's extensibility for research data. If measurements cannot be subclassed and auto-registered, the framework cannot capture domain-specific scientific results.

**Independent Test**: Can be fully tested by defining custom measurement models inheriting from Measurement, registering them via the registry, and verifying polymorphic queries and auto-generated components work correctly. Success is demonstrated when custom measurement types integrate seamlessly without manual form/filter/admin creation.

**Acceptance Scenarios**:

1. **Given** I define a new measurement type inheriting from Measurement (e.g., XRFMeasurement with element and concentration fields), **When** I register it using the FairDM registry, **Then** the registry auto-generates appropriate forms, filters, tables, and admin interfaces.
2. **Given** I have multiple measurement types registered (XRFMeasurement, WaterQualityMeasurement), **When** I query Measurement.objects.all(), **Then** I receive polymorphic results returning the correct subclass instances with type-specific fields.
3. **Given** I have a custom measurement type with additional fields, **When** I create instances via the auto-generated form, **Then** both base Measurement fields and custom fields are properly handled and persisted.
4. **Given** I register a custom measurement without providing custom form/filter classes, **When** the registry auto-generates defaults, **Then** the generated components work correctly for CRUD operations.
5. **Given** I have polymorphic measurement types in the database, **When** I access the admin interface, **Then** each measurement type displays with its appropriate admin configuration.

---

### User Story 2 - Cross-Dataset Measurement-Sample Linking (Priority: P1)

As a researcher, I want to create measurements in my dataset that reference samples belonging to a different dataset, so that I can analyze shared samples across studies while maintaining clear provenance about which dataset owns the sample and which dataset owns the measurement.

**Why this priority**: Cross-dataset linking is a core research workflow. Samples are frequently shared between research groups, and measurements made on those samples must correctly attribute dataset ownership. This directly impacts data integrity, permissions, and FAIR provenance.

**Independent Test**: Can be fully tested by creating a measurement in Dataset A that references a sample from Dataset B, verifying that the measurement's dataset field correctly records Dataset A, the sample link correctly points to the sample in Dataset B, and that permission boundaries are preserved (researcher in Dataset A cannot edit the sample from Dataset B).

**Acceptance Scenarios**:

1. **Given** I have edit access to Dataset A and there is a sample from Dataset B that has been added to Dataset A, **When** I create a measurement in Dataset A and link it to that sample, **Then** the measurement is created successfully with the sample reference preserved.
2. **Given** a measurement in Dataset A references a sample originally from Dataset B, **When** I view the measurement, **Then** the provenance clearly shows which dataset owns the measurement and the original source dataset of the sample.
3. **Given** I have edit access to Dataset A containing a sample originally from Dataset B, **When** I attempt to edit that sample, **Then** the permission check is based on the sample's current dataset context and ownership rules.
4. **Given** a measurement references a sample, **When** an attempt is made to delete the sample, **Then** the deletion is prevented (PROTECT behavior on sample FK) with a clear message indicating measurements depend on this sample.
5. **Given** I am selecting a sample for a new measurement in Dataset A, **When** the sample selection interface renders, **Then** I can only see and select samples that have been added to Dataset A (whether created in A or added from other datasets).

---

### User Story 3 - Enhanced Measurement Admin Interface (Priority: P1)

As a portal administrator, I want a comprehensive Django admin interface for measurements that provides search, filtering, inline metadata editing, correct vocabulary references, and proper handling of polymorphic measurement types so that I can efficiently manage measurements and their metadata without writing custom code.

**Why this priority**: The admin interface is the primary tool for administrators to manage measurement data. The current admin has vocabulary mismatches (using Sample vocabularies instead of Measurement vocabularies) and limited functionality that must be corrected.

**Independent Test**: Can be fully tested by accessing the admin interface, performing searches, applying filters, editing measurements with inline metadata, and working with different polymorphic measurement types. Success is demonstrated when all admin operations work correctly, vocabularies reference the correct Measurement-specific types, and polymorphic types are handled.

**Acceptance Scenarios**:

1. **Given** I am in the measurement admin list view, **When** I search by measurement name or UUID, **Then** matching measurements appear in results.
2. **Given** I am viewing a measurement in the admin, **When** I add a description inline, **Then** the description type choices come from the Measurement vocabulary (not Sample vocabulary).
3. **Given** I am viewing a measurement in the admin, **When** I add a key date inline, **Then** the date type choices come from the Measurement vocabulary (not Sample vocabulary).
4. **Given** I am viewing the measurement admin list, **When** I apply filters for dataset, sample, or polymorphic type, **Then** the list updates to show only matching measurements.
5. **Given** I am editing a measurement, **When** I use the sample field, **Then** I can search and select samples with autocomplete functionality.
6. **Given** I have multiple polymorphic measurement types, **When** I view the admin list, **Then** each measurement displays with its appropriate type identifier.

---

### User Story 4 - Measurement Forms with Sample & Dataset Context (Priority: P2)

As a developer implementing measurement creation/edit views, I want measurement forms that handle both the sample and dataset context correctly, provide clear help text, use appropriate widgets, handle polymorphic types, and provide base mixins for custom measurement forms so that users have an intuitive data entry experience and I can reuse common functionality.

**Why this priority**: Forms are the primary user interface for measurement creation and editing. The current form has minimal configuration and excluded fields that reference non-existent model fields. Quality forms with reusable mixins directly impact user experience and developer productivity.

**Independent Test**: Can be fully tested by instantiating forms for different measurement types with various sample/dataset contexts, rendering them, and submitting valid/invalid data. Success is demonstrated when forms properly handle cross-dataset sample selection, validate correctly, and provide reusable base functionality.

**Acceptance Scenarios**:

1. **Given** an authenticated user with access to a dataset creates a measurement, **When** the form renders, **Then** the dataset field defaults to the current dataset context and the sample field shows samples the user can access.
2. **Given** a developer creates a custom measurement form, **When** the form inherits from MeasurementFormMixin, **Then** common measurement fields (dataset, sample) are pre-configured with appropriate widgets including autocomplete.
3. **Given** a user fills the measurement form selecting a sample from a different dataset, **When** the form is submitted, **Then** validation passes, the measurement is created with the correct dataset assignment, and the cross-dataset sample reference is preserved.
4. **Given** a user submits a measurement form without selecting a sample, **When** the form is validated, **Then** validation fails with a clear error message indicating that a sample is required.
5. **Given** a user is editing an existing measurement, **When** the form renders, **Then** all current field values including polymorphic-specific fields are pre-populated correctly.
6. **Given** a form helper is provided, **When** the form renders, **Then** the form tag is excluded (for embedding in other templates) and crispy forms layout is applied.

---

### User Story 5 - Measurement Filtering & Search (Priority: P2)

As a portal user browsing measurements, I want to filter measurements by dataset, sample, polymorphic type, date ranges, and search by name/UUID so that I can quickly find relevant measurements without browsing all results, with base filter mixins available for custom measurement type filters.

**Why this priority**: Effective filtering is essential for usability as measurement collections grow. The current filter is empty with no configured fields. Base filter mixins reduce developer effort for custom measurement types.

**Independent Test**: Can be fully tested by creating measurements of various types with different attributes and applying different filter combinations. Success is demonstrated when filters correctly narrow results, handle polymorphic types, combine logically, and mixins provide reusable functionality.

**Acceptance Scenarios**:

1. **Given** multiple measurements exist across different datasets, **When** I filter by a specific dataset, **Then** only measurements from that dataset appear in results.
2. **Given** measurements exist for different samples, **When** I filter by a specific sample, **Then** only measurements for that sample appear in results.
3. **Given** measurements of different polymorphic types exist (XRF, ICP-MS), **When** I filter by measurement type, **Then** only measurements of that specific type appear in results.
4. **Given** I search for a keyword that appears in measurement names or UUIDs, **When** the filter is applied, **Then** all matching measurements appear in results.
5. **Given** I apply multiple filters (dataset AND sample), **When** the filters are applied together, **Then** only measurements matching ALL criteria appear in results.
6. **Given** I am developing a custom measurement type filter, **When** I inherit from MeasurementFilterMixin, **Then** I have pre-configured filters for common measurement fields.

---

### User Story 6 - Measurement Value Representation with Uncertainty (Priority: P2)

As a researcher recording measurement data, I want a consistent pattern for representing measured values along with their associated uncertainty or error estimates, so that my scientific results maintain precision and accuracy information throughout the system.

**Why this priority**: Value-with-uncertainty is a fundamental pattern in scientific data. The existing `get_value()` and `print_value()` methods provide a basic pattern, but the approach should be documented and formalized as a reusable convention for custom measurement types.

**Independent Test**: Can be fully tested by creating measurement types with value and uncertainty fields, invoking value display methods, and verifying the formatted output. Success is demonstrated when values render with correct uncertainty notation and the pattern is reusable across measurement types.

**Acceptance Scenarios**:

1. **Given** a measurement type defines a `value` field and an `uncertainty` field, **When** I call `get_value()`, **Then** the result represents the value with its uncertainty (e.g., value ± uncertainty).
2. **Given** a measurement type defines a `value` field but uncertainty is null, **When** I call `get_value()`, **Then** the result returns just the value without uncertainty notation.
3. **Given** a measurement type does not define a `value` field, **When** I call `get_value()`, **Then** the result falls back to the measurement's `name` field.
4. **Given** a measurement has a value with uncertainty, **When** I call `print_value()`, **Then** a human-readable string is returned in the format "value ± uncertainty".
5. **Given** a measurement has a value with units (via django-pint or similar), **When** `get_value()` is called, **Then** the unit information is preserved in the return value.

---

### User Story 7 - Optimized Measurement QuerySets (Priority: P3)

As a developer building measurement views, I want optimized QuerySet methods that prefetch related data (sample, dataset, contributors), handle polymorphic queries efficiently, and provide common query patterns so that views perform well even with large measurement collections of mixed types.

**Why this priority**: QuerySet optimization prevents N+1 query problems and improves performance. The current measurement model has no custom queryset or manager methods. While important, it can be added after core CRUD operations work.

**Independent Test**: Can be fully tested by executing QuerySet methods with query logging enabled. Success is demonstrated when complex polymorphic queries execute with minimal database hits.

**Acceptance Scenarios**:

1. **Given** 1000 measurements of mixed polymorphic types exist with samples, datasets, and contributors, **When** I call `Measurement.objects.with_related().all()`, **Then** direct relationships (sample, dataset, contributors) are loaded with minimal database queries via select_related and prefetch_related, without prefetching deep nested relationships like sample's dataset or contributors' organizations.
2. **Given** I need measurement metadata, **When** I call `Measurement.objects.with_metadata()`, **Then** descriptions, dates, and identifiers are prefetched without additional queries per measurement.
3. **Given** I query polymorphic measurements, **When** I use type-specific filtering, **Then** the correct subclass instances are returned with their type-specific fields.
4. **Given** I chain multiple QuerySet methods, **When** I call `Measurement.objects.with_related().with_metadata().filter(dataset=my_dataset)`, **Then** both optimizations and filters apply correctly and efficiently.
5. **Given** a specific view requires deep nested data, **When** I call `Measurement.objects.with_related().select_related('sample__dataset')`, **Then** the additional optimization chains correctly with the base optimization.

---

### User Story 8 - FAIR Metadata for Measurements (Priority: P3)

As a researcher publishing measurement data, I want to attach rich metadata (descriptions of methods and quality control, key dates, persistent identifiers, contributor attribution) to measurements using Measurement-specific vocabularies so that my data meets FAIR principles and is discoverable and citable.

**Why this priority**: FAIR metadata is essential for data discoverability and reproducibility. The current metadata models exist but incorrectly reference Sample vocabularies instead of Measurement vocabularies. This must be corrected for proper FAIR compliance.

**Independent Test**: Can be fully tested by adding metadata of various types to measurements and verifying correct vocabulary usage, validation, and display. Success is demonstrated when all metadata types correctly use Measurement-specific controlled vocabularies.

**Acceptance Scenarios**:

1. **Given** I am adding a description to a measurement, **When** I select the description type, **Then** the available types come from the Measurement description vocabulary (e.g., methods, quality_control, abstract).
2. **Given** I am adding a key date to a measurement, **When** I select the date type, **Then** the available types come from the Measurement date vocabulary (e.g., measured, analyzed, reviewed).
3. **Given** I am adding an identifier to a measurement, **When** I provide a DOI, **Then** the identifier is validated and stored with correct type information.
4. **Given** I am attributing a contributor to a measurement, **When** I specify a role, **Then** the available roles come from the Measurement contributor roles vocabulary.
5. **Given** a measurement has complete metadata, **When** I view the measurement, **Then** all metadata is displayed with proper labeling and formatting.

---

### Quality Standards

### Comprehensive Docstrings (addresses analysis issue H1)

All code added in this feature MUST include comprehensive docstrings that meet these criteria:

**Module-level docstrings**:
- Purpose: 1-2 sentence summary of what the module provides
- Audience: Who should use this module (portal developers, administrators, framework contributors)
- Key exports: List main classes/functions if module has 5+ exports
- Example: See `fairdm/core/sample/permissions.py` docstring

**Class docstrings**:
- Purpose: What the class represents and its role in the system
- Usage context: When developers should use this class
- Key attributes: List important attributes if class has 5+ fields
- Example usage: Short code snippet showing typical instantiation/usage
- Cross-reference: Link to relevant documentation section using "See: Developer Guide > ..."
- Example: See `fairdm_demo/models.py` ExampleMeasurement docstring

**Method/function docstrings**:
-Google-style format with Args, Returns, Raises sections
- Purpose: 1 sentence explaining what the method does
- Args: Type and description for each parameter
- Returns: Type and description of return value
- Raises: Document expected exceptions
- Example: See `fairdm/core/sample/permissions.py` SamplePermissionBackend.has_perm() docstring

**Minimum documentation threshold**:
- All public classes: comprehensive docstring required
- All public methods/functions: docstring with Args/Returns required
- Private methods: docstring optional but recommended for complex logic
- Module constants: inline comment explaining purpose

### Demo Models (addresses analysis issue H2)

Demo measurement models are already specified in `fairdm_demo/models.py` lines 479-637:

**ExampleMeasurement** (lines 479-513):
- Purpose: Demonstrates basic measurement registration patterns
- Fields: char_field, text_field, integer_field, big_integer_field, positive_integer_field, positive_small_integer_field, small_integer_field, boolean_field, date_field, date_time_field, time_field, decimal_field, float_field
- Usage: Reference for portal developers learning field types
- Docstring: Includes cross-reference to Developer Guide > Models > Measurement Models

**XRFMeasurement** (lines 539-574):
- Purpose: Demonstrates domain-specific analytical measurement
- Fields: element, concentration_ppm, detection_limit_ppm, instrument_model, measurement_conditions
- Usage: Example of geochemical/materials science measurement type
- Pattern: Shows how to model analytical parameters and instrument metadata

**ICP_MS_Measurement** (lines 579-637):
- Purpose: Demonstrates advanced measurement with validation patterns
- Fields: isotope, counts_per_second, concentration_ppb, uncertainty_percent, dilution_factor, internal_standard, analysis_date
- Usage: Example of isotope-specific mass spectrometry data
- Pattern: Shows how to handle uncertainty, calibration factors, and temporal metadata

No additional demo models required - existing models adequately demonstrate field types, metadata patterns, and domain-specific configurations.

### Test Organization (addresses analysis issue H4)

Tests MUST follow FairDM's layer-based organization mirroring source structure:

**Directory structure**:
```
tests/unit/fairdm/core/measurement/
├── conftest.py              # Measurement-specific fixtures
├── test_models.py          # Model + QuerySet tests (T018)
├── test_admin.py           # Admin interface tests (T019)
├── test_forms.py           # Form tests (T020)
├── test_filters.py         # Filter tests (T021)
├── test_permissions.py     # Permission backend tests (T022)
├── test_registry.py        # Registry integration tests (T023)
└── test_integration.py     # Integration tests (T024)
```

**NOT a flat single-file structure** - tests are organized by concern (models, admin, forms, etc.) following FairDM's standardized test organization pattern documented in `docs/contributing/testing/test-organization.md`.

**conftest.py** (T017) provides measurement-specific fixtures:
- Factory fixtures: Measurement, MeasurementDescription, MeasurementDate, MeasurementIdentifier
- Relationship fixtures: Dataset, Sample, User with guardian permissions
- Scope: Module-level fixtures shared across measurement tests
- Example pattern: See `tests/test_core/test_sample/conftest.py`

### Measurable Success Criteria (addresses analysis issue H5)

Replace vague adjectives with measurable criteria:

**"Appropriate" measurement**:
- QuerySet reduces queries by ≥80% vs naive implementation (10+ relationships → ≤2 queries)
- Form validation prevents invalid data with specific error messages
- Admin interface handles ≥1000 measurements without pagination slowdown (<2 seconds load time)

**"Clear" user feedback**:
- Error messages include: (1) what went wrong, (2) why it's invalid, (3) how to fix it
- Example: "Sample 'Rock-001' cannot be deleted because 3 measurements depend on it. Delete measurements first or contact administrator."
- Help text on forms: <50 words, active voice, explains purpose and format

**"Proper" polymorphic handling**:
- Queryset returns correct subclass instances (not base Measurement)
- Admin type selection interface lists all registered measurement types from registry
- Form inheritance preserves both base and subclass field validation

**"Comprehensive" admin interface**:
- Search: by name, UUID, sample name, dataset title
- Filters: dataset, sample, polymorphic type, date ranges
- Inlines: descriptions (4 types), dates (3 types), identifiers (unlimited), contributors (unlimited)
- Actions: bulk export, bulk permission assignment

### Permission Backend Registration (addresses analysis issue H6)

MeasurementPermissionBackend requires **MANUAL** registration in Django settings:

**Registration location**: `fairdm/conf/settings/auth.py`

**Pattern** (following SamplePermissionBackend at line 51):
```python
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    "guardian.backends.ObjectPermissionBackend",
    "fairdm.core.sample.permissions.SamplePermissionBackend",
    "fairdm.core.measurement.permissions.MeasurementPermissionBackend",  # ADD THIS
]
```

**NOT auto-configured** - Django requires explicit backend registration. Missing registration means permission inheritance from Dataset will not work.

**Task impact**: T004 MUST document this manual registration requirement and verify it in deployment checklist.

### Medium Priority Clarifications

#### Terminology Consistency (M1)

**Admin class naming**:
- **MeasurementChildAdmin**: NEW comprehensive admin class to be created in `fairdm/core/measurement/admin.py` (T007)
- **MeasurementAdmin**: EXISTING basic admin class in `fairdm/core/admin.py` to be REMOVED (T009)
- Pattern: Follows Sample app naming (SampleChildAdmin vs old SampleAdmin)
- Rationale: "ChildAdmin" indicates polymorphic child model admin, consistent with django-polymorphic conventions

#### Data Audit Checklist (M2)

Before deploying vocabulary changes, administrators MUST audit existing data:

**Pre-deployment audit steps**:
1. Query all MeasurementDescription records: `MeasurementDescription.objects.values_list('type', flat=True).distinct()`
2. Query all MeasurementDate records: `MeasurementDate.objects.values_list('type', flat=True).distinct()`
3. Compare results with new Measurement vocabulary collections (from `fairdm/core/measurement/models.py`)
4. Identify records with vocabulary types that don't exist in Measurement collections
5. Either: (a) update invalid records to valid Measurement vocabulary types, OR (b) add missing types to Measurement vocabulary collections

**Validation query examples**:
```python
# Check for description types not in Measurement vocabulary
invalid_descriptions = MeasurementDescription.objects.exclude(
    type__in=Measurement.DESCRIPTION_TYPES
)

# Check for date types not in Measurement vocabulary
invalid_dates = MeasurementDate.objects.exclude(
    type__in=Measurement.DATE_TYPES
)
```

**Deployment blocker**: If invalid records exist, deployment MUST be paused until data is corrected.

#### Polymorphic Admin Validation (M3)

**Validation rules** for measurement child admins:

1. **Inheritance requirement**: All custom measurement admins MUST inherit from `MeasurementChildAdmin`
2. **base_fieldsets requirement**: Child admins MUST define `base_fieldsets` as a tuple (not list) containing measurement base fields
3. **base_fieldsets structure**: Must include sections for: (1) Basic Info (name, dataset, sample), (2) Identification (uuid, timestamps)
4. **Inline inheritance**: Child admins inherit inlines from MeasurementChildAdmin automatically (descriptions, dates, identifiers, contributors)
5. **Override pattern**: Child admins can override `base_fieldsets` to add custom fields or reorder sections
6. **Registry integration**: MeasurementParentAdmin.get_child_models() queries `registry.measurements` to populate type selection

**Example validation** (T010 demo admins):
```python
from fairdm.core.measurement.admin import MeasurementChildAdmin

class XRFMeasurementAdmin(MeasurementChildAdmin):
    base_fieldsets = (
        ("Basic Information", {"fields": ("name", "dataset", "sample")}),
        ("XRF Data", {"fields": ("element", "concentration_ppm", "detection_limit_ppm")}),
        ("Instrument", {"fields": ("instrument_model", "measurement_conditions")}),
        ("Identification", {"fields": ("uuid", "added", "modified")}),
    )
```

#### Sample Selection Workflow (M4)

**Clarified workflow** for cross-dataset sample usage:

1. **Dataset inclusion**: User MUST first ensure sample is included in their dataset:
   - Option A: Create new sample directly in dataset
   - Option B: Add reference to existing sample from another dataset (via dataset.samples.add())
2. **Measurement creation**: When creating measurement, sample field shows ONLY samples included in measurement's dataset
3. **Filter implementation**: Form's sample field uses queryset filtered by `dataset=self.cleaned_data['dataset']`
4. **Permission boundary**: Measurement edit permissions controlled by measurement's dataset, sample edit permissions controlled by sample's dataset

**AutoComplete widget configuration** (M5):

Sample and dataset fields MUST use `django-autocomplete-light` or `django-select2` widgets:

**Configuration pattern**:
```python
from django_select2.forms import ModelSelect2Widget

class MeasurementFormMixin:
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Dataset autocomplete with guardian permission filtering
        self.fields['dataset'].widget = ModelSelect2Widget(
            search_fields=['title__icontains', 'project__title__icontains'],
            queryset=Dataset.objects.filter(/* guardian permissions */)
        )

        # Sample autocomplete filtered by selected dataset
        self.fields['sample'].widget = ModelSelect2Widget(
            search_fields=['name__icontains', 'uuid__icontains'],
            dependent_fields={'dataset': 'dataset__id'},  # Filter by dataset
            queryset=Sample.objects.all()
        )
```

**Widget requirements**:
- Search fields: minimum 2 searchable fields (name/title + UUID/ID)
- Result display: Show name/title + dataset context
- Minimum input length: 2 characters before triggering search
- Max results: 20 per page with pagination

#### QuerySet Optimization Verification (M6)

**Verification method** for 80% query reduction claim:

**Test setup**:
```python
from django.test.utils import override_settings
from django.db import connection
from django.test import TestCase

@override_settings(DEBUG=True)
class TestMeasurementQuerySetOptimization(TestCase):
    def test_with_related_reduces_queries(self):
        # Create 100 measurements with samples, datasets, contributors
        measurements = create_test_measurements(count=100)

        # BASELINE: Naive query (no optimization)
        connection.queries_log.clear()
        for m in Measurement.objects.all():
            _ = m.sample.name
            _ = m.dataset.title
            _ = m.contributors.count()
        baseline_queries = len(connection.queries)

        # OPTIMIZED: with_related()
        connection.queries_log.clear()
        for m in Measurement.objects.with_related():
            _ = m.sample.name
            _ = m.dataset.title
            _ = m.contributors.count()
        optimized_queries = len(connection.queries)

        # VERIFY: ≥80% reduction
        reduction_percent = (baseline_queries - optimized_queries) / baseline_queries * 100
        assert reduction_percent >= 80, f"Only {reduction_percent}% query reduction"
```

**Expected results**:
- Baseline (naive): ~300+ queries (100 measurements × 3 relationships)
- Optimized: ≤60 queries (1 base query + relationship prefetches)
- Reduction: ≥80%

#### Vocabulary Validation Behavior (M7)

**Existing invalid data behavior**:

When records have vocabulary types that don't exist in new Measurement vocabulary collections:

1. **Read operations**: Records load normally, display shows raw type value
2. **Write operations**: Model's `clean()` method validates vocabulary type, raises `ValidationError` if invalid
3. **Form display**: Form field shows current invalid value but doesn't render as a valid choice option
4. **Admin save**: Admin validation prevents saving without correcting to valid vocabulary type

**Example scenario**:
```python
# Existing record has type='collection_method' (Sample vocabulary)
desc = MeasurementDescription.objects.get(pk=1)
desc.type  # Returns 'collection_method' (invalid for Measurement)

# Attempt to save triggers validation
desc.save()  # Raises ValidationError: "'collection_method' is not a valid Measurement description type"

# Must correct to valid Measurement vocabulary
desc.type = 'methods'  # Valid Measurement type
desc.save()  # Success
```

#### Permission Mapping Reference (M8)

**Complete permission mapping** for MeasurementPermissionBackend:

| Measurement Permission | Maps To Dataset Permission | Notes |
|----------------------|---------------------------|--------|
| `measurement.view_measurement` | `dataset.view_dataset` | View measurement requires view access to measurement's dataset |
| `measurement.change_measurement` | `dataset.change_dataset` | Edit measurement requires change access to measurement's dataset |
| `measurement.delete_measurement` | `dataset.delete_dataset` | Delete measurement requires delete access to measurement's dataset |
| `measurement.add_measurement` | `dataset.change_dataset` | Create measurement requires change access to target dataset |
| `measurement.import_data` | `dataset.import_data` | Bulk import requires import permission on target dataset |
| (N/A) | `dataset.view_dataset` (sample) | Viewing linked sample requires view access to **sample's** dataset (enforced by SamplePermissionBackend) |

**Cross-dataset permission boundary example**:
```
Measurement in Dataset A → Sample in Dataset B

User permissions:
- view_dataset (Dataset A) ✓
- change_dataset (Dataset A) ✓
- view_dataset (Dataset B) ✓
- change_dataset (Dataset B) ✗

Result:
- Can view measurement ✓ (via Dataset A permission)
- Can edit measurement ✓ (via Dataset A permission)
- Can view linked sample ✓ (via Dataset B permission)
- Cannot edit linked sample ✗ (requires Dataset B change permission)
```

## Edge Cases

- **Sample deletion with measurements**: The current model uses `on_delete=PROTECT` for the sample FK, meaning a sample cannot be deleted if measurements reference it. Verify this is correct behavior and that an appropriate error message is shown.
- **Cross-dataset permission boundaries**: When a measurement in Dataset A references a sample in Dataset B, verify that permissions remain isolated — editing the measurement requires permissions on Dataset A, while editing the sample requires permissions on Dataset B.
- **Measurement without a value field**: Custom measurement types are not required to have a `value` field. The `get_value()` method must gracefully fall back to the `name` field in this case.
- **Dataset deletion with measurements**: The current model uses `on_delete=CASCADE` for the dataset FK. Verify that deleting a dataset cascades to delete all measurements in that dataset, even if those measurements reference samples from other datasets.
- **Orphaned measurement metadata**: When a measurement is deleted, verify that associated descriptions, dates, and identifiers are also deleted (CASCADE).
- **Duplicate measurements on same sample**: The system should allow multiple measurements of the same type on the same sample (e.g., repeated XRF analyses).
- **Vocabulary mismatch fix impact**: Correcting MeasurementDescription and MeasurementDate vocabularies from "Sample" to "Measurement" will require a schema migration. If existing data uses Sample vocabulary values that don't exist in the Measurement vocabulary, the migration will fail and require manual data cleanup before deployment.
- **Empty measurement form exclusions**: The current form excludes fields (`keywords`, `depth`, `options`, `path`, `numchild`) that may not exist on the model. Clean up these references.
- **Plugin model mismatch**: The current plugins.py uses SampleDescription and SampleDate as inline models instead of MeasurementDescription and MeasurementDate. This must be corrected.
- **Polymorphic type deletion**: If a custom measurement type class is removed from code but records exist in the database, the polymorphic system should gracefully degrade to base Measurement.
- **Measurement ordering**: Current default ordering is by `-modified`. Verify this is appropriate and consider if ordering by sample or dataset is needed for alternative views.

## Requirements

### Functional Requirements

#### Model & Data Integrity

- **FR-001**: Measurement model MUST inherit from BasePolymorphicModel to support domain-specific measurement types via django-polymorphic. Direct instantiation of base Measurement model MUST be prevented — only polymorphic subclass instances (XRFMeasurement, WaterQualityMeasurement, etc.) can be created. Forms and admin MUST enforce this constraint.
- **FR-002**: Measurement model MUST include unique UUID identifier with 'm' prefix for stable internal referencing using ShortUUID.
- **FR-003**: Measurement model MUST include a required ForeignKey to Dataset (`on_delete=CASCADE`) representing the dataset that owns this measurement. This is the measurement's "home" dataset and controls edit permissions.
- **FR-004**: Measurement model MUST include a required ForeignKey to Sample (`on_delete=PROTECT`) representing the sample on which the measurement was performed. The sample MAY belong to a different dataset than the measurement.
- **FR-005**: Measurement model MUST support contributors via GenericRelation to the Contribution model, with roles defined by the Measurement contributor roles vocabulary.
- **FR-006**: Measurement model MUST include timestamps (`added`, `modified`) for audit trail purposes.
- **FR-007**: Measurement model MUST define `CONTRIBUTOR_ROLES`, `DESCRIPTION_TYPES`, and `DATE_TYPES` using Measurement-specific vocabulary collections (not Sample vocabularies).
- **FR-008**: Measurement `__str__` method MUST return a meaningful representation, delegating to `get_value()` to display the measurement's primary value when available.
- **FR-009**: Measurement `type_of` classproperty MUST return the base Measurement class for polymorphic type identification.
- **FR-010**: Measurement `get_absolute_url()` MUST return a URL pattern for the measurement's detail view using the measurement's UUID. The URL pattern should follow the convention `/measurements/{uuid}/` even though the detail view implementation is deferred to a future feature.

#### Cross-Dataset Linking & Provenance

- **FR-011**: The system MUST filter sample selection to only show samples that are included in the measurement's dataset. Users MUST first add samples to their dataset (either by creating new samples or adding references to existing samples from other datasets) before they can create measurements on those samples.
- **FR-012**: The system MUST clearly track and display provenance information showing which dataset owns a measurement and the original source dataset of referenced samples.
- **FR-013**: Permission enforcement MUST be dataset-scoped: editing a measurement requires edit permission on the measurement's dataset, while editing the referenced sample requires edit permission on the sample's dataset.
- **FR-014**: When selecting a sample for a measurement, the sample selection interface MUST show only samples that are included in the measurement's dataset, enforcing the workflow: add sample to dataset first, then create measurements.

#### Value Representation

- **FR-015**: Measurement model MUST provide a `get_value()` method that returns the measurement's primary value. If the subclass defines a `value` attribute, it MUST be returned; if `uncertainty` is also defined and non-null, the value MUST include uncertainty. If no `value` attribute exists, `name` is returned as fallback.
- **FR-016**: Measurement model MUST provide a `print_value()` method that returns a human-readable string representation of the value, formatted as "value ± uncertainty" when uncertainty is available.

#### Metadata Models

- **FR-017**: MeasurementDescription model MUST use a concrete ForeignKey to Measurement (not GenericRelation) for query performance. The description type MUST be validated against the Measurement description vocabulary (`FairDMDescriptions.from_collection("Measurement")`).
- **FR-018**: MeasurementDate model MUST use a concrete ForeignKey to Measurement. The date type MUST be validated against the Measurement date vocabulary (`FairDMDates.from_collection("Measurement")`).
- **FR-019**: MeasurementIdentifier model MUST use a concrete ForeignKey to Measurement. The identifier type MUST be validated against `FairDMIdentifiers`.
- **FR-020**: All measurement metadata models MUST cascade-delete when the parent measurement is deleted.

#### QuerySet Methods

- **FR-021**: Measurement model MUST use a custom MeasurementQuerySet to make optimized query methods available on `Measurement.objects`.
- **FR-022**: MeasurementQuerySet MUST provide `with_related()` method that prefetches direct relationships (sample, dataset, contributors via select_related/prefetch_related) to prevent N+1 query problems. Deep nested relationships (sample's dataset, contributors' organizations) are NOT prefetched by this method—specific views requiring deep nesting should chain additional select_related calls.
- **FR-023**: MeasurementQuerySet MUST provide `with_metadata()` method that prefetches metadata models (descriptions, dates, identifiers) using prefetch_related.
- **FR-024**: QuerySet optimization methods MUST reduce database queries by at least 80% compared to naive ORM usage when loading measurements with their directly related data (sample, dataset, basic contributors, metadata).
- **FR-025**: QuerySet methods MUST be chainable and composable with standard Django QuerySet operations including additional select_related/prefetch_related calls for view-specific optimization.

#### Forms

- **FR-026**: MeasurementForm MUST include fields for dataset, sample, and name with appropriate widgets.
- **FR-027**: MeasurementForm MUST use autocomplete widgets for dataset and sample ForeignKey fields for improved UX.
- **FR-028**: MeasurementForm MUST properly clean up field exclusions to only exclude fields that actually exist on the model.
- **FR-029**: MeasurementForm MUST accept optional `request` parameter in `__init__` to access user context for queryset filtering.
- **FR-030**: MeasurementForm MUST provide clear, helpful `help_text` for all fields wrapped in `gettext_lazy()` for internationalization.
- **FR-031**: Forms SHOULD provide MeasurementFormMixin with pre-configured widgets for common measurement fields (dataset, sample) for reuse in custom measurement type forms.

#### Filters

- **FR-032**: MeasurementFilter MUST extend `django_filters.FilterSet` providing a consistent filtering interface with actual configured filter fields (the current filter has no fields configured).
- **FR-033**: MeasurementFilter MUST support filtering by dataset (exact match or choice).
- **FR-034**: MeasurementFilter MUST support filtering by sample (exact match or choice).
- **FR-035**: MeasurementFilter MUST support filtering by polymorphic measurement type.
- **FR-036**: MeasurementFilter MUST provide generic search field that matches across name and UUID.
- **FR-037**: Filters SHOULD provide MeasurementFilterMixin with common measurement filter configurations for reuse in custom measurement type filters.

#### Admin Interface

- **FR-038**: MeasurementParentAdmin MUST be registered with Django admin site for the base Measurement model, inheriting from PolymorphicParentModelAdmin to handle type selection when creating new measurements and routing to appropriate child admin for editing.
- **FR-039**: MeasurementParentAdmin MUST provide search by name and UUID and include PolymorphicChildModelFilter in list_filter for filtering by measurement type.
- **FR-040**: MeasurementParentAdmin MUST provide `list_display` showing name, sample, dataset, polymorphic type, and added/modified dates.
- **FR-041**: MeasurementParentAdmin MUST dynamically discover child models using `registry.measurements` (similar to SampleParentAdmin pattern).
- **FR-042**: MeasurementChildAdmin (base class defined in fairdm/core/admin.py, currently named MeasurementAdmin) MUST inherit from PolymorphicChildModelAdmin and provide common configuration for all measurement subtype admins including inline editors for MeasurementDescription, MeasurementDate, MeasurementIdentifier, and Contributions.
- **FR-043**: MeasurementChildAdmin MUST define base_fieldsets (tuple, not list) to allow polymorphic admin to automatically add subclass-specific fields.
- **FR-044**: MeasurementChildAdmin MUST use autocomplete functionality for sample and dataset ForeignKey fields.
- **FR-045**: Individual measurement subtype admins (e.g., XRFMeasurementAdmin) MUST inherit from MeasurementChildAdmin and set base_model attribute to enable proper polymorphic admin functionality.
- **FR-046**: MeasurementChildAdmin MUST make UUID and timestamps readonly to prevent accidental modification.
- **FR-047**: Registry validation MUST enforce that custom admin classes for Measurement subclasses inherit from MeasurementChildAdmin (matching the pattern used for Sample subclasses).

#### Registry Integration

- **FR-048**: Measurement model MUST integrate with FairDM registry system for auto-generation of forms, filters, tables without duplicating registry functionality.
- **FR-049**: Measurement registration MUST leverage existing registry patterns and configuration classes.
- **FR-050**: Registry MUST support polymorphic measurement types with type-specific field configurations.
- **FR-051**: Registry MUST auto-generate ModelForm when custom form not provided, using configured fields.
- **FR-052**: Registry MUST auto-generate FilterSet when custom filter not provided, using configured filterset_fields.
- **FR-053**: Registry MUST auto-generate django-tables2 Table when custom table not provided, using configured table_fields.
- **FR-054**: MeasurementFormMixin and MeasurementFilterMixin MUST be designed to work with registry-generated forms/filters.
- **FR-055**: Registry MUST enforce that custom admin_class for Measurement subclasses inherits from MeasurementChildAdmin (imported from fairdm.core.admin), matching the validation pattern used for Sample subclasses.

#### Permissions

- **FR-056**: Measurement model MUST define custom permissions for data operations: view_measurement, add_measurement, change_measurement, delete_measurement, import_data.
- **FR-057**: Measurement permissions MUST integrate with django-guardian for object-level permission enforcement.
- **FR-058**: Measurement permissions MUST be scoped to the measurement's own dataset, independent of the referenced sample's dataset permissions.

#### Plugin Corrections

- **FR-059**: Measurement plugins MUST use MeasurementDescription and MeasurementDate as inline models (not SampleDescription and SampleDate as currently configured).
- **FR-060**: Measurement plugins MUST reference Measurement-specific vocabularies for description types and date types.

#### Testing Requirements

- **FR-061**: Measurement model MUST have unit tests for: model creation, polymorphic behavior, validation rules, field constraints, cross-dataset sample linking, and value/uncertainty methods.
- **FR-062**: MeasurementQuerySet methods MUST have unit tests for: `with_related()`, `with_metadata()`, polymorphic queries, and query chaining.
- **FR-063**: MeasurementForm MUST have unit tests for: form validation, polymorphic type handling, queryset filtering, default values, field widgets, request context handling, and cross-dataset sample selection.
- **FR-064**: MeasurementFormMixin MUST have unit tests verifying proper widget configuration and field setup for common measurement fields.
- **FR-065**: MeasurementFilter MUST have unit tests for: each filter field, polymorphic type filtering, generic search functionality, and edge cases (empty results, all results).
- **FR-066**: MeasurementFilterMixin MUST have unit tests verifying filter configuration and integration with custom measurement type filters.
- **FR-067**: MeasurementParentAdmin and MeasurementChildAdmin MUST have integration tests for: search, filters, polymorphic type handling, inline editing, vocabulary correctness, widget functionality, and type selection interface.
- **FR-068**: Cross-dataset measurement-sample linking MUST have dedicated integration tests verifying permission boundaries are correctly enforced.
- **FR-069**: All tests MUST use factory-boy factories from fairdm.factories for test data generation.
- **FR-070**: Test organization MUST mirror source code structure in tests/test_core/test_measurement/ with unit and integration tests in flat structure.
- **FR-071**: Tests MUST verify registry integration works correctly for polymorphic measurement types without duplicating registry test coverage.
- **FR-072**: Vocabulary correction (from Sample to Measurement) for MeasurementDescription and MeasurementDate MUST have explicit test coverage ensuring correct vocabulary usage.

### Key Entities

- **Measurement**: Polymorphic base model for scientific observations; core fields include UUID (m-prefixed), name, dataset FK (CASCADE, home dataset), sample FK (PROTECT, may be cross-dataset), contributors via GenericRelation. Provides `get_value()` and `print_value()` methods for value-with-uncertainty display.
- **MeasurementDescription**: Typed free-text descriptions with concrete ForeignKey to Measurement, validated against Measurement description vocabulary.
- **MeasurementDate**: Typed dates linked to measurement, validated against Measurement date vocabulary.
- **MeasurementIdentifier**: External identifiers (DOI, Handle) linked to measurement with type validation.
- **MeasurementQuerySet**: Custom QuerySet providing `with_related()` and `with_metadata()` optimized query methods for polymorphic measurement retrieval.
- **MeasurementForm**: ModelForm for measurement creation/editing with dataset and sample context awareness, cross-dataset sample selection.
- **MeasurementFormMixin**: Reusable mixin providing common measurement form functionality (autocomplete widgets, field configuration) for custom measurement types.
- **MeasurementFilter**: FilterSet for measurement searching and filtering including polymorphic type and cross-relationship query support.
- **MeasurementFilterMixin**: Reusable mixin providing common measurement filter functionality for custom measurement types.
- **MeasurementParentAdmin**: Polymorphic parent admin registered for base Measurement model, handles type selection when creating new measurements and routes to appropriate child admin for editing. Uses `registry.measurements` to dynamically discover registered measurement subtypes.
- **MeasurementChildAdmin**: Base admin class for measurement subtype admins (currently named MeasurementAdmin in fairdm/core/admin.py), inherits from PolymorphicChildModelAdmin, provides common configuration including inlines, fieldsets, autocomplete, and readonly fields.
- **Sample**: Parent model that measurements are performed on. Must be included in the measurement's dataset before measurements can be created on it.
- **Dataset**: Container that owns measurements and controls edit permissions. A measurement's dataset is independent of its sample's dataset.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Portal developers can define and register custom polymorphic measurement types in under 20 minutes (model definition + registration).
- **SC-002**: Measurement CRUD operations complete with proper validation and error messages within 2 seconds for typical use cases.
- **SC-003**: Measurement list view with 1000+ measurements of mixed polymorphic types and filters applied loads in under 1 second with optimized querysets.
- **SC-004**: Measurement model achieves 90%+ test coverage with meaningful tests covering critical paths, edge cases, and cross-dataset linking scenarios.
- **SC-005**: Measurement forms provide clear validation feedback with user-friendly error messages for all invalid inputs, including cross-dataset sample selection.
- **SC-006**: Measurement admin interface allows administrators to search, filter, and edit measurements of any polymorphic type using correct Measurement-specific vocabularies.
- **SC-007**: MeasurementQuerySet optimization reduces database queries by 80%+ compared to naive ORM usage when loading measurements with related data.
- **SC-008**: Measurement filter combinations work correctly in 100% of test cases without unexpected results for polymorphic queries.
- **SC-009**: Custom measurement type developers report 60% less boilerplate code using provided mixins compared to manual implementation.
- **SC-010**: All vocabulary references (descriptions, dates, roles) correctly use Measurement-specific collections, verified by automated tests.

## Assumptions

### Technical Assumptions

- **A-001**: Django-polymorphic is already installed and configured in the framework.
- **A-002**: Django-guardian is already installed and configured for object-level permissions.
- **A-003**: Research-vocabs package is available for controlled vocabulary support, including Measurement-specific collections for descriptions, dates, and roles.
- **A-004**: ShortUUID package is available for generating unique identifiers with 'm' prefix.
- **A-005**: FairDM registry system (Feature 002) is already implemented and functional.
- **A-006**: BasePolymorphicModel, AbstractDescription, AbstractDate, AbstractIdentifier abstract bases already exist.
- **A-007**: Dataset model (Feature 004) is complete and functional with permissions.
- **A-008**: Sample model (Feature 005) is complete and functional.
- **A-009**: The Contribution model supports GenericRelation for polymorphic contributor attribution across core models.
- **A-010**: Crispy Forms is available for form rendering and layout.

### Scope Assumptions

- **A-011**: Client-side views (list views, detail views) are out of scope and handled in future features.
- **A-012**: REST API integration is out of scope for this feature.
- **A-013**: Measurement import/export functionality beyond basic admin is out of scope.
- **A-014**: The `get_value()` / `print_value()` pattern is a convention, not enforced — custom measurement types may choose not to follow it.

### Standards Assumptions

- **A-015**: FAIR metadata compliance is achieved through description, date, identifier, and contributor metadata models with controlled vocabularies.
- **A-016**: DataCite identifier types are sufficient for external identifier support.

## Dependencies

### Internal Dependencies

- **D-001**: FairDM registry system must be functional and tested (Feature 002) — CRITICAL: Polymorphic measurement integration builds on registry patterns.
- **D-002**: Dataset model must be complete with permissions system (Feature 004).
- **D-003**: Sample model must be complete and functional (Feature 005).
- **D-004**: Contributor models (Person, Organization) and Contribution through-model with GenericRelation support must exist.
- **D-005**: Research vocabularies for measurement description types, date types, identifier types, and contributor roles must be defined as Measurement-specific collections.

### External Dependencies

- **D-006**: Django-polymorphic package (v3.1+)
- **D-007**: Django-guardian package (v2.4+)
- **D-008**: Research-vocabs package (custom FairDM package)
- **D-009**: ShortUUID package (v1.0+)
- **D-010**: Django-crispy-forms package (v2.0+)
- **D-011**: Django-filter package (v23.0+)
- **D-012**: Django-tables2 package (v2.5+)

## Out of Scope

### Explicitly Excluded

- **OS-001**: Measurement list views and detail views in the portal UI (deferred to client-side integration feature).
- **OS-002**: REST API endpoints for measurements (deferred to API feature).
- **OS-003**: Measurement import/export wizards beyond basic admin functionality.
- **OS-004**: Custom measurement value types with units (django-pint integration is available but not required or enforced by this feature).
- **OS-005**: Real-time collaboration features for measurement editing.
- **OS-006**: Measurement provenance chain visualization (graph/tree views of measurement lineage).
- **OS-007**: Statistical analysis or aggregation of measurement values across datasets.
- **OS-008**: Automated quality control checks on measurement values.
- **OS-009**: Measurement workflow management and approval processes.

### Future Considerations

- **FC-001**: Consider standardized measurement value types with unit support (django-pint integration) as a future enhancement.
- **FC-002**: Evaluate measurement-to-measurement relationships (e.g., derived measurements, recalculated values) in future features.
- **FC-003**: Consider measurement quality flags or confidence levels as standardized metadata.
- **FC-004**: Evaluate batch measurement creation workflows for high-throughput data entry.
- **FC-005**: Consider measurement versioning (tracking corrections to measurement values over time).
- **FC-006**: Evaluate machine-readable metadata export (JSON-LD, DataCite) for measurement records.

## Technical Notes

### Current Code Issues to Address

The existing measurement code has several issues that must be corrected as part of this enhancement:

1. **Vocabulary mismatch**: `MeasurementDescription.VOCABULARY` and `MeasurementDate.VOCABULARY` both use `from_collection("Sample")` instead of `from_collection("Measurement")`. This must be corrected, potentially requiring a data migration.
2. **Plugin model mismatch**: `plugins.py` uses `SampleDescription` and `SampleDate` as inline models instead of `MeasurementDescription` and `MeasurementDate`.
3. **Form field exclusions**: `MeasurementForm` excludes fields (`keywords`, `depth`, `options`, `path`, `numchild`) that may not exist on the model. These exclusions must be cleaned up.
4. **Empty filter**: `MeasurementFilter` has `fields = []`, providing no actual filtering capability.
5. **No custom queryset**: Unlike Sample, Measurement has no custom queryset or manager methods for optimization.
6. **URL redirect to sample**: The current `get_absolute_url()` implementation returns `self.sample.get_absolute_url()`, redirecting to the parent sample. This should be updated to return a measurement-specific URL pattern (`/measurements/{uuid}/`) even though the detail view implementation is out of scope for this feature.

### Cross-Dataset Linking Architecture

The measurement model implements a filtered sample membership pattern:

- `dataset` FK (CASCADE): The "home" dataset that owns the measurement and controls edit permissions
- `sample` FK (PROTECT): The sample being measured, which must be included in the measurement's dataset

This design supports a common research workflow:

1. **Sample Collection**: Datasets can include samples either by creating new samples OR by adding references to samples originally created in other datasets (the mechanism for this is defined in the Sample model)
2. **Measurement Creation**: Measurements can only be created on samples that are already included in the measurement's dataset
3. **Cross-Dataset Provenance**: When a sample originally from Dataset B is added to Dataset A, measurements in Dataset A can reference it while preserving provenance about the sample's original source

Key architectural decisions:

- Deleting the measurement's home dataset deletes the measurement (CASCADE)
- Deleting a sample is prevented if measurements reference it (PROTECT)
- Edit permissions on the measurement are controlled by the measurement's dataset
- Sample selection is filtered to only show samples included in the measurement's dataset
- The workflow enforces: add sample to dataset first, then create measurements on it

### Polymorphic Model Considerations

1. **Queryset behavior**: Measurement.objects.all() returns polymorphic instances (typed subclasses) by default
2. **Inheritance order**: PolymorphicModel must be listed first in inheritance chain
3. **Proxy models**: Subclasses should be concrete models, not proxy models
4. **Type identification**: Each instance has access to `.type_of` classproperty for identifying its base class

### Polymorphic Admin Architecture

The measurement app follows the same polymorphic admin pattern as the sample app:

**Parent Admin** (`MeasurementParentAdmin` in `fairdm/core/admin.py`):

- Inherits from `PolymorphicParentModelAdmin`
- Registered for the base `Measurement` model with `admin.site.register(Measurement, MeasurementParentAdmin)`
- Handles type selection interface when creating new measurements
- Routes to appropriate child admin when editing existing measurements
- Uses `get_child_models()` method that returns `registry.measurements` for dynamic discovery
- Includes `PolymorphicChildModelFilter` in list_filter for filtering by type

**Child Admin Base** (`MeasurementChildAdmin` in `fairdm/core/admin.py`, currently named `MeasurementAdmin`):

- Inherits from `PolymorphicChildModelAdmin`
- Provides common configuration for all measurement subtype admins
- Uses `base_fieldsets` (tuple) instead of `fieldsets` (list) to allow polymorphic admin to automatically add subclass-specific fields
- Defines common inlines (descriptions, dates, identifiers, contributions)
- Configures autocomplete for sample and dataset fields
- Makes UUID and timestamps readonly

**Subtype Admins** (e.g., `XRFMeasurementAdmin` in user code):

- Inherit from `MeasurementChildAdmin`
- Set `base_model = Measurement` attribute
- Can override or extend base_fieldsets, inlines, etc. for type-specific needs
- Registry enforces this inheritance pattern during validation

This architecture allows:

- Unified interface for creating any measurement type
- Type-specific admin customization when needed
- Automatic discovery of new measurement types via registry
- Consistent UX across all polymorphic models in FairDM

### Form/Filter Mixin Strategy

Base mixins should provide:

**MeasurementFormMixin**:

- Pre-configured widget selection for dataset and sample fields (autocomplete)
- Request-based filtering for dataset querysets (user's accessible datasets)
- Filtered sample queryset limited to samples included in the measurement's dataset
- Proper field ordering (dataset, sample, then custom fields)
- Integration with crispy forms helper (form_tag=False for embedding)

**MeasurementFilterMixin**:

- Dataset filter
- Sample filter (respecting dataset membership constraints)
- Polymorphic type filter
- Search filter for name/UUID
- Date range filters (added/modified)

**MeasurementChildAdmin**:

- Standard inline configuration for descriptions, dates, identifiers, contributions
- Common list_display, list_filter, search_fields
- base_fieldsets organization (tuple for polymorphic compatibility)
- Read-only field configuration (UUID, timestamps)
- Autocomplete for sample (filtered to dataset samples) and dataset fields

### Migration Considerations

- Correcting vocabulary references in MeasurementDescription and MeasurementDate from Sample to Measurement collections requires a schema migration. If existing records use vocabulary values from the Sample collection that don't exist in the Measurement collection, the migration will fail. Deployments with existing data must audit and manually correct vocabulary mismatches before applying this migration.
- Adding a custom queryset manager should not require a migration since managers are not stored in the database.
- Cleaning up form field exclusions is code-only and requires no migrations.
