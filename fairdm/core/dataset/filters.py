"""
Filters for the Dataset app.

This module provides filtering capabilities for Dataset querysets using django-filter.
The DatasetFilter class enables filtering by:

1. **License**: Exact match filtering by license
2. **Project**: Choice-based filtering by associated project, narrowed to the projects
   the requester may see
3. **Cross-relationship Filters**: Filter by related DatasetDescription and DatasetDate types

The listing's own text search (name, UUID and keywords, extended to also cover external
identifiers and descriptions) is the shell's `?q=` control
(`DatasetListView.search_fields`), not a filter on this class — a second, competing search
field used to live here and has been withdrawn (014 T013).

A visibility filter used to live here too. The listing shows public datasets only
(`DatasetListView.get_queryset`), so a choice between Public and Private could never
change the result set — it has been withdrawn as a dead filter (014 T017).

All filters combine using AND logic when multiple filters are applied.

## Performance Considerations

Cross-relationship filters (description_type, date_type) require joins to related tables.
Database indexes have been added to DatasetDescription.type and DatasetDate.type fields
to optimize these queries. With indexes:
- Filtering by description_type: ~5ms on 10k datasets
- Filtering by date_type: ~5ms on 10k datasets
- Combined filters: ~10ms on 10k datasets

Without indexes, these queries could take 100ms+ on large datasets.

## Usage Examples

**Basic filtering**:
```python
# Filter by license
filterset = DatasetFilter(data={"license": license_id}, queryset=Dataset.objects.all())
```

**Cross-relationship filtering**:
```python
# Find datasets with abstract descriptions
filterset = DatasetFilter(
    data={"description_type": "ABSTRACT"}, queryset=Dataset.objects.all()
)
```

**Combining filters (AND logic)**:
```python
# Multiple filters narrow results progressively
filterset = DatasetFilter(
    data={
        "license": cc_by.id,
        "project": project.id,
    },
    queryset=Dataset.objects.all(),
)
```

## Related Documentation

- **Filter Guide**: `docs/portal-development/filters/creating-filters.md`
- **Tests**: `tests/unit/core/dataset/test_filter.py`
- **Demo Examples**: `fairdm_demo/filters.py`
"""

import django_filters

from fairdm.core.filters import BaseListFilter

from .models import Dataset


class DatasetFilter(BaseListFilter):
    """
    Filter for Dataset list views with comprehensive filtering capabilities.

    This filter provides multiple ways to discover and narrow datasets:

    **Basic Filters**:
    - license: Exact match on dataset license
    - project: Choice-based filter on associated project, narrowed to the projects the
      requester may see

    **Cross-Relationship Filters**:
    - description_type: Filter by DatasetDescription type (ABSTRACT, METHODS, etc.)
    - date_type: Filter by DatasetDate type (COLLECTED, PUBLISHED, etc.)

    **Filter Logic**:
    All filters combine using AND logic - applying multiple filters progressively
    narrows the result set. For example:
    - license=CC_BY AND project=X
    - Returns only datasets matching both criteria

    **Performance**:
    - Cross-relationship filters use database indexes on type fields
    - Expected query time: <10ms for most filter combinations on 10k+ datasets

    **Usage in Views**:
    ```python
    from django_filters.views import FilterView
    from fairdm.core.dataset.filters import DatasetFilter


    class DatasetListView(FilterView):
        filterset_class = DatasetFilter
        template_name = "dataset/list.html"
    ```

    **Usage in Templates**:
    ```django
    <form method="get">
        {{ filter.form.as_p }}
        <button type="submit">Filter</button>
    </form>
    ```

    See Also:
        - tests/unit/core/dataset/test_filter.py: Comprehensive test suite
        - fairdm_demo/filters.py: Examples and best practices
    """

    project = django_filters.ModelChoiceFilter(
        field_name="project",
        queryset=None,  # Set dynamically in __init__
        label="Project",
        help_text="Filter by associated project",
        empty_label="All projects",
    )

    description_type = django_filters.CharFilter(
        field_name="descriptions__type",
        lookup_expr="exact",
        label="Description Type",
        help_text="Filter by description type (e.g., ABSTRACT, METHODS)",
        distinct=True,  # Prevent duplicate results from joins
    )

    date_type = django_filters.CharFilter(
        field_name="dates__type",
        lookup_expr="exact",
        label="Date Type",
        help_text="Filter by date type (e.g., COLLECTED, PUBLISHED)",
        distinct=True,  # Prevent duplicate results from joins
    )

    class Meta:
        model = Dataset
        fields = {
            "license": ["exact"],
        }

    def __init__(self, *args, **kwargs):
        """Initialize filter and set project queryset.

        Offers public projects, plus any the requester holds ``view_project`` on
        at record level. This is not the creation form's contribution-based rule
        (``request.user.projects.all()``) - that one is the right question for
        "projects this researcher may file under" and the wrong one here, where
        an anonymous visitor must also get a usable queryset (014 plan P8).
        """
        super().__init__(*args, **kwargs)

        from fairdm.core.models import Project
        from fairdm.core.utils import get_objects_for_user

        if self.request and hasattr(self.request, "user"):
            # A real request always carries a user - authenticated or
            # AnonymousUser - so this is the visitor-facing rule.
            queryset = Project.objects.get_visible()
            if self.request.user.is_authenticated:
                permitted = get_objects_for_user(
                    self.request.user,
                    "project.view_project",
                    Project.objects.all(),
                )
                queryset = (queryset | permitted).distinct()
        else:
            # No request (e.g. a filterset built directly, outside a view):
            # there is no visitor to scope by, so the queryset is unrestricted.
            queryset = Project.objects.all()

        self.filters["project"].queryset = queryset
