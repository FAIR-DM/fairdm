"""Tests for FairDM API serializer generation (Feature 011 â€” US6).

Covers:
- Three-tier serializer resolution:
  1. ``serializer_class`` explicitly set â†’ used directly (no auto-generation)
  2. ``serializer_fields`` set â†’ auto-generated serializer with those fields only
  3. Only ``fields`` set â†’ auto-generated serializer using those fields
  4. Nothing set â†’ fallback auto-generation from model field inspection
- Each auto-generated serializer includes a ``url`` HyperlinkedIdentityField
- ``ObjectPermissionsAssignmentMixin`` present for guardian perm assignment
- Serializer cache: same model+fields combo returns identical class object
"""

import pytest
from rest_framework import serializers
from rest_framework_guardian.serializers import ObjectPermissionsAssignmentMixin

from fairdm.api.serializers import _SERIALIZER_CACHE, build_model_serializer

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def project_model():
    from fairdm.core.project.models import Project

    return Project


@pytest.fixture()
def simple_serializer(project_model):
    """Serializer built with an explicit field list and a view_name."""
    return build_model_serializer(
        project_model,
        ["uuid", "name", "visibility"],
        view_name="project-detail",
    )


# ---------------------------------------------------------------------------
# Tier 3 (explicit serializer_class) â€” verified at registry level
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGenerateViewsetTierThree:
    """When ``serializer_class`` is set in registry config, it is used directly."""

    def test_explicit_serializer_class_used_directly(self):
        """generate_viewset should return viewset with the custom serializer."""
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


# ---------------------------------------------------------------------------
# Tier 2 (serializer_fields override)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGenerateViewsetTierTwo:
    """When ``serializer_fields`` is set it overrides ``fields`` for the API."""

    def test_serializer_fields_override_fields(self):
        """Only the fields in ``serializer_fields`` appear in the serializer."""
        from fairdm.api.viewsets import generate_viewset
        from fairdm.core.project.models import Project
        from fairdm.registry.config import ModelConfiguration

        class Config(ModelConfiguration):
            model = Project
            fields = ["uuid", "name", "visibility", "status"]
            serializer_fields = ["uuid", "name"]  # Explicit API-only subset

        config = Config()
        viewset = generate_viewset(config)
        serializer_cls = viewset.serializer_class
        declared = {f for f in serializer_cls.Meta.fields if f != "url"}
        assert declared == {"uuid", "name"}
        assert "visibility" not in declared
        assert "status" not in declared


# ---------------------------------------------------------------------------
# Tier 1 (fields fallback) â€” tested via build_model_serializer directly
# ---------------------------------------------------------------------------


class TestBuildModelSerializer:
    """Unit tests for :func:`fairdm.api.serializers.build_model_serializer`."""

    def test_generated_class_name(self, project_model):
        """Generated class is named ``{ModelName}Serializer`` (no 'API' postfix)."""
        cls = build_model_serializer(project_model, ["uuid", "name"])
        assert cls.__name__ == "ProjectSerializer"
        assert "API" not in cls.__name__, (
            "Auto-generated serializer class names must not include 'API' postfix "
            "so drf-spectacular produces clean schema component names."
        )

    def test_fields_included(self, simple_serializer):
        """All requested fields appear in the serializer's Meta.fields."""
        for field in ("uuid", "name", "visibility"):
            assert field in simple_serializer.Meta.fields

    def test_url_field_included_when_view_name_provided(self, simple_serializer):
        """A ``url`` HyperlinkedIdentityField is prepended when view_name given."""
        assert "url" in simple_serializer.Meta.fields
        assert simple_serializer.Meta.fields[0] == "url"

    def test_url_field_absent_when_no_view_name(self, project_model):
        """No ``url`` field when no view_name is supplied."""
        cls = build_model_serializer(project_model, ["uuid", "name"])
        assert "url" not in cls.Meta.fields

    def test_is_model_serializer_subclass(self, simple_serializer):
        """Result is a ModelSerializer subclass."""
        assert issubclass(simple_serializer, serializers.ModelSerializer)

    def test_has_object_permissions_mixin(self, simple_serializer):
        """Result includes ObjectPermissionsAssignmentMixin for guardian perm assignment."""
        assert issubclass(simple_serializer, ObjectPermissionsAssignmentMixin)

    def test_get_permissions_map_returns_correct_perms(self, simple_serializer, project_model):
        """``get_permissions_map()`` maps each permission to the requesting user."""
        from unittest.mock import MagicMock

        model_name = project_model._meta.model_name
        expected_perms = {f"view_{model_name}", f"change_{model_name}", f"delete_{model_name}"}

        mock_user = MagicMock()
        mock_request = MagicMock(user=mock_user)
        # Instantiate the serializer with a context dict (the standard DRF way)
        instance = simple_serializer(data={}, context={"request": mock_request})
        perm_map = instance.get_permissions_map(created=True)
        assert set(perm_map.keys()) == expected_perms
        for _perm, users in perm_map.items():
            assert users == [mock_user]

    def test_caching_returns_same_class_object(self, project_model):
        """Calling build_model_serializer twice with the same args returns identical class."""
        _SERIALIZER_CACHE.clear()
        cls1 = build_model_serializer(project_model, ["uuid", "name"], view_name="project-detail")
        cls2 = build_model_serializer(project_model, ["uuid", "name"], view_name="project-detail")
        assert cls1 is cls2

    def test_different_fields_produce_different_classes(self, project_model):
        """Different field sets produce distinct serializer classes."""
        _SERIALIZER_CACHE.clear()
        cls1 = build_model_serializer(project_model, ["uuid", "name"])
        cls2 = build_model_serializer(project_model, ["uuid", "name", "visibility"])
        assert cls1 is not cls2

    def test_flattens_grouped_tuples(self, project_model):
        """Fields provided as grouped tuples are expanded to a flat list."""
        cls = build_model_serializer(project_model, [("uuid", "name"), "visibility"])
        for field in ("uuid", "name", "visibility"):
            assert field in cls.Meta.fields


# ---------------------------------------------------------------------------
# Tier 4 (no fields at all â€” fallback from model inspection)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGenerateViewsetTierFour:
    """When no field config is set, viewset auto-generates from model inspection."""

    def test_no_fields_config_produces_valid_serializer(self):
        """generate_viewset without any field config returns a workable serializer."""
        from fairdm.api.viewsets import generate_viewset
        from fairdm.core.project.models import Project
        from fairdm.registry.config import ModelConfiguration

        class Config(ModelConfiguration):
            model = Project
            # No fields, serializer_fields, or serializer_class

        config = Config()
        viewset = generate_viewset(config)
        # Must be a ModelSerializer subclass
        assert issubclass(viewset.serializer_class, serializers.ModelSerializer)
        # Must expose at least some fields
        assert len(viewset.serializer_class.Meta.fields) > 0


# ---------------------------------------------------------------------------
# Phase 9: Base serializer classes (FR-006 expanded)
# ---------------------------------------------------------------------------


class TestBaseSampleSerializer:
    """Unit tests for :class:`fairdm.api.serializers.BaseSampleSerializer`."""

    def test_meta_fields_include_all_required(self):
        """BaseSampleSerializer.Meta.fields must contain all guaranteed fields."""
        from fairdm.api.serializers import BaseSampleSerializer

        required = ["url", "uuid", "name", "local_id", "status", "dataset", "added", "modified", "polymorphic_ctype"]
        for field in required:
            assert field in BaseSampleSerializer.Meta.fields, (
                f"Required field '{field}' missing from BaseSampleSerializer.Meta.fields"
            )

    def test_meta_fields_exact(self):
        """BaseSampleSerializer.Meta.fields must be exactly the guaranteed list (order-insensitive)."""
        from fairdm.api.serializers import BaseSampleSerializer

        expected = {"url", "uuid", "name", "local_id", "status", "dataset", "added", "modified", "polymorphic_ctype"}
        assert set(BaseSampleSerializer.Meta.fields) == expected

    def test_is_model_serializer_subclass(self):
        """BaseSampleSerializer must be a ModelSerializer subclass."""
        from rest_framework import serializers

        from fairdm.api.serializers import BaseSampleSerializer

        assert issubclass(BaseSampleSerializer, serializers.ModelSerializer)

    def test_has_object_permissions_mixin(self):
        """BaseSampleSerializer must include ObjectPermissionsAssignmentMixin."""
        from rest_framework_guardian.serializers import ObjectPermissionsAssignmentMixin

        from fairdm.api.serializers import BaseSampleSerializer

        assert issubclass(BaseSampleSerializer, ObjectPermissionsAssignmentMixin)

    def test_meta_model_is_sample(self):
        """BaseSampleSerializer.Meta.model must be the Sample base class."""
        from fairdm.api.serializers import BaseSampleSerializer
        from fairdm.core.sample.models import Sample

        assert BaseSampleSerializer.Meta.model is Sample


class TestBaseMeasurementSerializer:
    """Unit tests for :class:`fairdm.api.serializers.BaseMeasurementSerializer`."""

    def test_meta_fields_include_all_required(self):
        """BaseMeasurementSerializer.Meta.fields must contain all guaranteed fields."""
        from fairdm.api.serializers import BaseMeasurementSerializer

        required = ["url", "uuid", "name", "sample", "dataset", "added", "modified", "polymorphic_ctype"]
        for field in required:
            assert field in BaseMeasurementSerializer.Meta.fields, (
                f"Required field '{field}' missing from BaseMeasurementSerializer.Meta.fields"
            )

    def test_meta_fields_exact(self):
        """BaseMeasurementSerializer.Meta.fields must be exactly the guaranteed list."""
        from fairdm.api.serializers import BaseMeasurementSerializer

        expected = {"url", "uuid", "name", "sample", "dataset", "added", "modified", "polymorphic_ctype"}
        assert set(BaseMeasurementSerializer.Meta.fields) == expected

    def test_is_model_serializer_subclass(self):
        from rest_framework import serializers

        from fairdm.api.serializers import BaseMeasurementSerializer

        assert issubclass(BaseMeasurementSerializer, serializers.ModelSerializer)

    def test_has_object_permissions_mixin(self):
        from rest_framework_guardian.serializers import ObjectPermissionsAssignmentMixin

        from fairdm.api.serializers import BaseMeasurementSerializer

        assert issubclass(BaseMeasurementSerializer, ObjectPermissionsAssignmentMixin)

    def test_meta_model_is_measurement(self):
        from fairdm.api.serializers import BaseMeasurementSerializer
        from fairdm.core.measurement.models import Measurement

        assert BaseMeasurementSerializer.Meta.model is Measurement


@pytest.mark.django_db
class TestAutoGeneratedSerializerInheritsBase:
    """Auto-generated serializers for registered Sample/Measurement subtypes
    must inherit from the corresponding base serializer class."""

    def test_auto_generated_sample_serializer_inherits_base(self):
        """generate_viewset for a Sample subtype produces a serializer inheriting BaseSampleSerializer."""
        from fairdm.api.serializers import BaseSampleSerializer
        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry import registry

        # Use the first registered sample from the demo app registry
        sample_models = list(registry.samples)
        assert sample_models, "No Sample types registered â€” ensure demo app is in INSTALLED_APPS"
        model = sample_models[0]
        config = registry.get_for_model(model)
        viewset = generate_viewset(config)
        assert issubclass(viewset.serializer_class, BaseSampleSerializer), (
            f"Auto-generated serializer for {model.__name__} does not inherit BaseSampleSerializer"
        )

    def test_auto_generated_measurement_serializer_inherits_base(self):
        """generate_viewset for a Measurement subtype produces a serializer inheriting BaseMeasurementSerializer."""
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
    """generate_viewset raises ImproperlyConfigured for non-conforming custom serializer_class."""

    def test_non_conforming_sample_serializer_raises(self):
        """Custom serializer_class not inheriting BaseSampleSerializer raises ImproperlyConfigured."""
        from django.core.exceptions import ImproperlyConfigured
        from rest_framework import serializers as drf_serializers

        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry.config import ModelConfiguration
        from fairdm_demo.models import CustomParentSample

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
        """Custom serializer_class not inheriting BaseMeasurementSerializer raises ImproperlyConfigured."""
        from django.core.exceptions import ImproperlyConfigured
        from rest_framework import serializers as drf_serializers

        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry.config import ModelConfiguration
        from fairdm_demo.models import ExampleMeasurement

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
        """Custom serializer_class inheriting BaseSampleSerializer does NOT raise."""
        from fairdm.api.serializers import BaseSampleSerializer
        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry.config import ModelConfiguration
        from fairdm_demo.models import CustomParentSample

        class ConformingSampleSerializer(BaseSampleSerializer):
            class Meta(BaseSampleSerializer.Meta):
                model = CustomParentSample
                fields = [*BaseSampleSerializer.Meta.fields, "char_field"]

        class Config(ModelConfiguration):
            model = CustomParentSample
            serializer_class = ConformingSampleSerializer  # type: ignore[assignment]

        config = Config()
        # Must not raise
        viewset = generate_viewset(config)
        assert viewset.serializer_class is ConformingSampleSerializer

    def test_conforming_measurement_serializer_succeeds(self):
        """Custom serializer_class inheriting BaseMeasurementSerializer does NOT raise."""
        from fairdm.api.serializers import BaseMeasurementSerializer
        from fairdm.api.viewsets import generate_viewset
        from fairdm.registry.config import ModelConfiguration
        from fairdm_demo.models import ExampleMeasurement

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


# ---------------------------------------------------------------------------
# Integration: endpoint field exposure via API response
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSerializerFieldsInAPIResponse:
    """Verify that the serializer fields actually appear in API responses."""

    def test_project_list_exposes_expected_fields(self, api_client):
        """Project list endpoint exposes uuid, name, status, visibility, added, modified."""
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
        """Dataset list endpoint exposes uuid, name, visibility."""
        from django.urls import reverse

        from fairdm.factories import DatasetFactory
        from fairdm.utils.choices import Visibility

        DatasetFactory(visibility=Visibility.PUBLIC)
        resp = api_client.get(reverse("api:dataset-list"))
        assert resp.status_code == 200
        result = resp.json()["results"][0]
        for field in ("uuid", "name", "visibility"):
            assert field in result, f"Expected '{field}' in dataset response"
