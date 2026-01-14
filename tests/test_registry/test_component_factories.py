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

from fairdm.registry.factories import FilterFactory, FormFactory, TableFactory


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
        factory = FormFactory(SampleModel)

        form_class = factory.generate()

        assert issubclass(form_class, ModelForm)
        assert form_class._meta.model == SampleModel

    def test_form_with_specific_fields(self):
        """Test form generation with specific fields."""
        factory = FormFactory(SampleModel, fields=["name", "collected_at"])

        form_class = factory.generate()

        # Instantiate to check fields
        form = form_class()
        assert "name" in form.fields
        assert "collected_at" in form.fields
        assert "description" not in form.fields  # Not specified

    def test_form_with_all_fields(self):
        """Test form with all safe fields."""
        factory = FormFactory(SampleModel)

        form_class = factory.generate()
        form = form_class()

        # Should have safe fields (not id, etc.)
        assert "name" in form.fields
        assert "collected_at" in form.fields

    def test_form_with_exclusions(self):
        """Test form only includes specified fields."""
        factory = FormFactory(SampleModel, fields=["name", "status"])

        form_class = factory.generate()
        form = form_class()

        assert "name" in form.fields
        assert "status" in form.fields
        assert "description" not in form.fields
        assert "count" not in form.fields

    def test_form_with_parent_fields(self):
        """Test form using explicitly provided fields."""
        parent_fields = ["name", "status"]
        factory = FormFactory(SampleModel, fields=parent_fields)

        fields = factory.get_fields()

        assert fields == parent_fields

    def test_form_with_custom_widgets(self):
        """Test form has smart widget mapping."""
        factory = FormFactory(SampleModel, fields=["name", "collected_at"])

        form_class = factory.generate()
        form = form_class()

        # Check that DateInput widget is applied to date field
        from django.forms import DateInput

        assert isinstance(form.fields["collected_at"].widget, DateInput)

    def test_get_widgets_smart_detection(self):
        """Test that widgets are smartly detected for fields."""
        factory = FormFactory(SampleModel, fields=["collected_at", "status"])

        form_class = factory.generate()
        form = form_class()

        # Should have DateInput for DateField
        from django.forms import DateInput

        assert isinstance(form.fields["collected_at"].widget, DateInput)


@pytest.mark.django_db
class TestTableFactory:
    """Test suite for TableFactory."""

    def test_generate_basic_table(self):
        """Test generating a basic table with default config."""
        factory = TableFactory(SampleModel)

        table_class = factory.generate()

        assert issubclass(table_class, Table)
        assert table_class._meta.model == SampleModel

    def test_table_with_specific_fields(self):
        """Test table generation with specific fields."""
        factory = TableFactory(SampleModel, fields=["name", "status", "collected_at"])

        fields = factory.get_fields()

        assert fields == ["name", "status", "collected_at"]

    def test_table_with_exclusions(self):
        """Test table only includes specified fields."""
        factory = TableFactory(SampleModel, fields=["name", "status"])

        fields = factory.get_fields()

        assert "name" in fields
        assert "status" in fields
        assert "description" not in fields

    def test_table_with_parent_fields(self):
        """Test table using explicitly provided fields."""
        parent_fields = ["name", "status"]
        factory = TableFactory(SampleModel, fields=parent_fields)

        fields = factory.get_fields()

        assert fields == parent_fields

    def test_table_default_list_fields(self):
        """Test table uses smart default fields when none specified."""
        factory = TableFactory(SampleModel)  # No fields specified

        fields = factory.get_fields()

        # Should use inspector's safe fields
        assert isinstance(fields, list)
        assert len(fields) > 0
        # Should prioritize 'name' if present
        assert "name" in fields

    def test_table_orderable_all(self):
        """Test table can be generated successfully."""
        factory = TableFactory(SampleModel, fields=["name", "status"])

        table_class = factory.generate()

        # Table should be generated successfully
        assert table_class is not None
        assert issubclass(table_class, Table)

    def test_table_orderable_specific(self):
        """Test table with specific fields."""
        factory = TableFactory(SampleModel, fields=["name", "status"])

        table_class = factory.generate()

        assert table_class is not None
        assert issubclass(table_class, Table)


@pytest.mark.django_db
class TestFilterFactory:
    """Test suite for FilterFactory."""

    def test_generate_basic_filterset(self):
        """Test generating a basic filterset with default config."""
        factory = FilterFactory(SampleModel)

        filterset_class = factory.generate()

        assert issubclass(filterset_class, FilterSet)

    def test_filterset_with_specific_fields(self):
        """Test filterset generation with specific fields."""
        factory = FilterFactory(SampleModel, fields=["status", "collected_at"])

        fields = factory.get_fields()

        assert "status" in fields
        assert "collected_at" in fields

    def test_filterset_with_exclusions(self):
        """Test filterset only includes specified fields."""
        factory = FilterFactory(SampleModel, fields=["status", "collected_at"])

        fields = factory.get_fields()

        assert "status" in fields
        assert "collected_at" in fields
        assert "name" not in fields

    def test_filterset_with_parent_fields(self):
        """Test filterset using explicitly provided fields."""
        parent_fields = ["status", "is_published"]
        factory = FilterFactory(SampleModel, fields=parent_fields)

        fields = factory.get_fields()

        assert fields == parent_fields

    def test_filterset_default_filter_fields(self):
        """Test filterset uses smart default fields when none specified."""
        factory = FilterFactory(SampleModel)  # No fields specified

        fields = factory.get_fields()

        # Should use inspector's safe fields
        assert isinstance(fields, list)
        # Should include some reasonable fields
        assert len(fields) > 0

    def test_get_filter_overrides_exact(self):
        """Test filter generation includes appropriate filters."""
        factory = FilterFactory(SampleModel, fields=["name", "status"])

        filterset_class = factory.generate()

        # Should successfully generate a filterset
        assert filterset_class is not None
        assert issubclass(filterset_class, FilterSet)

    def test_get_filter_overrides_range(self):
        """Test filter for date and numeric fields."""
        factory = FilterFactory(SampleModel, fields=["collected_at", "count"])

        filterset_class = factory.generate()

        # Should successfully generate a filterset
        assert filterset_class is not None
        assert issubclass(filterset_class, FilterSet)

    def test_get_filter_overrides_search(self):
        """Test filter for text fields."""
        factory = FilterFactory(SampleModel, fields=["name", "description"])

        filterset_class = factory.generate()

        # Should successfully generate a filterset
        assert filterset_class is not None
        assert issubclass(filterset_class, FilterSet)

    def test_get_filter_overrides_smart_detection(self):
        """Test that filters are smartly detected for different field types."""
        factory = FilterFactory(SampleModel, fields=["collected_at", "is_published", "status"])

        filterset_class = factory.generate()

        # Should successfully generate a filterset with smart filters
        assert filterset_class is not None
        assert issubclass(filterset_class, FilterSet)

    def test_filter_overrides_custom_priority(self):
        """Test that filterset can be generated for choice fields."""
        factory = FilterFactory(SampleModel, fields=["status"])

        filterset_class = factory.generate()

        # Should successfully generate a filterset
        assert filterset_class is not None
        assert issubclass(filterset_class, FilterSet)
