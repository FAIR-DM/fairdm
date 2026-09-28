"""Serializers for locations and GeoJSON features."""

from collections import OrderedDict

from django.core.exceptions import ImproperlyConfigured
from rest_framework import serializers
from rest_framework.fields import Field as Field
from rest_framework.serializers import LIST_SERIALIZER_KWARGS, ListSerializer

try:
    from rest_framework_gis.serializers import GeoFeatureModelSerializer
except ModuleNotFoundError as exc:
    raise ImproperlyConfigured(
        "fairdm.contrib.location.serializers requires djangorestframework-gis, "
        "which is not installed. Install the 'gis' extra: pip install fairdm[gis]"
    ) from exc

from .models import Point


class PointSerializer(serializers.ModelSerializer):
    """Serialize a location."""

    class Meta:
        model = Point
        exclude = ["id", "created", "elevation"]


class FeatureCollectionSerializer(ListSerializer):
    """Serialize a queryset as a GeoJSON ``FeatureCollection``."""

    @property
    def data(self):
        """Return the serialized data without wrapping it in a list."""
        return super(ListSerializer, self).data

    def to_representation(self, data):
        """Return the queryset's features as a ``FeatureCollection``."""
        return OrderedDict(
            (
                ("type", "FeatureCollection"),
                ("features", data.feature_collection()["features"]),
            )
        )


class FeatureSerializer(GeoFeatureModelSerializer):
    """Serialize a queryset as GeoJSON features, using the queryset's own feature annotation."""

    @classmethod
    def many_init(cls, *args, **kwargs):
        """Build a ``FeatureCollectionSerializer`` around the child serializer.

        Args:
            *args: Passed to the serializers.
            **kwargs: Passed to the child serializer, and the list-serializer options to the list serializer.

        Returns:
            The list serializer.
        """
        child_serializer = cls(*args, **kwargs)
        list_kwargs = {"child": child_serializer}
        list_kwargs.update(
            {
                key: value
                for key, value in kwargs.items()
                if key in LIST_SERIALIZER_KWARGS
            }
        )
        meta = getattr(cls, "Meta", None)
        list_serializer_class = getattr(
            meta, "list_serializer_class", FeatureCollectionSerializer
        )
        return list_serializer_class(*args, **list_kwargs)

    def to_representation(self, data):
        """Return the single record's feature."""
        data = data.features()
        return data.get().feature


class GeoFeatureSerializer(FeatureSerializer):
    """Serialize records as GeoJSON features using their ``geom`` field."""

    class Meta:
        geo_field = "geom"
        exclude = ["references", "last_modified"]
