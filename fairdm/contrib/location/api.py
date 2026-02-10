from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.response import Response
from rest_framework_gis.serializers import (
    GeoFeatureModelSerializer,
    GeometrySerializerMethodField,
)

from fairdm.api.serializers import BaseSerializerMixin
from fairdm.api.utils import DjangoFilterBackend
from fairdm.api.viewsets import BaseViewSet
from fairdm.contrib.samples.models import Sample

from .serializers import GeoFeatureSerializer


class SampleGeojsonSerializer(BaseSerializerMixin, GeoFeatureModelSerializer):
    geom = GeometrySerializerMethodField()

    def get_geom(self, obj):
        return obj.location.point

    class Meta:
        model = Sample
        geo_field = "geom"
        id_field = "uuid"
        fields = ["uuid", "title", "geom"]


class GeoJsonViewset(BaseViewSet):
    distance_filter_field = "point"
    distance_ordering_filter_field = "point"
    filter_backends = (DjangoFilterBackend,)

    @method_decorator(cache_page(60 * 60 * 2))
    def list(self, request, *args, **kwargs):
        if self.is_geojson():
            qs = self.filter_queryset(self.get_queryset())
            serializer = GeoFeatureSerializer(qs, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Overriding the default docstring"""
        instance = self.get_object()
        if self.is_geojson():
            instance = self.get_queryset().filter(uuid=self.get_object().uuid)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def is_geojson(self):
        if self.request.accepted_renderer:
            return self.request.accepted_renderer.format == "geojson"
