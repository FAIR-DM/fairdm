"""Tests for fairdm/registry/registry.py.

What a configuration builds for a model (forms, tables, filters, serializers, admin) is tested in
test_config.py. These tests cover registration, lookup and the partition into samples and
measurements.
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import models
from django.test import Client
from django_tables2 import Table

import fairdm
from demo.models import CustomSample, RockSample, WaterSample
from fairdm.core.models import Measurement, Sample
from fairdm.registry import registry
from fairdm.registry.config import ModelConfiguration
from fairdm.registry.exceptions import ConfigurationError, DuplicateRegistrationError
from tests.registry_models.models import ConcreteSample

User = get_user_model()


class TestSample(Sample):
    test_field = models.CharField(max_length=100)

    class Meta:
        app_label = "test_app"


class TestMeasurement(Measurement):
    value = models.FloatField()

    class Meta:
        app_label = "test_app"


class TestRegistration:
    def test_register_stores_the_configuration_it_was_given(self, clean_registry):
        config = ModelConfiguration(model=TestSample, fields=["test_field"])
        clean_registry.register(TestSample, config)

        assert clean_registry.get_for_model(TestSample) is config
        assert clean_registry.is_registered(TestSample) is True

    def test_the_decorator_registers_the_model(self, clean_registry):
        @fairdm.register
        class TestSampleConfig(ModelConfiguration):
            model = TestSample
            fields = ["test_field"]

        assert clean_registry.get_for_model(TestSample).fields == ["test_field"]

    def test_register_without_a_configuration_builds_a_default_one(
        self, clean_registry
    ):
        clean_registry.register(TestSample, None)

        assert clean_registry.get_for_model(TestSample).model is TestSample

    def test_registering_a_model_twice_raises(self, clean_registry):
        config = ModelConfiguration(model=TestSample, fields=["test_field"])
        clean_registry.register(TestSample, config)

        with pytest.raises(DuplicateRegistrationError):
            clean_registry.register(TestSample, config)

    def test_a_model_that_is_neither_sample_nor_measurement_is_refused(
        self, clean_registry
    ):
        class NotSampleModel(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        # Eligibility is the registry's decision, so building the configuration is legal and
        # registering it is what fails.
        config = ModelConfiguration(model=NotSampleModel, fields=["name"])
        with pytest.raises(ConfigurationError):
            clean_registry.register(NotSampleModel, config)


class TestLookup:
    def test_get_for_model_distinguishes_models(self, clean_registry):
        sample_config = ModelConfiguration(model=TestSample, fields=["test_field"])
        measurement_config = ModelConfiguration(model=TestMeasurement, fields=["value"])
        clean_registry.register(TestSample, sample_config)
        clean_registry.register(TestMeasurement, measurement_config)

        assert clean_registry.get_for_model(TestSample) is sample_config
        assert clean_registry.get_for_model(TestMeasurement) is measurement_config

    def test_an_unregistered_class_raises_keyerror(self, clean_registry):
        with pytest.raises(KeyError):
            clean_registry.get_for_model(TestSample)

    @pytest.mark.parametrize(
        ("label", "error"),
        [("invalid_app.model", LookupError), ("invalid_format", ValueError)],
    )
    def test_a_bad_string_label_raises(self, clean_registry, label, error):
        with pytest.raises(error):
            clean_registry.get_for_model(label)

    def test_is_registered_is_false_for_unregistered_and_malformed_labels(
        self, clean_registry
    ):
        assert clean_registry.is_registered(TestSample) is False
        assert clean_registry.is_registered("invalid_app.unregistered") is False
        assert clean_registry.is_registered("invalid_format") is False

    def test_get_all_configs_lists_every_configuration(self, clean_registry):
        assert clean_registry.get_all_configs() == []

        sample_config = ModelConfiguration(model=TestSample, fields=["test_field"])
        measurement_config = ModelConfiguration(model=TestMeasurement, fields=["value"])
        clean_registry.register(TestSample, sample_config)
        clean_registry.register(TestMeasurement, measurement_config)

        assert set(clean_registry.get_all_configs()) == {
            sample_config,
            measurement_config,
        }


class TestPartition:
    def test_samples_measurements_and_models_split_by_base_class(self, clean_registry):
        assert clean_registry.samples == []
        assert clean_registry.measurements == []

        clean_registry.register(
            TestSample, ModelConfiguration(model=TestSample, fields=["test_field"])
        )
        clean_registry.register(
            TestMeasurement, ModelConfiguration(model=TestMeasurement, fields=["value"])
        )

        assert clean_registry.samples == [TestSample]
        assert clean_registry.measurements == [TestMeasurement]
        assert set(clean_registry.models) == {TestSample, TestMeasurement}


class TestComponentAccessors:
    def test_components_are_rebuilt_on_every_call(self, clean_registry):
        clean_registry.register(TestSample)
        config = clean_registry.get_for_model(TestSample)

        # Nothing is cached, so an override of the accessor is honoured on every call and not
        # only the first.
        first = config.get_form_class()
        second = config.get_form_class()

        assert first is not second
        assert first.base_fields.keys() == second.base_fields.keys()

    def test_a_model_registered_with_no_field_lists_still_builds_its_components(
        self, clean_registry, db
    ):
        clean_registry.register(
            ConcreteSample,
            ModelConfiguration(model=ConcreteSample, display_name="Minimal"),
        )
        config = clean_registry.get_for_model(ConcreteSample)

        assert config.get_form_class()._meta.model is ConcreteSample
        assert config.get_table_class()._meta.model is ConcreteSample
        assert config.get_filterset_class()._meta.model is ConcreteSample
        assert config.get_admin_class().model is ConcreteSample


@pytest.mark.django_db
class TestDemoRegistrations:
    def test_the_demo_models_are_registered_as_samples(self):
        assert {RockSample, WaterSample, CustomSample} <= set(registry.samples)
        assert RockSample not in registry.measurements

    def test_generated_form_and_table_carry_the_model_fields(self):
        config = registry.get_for_model(RockSample)

        form = config.get_form_class()()
        table = config.get_table_class()([])

        assert {"name", "rock_type", "collection_date"} <= set(form.fields)
        assert "name" in table.columns

    def test_custom_classes_are_preserved(self):
        from demo.filters import CustomSampleFilter
        from demo.tables import CustomSampleTable

        config = registry.get_for_model(CustomSample)

        # CustomSample names its own filterset and table, so the resolved components are those
        # classes and not generated ones.
        assert config.get_filterset_class() is CustomSampleFilter
        assert config.get_table_class() is CustomSampleTable
        assert issubclass(config.get_table_class(), Table)

    def test_every_registered_model_has_an_admin_add_page_that_loads(self):
        user = User.objects.create_superuser(
            email="admin@test.com", password="testpass123"
        )
        client = Client()
        client.force_login(user)

        failed = []
        for config in registry.get_all_configs():
            meta = config.model._meta
            url = f"/admin/{meta.app_label}/{meta.model_name}/add/"
            try:
                status = client.get(url).status_code
            except Exception as error:
                failed.append(f"{url}: {error}")
                continue
            if status != 200:
                failed.append(f"{url}: status {status}")

        assert not failed, "These admin add pages failed to load:\n" + "\n".join(failed)
