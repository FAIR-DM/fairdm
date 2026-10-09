"""Tests for FairDM API serializer generation (Feature 011 â€” US6)."""

import pytest
from rest_framework import serializers


@pytest.mark.django_db
class TestGenerateViewsetTierThree:
    def test_explicit_serializer_class_used_directly(self):
        from rest_framework import serializers as drf_serializers

        from fairdm.api.viewsets import generate_viewset
        from fairdm.core.project.models import Project
        from fairdm.registry.config import ModelConfiguration

        class MyCustomSerializer(drf_serializers.ModelSerializer):
            class Meta:
                model = Project
                fields = ["uuid", "name"]

        class Config(ModelConfiguration):
            model = Project
            serializer_class = MyCustomSerializer  # type: ignore[assignment]

        config = Config()
        viewset = generate_viewset(config)
        assert viewset.serializer_class is MyCustomSerializer


@pytest.mark.django_db
class TestGenerateViewsetTierTwo:
    def test_serializer_fields_override_fields(self):
        from fairdm.api.viewsets import generate_viewset
        from fairdm.core.project.models import Project
        from fairdm.registry.config import ModelConfiguration

        class Config(ModelConfiguration):
            model = Project
            fields = ["uuid", "name", "visibility", "status"]
            serializer_fields = ["uuid", "name"]

        config = Config()
        viewset = generate_viewset(config)
        serializer_cls = viewset.serializer_class
        declared = {f for f in serializer_cls.Meta.fields if f != "url"}
        assert declared == {"uuid", "name"}
        assert "visibility" not in declared
        assert "status" not in declared


@pytest.mark.django_db
class TestGenerateViewsetTierFour:
    def test_no_fields_config_produces_valid_serializer(self):
        from fairdm.api.viewsets import generate_viewset
        from fairdm.core.project.models import Project
        from fairdm.registry.config import ModelConfiguration

        class Config(ModelConfiguration):
            model = Project

        config = Config()
        viewset = generate_viewset(config)
        assert issubclass(viewset.serializer_class, serializers.ModelSerializer)
        assert len(viewset.serializer_class.Meta.fields) > 0


class TestBaseSampleSerializer:
    def test_meta_fields_include_all_required(self):
        from fairdm.api.serializers import BaseSampleSerializer

        required = [
            "url",
            "uuid",
            "name",
            "local_id",
            "status",
            "dataset",
            "added",
            "modified",
        ]
        for field in required:
            assert field in BaseSampleSerializer.Meta.fields, (
                f"Required field '{field}' missing from BaseSampleSerializer.Meta.fields"
            )

    def test_meta_fields_exact(self):
        from fairdm.api.serializers import BaseSampleSerializer

        expected = {
            "url",
            "html_url",
            "uuid",
            "name",
            "local_id",
            "status",
            "dataset",
            "added",
            "modified",
            "descriptions",
            "dates",
            "identifiers",
            "keywords",
            "contributors",
        }
        assert set(BaseSampleSerializer.Meta.fields) == expected

    def test_is_model_serializer_subclass(self):
        from rest_framework import serializers

        from fairdm.api.serializers import BaseSampleSerializer

        assert issubclass(BaseSampleSerializer, serializers.ModelSerializer)

    def test_credits_its_creator(self):
        from fairdm.api.serializers import BaseSampleSerializer, CreatorCreditMixin

        assert issubclass(BaseSampleSerializer, CreatorCreditMixin)

    def test_meta_model_is_sample(self):
        from fairdm.api.serializers import BaseSampleSerializer
        from fairdm.core.sample.models import Sample

        assert BaseSampleSerializer.Meta.model is Sample


class TestBaseMeasurementSerializer:
    def test_meta_fields_include_all_required(self):
        from fairdm.api.serializers import BaseMeasurementSerializer

        required = [
            "url",
            "uuid",
            "name",
            "sample",
            "dataset",
            "added",
            "modified",
        ]
        for field in required:
            assert field in BaseMeasurementSerializer.Meta.fields, (
                f"Required field '{field}' missing from BaseMeasurementSerializer.Meta.fields"
            )

    def test_meta_fields_exact(self):
        from fairdm.api.serializers import BaseMeasurementSerializer

        expected = {
            "url",
            "html_url",
            "uuid",
            "name",
            "sample",
            "dataset",
            "added",
            "modified",
            "descriptions",
            "dates",
            "identifiers",
            "keywords",
            "contributors",
        }
        assert set(BaseMeasurementSerializer.Meta.fields) == expected

    def test_is_model_serializer_subclass(self):
        from rest_framework import serializers

        from fairdm.api.serializers import BaseMeasurementSerializer

        assert issubclass(BaseMeasurementSerializer, serializers.ModelSerializer)

    def test_credits_its_creator(self):
        from fairdm.api.serializers import BaseMeasurementSerializer, CreatorCreditMixin

        assert issubclass(BaseMeasurementSerializer, CreatorCreditMixin)

    def test_meta_model_is_measurement(self):
        from fairdm.api.serializers import BaseMeasurementSerializer
        from fairdm.core.measurement.models import Measurement

        assert BaseMeasurementSerializer.Meta.model is Measurement


@pytest.mark.django_db
class TestAutoGeneratedSerializerInheritsBase:
    def test_auto_generated_sample_serializer_inherits_base(self):
        from fairdm.api.serializers import BaseSampleSerializer
        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry import registry

        sample_models = list(registry.samples)
        assert sample_models, (
            "No Sample types registered â€” ensure demo app is in INSTALLED_APPS"
        )
        model = sample_models[0]
        config = registry.get_for_model(model)
        viewset = generate_viewset(config)
        assert issubclass(viewset.serializer_class, BaseSampleSerializer), (
            f"Auto-generated serializer for {model.__name__} does not inherit BaseSampleSerializer"
        )

    def test_auto_generated_measurement_serializer_inherits_base(self):
        from fairdm.api.serializers import BaseMeasurementSerializer
        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry import registry

        measurement_models = list(registry.measurements)
        assert measurement_models, "No Measurement types registered"
        model = measurement_models[0]
        config = registry.get_for_model(model)
        viewset = generate_viewset(config)
        assert issubclass(viewset.serializer_class, BaseMeasurementSerializer), (
            f"Auto-generated serializer for {model.__name__} does not inherit BaseMeasurementSerializer"
        )


@pytest.mark.django_db
class TestImproperlyConfiguredEnforcement:
    def test_non_conforming_sample_serializer_raises(self):
        from django.core.exceptions import ImproperlyConfigured
        from rest_framework import serializers as drf_serializers

        from demo.models import CustomParentSample
        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry.config import ModelConfiguration

        class NonConformingSampleSerializer(drf_serializers.ModelSerializer):
            class Meta:
                model = CustomParentSample
                fields = ["uuid"]

        class Config(ModelConfiguration):
            model = CustomParentSample
            serializer_class = NonConformingSampleSerializer  # type: ignore[assignment]

        config = Config()
        with pytest.raises(ImproperlyConfigured):
            generate_viewset(config)

    def test_non_conforming_measurement_serializer_raises(self):
        from django.core.exceptions import ImproperlyConfigured
        from rest_framework import serializers as drf_serializers

        from demo.models import ExampleMeasurement
        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry.config import ModelConfiguration

        class NonConformingMeasurementSerializer(drf_serializers.ModelSerializer):
            class Meta:
                model = ExampleMeasurement
                fields = ["uuid"]

        class Config(ModelConfiguration):
            model = ExampleMeasurement
            serializer_class = NonConformingMeasurementSerializer  # type: ignore[assignment]

        config = Config()
        with pytest.raises(ImproperlyConfigured):
            generate_viewset(config)

    def test_conforming_sample_serializer_succeeds(self):
        from demo.models import CustomParentSample
        from fairdm.api.serializers import BaseSampleSerializer
        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry.config import ModelConfiguration

        class ConformingSampleSerializer(BaseSampleSerializer):
            class Meta(BaseSampleSerializer.Meta):
                model = CustomParentSample
                fields = [*BaseSampleSerializer.Meta.fields, "char_field"]

        class Config(ModelConfiguration):
            model = CustomParentSample
            serializer_class = ConformingSampleSerializer  # type: ignore[assignment]

        config = Config()
        viewset = generate_viewset(config)
        assert viewset.serializer_class is ConformingSampleSerializer

    def test_conforming_measurement_serializer_succeeds(self):
        from demo.models import ExampleMeasurement
        from fairdm.api.serializers import BaseMeasurementSerializer
        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry.config import ModelConfiguration

        class ConformingMeasurementSerializer(BaseMeasurementSerializer):
            class Meta(BaseMeasurementSerializer.Meta):
                model = ExampleMeasurement
                fields = [*BaseMeasurementSerializer.Meta.fields, "value"]

        class Config(ModelConfiguration):
            model = ExampleMeasurement
            serializer_class = ConformingMeasurementSerializer  # type: ignore[assignment]

        config = Config()
        viewset = generate_viewset(config)
        assert viewset.serializer_class is ConformingMeasurementSerializer


@pytest.mark.django_db
class TestSerializerFieldsInAPIResponse:
    def test_project_list_exposes_expected_fields(self, api_client):
        from django.urls import reverse

        from fairdm.factories import ProjectFactory
        from fairdm.utils.choices import Visibility

        ProjectFactory(visibility=Visibility.PUBLIC)
        resp = api_client.get(reverse("api:project-list"))
        assert resp.status_code == 200
        result = resp.json()["results"][0]
        for field in ("uuid", "name", "visibility"):
            assert field in result, f"Expected '{field}' in project response"

    def test_dataset_list_exposes_expected_fields(self, api_client):
        from django.urls import reverse

        from fairdm.factories import DatasetFactory
        from fairdm.utils.choices import Visibility

        DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        resp = api_client.get(reverse("api:dataset-list"))
        assert resp.status_code == 200
        result = resp.json()["results"][0]
        for field in ("uuid", "name", "visibility"):
            assert field in result, f"Expected '{field}' in dataset response"


@pytest.mark.django_db
class TestRecordReferenceField:
    @pytest.fixture
    def serializer_class(self):
        from fairdm.api.serializers import RecordReferenceField
        from fairdm.core.project.models import Project

        class DatasetReference(serializers.Serializer):
            project = RecordReferenceField(
                queryset=Project.objects.all(), allow_null=True
            )

        return DatasetReference

    @staticmethod
    def context_for(user=None):
        from django.contrib.auth.models import AnonymousUser
        from rest_framework.test import APIRequestFactory

        request = APIRequestFactory().get("/")
        request.user = user or AnonymousUser()
        return {"request": request}

    def test_a_related_record_is_returned_as_its_identifier_and_address(
        self, serializer_class
    ):
        from django.urls import reverse

        from fairdm.factories import DatasetFactory, ProjectFactory
        from fairdm.utils.choices import Visibility

        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )

        data = serializer_class(dataset, context=self.context_for()).data

        assert data["project"]["uuid"] == project.uuid
        assert data["project"]["url"].endswith(
            reverse("api:project-detail", kwargs={"uuid": project.uuid})
        )

    def test_a_bare_identifier_is_accepted(self, serializer_class):
        from fairdm.factories import ProjectFactory

        project = ProjectFactory()
        serializer = serializer_class(
            data={"project": project.uuid}, context=self.context_for()
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["project"] == project

    def test_the_returned_object_is_accepted(self, serializer_class):
        from fairdm.factories import ProjectFactory

        project = ProjectFactory()
        serializer = serializer_class(
            data={"project": {"uuid": project.uuid, "url": "http://testserver/x/"}},
            context=self.context_for(),
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["project"] == project

    def test_an_unknown_identifier_is_refused(self, serializer_class):
        serializer = serializer_class(
            data={"project": "pNoSuchProject"}, context=self.context_for()
        )

        assert not serializer.is_valid()
        assert serializer.errors["project"][0].code == "does_not_exist"

    @pytest.mark.parametrize("as_text", [False, True])
    def test_a_database_number_is_refused(self, serializer_class, as_text):
        from fairdm.factories import ProjectFactory

        project = ProjectFactory()
        number = str(project.pk) if as_text else project.pk
        serializer = serializer_class(
            data={"project": number}, context=self.context_for()
        )

        assert not serializer.is_valid()
        assert "project" in serializer.errors

    def test_a_record_the_caller_may_not_see_is_returned_as_null(
        self, serializer_class
    ):
        from fairdm.factories import DatasetFactory, ProjectFactory
        from fairdm.utils.choices import Visibility

        project = ProjectFactory(visibility=Visibility.PRIVATE)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )

        data = serializer_class(dataset, context=self.context_for()).data

        assert data["project"] is None

    def test_a_record_the_caller_holds_the_view_level_on_is_returned(
        self, serializer_class
    ):
        from fairdm.contrib.contributors.choices import ContributionLevel
        from fairdm.factories import (
            ContributionFactory,
            DatasetFactory,
            PersonFactory,
            ProjectFactory,
        )
        from fairdm.utils.choices import Visibility

        project = ProjectFactory(visibility=Visibility.PRIVATE)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        viewer = PersonFactory(is_active=True, is_claimed=True)
        ContributionFactory(
            content_object=project, contributor=viewer, level=ContributionLevel.VIEW
        )

        data = serializer_class(dataset, context=self.context_for(viewer)).data

        assert data["project"]["uuid"] == project.uuid
