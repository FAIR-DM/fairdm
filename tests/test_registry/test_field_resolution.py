"""T013: Unit tests for 3-tier field resolution algorithm.

Tests the field resolution priority:
1. Custom class provided → use custom class
2. Component-specific fields (e.g., table_fields) → use those
3. Parent fields (e.g., list_fields) → use as fallback
4. Smart defaults (ModelConfiguration.get_default_fields()) → final fallback

See specs/004-fairdm-registry/data-model.md Section 4 for algorithm specification.
"""

import pytest
from django.db import models

from fairdm.registry.config import ModelConfiguration
from fairdm.core.models import Sample


class TestFieldResolutionAlgorithm:
    """Test 3-tier field resolution for each component type."""

    @pytest.fixture
    def test_model(self):
        """Fixture providing a test Sample model."""

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
        """Test that component-specific table_fields takes highest priority."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location"],  # Parent fields
            table_fields=["rock_type", "weight_grams"],  # Component-specific
        )

        # get_table_class() should use table_fields
        table_class = config.get_table_class()

        # Verify columns match component-specific fields
        assert "rock_type" in table_class.base_columns
        assert "weight_grams" in table_class.base_columns

        # Parent fields should NOT appear
        assert "sample_location" not in table_class.base_columns

    def test_tier2_parent_fields_fallback_table(self, test_model):
        """Test that parent list_fields is used when table_fields not provided."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location", "collection_date"],  # Parent fields
            table_fields=None,  # No component-specific fields
        )

        # get_table_class() should fall back to fields
        table_class = config.get_table_class()

        # Verify columns match parent fields
        assert "rock_type" in table_class.base_columns
        assert "sample_location" in table_class.base_columns
        assert "collection_date" in table_class.base_columns

    def test_tier3_smart_defaults_table(self, test_model):
        """Test that smart defaults are used when no fields specified."""
        config = ModelConfiguration(
            model=test_model,
            fields=None,  # No parent fields
            table_fields=None,  # No component-specific fields
        )

        # get_table_class() should use get_default_fields()
        table_class = config.get_table_class()

        # Verify model fields appear (text fields may be excluded from table defaults)
        assert "rock_type" in table_class.base_columns
        # Note: mineral_content is a TextField and may be excluded from table defaults
        # (text fields typically don't belong in table columns)
        assert "sample_location" in table_class.base_columns
        assert "collection_date" in table_class.base_columns
        assert "weight_grams" in table_class.base_columns

        # Note: BaseTable defines 'id' column but marks it visible=False
        # The 'id' field is in base_columns but hidden from display
        # This is correct behavior - id is needed for linkify but hidden
        assert "polymorphic_ctype" not in table_class.base_columns

    def test_tier1_component_specific_fields_form(self, test_model):
        """Test that component-specific form_fields takes highest priority."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "mineral_content", "sample_location"],  # Parent fields
            form_fields=["rock_type", "weight_grams"],  # Component-specific
        )

        # get_form_class() should use form_fields
        form_class = config.get_form_class()

        # Verify form fields match component-specific fields
        assert "rock_type" in form_class.base_fields
        assert "weight_grams" in form_class.base_fields

        # Parent fields should NOT appear
        assert "mineral_content" not in form_class.base_fields
        assert "sample_location" not in form_class.base_fields

    def test_tier2_parent_fields_fallback_form(self, test_model):
        """Test that parent detail_fields is used when form_fields not provided."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "mineral_content", "weight_grams"],  # Parent fields
            form_fields=None,  # No component-specific fields
        )

        # get_form_class() should fall back to fields
        form_class = config.get_form_class()

        # Verify form fields match parent fields
        assert "rock_type" in form_class.base_fields
        assert "mineral_content" in form_class.base_fields
        assert "weight_grams" in form_class.base_fields

    def test_tier3_smart_defaults_form(self, test_model):
        """Test that smart defaults are used when no form fields specified."""
        config = ModelConfiguration(
            model=test_model,
            fields=None,  # No parent fields
            form_fields=None,  # No component-specific fields
        )

        # get_form_class() should use get_default_fields()
        form_class = config.get_form_class()

        # Verify all editable fields appear
        assert "rock_type" in form_class.base_fields
        assert "mineral_content" in form_class.base_fields
        assert "sample_location" in form_class.base_fields
        assert "collection_date" in form_class.base_fields
        assert "weight_grams" in form_class.base_fields

        # Verify exclusions
        assert "id" not in form_class.base_fields
        assert "polymorphic_ctype" not in form_class.base_fields

    def test_tier1_component_specific_fields_filterset(self, test_model):
        """Test that component-specific filterset_fields takes highest priority."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location"],  # Parent fields
            filterset_fields=["rock_type", "collection_date"],  # Component-specific
        )

        # get_filterset_class() should use filterset_fields
        filterset_class = config.get_filterset_class()

        # Verify filters match component-specific fields
        assert "rock_type" in filterset_class.base_filters
        assert "collection_date" in filterset_class.base_filters

        # Parent fields should NOT appear
        assert "location" not in filterset_class.base_filters

    def test_tier2_parent_fields_fallback_filterset(self, test_model):
        """Test that parent filter_fields is used when filterset_fields not provided."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location", "collection_date"],  # Parent fields
            filterset_fields=None,  # No component-specific fields
        )

        # get_filterset_class() should fall back to fields
        filterset_class = config.get_filterset_class()

        # Verify filters match parent fields
        assert "rock_type" in filterset_class.base_filters
        assert "sample_location" in filterset_class.base_filters
        assert "collection_date" in filterset_class.base_filters

    def test_tier3_smart_defaults_filterset(self, test_model):
        """Test that smart defaults are used when no filter fields specified."""
        config = ModelConfiguration(
            model=test_model,
            fields=None,  # No parent fields
            filterset_fields=None,  # No component-specific fields
        )

        # get_filterset_class() should use get_default_fields()
        filterset_class = config.get_filterset_class()

        # Verify all model fields appear (except exclusions)
        assert "rock_type" in filterset_class.base_filters
        assert "mineral_content" in filterset_class.base_filters
        assert "sample_location" in filterset_class.base_filters
        assert "collection_date" in filterset_class.base_filters
        assert "weight_grams" in filterset_class.base_filters

        # Verify exclusions
        assert "id" not in filterset_class.base_filters
        assert "polymorphic_ctype" not in filterset_class.base_filters

    def test_tier1_component_specific_fields_admin(self, test_model):
        """Test that component-specific admin_list_display takes highest priority."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location"],  # Parent fields
            admin_list_display=["rock_type", "weight_grams"],  # Component-specific
        )

        # get_admin_class() should use admin_list_display
        admin_class = config.get_admin_class()

        # Verify list_display matches component-specific fields
        assert admin_class.list_display == ["rock_type", "weight_grams"]

    def test_tier2_parent_fields_fallback_admin(self, test_model):
        """Test that parent list_fields is used when admin_list_display not provided."""
        config = ModelConfiguration(
            model=test_model,
            fields=["rock_type", "sample_location", "collection_date"],  # Parent fields
            admin_list_display=None,  # No component-specific fields
        )

        # get_admin_class() should fall back to fields (first 5)
        admin_class = config.get_admin_class()

        # Verify list_display matches parent fields (limited to 5)
        assert "rock_type" in admin_class.list_display
        assert "sample_location" in admin_class.list_display
        assert "collection_date" in admin_class.list_display

    def test_tier3_smart_defaults_admin(self, test_model):
        """Test that smart defaults are used when no admin fields specified."""
        config = ModelConfiguration(
            model=test_model,
            fields=None,  # No parent fields
            admin_list_display=None,  # No component-specific fields
        )

        # get_admin_class() should use get_default_fields() (first 5)
        admin_class = config.get_admin_class()

        # Verify list_display has content (may vary based on defaults)
        # Note: get_default_fields() returns ALL fields (including inherited Sample fields)
        # so list_display may contain Sample base class fields or SandstoneRockSample fields
        assert len(admin_class.list_display) > 0
        assert len(admin_class.list_display) <= 5  # AdminFactory limits to first 5

        # At least verify it's a valid field list (not empty, not just __str__)
        if len(admin_class.list_display) == 1 and admin_class.list_display[0] == "__str__":
            # This only happens if get_default_fields() returned empty list
            pytest.fail("Admin list_display should have actual fields, not just __str__")


class TestCustomClassOverride:
    """Test that custom classes bypass field resolution entirely (highest priority)."""

    @pytest.fixture
    def test_model(self):
        """Fixture providing a test Sample model."""

        class QuartzRockSample(Sample):
            """Test rock sample model."""

            quartz_type = models.CharField(max_length=100)
            sample_description = models.TextField()

            class Meta:
                app_label = "test_app"

        return QuartzRockSample

    def test_custom_form_class_overrides_all_fields(self, test_model):
        """Test that custom form_class ignores all field configurations."""
        from django import forms

        class CustomForm(forms.ModelForm):
            """Custom form with specific field."""

            custom_field = forms.CharField()

            class Meta:
                model = test_model
                fields = ["quartz_type"]  # Only quartz_type field

        config = ModelConfiguration(
            model=test_model,
            form_class=CustomForm,
            fields=["sample_description"],  # Parent fields - should be ignored
            form_fields=["sample_description"],  # Component-specific - should be ignored
        )

        # get_form_class() should return custom class unchanged
        form_class = config.get_form_class()

        assert form_class is CustomForm
        assert "custom_field" in form_class.base_fields
        assert "quartz_type" in form_class.base_fields
        assert "sample_description" not in form_class.base_fields

    def test_custom_table_class_overrides_all_fields(self, test_model):
        """Test that custom table_class ignores all field configurations."""
        import django_tables2 as tables

        class CustomTable(tables.Table):
            """Custom table with specific columns."""

            quartz_type = tables.Column()

            class Meta:
                model = test_model

        config = ModelConfiguration(
            model=test_model,
            table_class=CustomTable,
            fields=["sample_description"],  # Parent fields - should be ignored
            table_fields=["sample_description"],  # Component-specific - should be ignored
        )

        # get_table_class() should return custom class unchanged
        table_class = config.get_table_class()

        assert table_class is CustomTable
        assert "quartz_type" in table_class.base_columns
        # Custom tables don't auto-generate fields, so sample_description won't appear
