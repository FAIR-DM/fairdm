"""Queryset methods for locations, including GeoJSON feature output."""

from django.contrib.gis.db import models
from django.contrib.postgres.aggregates import JSONBAgg

from fairdm.db.gis.functions import AsGeoFeature


class PointManager(models.QuerySet):
    """Queryset that annotates locations with distances and GeoJSON features."""

    def with_distance(self, point):
        """Annotate each location with its distance from a point.

        Args:
            point: The point to measure from.

        Returns:
            The queryset with a ``distance`` annotation.
        """
        return self.annotate(distance=models.Distance("geom", point))

    def get_feature(self, *args, **kwargs):
        """Return the single location matching the lookups, annotated as a GeoJSON feature.

        Args:
            *args: Field names that become the feature's properties.
            **kwargs: Lookups passed to ``get``.

        Returns:
            The matching location with a ``feature`` annotation.
        """
        return self.annotate(feature=AsGeoFeature(*args)).get(*args, **kwargs)

    def features(self, *args):
        """Annotate each location as a GeoJSON feature.

        Args:
            *args: Field names that become the feature's properties. Defaults to every field.

        Returns:
            The queryset with a ``feature`` annotation.
        """
        if not args:
            args = [f.name for f in self.model._meta.fields]
        return self.annotate(feature=AsGeoFeature(*args))

    def feature_collection(self, *args):
        """Aggregate the locations' features into one list.

        Args:
            *args: Field names that become each feature's properties.

        Returns:
            A dict with the ``features`` list.
        """
        return self.features(*args).aggregate(features=JSONBAgg("feature"))

    def as_feature_collection(self, *args):
        """Return the locations as a GeoJSON ``FeatureCollection``.

        Args:
            *args: Field names that become each feature's properties.

        Returns:
            A GeoJSON ``FeatureCollection`` dict.
        """
        return dict(type="FeatureCollection", **self.feature_collection())
