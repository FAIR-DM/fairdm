"""Tests for the system check on registered types (``fairdm/api/checks.py``)."""

import pytest

from demo.models import RockSample, XRFMeasurement
from fairdm.registry import ModelConfiguration, registry


@pytest.fixture
def register_for_the_test(monkeypatch):
    """Return a function replacing a registered type's configuration for one test."""

    def register_for_the_test(model, **configuration):
        config = ModelConfiguration(model=model, **configuration)
        monkeypatch.setitem(registry._registry, model, config)

    return register_for_the_test


@pytest.mark.django_db
class TestRegistrationCheck:
    @pytest.fixture
    def check(self):
        from fairdm.api.checks import check_registered_types

        return check_registered_types

    def test_the_shipped_registrations_produce_no_error(self, check):
        assert check(None) == []

    @pytest.mark.parametrize(
        ("model", "serializer_fields", "missing"),
        [
            (RockSample, ["collection_date"], "rock_type"),
            (XRFMeasurement, ["element"], "concentration_ppm"),
        ],
        ids=["sample", "measurement"],
    )
    def test_a_required_field_left_out_of_the_api_fields_is_an_error(
        self, check, register_for_the_test, model, serializer_fields, missing
    ):
        register_for_the_test(model, serializer_fields=serializer_fields)

        errors = check(None)

        assert len(errors) == 1
        assert errors[0].id == "fairdm.E600"
        assert errors[0].obj is model
        assert missing in errors[0].msg

    def test_every_missing_field_is_named(self, check, register_for_the_test):
        register_for_the_test(RockSample, serializer_fields=["weight_grams"])

        errors = check(None)

        assert [e.id for e in errors] == ["fairdm.E600", "fairdm.E600"]
        for name in ("rock_type", "collection_date"):
            assert any(name in error.msg for error in errors)

    def test_a_serializer_of_the_developers_own_is_held_to_the_same_rule(
        self, check, register_for_the_test
    ):
        from fairdm.api.serializers import BaseSampleSerializer

        class WithoutTheName(BaseSampleSerializer):
            class Meta(BaseSampleSerializer.Meta):
                model = RockSample
                fields = ["uuid", "dataset", "rock_type", "collection_date"]

        register_for_the_test(RockSample, serializer_class=WithoutTheName)

        errors = check(None)

        assert [e.id for e in errors] == ["fairdm.E600"]
        assert "name" in errors[0].msg

    def test_a_required_field_the_api_only_reads_is_an_error(
        self, check, register_for_the_test
    ):
        from rest_framework import serializers

        from fairdm.api.serializers import BaseSampleSerializer

        class ReadsTheRockType(BaseSampleSerializer):
            rock_type = serializers.CharField(read_only=True)

            class Meta(BaseSampleSerializer.Meta):
                model = RockSample
                fields = [
                    *BaseSampleSerializer.Meta.fields,
                    "rock_type",
                    "collection_date",
                ]

        register_for_the_test(RockSample, serializer_class=ReadsTheRockType)

        errors = check(None)

        assert [e.id for e in errors] == ["fairdm.E600"]
        assert "rock_type" in errors[0].msg

    def test_the_check_is_registered_with_django(self):
        from django.core.checks.registry import registry as checks
        from fairdm.api.checks import check_registered_types

        assert check_registered_types in checks.registered_checks
