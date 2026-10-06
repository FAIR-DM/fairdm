"""Tests for FairDM API serializer generation (Feature 011 â€” US6)."""

import pytest
from rest_framework import serializers
from rest_framework_guardian.serializers import ObjectPermissionsAssignmentMixin

from fairdm.api.serializers import _SERIALIZER_CACHE, build_model_serializer


@pytest.fixture()
def project_model():
    from fairdm.core.project.models import Project

    return Project


@pytest.fixture()
def simple_serializer(project_model):
    return build_model_serializer(
        project_model,
        ["uuid", "name", "visibility"],
        view_name="project-detail",
    )


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


class TestBuildModelSerializer:
    def test_generated_class_name(self, project_model):
        cls = build_model_serializer(project_model, ["uuid", "name"])
        assert cls.__name__ == "ProjectSerializer"
        assert "API" not in cls.__name__, (
            "Auto-generated serializer class names must not include 'API' postfix "
            "so drf-spectacular produces clean schema component names."
        )

    def test_fields_included(self, simple_serializer):
        for field in ("uuid", "name", "visibility"):
            assert field in simple_serializer.Meta.fields

    def test_url_field_included_when_view_name_provided(self, simple_serializer):
        assert "url" in simple_serializer.Meta.fields
        assert simple_serializer.Meta.fields[0] == "url"

    def test_url_field_absent_when_no_view_name(self, project_model):
        cls = build_model_serializer(project_model, ["uuid", "name"])
        assert "url" not in cls.Meta.fields

    def test_is_model_serializer_subclass(self, simple_serializer):
        assert issubclass(simple_serializer, serializers.ModelSerializer)

    def test_a_core_record_serializer_credits_its_creator(self, simple_serializer):
        from fairdm.api.serializers import CreatorCreditMixin

        assert issubclass(simple_serializer, CreatorCreditMixin)
        assert not issubclass(simple_serializer, ObjectPermissionsAssignmentMixin)

    def test_a_serializer_for_another_model_still_assigns_stored_permissions(self):
        from fairdm.contrib.contributors.models import Organization

        cls = build_model_serializer(Organization, ["name"])

        assert issubclass(cls, ObjectPermissionsAssignmentMixin)

    def test_get_permissions_map_returns_correct_perms(self):
        from unittest.mock import MagicMock

        from fairdm.contrib.contributors.models import Organization

        cls = build_model_serializer(Organization, ["name"])
        expected_perms = {
            "view_organization",
            "change_organization",
            "delete_organization",
        }

        mock_user = MagicMock()
        mock_request = MagicMock(user=mock_user)
        instance = cls(data={}, context={"request": mock_request})
        perm_map = instance.get_permissions_map(created=True)
        assert set(perm_map.keys()) == expected_perms
        for _perm, users in perm_map.items():
            assert users == [mock_user]

    def test_caching_returns_same_class_object(self, project_model):
        _SERIALIZER_CACHE.clear()
        cls1 = build_model_serializer(
            project_model, ["uuid", "name"], view_name="project-detail"
        )
        cls2 = build_model_serializer(
            project_model, ["uuid", "name"], view_name="project-detail"
        )
        assert cls1 is cls2

    def test_different_fields_produce_different_classes(self, project_model):
        _SERIALIZER_CACHE.clear()
        cls1 = build_model_serializer(project_model, ["uuid", "name"])
        cls2 = build_model_serializer(project_model, ["uuid", "name", "visibility"])
        assert cls1 is not cls2

    def test_flattens_grouped_tuples(self, project_model):
        cls = build_model_serializer(project_model, [("uuid", "name"), "visibility"])
        for field in ("uuid", "name", "visibility"):
            assert field in cls.Meta.fields


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
            "polymorphic_ctype",
        ]
        for field in required:
            assert field in BaseSampleSerializer.Meta.fields, (
                f"Required field '{field}' missing from BaseSampleSerializer.Meta.fields"
            )

    def test_meta_fields_exact(self):
        from fairdm.api.serializers import BaseSampleSerializer

        expected = {
            "url",
            "uuid",
            "name",
            "local_id",
            "status",
            "dataset",
            "added",
            "modified",
            "polymorphic_ctype",
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
            "polymorphic_ctype",
        ]
        for field in required:
            assert field in BaseMeasurementSerializer.Meta.fields, (
                f"Required field '{field}' missing from BaseMeasurementSerializer.Meta.fields"
            )

    def test_meta_fields_exact(self):
        from fairdm.api.serializers import BaseMeasurementSerializer

        expected = {
            "url",
            "uuid",
            "name",
            "sample",
            "dataset",
            "added",
            "modified",
            "polymorphic_ctype",
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

        DatasetFactory(visibility=Visibility.PUBLIC)
        resp = api_client.get(reverse("api:dataset-list"))
        assert resp.status_code == 200
        result = resp.json()["results"][0]
        for field in ("uuid", "name", "visibility"):
            assert field in result, f"Expected '{field}' in dataset response"
