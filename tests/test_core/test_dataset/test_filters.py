"""
Unit tests for Dataset filtering using django-filter.

This module tests the DatasetFilter class which provides filtering capabilities
for datasets based on:

1. **License filtering**: Exact match filtering by license
2. **Project filtering**: Choice-based filtering by associated project
3. **Visibility filtering**: Choice-based filtering by visibility level
4. **Cross-relationship filters**: Filter by related descriptions and dates
5. **Multiple filter combinations**: AND logic when multiple filters applied
6. **Performance**: Ensure efficient queries on large datasets

The listing's own text search (name, UUID, external identifiers, descriptions and
keywords) is covered against the rendered listing in `test_views.py`
(`TestDatasetListingSearch`), not here — the filterset's own competing `search` field was
withdrawn (014 plan P8), and `TestGenericSearch`, which exercised it directly, was
removed with it (014 T013).

These tests follow TDD principles - they are written FIRST and should FAIL
until DatasetFilter is properly implemented.

## Test Organization

- TestLicenseFilter: Tests for filtering by license
- TestProjectFilter: Tests for filtering by project
- TestVisibilityFilter: Tests for filtering by visibility level
- TestCrossRelationshipFilters: Tests for filters on related models
- TestMultipleFilterCombinations: Tests AND logic with multiple filters
- TestFilterPerformance: Tests query efficiency on large datasets
- TestFilterFormRendering: Tests filter form generation

## Related Files

- Implementation: `fairdm/core/dataset/filters.py`
- Model: `fairdm/core/dataset/models.py`
- Demo examples: `fairdm_demo/filters.py`
"""

import pytest
from django.contrib.auth import get_user_model
from licensing.models import License

from fairdm.core.dataset.filters import DatasetFilter
from fairdm.core.dataset.models import Dataset
from fairdm.factories import (
    DatasetDescriptionFactory,
    DatasetFactory,
    ProjectFactory,
)

User = get_user_model()


@pytest.mark.django_db
class TestLicenseFilter:
    """Test filtering datasets by license.

    Verifies that the license filter correctly matches datasets by their
    assigned license using exact match semantics.
    """

    def test_filter_by_license_exact_match(self):
        """License filter should return only datasets with specified license."""
        # Arrange
        cc_by = License.objects.get(name="CC BY 4.0")
        cc0 = License.objects.get(name="CC0 1.0")

        ds1 = DatasetFactory(license=cc_by)
        ds2 = DatasetFactory(license=cc_by)
        DatasetFactory(license=cc0)  # Should be excluded

        # Act
        # Base queryset is `all_objects`, not `objects`: this test's subject is
        # license filtering, not visibility, and `DatasetFactory()` defaults to
        # PRIVATE (004-core-datasets FR-019), which the privacy-first default
        # manager would otherwise exclude before the license filter ever runs.
        filterset = DatasetFilter(
            data={"license": cc_by.id}, queryset=Dataset.all_objects.all()
        )

        # Assert
        assert filterset.is_valid()
        assert filterset.qs.count() == 2
        assert ds1 in filterset.qs
        assert ds2 in filterset.qs

    def test_filter_without_license_shows_all(self):
        """When no license filter applied, should show all datasets."""
        # Arrange
        DatasetFactory.create_batch(3)

        # Act
        # `all_objects`: subject is license filtering, not visibility (see above).
        filterset = DatasetFilter(data={}, queryset=Dataset.all_objects.all())

        # Assert
        assert filterset.is_valid()
        assert filterset.qs.count() == 3


@pytest.mark.django_db
class TestProjectFilter:
    """Test filtering datasets by project.

    Verifies that the project filter correctly matches datasets associated
    with a specific project using choice-based filtering.
    """

    def test_filter_by_project(self):
        """Project filter should return only datasets in specified project."""
        # Arrange
        project1 = ProjectFactory()
        project2 = ProjectFactory()

        ds1 = DatasetFactory(project=project1)
        ds2 = DatasetFactory(project=project1)
        DatasetFactory(project=project2)  # Should be excluded

        # Act
        # `all_objects`: subject is project filtering, not visibility (see above).
        filterset = DatasetFilter(
            data={"project": project1.id}, queryset=Dataset.all_objects.all()
        )

        # Assert
        assert filterset.is_valid()
        assert filterset.qs.count() == 2
        assert ds1 in filterset.qs
        assert ds2 in filterset.qs

    def test_filter_by_null_project(self):
        """Project filter should handle datasets without project."""
        # Arrange
        DatasetFactory(project=None)
        DatasetFactory(project=ProjectFactory())

        # Act
        filterset = DatasetFilter(data={"project": ""}, queryset=Dataset.objects.all())

        # Assert
        assert filterset.is_valid()
        # Implementation detail: depends on whether null choice is included
        # This test documents expected behavior


@pytest.mark.django_db
class TestVisibilityFilter:
    """Test filtering datasets by visibility level.

    Verifies that the visibility filter correctly matches datasets by their
    visibility setting (PUBLIC or PRIVATE).
    """

    def test_filter_by_visibility_public(self):
        """Visibility filter should return only PUBLIC datasets when PUBLIC selected."""
        # Arrange
        ds_public = DatasetFactory(visibility=Dataset.VISIBILITY_CHOICES.PUBLIC)
        DatasetFactory(visibility=Dataset.VISIBILITY_CHOICES.PRIVATE)

        # Act
        filterset = DatasetFilter(
            data={"visibility": Dataset.VISIBILITY_CHOICES.PUBLIC},
            queryset=Dataset.objects.all(),
        )

        # Assert
        assert filterset.is_valid()
        assert filterset.qs.count() == 1
        assert ds_public in filterset.qs

    def test_filter_by_visibility_private(self):
        """Visibility filter should return only PRIVATE datasets when PRIVATE selected."""
        # Arrange
        DatasetFactory(visibility=Dataset.VISIBILITY_CHOICES.PUBLIC)
        ds_private = DatasetFactory(visibility=Dataset.VISIBILITY_CHOICES.PRIVATE)

        # Act
        # Base queryset is `all_objects`: this test's subject IS visibility, and
        # `Dataset.objects` (privacy-first, 004-core-datasets FR-019) would exclude
        # the private row before the filter ever saw it, leaving nothing to prove
        # the filter itself narrows correctly. `all_objects` supplies both rows so
        # the filter — not the manager — is what is under test.
        filterset = DatasetFilter(
            data={"visibility": Dataset.VISIBILITY_CHOICES.PRIVATE},
            queryset=Dataset.all_objects.all(),
        )

        # Assert
        assert filterset.is_valid()
        assert filterset.qs.count() == 1
        assert ds_private in filterset.qs

    @pytest.mark.skip(
        reason="INTERNAL visibility does not exist - only PUBLIC and PRIVATE"
    )
    def test_filter_by_visibility_internal(self):
        """Skipped - INTERNAL visibility level does not exist."""
        pass


@pytest.mark.django_db
class TestCrossRelationshipFilters:
    """Test filtering by related model fields.

    Verifies that filters can traverse relationships to filter on
    DatasetDescription and DatasetDate fields.
    """

    @pytest.mark.skip(
        reason="Cross-relationship filtering by description type not yet implemented in DatasetFilter"
    )
    def test_filter_by_description_type(self):
        """Should filter datasets by description type."""
        # TODO: Implement description_type filter in DatasetFilter
        pass

    @pytest.mark.skip(
        reason="Cross-relationship filtering by date type not yet implemented in DatasetFilter"
    )
    def test_filter_by_date_type(self):
        """Should filter datasets by date type."""
        # TODO: Implement date_type filter in DatasetFilter
        pass

    @pytest.mark.skip(
        reason="Cross-relationship filtering not yet implemented in DatasetFilter"
    )
    def test_cross_relationship_filter_with_no_related_data(self):
        """Cross-relationship filter should handle datasets without related data."""
        pass


@pytest.mark.django_db
class TestMultipleFilterCombinations:
    """Test combining multiple filters with AND logic.

    Verifies that when multiple filters are applied, they combine using
    AND logic to progressively narrow the result set.
    """

    def test_combine_license_and_project(self):
        """Combining license and project filters should use AND logic."""
        # Arrange
        cc_by = License.objects.get(name="CC BY 4.0")
        cc0 = License.objects.get(name="CC0 1.0")
        project1 = ProjectFactory()
        project2 = ProjectFactory()

        ds_match = DatasetFactory(license=cc_by, project=project1)
        DatasetFactory(license=cc_by, project=project2)  # Wrong project
        DatasetFactory(license=cc0, project=project1)  # Wrong license

        # Act
        # `all_objects`: subject is license/project filtering, not visibility (see above).
        filterset = DatasetFilter(
            data={"license": cc_by.id, "project": project1.id},
            queryset=Dataset.all_objects.all(),
        )

        # Assert
        assert filterset.is_valid()
        assert filterset.qs.count() == 1
        assert ds_match in filterset.qs

    def test_combine_all_filters(self):
        """Combining all available filters should progressively narrow results.

        014 T013 — the withdrawn `search` field (see module docstring) is no longer part
        of this combination; the decoys are distinguished by license, project and
        visibility instead, which still all exist on this filterset.
        """
        # Arrange
        cc_by = License.objects.get(name="CC BY 4.0")
        cc0 = License.objects.get(name="CC0 1.0")
        project = ProjectFactory()
        other_project = ProjectFactory()

        ds_match = DatasetFactory(
            license=cc_by,
            project=project,
            visibility=Dataset.VISIBILITY_CHOICES.PUBLIC,
        )

        # Create datasets that don't match all criteria
        DatasetFactory(
            license=cc_by,
            project=other_project,  # Wrong project
            visibility=Dataset.VISIBILITY_CHOICES.PUBLIC,
        )
        DatasetFactory(
            license=cc0,  # Wrong license
            project=project,
            visibility=Dataset.VISIBILITY_CHOICES.PUBLIC,
        )
        DatasetFactory(
            license=cc_by,
            project=project,
            visibility=Dataset.VISIBILITY_CHOICES.PRIVATE,  # Wrong visibility
        )

        # Act
        filterset = DatasetFilter(
            data={
                "license": cc_by.id,
                "project": project.id,
                "visibility": Dataset.VISIBILITY_CHOICES.PUBLIC,
            },
            queryset=Dataset.objects.all(),
        )

        # Assert
        assert filterset.is_valid()
        assert filterset.qs.count() == 1
        assert ds_match in filterset.qs


@pytest.mark.django_db
class TestFilterPerformance:
    """Test filter performance with large datasets.

    Verifies that filters execute efficiently even with large numbers of
    datasets and related objects. Uses Django's query counting to ensure
    cross-relationship filters don't create N+1 query problems.
    """

    def test_cross_relationship_filter_query_count(self, django_assert_max_num_queries):
        """Cross-relationship filters should not cause N+1 query problems."""
        # Arrange - Create 50 datasets with descriptions
        datasets = DatasetFactory.create_batch(50)
        for ds in datasets[:25]:  # Half have Abstract
            DatasetDescriptionFactory(related=ds, type="Abstract")
        for ds in datasets[25:]:  # Half have Methods
            DatasetDescriptionFactory(related=ds, type="Methods")

        # Act & Assert - Should use at most 5 queries regardless of dataset count
        # (1 for filter setup, 1 for count, 1 for main query, 2 for joins)
        # `all_objects`: subject is query-count under cross-relationship filtering,
        # not visibility (see above); `DatasetFactory()` defaults to PRIVATE.
        with django_assert_max_num_queries(5):
            filterset = DatasetFilter(
                data={"description_type": "Abstract"},
                queryset=Dataset.all_objects.all(),
            )
            result_count = filterset.qs.count()
            assert result_count == 25


@pytest.mark.django_db
class TestFilterFormRendering:
    """Test filter form generation and rendering.

    Verifies that the DatasetFilter correctly generates form fields for
    all filters and that the form can be rendered in templates.
    """

    def test_filter_form_has_all_fields(self):
        """Filter form should include all defined filter fields."""
        # Act
        filterset = DatasetFilter(queryset=Dataset.objects.all())

        # Assert
        expected_fields = [
            "license",
            "project",
            "visibility",
            "description_type",
            "date_type",
        ]
        for field_name in expected_fields:
            assert field_name in filterset.form.fields, f"Missing field: {field_name}"

    def test_filter_form_renders_without_errors(self):
        """Filter form should render successfully."""
        # Act
        filterset = DatasetFilter(queryset=Dataset.objects.all())

        # Assert - Just verify it doesn't raise an exception
        form_html = str(filterset.form)
        assert form_html
        assert "license" in form_html
        assert "project" in form_html

    def test_filter_form_with_data_is_valid(self):
        """Filter form should validate successfully with valid data."""
        # Arrange
        license_obj = License.objects.first()
        project = ProjectFactory()

        # Act
        filterset = DatasetFilter(
            data={
                "license": license_obj.id,
                "project": project.id,
                "visibility": Dataset.VISIBILITY_CHOICES.PUBLIC,
            },
            queryset=Dataset.objects.all(),
        )

        # Assert
        assert filterset.is_valid()
