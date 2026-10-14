"""QuerySet for measurements, with helpers that load related records in a bounded number of queries."""

from django.contrib.gis.db.models import PointField
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Case, F, When
from polymorphic.managers import PolymorphicQuerySet

from fairdm.contrib.location.managers import Spatial
from fairdm.core.managers import RecordVisibilityMixin


class MeasurementQuerySet(RecordVisibilityMixin, PolymorphicQuerySet):
    """QuerySet for measurements, whose methods chain with the standard queryset operations.

    ``with_related()`` prefetches direct relationships without deep nesting, which views add
    themselves when needed. See docs/portal-development/measurements.md.

    ``inside()``, ``within_distance()`` and ``nearest()`` find measurements by their effective
    location: their own, else their sample's for a viewer who may open the sample.
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

    def inside(self, area, user=None):
        """Return the measurements whose effective location lies in an area, the edge included.

        The answer is the union of two subqueries, each on one table so each uses its own
        spatial index: measurements whose own location is covered, and measurements with none
        whose sample, visible to the viewer, is covered. An ``OR`` across the join would use
        neither index.

        Args:
            area: A GEOS polygon, or a ``(west, south, east, north)`` tuple in degrees.
            user: The viewer, or ``None`` for a visitor who is not signed in.

        Returns:
            The measurements inside the area.
        """
        from fairdm.core.measurement.models import Measurement
        from fairdm.core.sample.models import Sample

        area = Spatial.polygon(area)
        own = Measurement.objects.filter(location__coveredby=area)
        samples = Sample.objects.visible_to(user).inside(area)
        inherited = Measurement.objects.filter(
            location__isnull=True, sample__in=samples.values("pk")
        )
        return self.filter(pk__in=own.values("pk").union(inherited.values("pk")))

    def within_distance(self, point, distance, user=None):
        """Return the measurements whose effective location is within a distance of a point.

        Built from the same two subqueries as :meth:`inside`.

        Args:
            point: A GEOS point.
            distance: A ``D`` measure, or a number of metres.
            user: The viewer, or ``None`` for a visitor who is not signed in.

        Returns:
            The measurements within the distance, measured on the ground.
        """
        from fairdm.core.measurement.models import Measurement
        from fairdm.core.sample.models import Sample

        near = (Spatial.point(point), Spatial.distance(distance))
        own = Measurement.objects.alias(geography=Spatial.geography()).filter(
            geography__dwithin=near
        )
        samples = Sample.objects.visible_to(user).within_distance(*near)
        inherited = Measurement.objects.filter(
            location__isnull=True, sample__in=samples.values("pk")
        )
        return self.filter(pk__in=own.values("pk").union(inherited.values("pk")))

    def nearest(self, point, user=None):
        """Order the measurements by the distance of their effective location from a point.

        Args:
            point: A GEOS point.
            user: The viewer, or ``None`` for a visitor who is not signed in.

        Returns:
            The measurements nearest first, each carrying ``distance`` as a ``D`` measure, or
            ``None`` for one with no effective location, which comes last.
        """
        return (
            self.with_effective_location(user)
            .annotate(
                distance=Distance(
                    Spatial.geography("effective_location"), Spatial.point(point)
                )
            )
            .order_by(F("distance").asc(nulls_last=True))
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
