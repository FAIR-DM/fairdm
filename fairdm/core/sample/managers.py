"""Custom QuerySet and Manager for Sample model.

Provides optimized query methods for common Sample operations including:
- Prefetching related data (dataset, location, contributors)
- Prefetching metadata (descriptions, dates, identifiers)
- Filtering by relationship types
- Traversing sample hierarchies
"""

from polymorphic.managers import PolymorphicQuerySet


class SampleQuerySet(PolymorphicQuerySet):
    """Custom QuerySet for Sample model with optimization methods.

    This QuerySet provides methods to efficiently query samples and their
    related data, preventing N+1 query problems through strategic use of
    select_related and prefetch_related.

    All methods are chainable and composable with standard Django QuerySet
    operations (filter, exclude, order_by, etc.).
    """

    def with_related(self):
        """Prefetch commonly accessed related objects.

        Optimizes queries by prefetching:
        - dataset (ForeignKey)
        - location (ForeignKey)
        - contributors (GenericRelation)

        Returns:
            SampleQuerySet: Chainable queryset with related data prefetched

        Example:
            >>> samples = Sample.objects.with_related().filter(dataset=my_dataset)
            >>> # Accessing sample.dataset, sample.location, sample.contributors
            >>> # will not trigger additional queries
        """
        return self.select_related(
            "dataset",
            "location",
        ).prefetch_related(
            "contributors",
            "contributors__contributor",
            "contributors__roles",
        )

    def with_metadata(self):
        """Prefetch sample metadata (descriptions, dates, identifiers).

        Optimizes queries by prefetching all metadata models that use
        concrete ForeignKey relationships to Sample.

        Returns:
            SampleQuerySet: Chainable queryset with metadata prefetched

        Example:
            >>> samples = Sample.objects.with_metadata()
            >>> for sample in samples:
            >>> # These accesses don't trigger additional queries
            >>>     descriptions = sample.descriptions.all()
            >>>     dates = sample.dates.all()
            >>>     identifiers = sample.identifiers.all()
        """
        return self.prefetch_related(
            "descriptions",
            "dates",
            "identifiers",
        )

    def by_relationship(self, relationship_type):
        """Filter samples by their relationship type.

        Args:
            relationship_type: The type of relationship to filter by
                             (e.g., 'parent-child', 'derived-from', 'split-from')

        Returns:
            SampleQuerySet: Filtered queryset containing only samples with
                          the specified relationship type

        Example:
            >>> # Get all samples that have parent-child relationships
            >>> samples = Sample.objects.by_relationship("parent-child")
        """
        from .models import SampleRelation

        # Get sample IDs that participate in relationships of this type
        relationship_ids = SampleRelation.objects.filter(relationship_type=relationship_type).values_list(
            "source_id", "target_id"
        )

        # Flatten the list of (source, target) tuples to get unique sample IDs
        sample_ids = set()
        for source_id, target_id in relationship_ids:
            sample_ids.add(source_id)
            sample_ids.add(target_id)

        return self.filter(id__in=sample_ids)

    def get_descendants(self, sample, max_depth=None):
        """Get all descendant samples in a hierarchy.

        Uses iterative breadth-first search to traverse the sample hierarchy
        and collect all descendants. This is more efficient than recursive
        queries for moderate depths (<10 levels).

        Args:
            sample: The sample instance to get descendants for
            max_depth: Optional maximum depth to traverse (None = unlimited)

        Returns:
            SampleQuerySet: Queryset containing all descendant samples

        Example:
            >>> parent = Sample.objects.get(uuid="s_abc123")
            >>> descendants = Sample.objects.get_descendants(parent, max_depth=5)
            >>> # descendants includes all children, grandchildren, etc.
        """
        from .models import SampleRelation

        if max_depth is not None and max_depth <= 0:
            return self.none()

        descendant_ids = set()
        current_level = {sample.id}
        depth = 0

        while current_level:
            if max_depth is not None and depth >= max_depth:
                break

            # Get all samples that have current level samples as sources
            next_level = set(
                SampleRelation.objects.filter(source_id__in=current_level).values_list("target_id", flat=True)
            )

            # Remove any samples we've already seen to prevent cycles
            next_level = next_level - descendant_ids - {sample.id}

            descendant_ids.update(next_level)
            current_level = next_level
            depth += 1

        if not descendant_ids:
            return self.none()

        return self.filter(id__in=descendant_ids)

    def get_ancestors(self, sample, max_depth=None):
        """Get all ancestor samples in a hierarchy.

        Uses iterative breadth-first search to traverse the sample hierarchy
        in reverse (target to source) and collect all ancestors.

        Args:
            sample: The sample instance to get ancestors for
            max_depth: Optional maximum depth to traverse (None = unlimited)

        Returns:
            SampleQuerySet: Queryset containing all ancestor samples

        Example:
            >>> child = Sample.objects.get(uuid="s_xyz789")
            >>> ancestors = Sample.objects.get_ancestors(child, max_depth=3)
            >>> # ancestors includes all parents, grandparents, etc.
        """
        from .models import SampleRelation

        if max_depth is not None and max_depth <= 0:
            return self.none()

        ancestor_ids = set()
        current_level = {sample.id}
        depth = 0

        while current_level:
            if max_depth is not None and depth >= max_depth:
                break

            # Get all samples that have current level samples as targets
            next_level = set(
                SampleRelation.objects.filter(target_id__in=current_level).values_list("source_id", flat=True)
            )

            # Remove any samples we've already seen to prevent cycles
            next_level = next_level - ancestor_ids - {sample.id}

            ancestor_ids.update(next_level)
            current_level = next_level
            depth += 1

        if not ancestor_ids:
            return self.none()

        return self.filter(id__in=ancestor_ids)
