"""
Tests for Sample registry configuration (BaseSampleConfiguration).

Tests verify that the registry auto-generates forms, filters, tables, and
admin configurations for custom sample types via BaseSampleConfiguration, and
that a specimen type configuration inheriting the base receives its defaults
for whatever it leaves unset.
"""

import pytest

from fairdm.registry import registry


@pytest.mark.django_db
class TestSampleRegistryGeneration:
    """T026 - a registered specimen type receives a generated form, filter
    set, table and administrative entry, each carrying that type's own
    fields, asserted by naming the fields."""

    def test_generated_form_carries_the_specimen_types_own_fields(self, clean_registry):
        """RockSampleConfig declares `fields` naming rock-specific columns
        (rock_type, collection_date, weight_grams, hardness_mohs,
        mineral_content) alongside the shared `name`. The generated form must
        carry exactly those, not merely be non-`None`."""
        from fairdm_demo.models import RockSample

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
        """The filter set built for the same fields must expose filters for
        the rock-specific columns by name."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)
        filterset = config.get_filterset_class()()

        assert "rock_type" in filterset.filters
        assert "mineral_content" in filterset.filters
        assert "collection_date" in filterset.filters

    def test_generated_table_carries_the_specimen_types_own_fields(self, clean_registry):
        """The table built for the same fields must expose a column for at
        least one rock-specific field, by name, not merely have some
        non-zero number of columns."""
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)
        table = config.get_table_class()(RockSample.objects.none())

        column_names = set(table.columns.names())
        assert "name" in column_names
        assert "rock_type" in column_names

    def test_generated_admin_lists_the_specimen_types_own_fields(self, clean_registry):
        """The admin entry's `list_display` must name a field the type
        itself contributes, not just the base sample fields."""
        from fairdm.core.sample.admin import SampleChildAdmin
        from fairdm_demo.models import RockSample

        config = registry.get_for_model(RockSample)
        admin_class = config.get_admin_class()

        assert issubclass(admin_class, SampleChildAdmin)
        assert "name" in admin_class.list_display


class TestBaseSampleConfiguration:
    """T027 - a specimen type configuration inheriting BaseSampleConfiguration
    receives the base's defaults for a component setting it omits."""

    def test_omitting_fields_falls_back_to_the_bases_default_fields(self):
        """A subclass naming only `model` gets `BaseSampleConfiguration.fields`
        for every component, since it names no field list of its own."""
        from fairdm.core.sample.config import BaseSampleConfiguration
        from fairdm_demo.models import RockSample

        class MinimalRockConfig(BaseSampleConfiguration):
            model = RockSample

        config = MinimalRockConfig()

        assert config.resolve_fields("form") == BaseSampleConfiguration.fields
        assert config.resolve_fields("table") == BaseSampleConfiguration.fields
        assert config.resolve_fields("filterset") == BaseSampleConfiguration.fields

    def test_declaring_fields_overrides_the_bases_default_for_every_component(self):
        """A subclass that does declare `fields` gets its own list instead -
        the base's default never wins over a component the subclass named."""
        from fairdm.core.sample.config import BaseSampleConfiguration
        from fairdm_demo.models import RockSample

        class RockOnlyConfig(BaseSampleConfiguration):
            model = RockSample
            fields = ["name", "rock_type"]

        config = RockOnlyConfig()

        assert config.resolve_fields("form") == ["name", "rock_type"]
        assert config.resolve_fields("form") != BaseSampleConfiguration.fields


@pytest.mark.django_db
class TestRegistryUsesTheMixins:
    """T070 - the form and filter set the registry generates for a specimen
    type supplying neither carry the mixins' behaviour rather than plain
    defaults.

    Built from a bare `BaseSampleConfiguration` subclass rather than one of
    the registered demo configs: none of those name `dataset` in their own
    `fields`, so a registered config cannot show the mixin's dataset widget
    wiring. `get_form_class()`/`get_filterset_class()` need no registration to
    call - they build straight from the configuration instance.
    """

    def _config_for(self, model, fields):
        from fairdm.core.sample.config import BaseSampleConfiguration

        config_class = type(
            "_Config", (BaseSampleConfiguration,), {"model": model, "fields": fields}
        )
        return config_class()

    def test_generated_form_uses_the_sample_form_mixins_dataset_widget(self):
        """A specimen type config naming no `form_class` still gets
        `SampleFormMixin`'s wrapped Select2 widget for `dataset` - a plain
        `ModelForm` never sets one."""
        from django_addanother.widgets import AddAnotherWidgetWrapper
        from fairdm_demo.models import RockSample

        config = self._config_for(RockSample, ["name", "dataset"])
        form = config.get_form_class()()

        assert isinstance(form.fields["dataset"].widget, AddAnotherWidgetWrapper)

    def test_generated_filterset_carries_the_sample_filter_mixins_image_filter(self):
        """A specimen type config naming no `filterset_class` still gets
        `SampleFilterMixin`'s declared `image` filter - a plain `FilterSet`
        base would never have it, because it names no model field."""
        from fairdm_demo.models import RockSample

        config = self._config_for(RockSample, ["name", "rock_type"])
        filterset_class = config.get_filterset_class()

        assert "image" in filterset_class.base_filters
