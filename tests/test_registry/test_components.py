"""Tests for the component accessor contract on ModelConfiguration.

Covers the three tiers of customisation and the rules that make them dependable:
a field list is enough, a supplied class replaces one component only, an
overridden accessor is what every caller receives, and nothing is cached.
"""

import pytest
from django.db import models
from django.forms import ModelForm
from django_filters import FilterSet
from django_tables2 import Table

from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.registry.config import COMPONENTS, ModelConfiguration, _component_base

ACCESSORS = [
    "get_form_class",
    "get_table_class",
    "get_filterset_class",
    "get_serializer_class",
    "get_resource_class",
    "get_admin_class",
]


@pytest.fixture
def rock_sample():
    class RockSample(Sample):
        rock_type = models.CharField(max_length=100)
        depth = models.FloatField(null=True, blank=True)

        class Meta:
            app_label = "test_app"

    return RockSample


class TestComponentTable:
    """One table describes every component, so nothing is written out six times."""

    def test_every_accessor_has_a_component_entry(self):
        assert len(COMPONENTS) == 6
        for name, spec in COMPONENTS.items():
            assert f"get_{name}_class" in ACCESSORS, name
            assert spec.fields_attr
            assert spec.class_attr
            assert _component_base(name) is not None

    def test_component_names_match_their_configuration_attributes(self):
        for name, spec in COMPONENTS.items():
            assert hasattr(ModelConfiguration, spec.fields_attr), spec.fields_attr
            assert hasattr(ModelConfiguration, spec.class_attr), spec.class_attr


class TestPlainClassConfiguration:
    """The configuration is a declaration, read from class attributes."""

    def test_subclass_class_attributes_are_honoured(self, rock_sample):
        class RockConfig(ModelConfiguration):
            model = rock_sample
            fields = ["rock_type"]

        config = RockConfig()
        assert config.model is rock_sample
        assert config.fields == ["rock_type"]

    def test_keyword_construction_still_works(self, rock_sample):
        config = ModelConfiguration(model=rock_sample, fields=["rock_type"])
        assert config.fields == ["rock_type"]

    def test_single_positional_construction_still_works(self, rock_sample):
        config = ModelConfiguration(rock_sample)
        assert config.model is rock_sample

    def test_instances_do_not_share_mutable_class_defaults(self, rock_sample):
        a = ModelConfiguration(model=rock_sample)
        b = ModelConfiguration(model=rock_sample)
        a.fields.append("rock_type")
        assert b.fields == []
        assert ModelConfiguration.fields == []


class TestFieldResolutionInOnePlace:
    """Resolution order is component-specific, then shared, then defaults."""

    def test_component_specific_list_wins(self, rock_sample):
        config = ModelConfiguration(
            model=rock_sample, fields=["rock_type"], table_fields=["depth"]
        )
        assert config.resolve_fields("table") == ["depth"]
        assert config.resolve_fields("form") == ["rock_type"]

    def test_shared_list_is_the_fallback(self, rock_sample):
        config = ModelConfiguration(model=rock_sample, fields=["rock_type"])
        for name in COMPONENTS:
            assert config.resolve_fields(name) == ["rock_type"]

    def test_defaults_are_the_final_fallback(self, rock_sample):
        config = ModelConfiguration(model=rock_sample)
        resolved = config.resolve_fields("form")
        assert "rock_type" in resolved
        assert "id" not in resolved

    def test_grouping_tuples_are_flattened(self, rock_sample):
        config = ModelConfiguration(model=rock_sample, fields=[("rock_type", "depth")])
        assert config.resolve_fields("form") == ["rock_type", "depth"]


class TestAccessorsGenerate:
    """A field list alone yields every component."""

    def test_each_accessor_returns_a_class(self, rock_sample):
        config = ModelConfiguration(model=rock_sample, fields=["rock_type"])
        for accessor in ACCESSORS:
            cls = getattr(config, accessor)()
            assert isinstance(cls, type), accessor

    def test_form_and_table_cover_the_declared_fields(self, rock_sample):
        config = ModelConfiguration(model=rock_sample, fields=["rock_type"])
        assert issubclass(config.get_form_class(), ModelForm)
        assert "rock_type" in config.get_form_class().base_fields
        assert issubclass(config.get_table_class(), Table)
        assert "rock_type" in config.get_table_class().base_columns

    def test_filterset_covers_the_declared_fields(self, rock_sample):
        config = ModelConfiguration(model=rock_sample, fields=["rock_type"])
        filterset = config.get_filterset_class()
        assert issubclass(filterset, FilterSet)
        assert "rock_type" in filterset.base_filters


class TestNothingIsCached:
    """FR-014: each call builds the class again."""

    @pytest.mark.parametrize("accessor", ACCESSORS)
    def test_two_calls_return_distinct_classes(self, rock_sample, accessor):
        config = ModelConfiguration(model=rock_sample, fields=["rock_type"])
        first = getattr(config, accessor)()
        second = getattr(config, accessor)()
        assert first is not second, accessor

    def test_no_public_attribute_returns_a_component_class(self, rock_sample):
        config = ModelConfiguration(model=rock_sample, fields=["rock_type"])
        for name in COMPONENTS:
            assert not hasattr(config, name), (
                f"{name} is reachable as an attribute, which bypasses "
                f"get_{name}_class() and any override of it"
            )

    def test_clear_cache_is_gone(self, rock_sample):
        config = ModelConfiguration(model=rock_sample, fields=["rock_type"])
        assert not hasattr(config, "clear_cache")


class TestAccessorOverride:
    """FR-019 and FR-020: an override is what every caller receives."""

    def test_override_is_returned(self, rock_sample):
        class MyForm(ModelForm):
            class Meta:
                model = rock_sample
                fields = ["rock_type"]

        class RockConfig(ModelConfiguration):
            model = rock_sample
            fields = ["rock_type"]

            def get_form_class(self):
                return MyForm

        config = RockConfig()
        assert config.get_form_class() is MyForm

    def test_override_leaves_the_other_components_generated(self, rock_sample):
        class MyForm(ModelForm):
            class Meta:
                model = rock_sample
                fields = ["rock_type"]

        class RockConfig(ModelConfiguration):
            model = rock_sample
            fields = ["rock_type"]

            def get_form_class(self):
                return MyForm

        config = RockConfig()
        assert issubclass(config.get_table_class(), Table)
        assert issubclass(config.get_filterset_class(), FilterSet)

    def test_override_runs_on_every_call(self, rock_sample):
        calls = []

        class RockConfig(ModelConfiguration):
            model = rock_sample
            fields = ["rock_type"]

            def get_table_class(self):
                calls.append(1)
                return Table

        config = RockConfig()
        config.get_table_class()
        config.get_table_class()
        assert len(calls) == 2


class TestGeneratedFieldsAreExactlyDeclared:
    """SC-001 and SC-002, decision D15: nothing is added to the declared list."""

    def test_serializer_does_not_inject_id(self, rock_sample):
        config = ModelConfiguration(model=rock_sample, fields=["rock_type"])
        serializer = config.get_serializer_class()
        assert "id" not in serializer.Meta.fields

    def test_resource_does_not_inject_id(self, rock_sample):
        config = ModelConfiguration(model=rock_sample, fields=["rock_type"])
        resource = config.get_resource_class()
        assert "id" not in resource.Meta.fields


class TestGenerationTouchesNoDatabase:
    """FR-015: registration happens before the database is reachable.

    No `db` fixture is requested anywhere in this module, so pytest-django blocks
    database access outright. A generator that opened a connection would raise
    rather than merely be slow, which makes this a deterministic guard rather than
    a timing assertion.
    """

    def test_configuration_and_every_component_build_with_the_database_blocked(
        self, rock_sample
    ):
        config = ModelConfiguration(model=rock_sample, fields=["rock_type"])
        for accessor in ACCESSORS:
            assert isinstance(getattr(config, accessor)(), type), accessor


class TestConcreteModelsOnly:
    """FR-002: registration refuses anything but a concrete subclass.

    The check belongs to the registry rather than the configuration, because a
    configuration is a description and the registry is what decides which models it
    will accept. Building a configuration for an unregistrable model stays legal, so
    that other parts of the framework can use one to generate a component.
    """

    def test_base_sample_is_refused(self, clean_registry):
        from fairdm.registry.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="polymorphic base class"):
            clean_registry.register(Sample, ModelConfiguration(model=Sample))

    def test_base_measurement_is_refused(self, clean_registry):
        from fairdm.registry.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="polymorphic base class"):
            clean_registry.register(Measurement, ModelConfiguration(model=Measurement))

    def test_a_model_outside_both_hierarchies_is_refused(self, clean_registry):
        from django.db import models as dj_models

        from fairdm.registry.exceptions import ConfigurationError

        class NotASample(dj_models.Model):
            class Meta:
                app_label = "test_app"

        with pytest.raises(ConfigurationError, match="concrete subclass"):
            clean_registry.register(NotASample, ModelConfiguration(model=NotASample))


class TestFieldPathValidation:
    """FR-022: every segment of a related path resolves, not only the first."""

    def test_a_valid_related_path_is_accepted(self, rock_sample):
        config = ModelConfiguration(model=rock_sample, fields=["dataset__name"])
        assert "dataset__name" in config.fields

    def test_a_bad_final_segment_is_refused(self, rock_sample):
        from fairdm.registry.exceptions import FieldValidationError

        with pytest.raises(FieldValidationError, match="dataset__nonexistent"):
            ModelConfiguration(model=rock_sample, fields=["dataset__nonexistent"])

    def test_a_path_through_a_non_relation_is_refused(self, rock_sample):
        from fairdm.registry.exceptions import FieldValidationError

        with pytest.raises(FieldValidationError, match="not a relation"):
            ModelConfiguration(model=rock_sample, fields=["rock_type__nope"])


class TestValidationMessages:
    """FR-024: one sentence naming the model, the attribute, the value and a hint."""

    def test_the_message_reads_as_one_sentence(self, rock_sample):
        from fairdm.registry.exceptions import FieldValidationError

        with pytest.raises(FieldValidationError) as caught:
            ModelConfiguration(model=rock_sample, fields=["rock_typ"])

        message = str(caught.value)
        assert "rock_typ" in message
        assert "RockSample.fields" in message
        assert "Did you mean: rock_type?" in message
        # The old form nested the whole sentence inside a second one.
        assert message.count("Invalid field") == 1

    def test_the_attribute_that_declared_it_is_named(self, rock_sample):
        from fairdm.registry.exceptions import FieldValidationError

        with pytest.raises(FieldValidationError, match="RockSample.table_fields"):
            ModelConfiguration(model=rock_sample, table_fields=["nope"])


class TestUnregisteredModel:
    """FR-006: asking for an unregistered model's configuration raises."""

    def test_get_for_model_raises_and_names_the_model(
        self, clean_registry, rock_sample
    ):
        from fairdm.registry.exceptions import NotRegisteredError

        with pytest.raises(NotRegisteredError, match="RockSample"):
            clean_registry.get_for_model(rock_sample)

    def test_is_registered_answers_without_raising(self, clean_registry, rock_sample):
        assert clean_registry.is_registered(rock_sample) is False
