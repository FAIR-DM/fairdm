"""
Tests for FieldInspector - Smart field detection and introspection.

This module tests the FieldInspector class which provides intelligent
field detection and suggestions for FairDM model configuration.
"""

import pytest
from django.db import models

from fairdm.utils.inspection import FieldInspector


# Test model with various field types
class TestSampleModel(models.Model):
    """Sample model for testing field inspection."""

    # Basic fields
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True, null=True)

    # Date fields
    collected_at = models.DateField()
    analyzed_at = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    # Choice field
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("archived", "Archived"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Boolean field
    is_published = models.BooleanField(default=False)

    # Numeric fields
    count = models.IntegerField(default=0)
    measurement = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # File fields
    image = models.ImageField(upload_to="test/", blank=True)
    document = models.FileField(upload_to="test/", blank=True)

    # URL and Email
    website = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)

    # Foreign key (to self for testing)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")

    # Internal/auto fields that should be excluded
    internal_id = models.CharField(max_length=50, editable=False)
    password = models.CharField(max_length=128)  # Should be excluded

    class Meta:
        app_label = "test_inspection"


@pytest.mark.django_db
class TestFieldInspector:
    """Test suite for FieldInspector class."""

    def test_initialization(self):
        """Test FieldInspector initializes correctly."""
        inspector = FieldInspector(TestSampleModel)
        assert inspector.model == TestSampleModel
        assert inspector._fields_cache is None
        assert inspector._field_map_cache is None

    def test_get_all_fields(self):
        """Test retrieval of all model fields."""
        inspector = FieldInspector(TestSampleModel)
        fields = inspector._get_all_fields()

        assert len(fields) > 0
        field_names = [f.name for f in fields]
        assert "name" in field_names
        assert "collected_at" in field_names
        assert "status" in field_names

    def test_get_field(self):
        """Test getting a specific field by name."""
        inspector = FieldInspector(TestSampleModel)

        name_field = inspector.get_field("name")
        assert name_field is not None
        assert isinstance(name_field, models.CharField)

        nonexistent = inspector.get_field("nonexistent_field")
        assert nonexistent is None

    def test_should_exclude_field(self):
        """Test field exclusion logic."""
        inspector = FieldInspector(TestSampleModel)

        # Should exclude 'id'
        assert inspector.should_exclude_field("id")

        # Should exclude password
        assert inspector.should_exclude_field("password")

        # Should exclude auto_now fields
        assert inspector.should_exclude_field("modified")

        # Should exclude non-editable fields
        assert inspector.should_exclude_field("internal_id")

        # Should NOT exclude regular fields
        assert not inspector.should_exclude_field("name")
        assert not inspector.should_exclude_field("collected_at")

    def test_get_safe_fields(self):
        """Test retrieval of safe fields for forms/tables."""
        inspector = FieldInspector(TestSampleModel)
        safe_fields = inspector.get_safe_fields()

        # Should include these
        assert "name" in safe_fields
        assert "description" in safe_fields
        assert "collected_at" in safe_fields
        assert "status" in safe_fields

        # Should exclude these
        assert "id" not in safe_fields
        assert "password" not in safe_fields
        assert "modified" not in safe_fields  # auto_now
        assert "analyzed_at" not in safe_fields  # auto_now_add
        assert "internal_id" not in safe_fields  # editable=False

    def test_get_safe_fields_with_custom_exclude(self):
        """Test safe fields with additional exclusions."""
        inspector = FieldInspector(TestSampleModel)
        safe_fields = inspector.get_safe_fields(exclude=["name", "description"])

        assert "name" not in safe_fields
        assert "description" not in safe_fields
        assert "collected_at" in safe_fields

    def test_get_date_fields(self):
        """Test detection of date/datetime fields."""
        inspector = FieldInspector(TestSampleModel)
        date_fields = inspector.get_date_fields()

        assert "collected_at" in date_fields
        assert "analyzed_at" in date_fields
        assert "modified" in date_fields
        assert "name" not in date_fields

    def test_get_choice_fields(self):
        """Test detection of fields with choices."""
        inspector = FieldInspector(TestSampleModel)
        choice_fields = inspector.get_choice_fields()

        assert "status" in choice_fields
        assert "name" not in choice_fields

    def test_get_relation_fields(self):
        """Test detection of relationship fields."""
        inspector = FieldInspector(TestSampleModel)
        relation_fields = inspector.get_relation_fields()

        assert "parent" in relation_fields
        assert "name" not in relation_fields

    def test_get_text_fields(self):
        """Test detection of text fields."""
        inspector = FieldInspector(TestSampleModel)
        text_fields = inspector.get_text_fields()

        assert "name" in text_fields
        assert "description" in text_fields
        assert "collected_at" not in text_fields

    def test_get_boolean_fields(self):
        """Test detection of boolean fields."""
        inspector = FieldInspector(TestSampleModel)
        boolean_fields = inspector.get_boolean_fields()

        assert "is_published" in boolean_fields
        assert "name" not in boolean_fields

    def test_get_numeric_fields(self):
        """Test detection of numeric fields."""
        inspector = FieldInspector(TestSampleModel)
        numeric_fields = inspector.get_numeric_fields()

        assert "count" in numeric_fields
        assert "measurement" in numeric_fields
        assert "name" not in numeric_fields

    def test_get_file_fields(self):
        """Test detection of file/image fields."""
        inspector = FieldInspector(TestSampleModel)
        file_fields = inspector.get_file_fields()

        assert "image" in file_fields
        assert "document" in file_fields
        assert "name" not in file_fields

    def test_suggest_widget_date(self):
        """Test widget suggestion for date field."""
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("collected_at")
        assert widget == "DateInput"

    def test_suggest_widget_datetime(self):
        """Test widget suggestion for datetime field."""
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("analyzed_at")
        assert widget == "SplitDateTimeWidget"

    def test_suggest_widget_image(self):
        """Test widget suggestion for image field."""
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("image")
        assert widget == "ImageWidget"

    def test_suggest_widget_file(self):
        """Test widget suggestion for file field."""
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("document")
        assert widget == "FileInput"

    def test_suggest_widget_foreign_key(self):
        """Test widget suggestion for foreign key."""
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("parent")
        assert widget == "Select2Widget"

    def test_suggest_widget_text(self):
        """Test widget suggestion for textarea."""
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("description")
        assert widget == "Textarea"

    def test_suggest_widget_url(self):
        """Test widget suggestion for URL field."""
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("website")
        assert widget == "URLInput"

    def test_suggest_widget_email(self):
        """Test widget suggestion for email field."""
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("contact_email")
        assert widget == "EmailInput"

    def test_suggest_widget_choice(self):
        """Test widget suggestion for choice field."""
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("status")
        # Should suggest RadioSelect for few choices
        assert widget == "RadioSelect"

    def test_suggest_widget_boolean(self):
        """Test widget suggestion for boolean field."""
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("is_published")
        assert widget == "CheckboxInput"

    def test_suggest_filter_type_date(self):
        """Test filter suggestion for date field."""
        inspector = FieldInspector(TestSampleModel)
        filter_type = inspector.suggest_filter_type("collected_at")
        assert filter_type == "DateFromToRangeFilter"

    def test_suggest_filter_type_boolean(self):
        """Test filter suggestion for boolean field."""
        inspector = FieldInspector(TestSampleModel)
        filter_type = inspector.suggest_filter_type("is_published")
        assert filter_type == "BooleanFilter"

    def test_suggest_filter_type_choice(self):
        """Test filter suggestion for choice field."""
        inspector = FieldInspector(TestSampleModel)
        filter_type = inspector.suggest_filter_type("status")
        assert filter_type == "MultipleChoiceFilter"

    def test_suggest_filter_type_foreign_key(self):
        """Test filter suggestion for foreign key."""
        inspector = FieldInspector(TestSampleModel)
        filter_type = inspector.suggest_filter_type("parent")
        assert filter_type == "ModelChoiceFilter"

    def test_suggest_filter_type_numeric(self):
        """Test filter suggestion for numeric field."""
        inspector = FieldInspector(TestSampleModel)
        filter_type = inspector.suggest_filter_type("count")
        assert filter_type == "RangeFilter"

    def test_suggest_filter_type_text(self):
        """Test filter suggestion for text field."""
        inspector = FieldInspector(TestSampleModel)
        filter_type = inspector.suggest_filter_type("name")
        assert filter_type == "CharFilter"

    def test_get_default_list_fields(self):
        """Test default list fields for tables."""
        inspector = FieldInspector(TestSampleModel)
        list_fields = inspector.get_default_list_fields()

        # Should prioritize name if present
        assert "name" in list_fields

        # Should include status
        assert "status" in list_fields

        # Should not include TextField
        assert "description" not in list_fields

        # Should be a reasonable number
        assert len(list_fields) <= 5

    def test_get_default_filter_fields(self):
        """Test default filter fields."""
        inspector = FieldInspector(TestSampleModel)
        filter_fields = inspector.get_default_filter_fields()

        # Should include date fields
        assert "collected_at" in filter_fields

        # Should include choice fields
        assert "status" in filter_fields

        # Should include boolean fields
        assert "is_published" in filter_fields

        # Should include FK but not M2M
        assert "parent" in filter_fields

    def test_group_fields_for_admin(self):
        """Test field grouping for admin fieldsets."""
        inspector = FieldInspector(TestSampleModel)
        groups = inspector.group_fields_for_admin()

        # Should have created groups
        assert "Basic Information" in groups
        assert "Dates" in groups
        assert "Status & Settings" in groups

        # Check groupings
        assert "name" in groups["Basic Information"]
        assert "collected_at" in groups["Dates"]
        assert "status" in groups["Status & Settings"]

    def test_get_field_info(self):
        """Test comprehensive field information retrieval."""
        inspector = FieldInspector(TestSampleModel)

        info = inspector.get_field_info("name")
        assert info["exists"] is True
        assert info["name"] == "name"
        assert info["type"] == "CharField"
        assert info["required"] is True  # Not blank
        assert info["suggested_widget"] is None  # Default for CharField

        info = inspector.get_field_info("collected_at")
        assert info["exists"] is True
        assert info["type"] == "DateField"
        assert info["suggested_widget"] == "DateInput"
        assert info["suggested_filter"] == "DateFromToRangeFilter"

        info = inspector.get_field_info("nonexistent")
        assert info["exists"] is False
