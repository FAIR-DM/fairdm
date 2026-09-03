"""Custom QuerySet and Manager for Measurement model.

Provides optimized query methods for common Measurement operations including:
- Prefetching related data (sample, dataset, contributors)
- Prefetching metadata (descriptions, dates, identifiers)
- Handling polymorphic measurement types efficiently
"""

from polymorphic.managers import PolymorphicQuerySet


class MeasurementQuerySet(PolymorphicQuerySet):
    """Custom QuerySet for Measurement model with optimization methods.

    This QuerySet provides methods to efficiently query measurements and their
    related data, preventing N+1 query problems through strategic use of
    select_related and prefetch_related.

    All methods are chainable and composable with standard Django QuerySet
    operations (filter, exclude, order_by, etc.).

    See Also:
        - Developer Guide: docs/portal-development/measurements.md#step-5-queryset-optimization
        - Registry Guide: docs/portal-development/using_the_registry.md#queryset-optimization-for-measurements

    Note:
        Balances query optimization with flexibility. With_related() prefetches
        direct relationships (sample, dataset, contributors) without deep nested
        prefetching (e.g., sample's dataset), which should be added by specific
        views when needed.
    """

    def published(self):
        """Measurements whose own dataset is published (FR-011).

        Deliberately `dataset__published`, never `sample__dataset__published`: a
        measurement's presence is decided by the dataset that owns it, never by the
        dataset that owns its sample (FR-012, D3). A bare filter with no
        `select_related` - this method is also called to build filter choice lists,
        where those joins fetch nothing anyone reads. The listing's eager loading is
        `DataTableView.get_queryset()`'s deliverable (data-model.md, research.md R3).
        """
        return self.filter(dataset__published=True)

    def with_related(self):
        """Prefetch commonly accessed related objects.

        Optimizes queries by prefetching:
        - sample (ForeignKey) - the sample this measurement was made on
        - dataset (ForeignKey) - the dataset that owns this measurement
        - contributors (GenericRelation) - contributors and their roles

        Does NOT prefetch deep nested relationships (e.g., sample's dataset,
        contributors' organizations) to keep queries balanced. Views requiring
        deep nested data should chain additional select_related calls.

        Returns:
            MeasurementQuerySet: Chainable queryset with related data prefetched

        Example:
            >>> measurements = Measurement.objects.with_related().filter(dataset=my_dataset)
            >>> # Accessing measurement.sample, measurement.dataset, measurement.contributors
            >>> # will not trigger additional queries
            >>>
            >>> # Chain with additional prefetching for deep nested data:
            >>> measurements = Measurement.objects.with_related().select_related("sample__dataset")
        """
        return self.select_related(
            "sample",
            "dataset",
        ).prefetch_related(
            "contributors",
            "contributors__contributor",
            "contributors__roles",
        )

    def with_metadata(self):
        """Prefetch measurement metadata (descriptions, dates, identifiers).

        Optimizes queries by prefetching all metadata models that use
        concrete ForeignKey relationships to Measurement.

        Returns:
            MeasurementQuerySet: Chainable queryset with metadata prefetched

        Example:
            >>> measurements = Measurement.objects.with_metadata()
            >>> for measurement in measurements:
            >>> # These accesses don't trigger additional queries
            >>>     descriptions = measurement.descriptions.all()
            >>>     dates = measurement.dates.all()
            >>>     identifiers = measurement.identifiers.all()
        """
        return self.prefetch_related(
            "descriptions",
            "dates",
            "identifiers",
        )
