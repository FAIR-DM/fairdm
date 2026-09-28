"""Tests for fairdm/utils/inspection.py."""

import pytest
from django.db import models

from fairdm.utils.inspection import FieldInspector


class TestSampleModel(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True, null=True)

    collected_at = models.DateField()
    analyzed_at = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("archived", "Archived"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    is_published = models.BooleanField(default=False)

    count = models.IntegerField(default=0)
    measurement = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )

    image = models.ImageField(upload_to="test/", blank=True)
    document = models.FileField(upload_to="test/", blank=True)

    website = models.URLField(blank=True)
    contact_email = models.EmailField(blank=True)

    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    internal_id = models.CharField(max_length=50, editable=False)
    password = models.CharField(max_length=128)

    class Meta:
        app_label = "test_inspection"


@pytest.mark.django_db
class TestFieldInspector:
    def test_initialization(self):
        inspector = FieldInspector(TestSampleModel)
        assert inspector.model == TestSampleModel
        assert inspector._fields_cache is None
        assert inspector._field_map_cache is None

    def test_get_all_fields(self):
        inspector = FieldInspector(TestSampleModel)
        fields = inspector._get_all_fields()

        assert len(fields) > 0
        field_names = [f.name for f in fields]
        assert "name" in field_names
        assert "collected_at" in field_names
        assert "status" in field_names

    def test_get_field(self):
        inspector = FieldInspector(TestSampleModel)

        name_field = inspector.get_field("name")
        assert name_field is not None
        assert isinstance(name_field, models.CharField)

        nonexistent = inspector.get_field("nonexistent_field")
        assert nonexistent is None

    def test_should_exclude_field(self):
        inspector = FieldInspector(TestSampleModel)

        assert inspector.should_exclude_field("id")

        assert inspector.should_exclude_field("password")

        assert inspector.should_exclude_field("modified")

        assert inspector.should_exclude_field("internal_id")

        assert not inspector.should_exclude_field("name")
        assert not inspector.should_exclude_field("collected_at")

    def test_get_safe_fields(self):
        inspector = FieldInspector(TestSampleModel)
        safe_fields = inspector.get_safe_fields()

        assert "name" in safe_fields
        assert "description" in safe_fields
        assert "collected_at" in safe_fields
        assert "status" in safe_fields

        assert "id" not in safe_fields
        assert "password" not in safe_fields
        assert "modified" not in safe_fields  # auto_now
        assert "analyzed_at" not in safe_fields  # auto_now_add
        assert "internal_id" not in safe_fields  # editable=False

    def test_get_safe_fields_with_custom_exclude(self):
        inspector = FieldInspector(TestSampleModel)
        safe_fields = inspector.get_safe_fields(exclude=["name", "description"])

        assert "name" not in safe_fields
        assert "description" not in safe_fields
        assert "collected_at" in safe_fields

    def test_get_date_fields(self):
        inspector = FieldInspector(TestSampleModel)
        date_fields = inspector.get_date_fields()

        assert "collected_at" in date_fields
        assert "analyzed_at" in date_fields
        assert "modified" in date_fields
        assert "name" not in date_fields

    def test_get_choice_fields(self):
        inspector = FieldInspector(TestSampleModel)
        choice_fields = inspector.get_choice_fields()

        assert "status" in choice_fields
        assert "name" not in choice_fields

    def test_get_relation_fields(self):
        inspector = FieldInspector(TestSampleModel)
        relation_fields = inspector.get_relation_fields()

        assert "parent" in relation_fields
        assert "name" not in relation_fields

    def test_get_text_fields(self):
        inspector = FieldInspector(TestSampleModel)
        text_fields = inspector.get_text_fields()

        assert "name" in text_fields
        assert "description" in text_fields
        assert "collected_at" not in text_fields

    def test_get_boolean_fields(self):
        inspector = FieldInspector(TestSampleModel)
        boolean_fields = inspector.get_boolean_fields()

        assert "is_published" in boolean_fields
        assert "name" not in boolean_fields

    def test_get_numeric_fields(self):
        inspector = FieldInspector(TestSampleModel)
        numeric_fields = inspector.get_numeric_fields()

        assert "count" in numeric_fields
        assert "measurement" in numeric_fields
        assert "name" not in numeric_fields

    def test_get_file_fields(self):
        inspector = FieldInspector(TestSampleModel)
        file_fields = inspector.get_file_fields()

        assert "image" in file_fields
        assert "document" in file_fields
        assert "name" not in file_fields

    def test_suggest_widget_date(self):
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("collected_at")
        assert widget == "DateInput"

    def test_suggest_widget_datetime(self):
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("analyzed_at")
        assert widget == "SplitDateTimeWidget"

    def test_suggest_widget_image(self):
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("image")
        assert widget == "ImageWidget"

    def test_suggest_widget_file(self):
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("document")
        assert widget == "FileInput"

    def test_suggest_widget_foreign_key(self):
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("parent")
        assert widget == "Select2Widget"

    def test_suggest_widget_text(self):
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("description")
        assert widget == "Textarea"

    def test_suggest_widget_url(self):
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("website")
        assert widget == "URLInput"

    def test_suggest_widget_email(self):
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("contact_email")
        assert widget == "EmailInput"

    def test_suggest_widget_choice(self):
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("status")
        assert widget == "RadioSelect"

    def test_suggest_widget_boolean(self):
        inspector = FieldInspector(TestSampleModel)
        widget = inspector.suggest_widget("is_published")
        assert widget == "CheckboxInput"

    def test_suggest_filter_type_date(self):
        inspector = FieldInspector(TestSampleModel)
        filter_type = inspector.suggest_filter_type("collected_at")
        assert filter_type == "DateFromToRangeFilter"

    def test_suggest_filter_type_boolean(self):
        inspector = FieldInspector(TestSampleModel)
        filter_type = inspector.suggest_filter_type("is_published")
        assert filter_type == "BooleanFilter"

    def test_suggest_filter_type_choice(self):
        inspector = FieldInspector(TestSampleModel)
        filter_type = inspector.suggest_filter_type("status")
        assert filter_type == "MultipleChoiceFilter"

    def test_suggest_filter_type_foreign_key(self):
        inspector = FieldInspector(TestSampleModel)
        filter_type = inspector.suggest_filter_type("parent")
        assert filter_type == "ModelChoiceFilter"

    def test_suggest_filter_type_numeric(self):
        inspector = FieldInspector(TestSampleModel)
        filter_type = inspector.suggest_filter_type("count")
        assert filter_type == "RangeFilter"

    def test_suggest_filter_type_text(self):
        inspector = FieldInspector(TestSampleModel)
        filter_type = inspector.suggest_filter_type("name")
        assert filter_type == "CharFilter"

    def test_get_default_list_fields(self):
        inspector = FieldInspector(TestSampleModel)
        list_fields = inspector.get_default_list_fields()

        assert "name" in list_fields

        assert "status" in list_fields

        assert "description" not in list_fields

        assert len(list_fields) <= 5

    def test_get_default_filter_fields(self):
        inspector = FieldInspector(TestSampleModel)
        filter_fields = inspector.get_default_filter_fields()

        assert "collected_at" in filter_fields

        assert "status" in filter_fields

        assert "is_published" in filter_fields

        assert "parent" in filter_fields

    def test_group_fields_for_admin(self):
        inspector = FieldInspector(TestSampleModel)
        groups = inspector.group_fields_for_admin()

        assert "Basic Information" in groups
        assert "Dates" in groups
        assert "Status & Settings" in groups

        assert "name" in groups["Basic Information"]
        assert "collected_at" in groups["Dates"]
        assert "status" in groups["Status & Settings"]

    def test_get_field_info(self):
        inspector = FieldInspector(TestSampleModel)

        info = inspector.get_field_info("name")
        assert info["exists"] is True
        assert info["name"] == "name"
        assert info["type"] == "CharField"
        assert info["required"] is True
        assert info["suggested_widget"] is None

        info = inspector.get_field_info("collected_at")
        assert info["exists"] is True
        assert info["type"] == "DateField"
        assert info["suggested_widget"] == "DateInput"
        assert info["suggested_filter"] == "DateFromToRangeFilter"

        info = inspector.get_field_info("nonexistent")
        assert info["exists"] is False


class TestDefaultFields:
    # Two divergent copies of this rule once ran in the same request path, so the API and the admin
    # showed different default fields.
    @pytest.fixture
    def wide_model(self):
        from django.db import models as dj

        class Tag(dj.Model):
            name = dj.CharField(max_length=50)

            class Meta:
                app_label = "test_app"

        class Membership(dj.Model):
            note = dj.CharField(max_length=50)

            class Meta:
                app_label = "test_app"

        class Specimen(dj.Model):
            name = dj.CharField(max_length=100)
            created = dj.DateTimeField(auto_now_add=True)
            updated = dj.DateTimeField(auto_now=True)
            internal = dj.CharField(max_length=10, editable=False)
            password = dj.CharField(max_length=10)
            password_hint = dj.CharField(max_length=10)
            plain_tags = dj.ManyToManyField(Tag, related_name="plain")
            through_tags = dj.ManyToManyField(
                Tag, through=Membership, related_name="via"
            )

            class Meta:
                app_label = "test_app"

        return Specimen

    def test_it_includes_the_model_s_own_editable_fields(self, wide_model):
        fields = FieldInspector(wide_model).get_default_fields()
        assert "name" in fields
        assert "plain_tags" in fields

    def test_it_excludes_the_primary_key(self, wide_model):
        assert "id" not in FieldInspector(wide_model).get_default_fields()

    def test_it_excludes_automatic_timestamps(self, wide_model):
        fields = FieldInspector(wide_model).get_default_fields()
        assert "created" not in fields
        assert "updated" not in fields

    def test_it_excludes_non_editable_fields(self, wide_model):
        assert "internal" not in FieldInspector(wide_model).get_default_fields()

    def test_it_excludes_a_many_to_many_with_an_explicit_through(self, wide_model):
        assert "through_tags" not in FieldInspector(wide_model).get_default_fields()

    def test_it_excludes_password_by_exact_name_not_substring(self, wide_model):
        fields = FieldInspector(wide_model).get_default_fields()
        assert "password" not in fields
        assert "password_hint" in fields

    def test_a_pointer_suffix_is_matched_as_a_suffix(self):
        from django.db import models as dj

        class Odd(dj.Model):
            sample_ptr_note = dj.CharField(max_length=10)

            class Meta:
                app_label = "test_app"

        assert "sample_ptr_note" in FieldInspector(Odd).get_default_fields()

    def test_the_configuration_uses_the_same_implementation(self, wide_model):
        from fairdm.registry.config import ModelConfiguration

        assert (
            ModelConfiguration.get_default_fields(wide_model)
            == FieldInspector(wide_model).get_default_fields()
        )


class TestResolvePath:
    @pytest.fixture
    def linked(self):
        from django.db import models as dj

        class Owner(dj.Model):
            title = dj.CharField(max_length=50)

            class Meta:
                app_label = "test_app"

        class Item(dj.Model):
            name = dj.CharField(max_length=50)
            owner = dj.ForeignKey(Owner, on_delete=dj.CASCADE)

            class Meta:
                app_label = "test_app"

        return Item

    def test_a_single_segment_resolves(self, linked):
        assert FieldInspector(linked).resolve_path("name") == (True, None)

    def test_a_two_segment_path_resolves(self, linked):
        assert FieldInspector(linked).resolve_path("owner__title") == (True, None)

    def test_a_bad_final_segment_does_not_resolve(self, linked):
        resolves, reason = FieldInspector(linked).resolve_path("owner__nope")
        assert resolves is False
        assert reason is None

    def test_a_path_through_a_non_relation_says_so(self, linked):
        resolves, reason = FieldInspector(linked).resolve_path("name__nope")
        assert resolves is False
        assert "not a relation" in reason

    def test_close_matches_suggest_a_correction(self, linked):
        assert "name" in FieldInspector(linked).close_matches("nam")
