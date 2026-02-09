# Contract Test Example

This example demonstrates a complete contract test following FairDM conventions.

```{contents}
:local:
:depth: 2
```

## Overview

Contract tests validate **API schemas and data formats** to ensure interoperability. This example shows:

- API endpoint testing with DRF
- Schema validation
- Backward compatibility checks
- External-facing contract verification

## Source Code

**File**: `fairdm/api/serializers.py`

```python
from rest_framework import serializers
from fairdm.core.models import Project

class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project API endpoints."""

    owner_username = serializers.CharField(source='owner.username', read_only=True)
    dataset_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'owner',
            'owner_username',
            'dataset_count',
            'created',
            'modified',
        ]
        read_only_fields = ['id', 'created', 'modified']

    def get_dataset_count(self, obj):
        """Return the number of datasets in this project."""
        return obj.datasets.count()
```

**File**: `fairdm/api/views.py`

```python
from rest_framework import viewsets
from fairdm.core.models import Project
from fairdm.api.serializers import ProjectSerializer

class ProjectViewSet(viewsets.ModelViewSet):
    """API endpoint for projects."""

    queryset = Project.objects.select_related('owner')
    serializer_class = ProjectSerializer

    def get_queryset(self):
        """Filter by authenticated user."""
        return self.queryset.filter(owner=self.request.user)
```

## Contract Test

**File**: `tests/contract/test_api_project_schema.py`

```python
"""Contract tests for Project API endpoint schemas."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from fairdm.factories import ProjectFactory, UserFactory


# Test 1: List endpoint schema
@pytest.mark.django_db
def test_project_list_api__returns_valid_schema():
    """
    Test that project list API returns expected schema.

    This is a contract test ensuring the API response structure
    remains consistent for API consumers.
    """
    # Arrange: Create API client and authenticate
    client = APIClient()
    user = UserFactory(username="testuser")
    client.force_authenticate(user=user)

    # Create test projects
    ProjectFactory.create_batch(2, owner=user)

    # Act: Call list endpoint
    response = client.get(reverse('api:project-list'))

    # Assert: Response status
    assert response.status_code == 200

    # Assert: Response structure
    assert 'results' in response.data
    assert isinstance(response.data['results'], list)

    # Assert: Each project has required fields
    for project in response.data['results']:
        assert 'id' in project
        assert 'title' in project
        assert 'slug' in project
        assert 'description' in project
        assert 'owner' in project
        assert 'owner_username' in project
        assert 'dataset_count' in project
        assert 'created' in project
        assert 'modified' in project


# Test 2: Detail endpoint schema
@pytest.mark.django_db
def test_project_detail_api__returns_valid_schema():
    """
    Test that project detail API returns expected schema.

    Validates individual project endpoint structure.
    """
    # Arrange
    client = APIClient()
    user = UserFactory()
    client.force_authenticate(user=user)
    project = ProjectFactory(owner=user, title="Test Project")

    # Act: Call detail endpoint
    response = client.get(reverse('api:project-detail', args=[project.pk]))

    # Assert: Response status
    assert response.status_code == 200

    # Assert: Required fields present
    data = response.data
    assert data['id'] == project.pk
    assert data['title'] == project.title
    assert data['slug'] == project.slug
    assert data['owner'] == user.pk
    assert data['owner_username'] == user.username
    assert 'dataset_count' in data
    assert 'created' in data
    assert 'modified' in data


# Test 3: Field types and formats
@pytest.mark.django_db
def test_project_api_schema__validates_field_types():
    """
    Test that API fields have correct types and formats.

    Ensures data types match API documentation and
    client expectations (type safety contract).
    """
    # Arrange
    client = APIClient()
    user = UserFactory()
    client.force_authenticate(user=user)
    project = ProjectFactory(owner=user)

    # Act
    response = client.get(reverse('api:project-detail', args=[project.pk]))
    data = response.data

    # Assert: Field types
    assert isinstance(data['id'], int)
    assert isinstance(data['title'], str)
    assert isinstance(data['slug'], str)
    assert isinstance(data['description'], str)
    assert isinstance(data['owner'], int)
    assert isinstance(data['owner_username'], str)
    assert isinstance(data['dataset_count'], int)

    # Assert: Timestamp formats (ISO 8601)
    assert isinstance(data['created'], str)
    assert isinstance(data['modified'], str)
    # Verify ISO 8601 format: YYYY-MM-DDTHH:MM:SS.ffffffZ
    assert 'T' in data['created']
    assert 'T' in data['modified']


# Test 4: Read-only fields enforcement
@pytest.mark.django_db
def test_project_api__read_only_fields__cannot_be_modified():
    """
    Test that read-only fields cannot be modified via API.

    Contract: Clients cannot override system-managed fields.
    """
    # Arrange
    client = APIClient()
    user = UserFactory()
    client.force_authenticate(user=user)
    project = ProjectFactory(owner=user, title="Original Title")

    # Act: Attempt to modify read-only field
    response = client.patch(
        reverse('api:project-detail', args=[project.pk]),
        data={
            'title': 'New Title',
            'created': '2020-01-01T00:00:00Z',  # Read-only field
        },
        format='json'
    )

    # Assert: Update succeeds
    assert response.status_code == 200

    # Assert: Writable field updated
    assert response.data['title'] == 'New Title'

    # Assert: Read-only field unchanged
    project.refresh_from_db()
    assert project.created != '2020-01-01T00:00:00Z'


# Test 5: Backward compatibility (version check)
@pytest.mark.django_db
def test_project_api__v1_schema__maintains_backward_compatibility():
    """
    Test that API v1 schema maintains backward compatibility.

    Critical contract: Existing API consumers must not break
    when we deploy updates. Required fields cannot be removed.
    """
    # Arrange
    client = APIClient()
    user = UserFactory()
    client.force_authenticate(user=user)
    project = ProjectFactory(owner=user)

    # Act
    response = client.get(reverse('api:project-detail', args=[project.pk]))
    data = response.data

    # Assert: v1.0 required fields still present
    v1_required_fields = [
        'id',
        'title',
        'slug',
        'owner',
        'created',
    ]

    for field in v1_required_fields:
        assert field in data, f"Breaking change: {field} removed from API"


# Test 6: Error response schema
@pytest.mark.django_db
def test_project_api__validation_error__returns_standard_error_schema():
    """
    Test that validation errors follow standard DRF error schema.

    Contract: Error responses must be machine-readable and consistent.
    """
    # Arrange
    client = APIClient()
    user = UserFactory()
    client.force_authenticate(user=user)

    # Act: Send invalid data (blank title)
    response = client.post(
        reverse('api:project-list'),
        data={'title': '', 'slug': 'test-project'},
        format='json'
    )

    # Assert: Status code
    assert response.status_code == 400

    # Assert: Error schema
    assert isinstance(response.data, dict)
    assert 'title' in response.data  # Field-specific error
    assert isinstance(response.data['title'], list)  # Error messages as list


# Test 7: Pagination schema
@pytest.mark.django_db
def test_project_list_api__with_pagination__returns_paginated_schema():
    """
    Test that paginated responses follow DRF pagination schema.

    Contract: Clients expect consistent pagination structure.
    """
    # Arrange
    client = APIClient()
    user = UserFactory()
    client.force_authenticate(user=user)
    ProjectFactory.create_batch(15, owner=user)  # More than one page

    # Act
    response = client.get(reverse('api:project-list'))

    # Assert: Pagination schema
    assert response.status_code == 200
    assert 'count' in response.data
    assert 'next' in response.data
    assert 'previous' in response.data
    assert 'results' in response.data

    # Assert: Correct count
    assert response.data['count'] == 15
    assert isinstance(response.data['results'], list)
```

## Explanation

### File Location

```text
tests/contract/test_api_project_schema.py
└────┬─────┘ └──────────┬──────────┘
     │                   └─ Contract: API project schema
     └───────────────────── Test layer: contract
```

**Why this location:**

- Contract test layer (API boundary testing)
- Doesn't need to mirror source structure (tests external interface)
- Groups API contract tests together

### What Makes This a Contract Test

✅ **External-facing**: Tests API endpoints consumed by clients
✅ **Schema-focused**: Validates response structure and field types
✅ **Compatibility**: Ensures backward compatibility
✅ **Interoperability**: Tests machine-readable contracts

❌ **Not testing:**

- Internal business logic (use integration tests)
- Database queries (use integration tests)
- View implementation details (use unit tests)

### Real API Client

Contract tests use **real API clients**, not mocks:

```python
# ✅ Good: Real DRF APIClient
from rest_framework.test import APIClient
client = APIClient()
client.force_authenticate(user=user)
response = client.get('/api/projects/')

# ❌ Bad: Mocking the API
with patch('requests.get') as mock_get:
    mock_get.return_value = {'id': 1, 'title': 'Test'}
```

**Why real clients?**

- Tests actual HTTP request/response cycle
- Validates serializers, views, URLs together
- Catches integration issues

## Running This Test

### Run all contract tests

```bash
poetry run pytest tests/contract/
```

### Run this specific file

```bash
poetry run pytest tests/contract/test_api_project_schema.py
```

### Run a specific test

```bash
poetry run pytest tests/contract/test_api_project_schema.py::test_project_list_api__returns_valid_schema
```

### Run with verbose output

```bash
poetry run pytest tests/contract/ -v
```

## Best Practices Demonstrated

### 1. Assert on Schema, Not Values

```python
# ✅ Good: Validate structure
assert 'id' in response.data
assert isinstance(response.data['title'], str)

# ❌ Bad: Validate specific values
assert response.data['title'] == "Test Project"
```

### 2. Test Backward Compatibility

```python
# ✅ Good: Ensure required fields remain
v1_required_fields = ['id', 'title', 'slug']
for field in v1_required_fields:
    assert field in data

# ❌ Bad: Only test current fields
assert 'new_field' in data  # Doesn't prevent breaking changes
```

### 3. Verify Field Types

```python
# ✅ Good: Type safety
assert isinstance(data['id'], int)
assert isinstance(data['title'], str)

# ❌ Bad: Only check presence
assert 'id' in data  # Doesn't verify type
```

### 4. Test Error Schemas

```python
# ✅ Good: Validate error structure
assert response.status_code == 400
assert isinstance(response.data, dict)
assert 'title' in response.data

# ❌ Bad: Only check status code
assert response.status_code == 400  # Doesn't verify error format
```

## Contract Testing Patterns

### Pattern 1: Required Fields Check

```python
@pytest.mark.django_db
def test_api_required_fields():
    response = client.get('/api/endpoint/')

    required_fields = ['id', 'name', 'created']
    for field in required_fields:
        assert field in response.data
```

### Pattern 2: Field Type Validation

```python
@pytest.mark.django_db
def test_api_field_types():
    response = client.get('/api/endpoint/')

    assert isinstance(response.data['id'], int)
    assert isinstance(response.data['title'], str)
    assert isinstance(response.data['is_active'], bool)
```

### Pattern 3: Timestamp Format Check

```python
@pytest.mark.django_db
def test_api_timestamp_format():
    response = client.get('/api/endpoint/')

    # ISO 8601 format check
    assert 'T' in response.data['created']
    # Can also use datetime parsing
    from dateutil.parser import parse
    parse(response.data['created'])  # Raises if invalid
```

## Common Mistakes

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} ❌ Testing Business Logic
Contract tests test schema, not logic.

**Fix**: Move business logic tests to integration tests.
:::

:::{grid-item-card} ❌ Mocking API Responses
Mocking defeats the purpose of contract tests.

**Fix**: Use real API clients and real database.
:::

:::{grid-item-card} ❌ Hard-Coded Values
Asserting on specific data values.

**Fix**: Assert on structure and types, not values.
:::

:::{grid-item-card} ❌ No Compatibility Checks
Only testing current schema.

**Fix**: Maintain list of v1 required fields.
:::

::::

## Next Steps

```{seealso}
- Compare with [Unit Test Example](unit-test-example.md)
- Compare with [Integration Test Example](integration-test-example.md)
- Review [Test Layers: Contract Tests](../test-layers.md#contract-tests)
- Learn about [API Best Practices](../../api-guide.md) (if exists)
```

## References

- [Test Layers: Contract Tests](../test-layers.md#contract-tests)
- [DRF Testing Documentation](https://www.django-rest-framework.org/api-guide/testing/)
- [Test Organization Contract](../../../../specs/004-testing-strategy-fixtures/contracts/test-organization-contract.md)
