"""QuerySet for measurements, with helpers that load related records in a bounded number of queries."""

from polymorphic.managers import PolymorphicQuerySet


class MeasurementQuerySet(PolymorphicQuerySet):
    """QuerySet for measurements, whose methods chain with the standard queryset operations.

    ``with_related()`` prefetches direct relationships without deep nesting, which views add
    themselves when needed. See docs/portal-development/measurements.md.
    """

    def published(self):
        """Return the measurements whose own dataset is published.

        Deliberately ``dataset__published``, never ``sample__dataset__published``: a measurement's
        presence is decided by the dataset that owns it, not the one that owns its sample. It is
        a bare filter with no ``select_related``, as it also builds filter choice lists.

        Returns:
            The measurements in published datasets.
        """
        return self.filter(dataset__published=True)

    def with_related(self):
        """Load each measurement's sample and dataset, and prefetch its contributors and their roles.

        Deeper relationships, such as the sample's dataset, are left to callers to chain.

        Returns:
            The queryset with the related records loaded.

        Example:
            ```python
            measurements = Measurement.objects.with_related().filter(dataset=my_dataset)
            ```
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
        """Prefetch the descriptions, dates and identifiers.

        Returns:
            The queryset with the prefetches applied.
        """
        return self.prefetch_related(
            "descriptions",
            "dates",
            "identifiers",
        )
