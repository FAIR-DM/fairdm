"""Tests for Sample registry configuration (BaseSampleConfiguration)."""

import pytest

from fairdm.registry import registry


@pytest.mark.django_db
class TestSampleRegistryGeneration:
    def test_generated_form_carries_the_specimen_types_own_fields(self, clean_registry):
        from demo.models import RockSample

        config = registry.get_for_model(RockSample)
        form = config.get_form_class()()

        assert set(form.fields) == {
            "name",
            "rock_type",
            "collection_date",
            "weight_grams",
            "hardness_mohs",
            "mineral_content",
        }

    def test_generated_filterset_carries_the_specimen_types_own_fields(
        self, clean_registry
    ):
        from demo.models import RockSample

        config = registry.get_for_model(RockSample)
        filterset = config.get_filterset_class()()

        assert "rock_type" in filterset.filters
        assert "mineral_content" in filterset.filters
        assert "collection_date" in filterset.filters

    def test_generated_table_carries_the_specimen_types_own_fields(
        self, clean_registry
    ):
        from demo.models import RockSample

        config = registry.get_for_model(RockSample)
        table = config.get_table_class()(RockSample.objects.none())

        column_names = set(table.columns.names())
        assert "name" in column_names
        assert "rock_type" in column_names

    def test_generated_admin_lists_the_specimen_types_own_fields(self, clean_registry):
        from demo.models import RockSample
        from fairdm.core.sample.admin import SampleChildAdmin

        config = registry.get_for_model(RockSample)
        admin_class = config.get_admin_class()

        assert issubclass(admin_class, SampleChildAdmin)
        assert "name" in admin_class.list_display


class TestBaseSampleConfiguration:
    def test_omitting_fields_falls_back_to_the_bases_default_fields(self):
        from demo.models import RockSample
        from fairdm.core.sample.config import BaseSampleConfiguration

        class MinimalRockConfig(BaseSampleConfiguration):
            model = RockSample

        config = MinimalRockConfig()

        assert config.resolve_fields("form") == BaseSampleConfiguration.fields
        assert config.resolve_fields("table") == BaseSampleConfiguration.fields
        assert config.resolve_fields("filterset") == BaseSampleConfiguration.fields

    def test_declaring_fields_overrides_the_bases_default_for_every_component(self):
        from demo.models import RockSample
        from fairdm.core.sample.config import BaseSampleConfiguration

        class RockOnlyConfig(BaseSampleConfiguration):
            model = RockSample
            fields = ["name", "rock_type"]

        config = RockOnlyConfig()

        assert config.resolve_fields("form") == ["name", "rock_type"]
        assert config.resolve_fields("form") != BaseSampleConfiguration.fields


@pytest.mark.django_db
class TestRegistryUsesTheMixins:
    def _config_for(self, model, fields):
        from fairdm.core.sample.config import BaseSampleConfiguration

        config_class = type(
            "_Config", (BaseSampleConfiguration,), {"model": model, "fields": fields}
        )
        return config_class()

    def test_generated_form_uses_the_sample_form_mixins_dataset_widget(self):
        from django_addanother.widgets import AddAnotherWidgetWrapper

        from demo.models import RockSample

        config = self._config_for(RockSample, ["name", "dataset"])
        form = config.get_form_class()()

        assert isinstance(form.fields["dataset"].widget, AddAnotherWidgetWrapper)

    def test_generated_filterset_carries_the_sample_filter_mixins_image_filter(self):
        from demo.models import RockSample

        config = self._config_for(RockSample, ["name", "rock_type"])
        filterset_class = config.get_filterset_class()

        assert "image" in filterset_class.base_filters
