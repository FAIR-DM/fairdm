"""Tests for fairdm/registry/config.py."""

import pytest
from django.contrib import admin
from django.db import models
from django.forms import ModelForm
from django_filters import FilterSet
from django_tables2 import Table

from demo.models import RockSample
from fairdm.core.models import Measurement, Sample
from fairdm.core.sample.admin import SampleChildAdmin
from fairdm.registry import registry
from fairdm.registry.config import (
    COMPONENTS,
    Authority,
    Citation,
    ModelConfiguration,
    ModelMetadata,
    _component_base,
)
from fairdm.registry.exceptions import (
    ConfigurationError,
    DuplicateRegistrationError,
    FieldValidationError,
    NotRegisteredError,
)
from tests.registry_models.models import ConcreteMeasurement, ConcreteSample


class TestGetDefaultFields:
    def test_get_default_fields_basic(self):
        class TestModel(Sample):
            rock_type = models.CharField(max_length=100)
            mineral_content = models.TextField()
            sample_count = models.IntegerField()

            class Meta:
                app_label = "test_app"

        defaults = ModelConfiguration.get_default_fields(TestModel)

        assert "rock_type" in defaults
        assert "mineral_content" in defaults
        assert "sample_count" in defaults

        assert "id" not in defaults

    def test_get_default_fields_excludes_polymorphic(self):
        class TestModel(Sample):
            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        defaults = ModelConfiguration.get_default_fields(TestModel)

        assert "polymorphic_ctype" not in defaults

        assert "rock_type" in defaults

    def test_get_default_fields_excludes_ptr_fields(self):
        class ParentSample(Sample):
            """Parent Sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        class ChildSample(ParentSample):
            """Child Sample inheriting from ParentSample."""

            mineral_content = models.TextField()

            class Meta:
                app_label = "test_app"

        defaults = ModelConfiguration.get_default_fields(ChildSample)

        assert "parentsample_ptr" not in defaults

        assert "rock_type" in defaults
        assert "mineral_content" in defaults

    def test_get_default_fields_excludes_auto_now(self):
        class TestModel(Sample):
            rock_type = models.CharField(max_length=100)
            sample_created_at = models.DateTimeField(auto_now_add=True)
            sample_updated_at = models.DateTimeField(auto_now=True)

            class Meta:
                app_label = "test_app"

        defaults = ModelConfiguration.get_default_fields(TestModel)

        assert "sample_created_at" not in defaults
        assert "sample_updated_at" not in defaults

        assert "rock_type" in defaults

    def test_get_default_fields_excludes_non_editable(self):
        class TestModel(Sample):
            rock_type = models.CharField(max_length=100)
            readonly_field = models.CharField(max_length=100, editable=False)

            class Meta:
                app_label = "test_app"

        defaults = ModelConfiguration.get_default_fields(TestModel)

        assert "readonly_field" not in defaults

        assert "rock_type" in defaults

    def test_get_default_fields_comprehensive_exclusions(self):
        class ParentModel(Sample):
            """Parent Sample model."""

            parent_rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        class TestModel(ParentModel):
            rock_name = models.CharField(max_length=100)
            mineral_description = models.TextField()
            sample_count = models.IntegerField()
            readonly_code = models.CharField(max_length=100, editable=False)
            sample_created_at = models.DateTimeField(auto_now_add=True)
            sample_updated_at = models.DateTimeField(auto_now=True)

            class Meta:
                app_label = "test_app"

        defaults = ModelConfiguration.get_default_fields(TestModel)

        assert "rock_name" in defaults
        assert "mineral_description" in defaults
        assert "sample_count" in defaults
        assert "parent_rock_type" in defaults

        assert "id" not in defaults
        assert "polymorphic_ctype" not in defaults
        assert "parentmodel_ptr" not in defaults
        assert "readonly_code" not in defaults
        assert "sample_created_at" not in defaults
        assert "sample_updated_at" not in defaults


class TestModelMetadata:
    def test_model_metadata_creation_empty(self):
        metadata = ModelMetadata()

        assert metadata.description == ""
        assert metadata.authority is None
        assert metadata.keywords == []
        assert metadata.repository_url == ""
        assert metadata.citation is None
        assert metadata.maintainer == ""
        assert metadata.maintainer_email == ""

    def test_model_metadata_with_all_fields(self):
        authority = Authority(
            name="Test Authority", short_name="TA", website="https://example.com"
        )
        citation = Citation(text="Test Citation", doi="10.1234/test")

        metadata = ModelMetadata(
            description="A comprehensive test metadata",
            authority=authority,
            keywords=["test", "metadata", "comprehensive"],
            repository_url="https://github.com/test/repo",
            citation=citation,
            maintainer="Test Maintainer",
            maintainer_email="maintainer@example.com",
        )

        assert metadata.description == "A comprehensive test metadata"
        assert metadata.authority.name == "Test Authority"
        assert metadata.keywords == ["test", "metadata", "comprehensive"]
        assert metadata.repository_url == "https://github.com/test/repo"
        assert metadata.citation.doi == "10.1234/test"
        assert metadata.maintainer == "Test Maintainer"
        assert metadata.maintainer_email == "maintainer@example.com"


class TestAuthority:
    def test_authority_minimal(self):
        authority = Authority(name="Test Authority")

        assert authority.name == "Test Authority"
        assert authority.short_name == ""
        assert authority.website == ""

    def test_authority_complete(self):
        authority = Authority(
            name="Test Authority", short_name="TA", website="https://example.com"
        )

        assert authority.name == "Test Authority"
        assert authority.short_name == "TA"
        assert authority.website == "https://example.com"

    def test_authority_frozen(self):
        authority = Authority(name="Test")

        with pytest.raises(AttributeError):
            authority.name = "Changed"


class TestCitation:
    def test_citation_empty(self):
        citation = Citation()

        assert citation.text == ""
        assert citation.doi == ""

    def test_citation_with_text_only(self):
        citation = Citation(text="Test Citation Text")

        assert citation.text == "Test Citation Text"
        assert citation.doi == ""

    def test_citation_with_doi_only(self):
        citation = Citation(doi="10.1234/test.doi")

        assert citation.text == ""
        assert citation.doi == "10.1234/test.doi"

    def test_citation_complete(self):
        citation = Citation(text="Complete Citation", doi="10.1234/complete")

        assert citation.text == "Complete Citation"
        assert citation.doi == "10.1234/complete"

    def test_citation_frozen(self):
        citation = Citation(text="Test")

        with pytest.raises(AttributeError):
            citation.text = "Changed"


class TestModelConfiguration:
    def test_model_configuration_with_model(self, db):
        config = ModelConfiguration(model=ConcreteSample)

        assert config.model == ConcreteSample
        assert isinstance(config.metadata, ModelMetadata)

    def test_model_configuration_field_attributes(self, db):
        config = ModelConfiguration(
            model=ConcreteSample,
            table_fields=["name", "status"],
            form_fields=["name", "status"],
            filterset_fields=["status"],
        )

        assert config.table_fields == ["name", "status"]
        assert config.form_fields == ["name", "status"]
        assert config.filterset_fields == ["status"]


class TestAutoGeneratedComponents:
    def test_filterset_property_auto_generated(self, clean_registry, db):
        from django_filters import FilterSet

        config = ModelConfiguration(
            model=ConcreteSample,
            filterset_fields=["name", "status"],
        )
        registry.register(ConcreteSample, config=config)

        filterset_class = config.get_filterset_class()
        assert issubclass(filterset_class, FilterSet)

    def test_form_property_auto_generated(self, clean_registry, db):
        from django.forms import ModelForm

        config = ModelConfiguration(
            model=ConcreteSample,
            form_fields=["name", "status"],
        )
        registry.register(ConcreteSample, config=config)

        form_class = config.get_form_class()
        assert issubclass(form_class, ModelForm)

    def test_table_property_auto_generated(self, clean_registry, db):
        from django_tables2 import Table

        config = ModelConfiguration(
            model=ConcreteSample,
            table_fields=["name", "status"],
        )
        registry.register(ConcreteSample, config=config)

        table_class = config.get_table_class()
        assert issubclass(table_class, Table)

    def test_resource_property_auto_generated(self, clean_registry, db):
        from import_export.resources import ModelResource

        config = ModelConfiguration(
            model=ConcreteSample,
            resource_fields=["name", "status"],
        )
        registry.register(ConcreteSample, config=config)

        resource_class = config.get_resource_class()
        assert issubclass(resource_class, ModelResource)

    def test_admin_property_auto_generated(self, clean_registry, db):
        from django.contrib.admin import ModelAdmin

        config = ModelConfiguration(
            model=ConcreteSample,
            admin_list_display=["name", "status"],
        )
        registry.register(ConcreteSample, config=config)

        admin_class = config.get_admin_class()
        assert issubclass(admin_class, ModelAdmin)


class TestComponentOverrides:
    def test_custom_form_class_override(self, clean_registry, db):
        from django import forms

        class CustomSampleForm(forms.ModelForm):
            class Meta:
                model = ConcreteSample
                fields = ["name"]

        config = ModelConfiguration(
            model=ConcreteSample,
            form_class=CustomSampleForm,
        )
        registry.register(ConcreteSample, config=config)

        assert config.form_class == CustomSampleForm
        assert config.get_form_class() == CustomSampleForm

    def test_custom_filterset_class_override(self, clean_registry, db):
        from django_filters import CharFilter, FilterSet

        class CustomSampleFilter(FilterSet):
            name = CharFilter(lookup_expr="icontains")

            class Meta:
                model = ConcreteSample
                fields = ["name"]

        config = ModelConfiguration(
            model=ConcreteSample,
            filterset_class=CustomSampleFilter,
        )
        registry.register(ConcreteSample, config=config)

        assert config.filterset_class == CustomSampleFilter
        assert config.get_filterset_class() == CustomSampleFilter

    def test_custom_table_class_override(self, clean_registry, db):
        import django_tables2 as tables

        class CustomSampleTable(tables.Table):
            name = tables.Column()

            class Meta:
                model = ConcreteSample
                fields = ["name"]

        config = ModelConfiguration(
            model=ConcreteSample,
            table_class=CustomSampleTable,
        )
        registry.register(ConcreteSample, config=config)

        assert config.table_class == CustomSampleTable
        assert config.get_table_class() == CustomSampleTable


class TestRegistryItemStructure:
    def test_registry_item_has_config(self, clean_registry, db):
        config = ModelConfiguration(
            model=ConcreteSample,
            display_name="Structure Test",
        )
        registry.register(ConcreteSample, config=config)

        assert ConcreteSample in registry._registry
        stored_config = registry.get_for_model(ConcreteSample)
        assert isinstance(stored_config, ModelConfiguration)
        assert stored_config.display_name == "Structure Test"


class TestRegistryEdgeCases:
    def test_register_with_config(self, clean_registry, db):
        config = ModelConfiguration(model=ConcreteSample)
        registry.register(ConcreteSample, config=config)

        assert ConcreteSample in registry._registry
        stored_config = registry.get_for_model(ConcreteSample)
        assert isinstance(stored_config, ModelConfiguration)
        assert stored_config.model == ConcreteSample

    def test_get_for_model_returns_config(self, clean_registry, db):
        config = ModelConfiguration(
            model=ConcreteSample,
            display_name="Test Config",
        )
        registry.register(ConcreteSample, config=config)

        retrieved_config = registry.get_for_model(ConcreteSample)
        assert retrieved_config.get_display_name() == "Test Config"

    def test_multiple_registrations_same_session(self, clean_registry, db):
        sample_config = ModelConfiguration(
            model=ConcreteSample,
            display_name="Sample Config",
        )
        measurement_config = ModelConfiguration(
            model=ConcreteMeasurement,
            display_name="Measurement Config",
        )

        registry.register(ConcreteSample, config=sample_config)
        registry.register(ConcreteMeasurement, config=measurement_config)

        assert ConcreteSample in registry._registry
        assert ConcreteMeasurement in registry._registry


class TestRegistryIntegration:
    def test_registry_stores_config(self, clean_registry, db):
        config = ModelConfiguration(
            model=ConcreteSample,
            display_name="Integration Test",
        )
        registry.register(ConcreteSample, config=config)

        assert ConcreteSample in registry._registry
        stored_config = registry.get_for_model(ConcreteSample)
        assert stored_config.get_display_name() == "Integration Test"


class TestAdminInheritanceValidation:
    def test_sample_with_wrong_admin_class_raises_error(self):
        class WrongAdmin(admin.ModelAdmin):
            """Wrong admin class - doesn't inherit from SampleChildAdmin."""

            pass

        with pytest.raises(ConfigurationError) as exc_info:
            ModelConfiguration(
                model=RockSample,
                admin_class=WrongAdmin,
                fields=["name", "rock_type"],
            )

        assert "RockSample" in str(exc_info.value)
        assert "WrongAdmin" in str(exc_info.value)

    def test_sample_with_correct_admin_class_passes(self):
        class CorrectAdmin(SampleChildAdmin):
            """Correct admin class - inherits from SampleChildAdmin."""

            base_model = RockSample
            show_in_index = True

        config = ModelConfiguration(
            model=RockSample,
            admin_class=CorrectAdmin,
            fields=["name", "rock_type"],
        )

        assert config.get_admin_class() == CorrectAdmin

    def test_sample_without_admin_class_passes(self):
        config = ModelConfiguration(
            model=RockSample,
            fields=["name", "rock_type"],
        )

        assert config.get_admin_class() is not None
        assert issubclass(config.get_admin_class(), admin.ModelAdmin)

    def test_autogenerated_sample_admin_inherits_from_child_admin(self):
        config = ModelConfiguration(
            model=RockSample,
            fields=["name", "rock_type"],
        )

        admin_class = config.get_admin_class()
        assert issubclass(admin_class, SampleChildAdmin), (
            f"Auto-generated admin for {RockSample.__name__} should inherit from SampleChildAdmin, "
            f"but got bases: {admin_class.__bases__}"
        )

        assert hasattr(admin_class, "base_model")
        assert admin_class.base_model == RockSample
        assert hasattr(admin_class, "show_in_index")
        assert admin_class.show_in_index is True

    def test_measurement_with_wrong_admin_class_raises_error(self, unique_app_label):
        from django.db import models

        class TestMeasurement(Measurement):
            value = models.FloatField()

            class Meta:
                app_label = unique_app_label

        class WrongMeasurementAdmin(admin.ModelAdmin):
            """Wrong admin class - doesn't inherit from MeasurementChildAdmin."""

            pass

        with pytest.raises(ConfigurationError) as exc_info:
            ModelConfiguration(
                model=TestMeasurement,
                admin_class=WrongMeasurementAdmin,
                fields=["value"],
            )

        assert "TestMeasurement" in str(exc_info.value)

    def test_measurement_with_correct_admin_class_passes(self, unique_app_label):
        from django.db import models

        from fairdm.core.measurement.admin import MeasurementChildAdmin

        class TestMeasurement2(Measurement):
            value = models.FloatField()

            class Meta:
                app_label = unique_app_label

        class CorrectMeasurementAdmin(MeasurementChildAdmin):
            """Correct admin class - inherits from MeasurementChildAdmin."""

            base_model = TestMeasurement2
            show_in_index = True

        config = ModelConfiguration(
            model=TestMeasurement2,
            admin_class=CorrectMeasurementAdmin,
            fields=["value"],
        )

        assert config.get_admin_class() == CorrectMeasurementAdmin

    def test_autogenerated_measurement_admin_inherits_from_child_admin(
        self, unique_app_label
    ):
        from django.db import models

        from fairdm.core.measurement.admin import MeasurementChildAdmin

        class TestMeasurement3(Measurement):
            value = models.FloatField()

            class Meta:
                app_label = unique_app_label

        config = ModelConfiguration(
            model=TestMeasurement3,
            fields=["value"],
        )

        admin_class = config.get_admin_class()
        assert issubclass(admin_class, MeasurementChildAdmin), (
            f"Auto-generated admin for {TestMeasurement3.__name__} should inherit from MeasurementChildAdmin, "
            f"but got bases: {admin_class.__bases__}"
        )

        assert hasattr(admin_class, "base_model")
        assert admin_class.base_model == TestMeasurement3
        assert hasattr(admin_class, "show_in_index")
        assert admin_class.show_in_index is True

    def test_admin_class_as_string_reference(self):
        from demo.models import WaterSample

        config = ModelConfiguration(
            model=WaterSample,
            admin_class="demo.admin.WaterSampleAdmin",
            fields=["name", "ph_level"],
        )

        from demo.admin import WaterSampleAdmin

        assert config.get_admin_class() == WaterSampleAdmin


class TestFieldResolutionAlgorithm:
    @pytest.fixture
    def test_model(self):
        class SandstoneRockSample(Sample):
            """Test rock sample model."""

            rock_type = models.CharField(max_length=100)
            mineral_content = models.TextField()
            sample_location = models.CharField(max_length=200)
            collection_date = models.DateField()
            weight_grams = models.FloatField()

            class Meta:
                app_label = "test_app"

        return SandstoneRockSample

    def test_tier1_component_specific_fields_table(self, test_model):
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location"],
            table_fields=["rock_type", "weight_grams"],
        )

        table_class = config.get_table_class()

        assert "rock_type" in table_class.base_columns
        assert "weight_grams" in table_class.base_columns

        assert "sample_location" not in table_class.base_columns

    def test_tier2_parent_fields_fallback_table(self, test_model):
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location", "collection_date"],
            table_fields=None,
        )

        table_class = config.get_table_class()

        assert "rock_type" in table_class.base_columns
        assert "sample_location" in table_class.base_columns
        assert "collection_date" in table_class.base_columns

    def test_tier3_smart_defaults_table(self, test_model):
        config = ModelConfiguration(
            model=test_model,
            fields=None,
            table_fields=None,
        )

        table_class = config.get_table_class()

        assert "rock_type" in table_class.base_columns
        assert "sample_location" in table_class.base_columns
        assert "collection_date" in table_class.base_columns
        assert "weight_grams" in table_class.base_columns

        assert "polymorphic_ctype" not in table_class.base_columns

    def test_tier1_component_specific_fields_form(self, test_model):
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "mineral_content", "sample_location"],
            form_fields=["rock_type", "weight_grams"],
        )

        form_class = config.get_form_class()

        assert "rock_type" in form_class.base_fields
        assert "weight_grams" in form_class.base_fields

        assert "mineral_content" not in form_class.base_fields
        assert "sample_location" not in form_class.base_fields

    def test_tier2_parent_fields_fallback_form(self, test_model):
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "mineral_content", "weight_grams"],
            form_fields=None,
        )

        form_class = config.get_form_class()

        assert "rock_type" in form_class.base_fields
        assert "mineral_content" in form_class.base_fields
        assert "weight_grams" in form_class.base_fields

    def test_tier3_smart_defaults_form(self, test_model):
        config = ModelConfiguration(
            model=test_model,
            fields=None,
            form_fields=None,
        )

        form_class = config.get_form_class()

        assert "rock_type" in form_class.base_fields
        assert "mineral_content" in form_class.base_fields
        assert "sample_location" in form_class.base_fields
        assert "collection_date" in form_class.base_fields
        assert "weight_grams" in form_class.base_fields

        assert "id" not in form_class.base_fields
        assert "polymorphic_ctype" not in form_class.base_fields

    def test_tier1_component_specific_fields_filterset(self, test_model):
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location"],
            filterset_fields=["rock_type", "collection_date"],
        )

        filterset_class = config.get_filterset_class()

        assert "rock_type" in filterset_class.base_filters
        assert "collection_date" in filterset_class.base_filters

        assert "location" not in filterset_class.base_filters

    def test_tier2_parent_fields_fallback_filterset(self, test_model):
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location", "collection_date"],
            filterset_fields=None,
        )

        filterset_class = config.get_filterset_class()

        assert "rock_type" in filterset_class.base_filters
        assert "sample_location" in filterset_class.base_filters
        assert "collection_date" in filterset_class.base_filters

    def test_tier3_smart_defaults_filterset(self, test_model):
        config = ModelConfiguration(
            model=test_model,
            fields=None,
            filterset_fields=None,
        )

        filterset_class = config.get_filterset_class()

        assert "rock_type" in filterset_class.base_filters
        assert "mineral_content" in filterset_class.base_filters
        assert "sample_location" in filterset_class.base_filters
        assert "collection_date" in filterset_class.base_filters
        assert "weight_grams" in filterset_class.base_filters

        assert "id" not in filterset_class.base_filters
        assert "polymorphic_ctype" not in filterset_class.base_filters

    def test_tier1_component_specific_fields_admin(self, test_model):
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location"],
            admin_list_display=["rock_type", "weight_grams"],
        )

        admin_class = config.get_admin_class()

        assert admin_class.list_display == ["rock_type", "weight_grams"]

    def test_tier2_parent_fields_fallback_admin(self, test_model):
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location", "collection_date"],
            admin_list_display=None,
        )

        admin_class = config.get_admin_class()

        assert "rock_type" in admin_class.list_display
        assert "sample_location" in admin_class.list_display
        assert "collection_date" in admin_class.list_display

    def test_tier3_smart_defaults_admin(self, test_model):
        config = ModelConfiguration(
            model=test_model,
            fields=None,
            admin_list_display=None,
        )

        admin_class = config.get_admin_class()

        assert len(admin_class.list_display) > 0
        assert len(admin_class.list_display) <= 5  # AdminFactory limits to first 5

        if (
            len(admin_class.list_display) == 1
            and admin_class.list_display[0] == "__str__"
        ):
            pytest.fail(
                "Admin list_display should have actual fields, not just __str__"
            )


class TestCustomClassOverride:
    @pytest.fixture
    def test_model(self):
        class QuartzRockSample(Sample):
            """Test rock sample model."""

            quartz_type = models.CharField(max_length=100)
            sample_description = models.TextField()

            class Meta:
                app_label = "test_app"

        return QuartzRockSample

    def test_custom_form_class_wins_over_the_shared_field_list(self, test_model):
        from django import forms

        class CustomForm(forms.ModelForm):
            """Custom form with specific field."""

            custom_field = forms.CharField()

            class Meta:
                model = test_model
                fields = ["quartz_type"]

        config = ModelConfiguration(
            model=test_model,
            form_class=CustomForm,
            # Legal: the shared list still feeds the five generated components. Only a component's own list
            # next to its own class is dead.
            fields=["sample_description"],
        )

        form_class = config.get_form_class()

        assert form_class is CustomForm
        assert "custom_field" in form_class.base_fields
        assert "quartz_type" in form_class.base_fields
        assert "sample_description" not in form_class.base_fields
        assert config.resolve_fields("table") == ["sample_description"]

    def test_custom_table_class_wins_over_the_shared_field_list(self, test_model):
        import django_tables2 as tables

        class CustomTable(tables.Table):
            """Custom table with specific columns."""

            quartz_type = tables.Column()

            class Meta:
                model = test_model

        config = ModelConfiguration(
            model=test_model,
            table_class=CustomTable,
            fields=["sample_description"],
        )

        table_class = config.get_table_class()

        assert table_class is CustomTable
        assert "quartz_type" in table_class.base_columns

    def test_component_field_list_beside_its_own_class_is_refused(self, test_model):
        # Django refuses the same pair on ModelFormMixin. Preferring the class silently leaves a list that does nothing.
        from django import forms
        from django.core.exceptions import ImproperlyConfigured

        class CustomForm(forms.ModelForm):
            class Meta:
                model = test_model
                fields = ["quartz_type"]

        with pytest.raises(ImproperlyConfigured, match="form_fields and form_class"):
            ModelConfiguration(
                model=test_model,
                form_class=CustomForm,
                form_fields=["sample_description"],
            )

    def test_the_refusal_covers_every_component(self, test_model):
        import django_tables2 as tables
        from django.core.exceptions import ImproperlyConfigured

        class CustomTable(tables.Table):
            class Meta:
                model = test_model

        with pytest.raises(ImproperlyConfigured, match="table_fields and table_class"):
            ModelConfiguration(
                model=test_model,
                table_class=CustomTable,
                table_fields=["sample_description"],
            )


class TestRegistrationValidation:
    def test_model_required(self):
        with pytest.raises(ConfigurationError):
            ModelConfiguration(model=None)

    def test_model_must_inherit_from_sample_or_measurement(self, clean_registry):
        class InvalidModel(models.Model):
            """Regular Django model (not Sample/Measurement)."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        with pytest.raises(ConfigurationError):
            clean_registry.register(InvalidModel)

    def test_duplicate_registration_rejected(self, clean_registry):
        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        clean_registry.register(RockSample)

        with pytest.raises(DuplicateRegistrationError):
            clean_registry.register(RockSample)

    def test_invalid_field_name_in_list_fields(self):
        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        with pytest.raises(FieldValidationError, match="nonexistent_field"):
            ModelConfiguration(
                model=RockSample,
                fields=["rock_type", "nonexistent_field"],
            )

    def test_invalid_field_name_in_component_specific_fields(self):
        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        with pytest.raises(FieldValidationError, match="bad_field"):
            ModelConfiguration(
                model=RockSample,
                table_fields=["rock_type", "bad_field"],
            )

    def test_invalid_related_field_path(self):
        # Only the base field is validated. The rest of the path depends on the queryset, and Django raises at runtime.
        class RelatedModel(models.Model):
            """Related model."""

            title = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        class RockSample(Sample):
            """Test Sample with foreign key."""

            rock_type = models.CharField(max_length=100)
            source_ref = models.ForeignKey(RelatedModel, on_delete=models.CASCADE)

            class Meta:
                app_label = "test_app"

        config = ModelConfiguration(
            model=RockSample,
            fields=["rock_type", "source_ref__title"],
        )
        assert "source_ref__title" in config.fields

        with pytest.raises(FieldValidationError):
            ModelConfiguration(
                model=RockSample,
                fields=["rock_type", "nonexistent__title"],
            )


class TestFieldValidationWithFuzzyMatching:
    def test_fuzzy_match_suggests_close_field_names(self):
        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)
            mineral_content = models.TextField()

            class Meta:
                app_label = "test_app"

        with pytest.raises(FieldValidationError) as exc_info:
            ModelConfiguration(
                model=RockSample,
                fields=["rock_type", "mineral_contnt"],
            )

        assert "mineral_contnt" in str(exc_info.value)
        assert "mineral_content" in exc_info.value.suggestion

    def test_no_suggestions_when_no_close_matches(self):
        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        with pytest.raises(FieldValidationError) as exc_info:
            ModelConfiguration(
                model=RockSample,
                fields=["rock_type", "xyz123"],
            )

        assert "xyz123" in str(exc_info.value)


class TestSearchFieldsValidation:
    def test_a_path_that_does_not_resolve_is_refused(self):
        class SearchFieldsUnresolvedSample(Sample):
            class Meta:
                app_label = "test_app"

        with pytest.raises(FieldValidationError) as exc_info:
            ModelConfiguration(
                model=SearchFieldsUnresolvedSample,
                search_fields=["no_such_field"],
            )

        message = str(exc_info.value)
        assert "no_such_field" in message
        assert "search_fields" in message

    @pytest.mark.parametrize(
        "field_factory",
        [
            lambda: models.DecimalField(max_digits=5, decimal_places=2),
            lambda: models.BooleanField(),
            lambda: models.DateField(),
        ],
        ids=["DecimalField", "BooleanField", "DateField"],
    )
    def test_a_non_text_field_is_refused_naming_the_type_and_field(self, field_factory):
        field = field_factory()
        model = type(
            f"SearchFieldsNonText{field.__class__.__name__}",
            (Sample,),
            {
                "value": field,
                "__module__": __name__,
                "Meta": type("Meta", (), {"app_label": "test_app"}),
            },
        )

        with pytest.raises(FieldValidationError) as exc_info:
            ModelConfiguration(model=model, search_fields=["value"])

        message = str(exc_info.value)
        assert "value" in message
        assert model.__name__ in message
        assert not exc_info.value.suggestion


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
    def test_every_accessor_has_a_component_entry(self):
        assert len(COMPONENTS) == 6
        for name, spec in COMPONENTS.items():
            assert f"get_{name}_class" in ACCESSORS, name
            assert spec.fields_attr
            assert spec.class_attr
            assert _component_base(name) is not None

    def test_component_names_match_their_configuration_attributes(self):
        for spec in COMPONENTS.values():
            assert hasattr(ModelConfiguration, spec.fields_attr), spec.fields_attr
            assert hasattr(ModelConfiguration, spec.class_attr), spec.class_attr


class TestPlainClassConfiguration:
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
    def test_serializer_does_not_inject_id(self, rock_sample):
        config = ModelConfiguration(model=rock_sample, fields=["rock_type"])
        serializer = config.get_serializer_class()
        assert "id" not in serializer.Meta.fields

    def test_resource_does_not_inject_id(self, rock_sample):
        config = ModelConfiguration(model=rock_sample, fields=["rock_type"])
        resource = config.get_resource_class()
        assert "id" not in resource.Meta.fields


class TestGenerationTouchesNoDatabase:
    # No `db` fixture is requested, so pytest-django blocks database access and a generator that
    # connected would raise.
    def test_configuration_and_every_component_build_with_the_database_blocked(
        self, rock_sample
    ):
        config = ModelConfiguration(model=rock_sample, fields=["rock_type"])
        for accessor in ACCESSORS:
            assert isinstance(getattr(config, accessor)(), type), accessor


class TestConcreteModelsOnly:
    def test_base_sample_is_refused(self, clean_registry):
        with pytest.raises(ConfigurationError):
            clean_registry.register(Sample, ModelConfiguration(model=Sample))

    def test_base_measurement_is_refused(self, clean_registry):
        with pytest.raises(ConfigurationError):
            clean_registry.register(Measurement, ModelConfiguration(model=Measurement))

    def test_a_model_outside_both_hierarchies_is_refused(self, clean_registry):
        class NotASample(models.Model):
            class Meta:
                app_label = "test_app"

        with pytest.raises(ConfigurationError):
            clean_registry.register(NotASample, ModelConfiguration(model=NotASample))


class TestFieldPathValidation:
    def test_a_valid_related_path_is_accepted(self, rock_sample):
        config = ModelConfiguration(model=rock_sample, fields=["dataset__name"])
        assert "dataset__name" in config.fields

    def test_a_bad_final_segment_is_refused(self, rock_sample):
        with pytest.raises(FieldValidationError, match="dataset__nonexistent"):
            ModelConfiguration(model=rock_sample, fields=["dataset__nonexistent"])

    def test_a_path_through_a_non_relation_is_refused(self, rock_sample):
        with pytest.raises(FieldValidationError):
            ModelConfiguration(model=rock_sample, fields=["rock_type__nope"])


class TestValidationMessages:
    def test_the_message_names_the_model_attribute_value_and_suggestion(
        self, rock_sample
    ):
        with pytest.raises(FieldValidationError) as caught:
            ModelConfiguration(model=rock_sample, fields=["rock_typ"])

        message = str(caught.value)
        assert "rock_typ" in message
        assert "RockSample.fields" in message

    def test_the_attribute_that_declared_it_is_named(self, rock_sample):
        with pytest.raises(FieldValidationError, match="RockSample.table_fields"):
            ModelConfiguration(model=rock_sample, table_fields=["nope"])


class TestUnregisteredModel:
    def test_get_for_model_raises_and_names_the_model(
        self, clean_registry, rock_sample
    ):
        with pytest.raises(NotRegisteredError, match="RockSample"):
            clean_registry.get_for_model(rock_sample)

    def test_is_registered_answers_without_raising(self, clean_registry, rock_sample):
        assert clean_registry.is_registered(rock_sample) is False


class TestNonFunctionalGuards:
    def test_registration_issues_no_queries(
        self, db, clean_registry, rock_sample, django_assert_num_queries
    ):
        with django_assert_num_queries(0):
            clean_registry.register(rock_sample)

    def test_all_six_accessors_issue_no_queries(
        self, db, clean_registry, rock_sample, django_assert_num_queries
    ):
        clean_registry.register(rock_sample)
        config = clean_registry.get_for_model(rock_sample)

        with django_assert_num_queries(0):
            for accessor in ACCESSORS:
                getattr(config, accessor)()
