"""
Tests for Component Factories - Form, Table, and Filter generation.

This module tests the factory classes that generate Django components
from ModelConfiguration settings.
"""

import pytest
from django.db import models
from django.forms import ModelForm
from django_filters import FilterSet
from django_tables2 import Table

from fairdm.config_components import FiltersConfig, FormConfig, TableConfig
from fairdm.utils.component_factories import FilterFactory, FormFactory, TableFactory


# Test model
class SampleModel(models.Model):
    """Sample model for testing factory generation."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    collected_at = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[("draft", "Draft"), ("active", "Active")],
        default="draft",
    )
    count = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)

    class Meta:
        app_label = "test_factories"


@pytest.mark.django_db
class TestFormFactory:
    """Test suite for FormFactory."""

    def test_generate_basic_form(self):
        """Test generating a basic form with default config."""
        config = FormConfig()
        factory = FormFactory(SampleModel, config)

        form_class = factory.generate()

        assert issubclass(form_class, ModelForm)
        assert form_class._meta.model == SampleModel

    def test_form_with_specific_fields(self):
        """Test form generation with specific fields."""
        config = FormConfig(fields=["name", "collected_at"])
        factory = FormFactory(SampleModel, config)

        form_class = factory.generate()

        # Instantiate to check fields
        form = form_class()
        assert "name" in form.fields
        assert "collected_at" in form.fields
        assert "description" not in form.fields  # Not in config

    def test_form_with_all_fields(self):
        """Test form with __all__ fields."""
        config = FormConfig(fields="__all__")
        factory = FormFactory(SampleModel, config)

        form_class = factory.generate()
        form = form_class()

        assert "name" in form.fields
        assert "description" in form.fields
        assert "collected_at" in form.fields

    def test_form_with_exclusions(self):
        """Test form with field exclusions."""
        config = FormConfig(fields="__all__", exclude=["description", "count"])
        factory = FormFactory(SampleModel, config)

        form_class = factory.generate()
        form = form_class()

        assert "name" in form.fields
        assert "description" not in form.fields
        assert "count" not in form.fields

    def test_form_with_parent_fields(self):
        """Test form using parent config fields."""
        config = FormConfig()  # No fields specified
        parent_fields = ["name", "status"]
        factory = FormFactory(SampleModel, config, parent_fields=parent_fields)

        fields = factory.get_fields()

        assert fields == parent_fields

    def test_form_with_custom_widgets(self):
        """Test form with custom widget configuration."""
        config = FormConfig(
            fields=["name", "collected_at"],
            widgets={"name": "TextInput"},
        )
        factory = FormFactory(SampleModel, config)

        widgets = factory.get_widgets()

        assert "name" in widgets
        assert widgets["name"] == "TextInput"

    def test_get_widgets_smart_detection(self):
        """Test that widgets are smartly detected for fields."""
        config = FormConfig(fields=["collected_at", "status"])
        factory = FormFactory(SampleModel, config)

        widgets = factory.get_widgets()

        # Should suggest DateInput for DateField
        assert "collected_at" in widgets
        assert widgets["collected_at"] == "DateInput"

        # Should suggest RadioSelect for choice field with few choices
        assert "status" in widgets
        assert widgets["status"] == "RadioSelect"


@pytest.mark.django_db
class TestTableFactory:
    """Test suite for TableFactory."""

    def test_generate_basic_table(self):
        """Test generating a basic table with default config."""
        config = TableConfig()
        factory = TableFactory(SampleModel, config)

        table_class = factory.generate()

        assert issubclass(table_class, Table)
        assert table_class._meta.model == SampleModel

    def test_table_with_specific_fields(self):
        """Test table generation with specific fields."""
        config = TableConfig(fields=["name", "status", "collected_at"])
        factory = TableFactory(SampleModel, config)

        fields = factory.get_fields()

        assert fields == ["name", "status", "collected_at"]

    def test_table_with_exclusions(self):
        """Test table with field exclusions."""
        config = TableConfig(
            fields=["name", "description", "status"],
            exclude=["description"],
        )
        factory = TableFactory(SampleModel, config)

        fields = factory.get_fields()

        assert "name" in fields
        assert "status" in fields
        assert "description" not in fields

    def test_table_with_parent_fields(self):
        """Test table using parent config fields."""
        config = TableConfig()  # No fields specified
        parent_fields = ["name", "status"]
        factory = TableFactory(SampleModel, config, parent_fields=parent_fields)

        fields = factory.get_fields()

        assert fields == parent_fields

    def test_table_default_list_fields(self):
        """Test table uses smart default fields when none specified."""
        config = TableConfig()  # No fields, no parent
        factory = TableFactory(SampleModel, config)

        fields = factory.get_fields()

        # Should use inspector's default list fields
        assert isinstance(fields, list)
        assert len(fields) > 0
        # Should prioritize 'name' if present
        assert "name" in fields

    def test_table_orderable_all(self):
        """Test table with all columns orderable."""
        config = TableConfig(fields=["name", "status"], orderable=True)
        factory = TableFactory(SampleModel, config)

        table_class = factory.generate()

        # Check that orderable was set
        # Note: Actual verification would require instantiating the table
        assert table_class is not None

    def test_table_orderable_specific(self):
        """Test table with specific columns orderable."""
        config = TableConfig(fields=["name", "status"], orderable=["name"])
        factory = TableFactory(SampleModel, config)

        table_class = factory.generate()

        assert table_class is not None


@pytest.mark.django_db
class TestFilterFactory:
    """Test suite for FilterFactory."""

    def test_generate_basic_filterset(self):
        """Test generating a basic filterset with default config."""
        config = FiltersConfig()
        factory = FilterFactory(SampleModel, config)

        filterset_class = factory.generate()

        assert issubclass(filterset_class, FilterSet)

    def test_filterset_with_specific_fields(self):
        """Test filterset generation with specific fields."""
        config = FiltersConfig(fields=["status", "collected_at"])
        factory = FilterFactory(SampleModel, config)

        fields = factory.get_fields()

        assert "status" in fields
        assert "collected_at" in fields

    def test_filterset_with_exclusions(self):
        """Test filterset with field exclusions."""
        config = FiltersConfig(
            fields=["name", "status", "collected_at"],
            exclude=["name"],
        )
        factory = FilterFactory(SampleModel, config)

        fields = factory.get_fields()

        assert "status" in fields
        assert "collected_at" in fields
        assert "name" not in fields

    def test_filterset_with_parent_fields(self):
        """Test filterset using parent config fields."""
        config = FiltersConfig()  # No fields specified
        parent_fields = ["status", "is_published"]
        factory = FilterFactory(SampleModel, config, parent_fields=parent_fields)

        fields = factory.get_fields()

        assert fields == parent_fields

    def test_filterset_default_filter_fields(self):
        """Test filterset uses smart default fields when none specified."""
        config = FiltersConfig()  # No fields, no parent
        factory = FilterFactory(SampleModel, config)

        fields = factory.get_fields()

        # Should use inspector's default filter fields
        assert isinstance(fields, list)
        # Should include date, choice, and boolean fields
        assert "collected_at" in fields or "status" in fields or "is_published" in fields

    def test_get_filter_overrides_exact(self):
        """Test filter overrides for exact match fields."""
        config = FiltersConfig(
            fields=["name", "status"],
            exact_fields=["status"],
        )
        factory = FilterFactory(SampleModel, config)

        overrides = factory.get_filter_overrides()

        assert "status" in overrides
        assert overrides["status"] == "exact"

    def test_get_filter_overrides_range(self):
        """Test filter overrides for range fields."""
        config = FiltersConfig(
            fields=["collected_at", "count"],
            range_fields=["collected_at", "count"],
        )
        factory = FilterFactory(SampleModel, config)

        overrides = factory.get_filter_overrides()

        # Date field should get DateFromToRangeFilter
        assert "collected_at" in overrides
        assert "Range" in overrides["collected_at"]

        # Numeric field should get RangeFilter
        assert "count" in overrides
        assert "Range" in overrides["count"]

    def test_get_filter_overrides_search(self):
        """Test filter overrides for search fields."""
        config = FiltersConfig(
            fields=["name", "description"],
            search_fields=["name"],
        )
        factory = FilterFactory(SampleModel, config)

        overrides = factory.get_filter_overrides()

        assert "name" in overrides
        assert overrides["name"] == "CharFilter"

    def test_get_filter_overrides_smart_detection(self):
        """Test that filters are smartly detected when not explicitly configured."""
        config = FiltersConfig(fields=["collected_at", "is_published", "status"])
        factory = FilterFactory(SampleModel, config)

        overrides = factory.get_filter_overrides()

        # Should detect date field needs range filter
        assert "collected_at" in overrides
        assert "Range" in overrides["collected_at"]

        # Should detect boolean field
        assert "is_published" in overrides
        assert "Boolean" in overrides["is_published"]

        # Should detect choice field
        assert "status" in overrides
        assert "Choice" in overrides["status"]

    def test_filter_overrides_custom_priority(self):
        """Test that custom filter overrides take priority over smart detection."""
        config = FiltersConfig(
            fields=["status"],
            filter_overrides={"status": "CharFilter"},
        )
        factory = FilterFactory(SampleModel, config)

        overrides = factory.get_filter_overrides()

        # Should use custom override, not smart detection
        assert overrides["status"] == "CharFilter"
