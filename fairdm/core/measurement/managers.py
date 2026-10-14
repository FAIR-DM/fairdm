"""QuerySet for measurements, with helpers that load related records in a bounded number of queries."""

from django.contrib.gis.db.models import PointField
from django.db.models import Case, F, When
from polymorphic.managers import PolymorphicQuerySet

from fairdm.core.managers import RecordVisibilityMixin


class MeasurementQuerySet(RecordVisibilityMixin, PolymorphicQuerySet):
    """QuerySet for measurements, whose methods chain with the standard queryset operations.

    ``with_related()`` prefetches direct relationships without deep nesting, which views add
    themselves when needed. See docs/portal-development/measurements.md.
    """

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

    def with_effective_location(self, user=None):
        """Annotate ``effective_location``: the measurement's own location, else its sample's.

        The sample's location is used only where the viewer may open the sample, so a
        measurement in a published dataset never gives away where an unpublished sample was taken.

        Args:
            user: The viewer, or ``None`` for a visitor who is not signed in.

        Returns:
            The queryset, each measurement carrying ``effective_location`` as a WGS 84 point or
            ``None``.

        Example:
            ```python
            for measurement in Measurement.objects.with_effective_location(
                request.user
            ):
                print(measurement.effective_location)
            ```
        """
        from fairdm.core.sample.models import Sample

        visible_samples = Sample.objects.visible_to(user).values("pk")
        return self.annotate(
            effective_location=Case(
                When(location__isnull=False, then=F("location")),
                When(sample__in=visible_samples, then=F("sample__location")),
                default=None,
                output_field=PointField(srid=4326),
            )
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
