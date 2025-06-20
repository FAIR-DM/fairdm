from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_access_policy.access_view_set_mixin import AccessViewSetMixin
from rest_flex_fields import is_expanded
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_pandas import PandasMixin

from fairdm.contrib.api.access_policies import CoreAccessPolicy
from fairdm.contrib.api.utils import api_doc
from fairdm.models import Dataset, Measurement, Project, Sample
from fairdm.registry import registry

from . import serializers
from .serializers import DatasetSerializer, ProjectSerializer, SampleSerializer


class BaseViewSet(AccessViewSetMixin, viewsets.ModelViewSet):
    access_policy = CoreAccessPolicy
    permission_classes = [
        DjangoModelPermissionsOrAnonReadOnly,
    ]


@extend_schema_view(
    list=extend_schema(description=api_doc(Project, "list")),
)
class ProjectViewset(ReadOnlyModelViewSet):
    """A project is a collection of datasets and associated metadata. The Project model
    is the top level model in the FairDM schema heirarchy and all datasets, samples,
    sites and measurements should relate back to a project."""

    max_paginate_by = 100
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()
    fields = {
        # "list": ["id", "name", "created", "modified"],
        "detail": ["url", "name", "created", "modified"],
    }

    def get_queryset(self):
        queryset = Project.objects.all()
        if is_expanded(self.request, "datasets"):
            queryset = queryset.prefetch_related("datasets")
        return queryset

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        kwargs.setdefault("fields", self.fields.get(self.action, []))
        return serializer_class(*args, **kwargs)


@extend_schema_view(
    list=extend_schema(description=api_doc(Dataset, "list")),
)
class DatasetViewset(ReadOnlyModelViewSet):
    serializer_class = DatasetSerializer
    queryset = Dataset.objects.prefetch_related("contributors", "descriptions", "keywords").all()


@extend_schema_view(
    list=extend_schema(description=api_doc(Sample, "list")),
)
class SampleViewset(PandasMixin, ReadOnlyModelViewSet):
    # renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [PandasCSVRenderer]
    serializer_class = SampleSerializer
    lookup_field = "uuid"
    queryset = (
        Sample.objects.prefetch_related("contributors", "keywords").select_related("dataset", "dataset__project").all()
    )


class MeasurementViewset(ReadOnlyModelViewSet):
    serializer_class = serializers.MeasurementSerializer
    queryset = Measurement.objects.all()

    def get_serializer_class(self):
        serializer = self.serializer_class
        serializer.Meta.model = self.queryset.model
        return serializer


def sample_viewset_factory(sample_type):
    """Factory function to create a SampleViewset for a specific sample type."""
    config = sample_type["config"]
    viewset_class = type(
        sample_type["class"].__name__,
        (SampleViewset,),
        {"queryset": sample_type["class"].objects.all(), "serializer_class": config.get_serializer_class()},
    )
    return viewset_class


def measurement_viewset_factory(measurement_type):
    """Factory function to create a MeasurementViewset for a specific measurement type."""
    config = measurement_type["config"]
    viewset_class = type(
        measurement_type["class"].__name__,
        (MeasurementViewset,),
        {"queryset": measurement_type["class"].objects.all(), "serializer_class": config.get_serializer_class()},
    )
    return viewset_class


sample_viewsets = []
for sample_type in registry.samples:
    sample_viewsets.append(sample_viewset_factory(sample_type))

measurement_viewsets = []
for measurement_type in registry.measurements:
    measurement_viewsets.append(
        measurement_viewset_factory(measurement_type)
    )  # Create a viewset for each measurement type


# @extend_schema_view(
#     list=extend_schema(description=api_doc(measurement.Measurement, "list")),
# )
# class MeasurementViewset(ReadOnlyModelViewSet):
#     """A viewset for the Measurement model, which is used to store measurements taken on samples."""

#     queryset = measurement.Measurement.objects.all()
#     serializer_class = serializers.MeasurementSerializer

#     def get_serializer_class(self):
#         serializer = self.serializer_class
#         serializer.Meta.model = self.queryset.model
#         return serializer
