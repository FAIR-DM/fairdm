from parler_rest.serializers import TranslatableModelSerializer, TranslatedFieldsField
from rest_flex_fields.serializers import FlexFieldsSerializerMixin
from rest_framework import serializers
from rest_framework.serializers import HyperlinkedIdentityField, HyperlinkedModelSerializer, ModelSerializer

from fairdm.contrib.identity.models import Authority, Database
from fairdm.contrib.location.models import Point
from fairdm.models import Dataset, Project, Sample

from .utils import BaseSerializerMixin


class DescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ["type", "text"]


# class DateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Date
#         fields = ["type", "value"]


class ProjectSerializer(FlexFieldsSerializerMixin, ModelSerializer):
    web = HyperlinkedIdentityField(view_name="project-detail")
    # dates = DateSerializer(many=True)
    # descriptions = serializer_factory(Project.descriptions_model, DescriptionSerializer)(many=True)

    class Meta:
        model = Project
        depth = 1
        exclude = ["visibility", "options"]
        # fields = ["web", "name", "created", "modified", "dates", "datasets"]
        expandable_fields = {
            # "dates": (DateSerializer, {"many": True}),
            "datasets": (
                "fairdm.contrib.api.serializers.DatasetSerializer",
                {"many": True},
            ),
        }


class ProjectAPISerializer(BaseSerializerMixin, ProjectSerializer, HyperlinkedModelSerializer):
    pass


class DatasetSerializer(BaseSerializerMixin, HyperlinkedModelSerializer):
    web = HyperlinkedIdentityField(view_name="dataset-detail")
    # dates = DateSerializer(many=True)

    # sample_types = serializers.SerializerMethodField()
    # sample_count = serializers.SerializerMethodField()
    license = serializers.StringRelatedField()

    class Meta:
        model = Dataset
        exclude = ["visibility"]
        expandable_fields = {"project": ProjectSerializer}

    def get_sample_types(self, obj):
        return obj.sample_types


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Point
        fields = ["x", "y"]


class SampleSerializer(FlexFieldsSerializerMixin, ModelSerializer):
    # web = HyperlinkedIdentityField(view_name="sample-detail")
    location = LocationSerializer(many=False, read_only=True)

    class Meta:
        model = Sample
        exclude = ["id", "options"]


class MeasurementSerializer(FlexFieldsSerializerMixin, ModelSerializer):
    sample = SampleSerializer(
        fields=[
            "type",
            "name",
            "details",
            "parent",
            "dataset",
        ]
    )

    class Meta:
        fields = ["sample", "name"]


class DatabaseSerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Database)
    # image = serializers.ImageField()

    class Meta:
        model = Database
        exclude = ["id"]


class AuthoritySerializer(TranslatableModelSerializer):
    translations = TranslatedFieldsField(shared_model=Authority)

    class Meta:
        model = Authority
        exclude = ["id"]


class IdentitySerializer(serializers.Serializer):
    database = DatabaseSerializer()
    authority = AuthoritySerializer()
