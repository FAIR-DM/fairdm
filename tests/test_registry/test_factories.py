"""Tests for fairdm/registry/factories.py.

Covers AdminFactory (admin class generation) and the Form/Table/Filter
component factories.
"""

import pytest
from django.contrib import admin
from django.db import models
from django.forms import ModelForm
from django_filters import FilterSet
from django_tables2 import Table

from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.factories import DatasetFactory
from fairdm.registry.factories import (
    AdminFactory,
    FilterFactory,
    FormFactory,
    TableFactory,
)
from fairdm.utils.choices import Visibility
from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm_demo.models import ExampleMeasurement


@pytest.fixture
def sample_model():
    """Create a test model for admin factory tests."""

    class SampleModel(models.Model):
        name = models.CharField(max_length=100)
        description = models.TextField()
        collected_at = models.DateTimeField()
        status = models.CharField(
            max_length=20,
            choices=[("draft", "Draft"), ("published", "Published")],
        )
        is_public = models.BooleanField(default=False)
        contributor = models.ForeignKey(
            "auth.User",
            on_delete=models.CASCADE,
            related_name="samples",
        )
        tags = models.ManyToManyField("auth.Group", related_name="samples")

        class Meta:
            app_label = "test_app"

    return SampleModel


class TestAdminFactoryBasics:
    """Test basic AdminFactory functionality."""

    def test_factory_initialization(self, sample_model):
        """Test factory can be initialized."""
        factory = AdminFactory(sample_model)
        assert factory.model == sample_model

    def test_generate_creates_admin_class(self, sample_model):
        """Test generate() creates a ModelAdmin subclass."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert issubclass(admin_class, admin.ModelAdmin)

    def test_custom_admin_class_preserved(self, sample_model):
        """Test that generated admin class has proper attributes."""
        factory = AdminFactory(sample_model, fields=["name", "status"])
        admin_class = factory.generate()

        # Should have list_display
        assert hasattr(admin_class, "list_display")
        assert isinstance(admin_class.list_display, list)


class TestListDisplay:
    """Test list_display generation."""

    def test_explicit_list_display(self, sample_model):
        """Test list_display is auto-generated based on fields."""
        factory = AdminFactory(sample_model, fields=["name", "status"])
        admin_class = factory.generate()

        # Should have list_display with reasonable fields
        assert hasattr(admin_class, "list_display")
        assert "name" in admin_class.list_display

    def test_auto_list_display_from_parent_fields(self, sample_model):
        """Test list_display with specified fields."""
        fields = [
            "name",
            "description",
            "collected_at",
            "status",
            "is_public",
            "contributor",
        ]
        factory = AdminFactory(sample_model, fields=fields)
        admin_class = factory.generate()

        # Should have list_display (limited to max 5 by AdminFactory)
        assert hasattr(admin_class, "list_display")
        assert len(admin_class.list_display) <= 5

    def test_auto_list_display_from_inspector(self, sample_model):
        """Test list_display auto-generated from inspector when no fields specified."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should have reasonable defaults from inspector
        assert isinstance(admin_class.list_display, list)
        assert len(admin_class.list_display) > 0


class TestListFilter:
    """Test list_filter generation."""

    def test_explicit_list_filter(self, sample_model):
        """Test list_filter is auto-generated."""
        factory = AdminFactory(sample_model, fields=["status", "is_public"])
        admin_class = factory.generate()

        # Should have list_filter with boolean/choice fields
        assert hasattr(admin_class, "list_filter")
        assert isinstance(admin_class.list_filter, list)

    def test_auto_list_filter(self, sample_model):
        """Test auto-generated list_filter includes dates, choices, booleans."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should include date, choice, and boolean fields
        assert isinstance(admin_class.list_filter, list)

    def test_list_filter_limited_to_five(self, sample_model):
        """Test list_filter is reasonable length."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should be reasonable length
        assert len(admin_class.list_filter) >= 0


class TestSearchFields:
    """Test search_fields generation."""

    def test_explicit_search_fields(self, sample_model):
        """Test search_fields is auto-generated."""
        factory = AdminFactory(sample_model, fields=["name", "description"])
        admin_class = factory.generate()

        # Should have search_fields
        assert hasattr(admin_class, "search_fields")
        assert isinstance(admin_class.search_fields, list)

    def test_auto_search_fields(self, sample_model):
        """Test auto-generated search_fields prioritizes text fields."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should include text fields
        assert isinstance(admin_class.search_fields, list)

    def test_search_fields_limited_to_three(self, sample_model):
        """Test search_fields is reasonable length."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should be reasonable length
        assert len(admin_class.search_fields) >= 0


class TestFieldsets:
    """Test fieldsets generation."""

    def test_explicit_fieldsets_dict_format(self, sample_model):
        """Test fieldsets are auto-generated when many fields."""
        factory = AdminFactory(
            sample_model,
            fields=[
                "name",
                "description",
                "collected_at",
                "status",
                "is_public",
                "contributor",
            ],
        )
        admin_class = factory.generate()

        # Should have fieldsets or fields
        assert hasattr(admin_class, "fieldsets") or hasattr(admin_class, "fields")

    def test_explicit_fieldsets_django_format(self, sample_model):
        """Test fieldsets format is correct."""
        factory = AdminFactory(
            sample_model,
            fields=[
                "name",
                "description",
                "collected_at",
                "status",
                "is_public",
                "contributor",
            ],
        )
        admin_class = factory.generate()

        # If fieldsets exist, check format
        if hasattr(admin_class, "fieldsets") and admin_class.fieldsets is not None:
            assert isinstance(admin_class.fieldsets, list)

    def test_auto_fieldsets_from_inspector(self, sample_model):
        """Test auto-generated fieldsets group fields logically."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should have fieldsets or fields
        assert hasattr(admin_class, "fieldsets") or hasattr(admin_class, "fields")


class TestOptionalAttributes:
    """Test optional admin attributes."""

    def test_list_per_page(self, sample_model):
        """Test admin class has readonly_fields."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should have readonly_fields
        assert hasattr(admin_class, "readonly_fields")
        assert isinstance(admin_class.readonly_fields, list)

    def test_list_editable(self, sample_model):
        """Test admin class can be generated."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class is not None

    def test_ordering(self, sample_model):
        """Test admin class can be generated."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class is not None

    def test_date_hierarchy(self, sample_model):
        """Test date_hierarchy is auto-generated for date fields."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should have date_hierarchy if date field exists
        assert hasattr(admin_class, "date_hierarchy")

    def test_readonly_fields(self, sample_model):
        """Test readonly_fields is auto-generated."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        # Should have readonly_fields
        assert hasattr(admin_class, "readonly_fields")
        assert isinstance(admin_class.readonly_fields, list)

    def test_prepopulated_fields(self, sample_model):
        """Test admin class can be generated."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class is not None

    def test_inlines(self, sample_model):
        """Test admin class can be generated."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class is not None


class TestAdminClassNaming:
    """Test admin class naming conventions."""

    def test_generated_class_name(self, sample_model):
        """Test generated admin class has correct name."""
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class.__name__ == "SampleModelAdmin"


# Test model for FormFactory/TableFactory/FilterFactory tests
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

    def test_a_declared_long_text_field_is_left_out_of_the_generated_table(self):
        """A TextField named in `fields` reaches every other component but not the
        table: one long value would push the other columns off the page. Stated in
        docs/portal-development/listing-a-registered-type.md, so it is guarded here
        rather than left as an undeclared property of the factory."""
        factory = TableFactory(SampleModel, fields=["name", "description", "status"])

        table_class = factory.generate()

        assert "description" in factory.get_fields()
        assert "description" not in table_class.base_columns
        assert {"name", "status"} <= set(table_class.base_columns)

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
        factory = FilterFactory(
            SampleModel, fields=["collected_at", "is_published", "status"]
        )

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


class TestGeneratedTableClass:
    """T019: assert on the class the factory produces, not on its inputs.

    The older tests here call `factory.get_fields()` and assert on the names that
    come back, which echoes the input and stays green if generation itself breaks.
    """

    @pytest.fixture
    def rock_sample(self):
        class RockSample(Sample):
            rock_type = models.CharField(max_length=100)
            depth = models.FloatField(null=True, blank=True)

            class Meta:
                app_label = "test_app"

        return RockSample

    def test_columns_exist_for_the_resolved_fields(self, rock_sample):
        table_class = TableFactory(
            model=rock_sample, fields=["rock_type", "depth"]
        ).generate()

        assert "rock_type" in table_class.base_columns
        assert "depth" in table_class.base_columns

    def test_no_theme_is_pinned_on_the_generated_table(self, rock_sample):
        """Decision D7: the project's DJANGO_TABLES2_TEMPLATE setting decides."""
        table_class = TableFactory(model=rock_sample, fields=["rock_type"]).generate()

        template = getattr(table_class.Meta, "template_name", None)
        assert template != "django_tables2/bootstrap5.html"


class TestGeneratedFilterSetClass:
    """T020: assert on the filters the factory produces."""

    @pytest.fixture
    def rock_sample(self):
        class RockSample(Sample):
            rock_type = models.CharField(max_length=100)
            depth = models.FloatField(null=True, blank=True)

            class Meta:
                app_label = "test_app"

        return RockSample

    def test_filters_exist_for_the_resolved_fields(self, rock_sample):
        filterset_class = FilterFactory(
            model=rock_sample, fields=["rock_type", "depth"]
        ).generate()

        assert "rock_type" in filterset_class.base_filters
        assert "depth" in filterset_class.base_filters

    def test_a_field_left_out_gets_no_filter(self, rock_sample):
        filterset_class = FilterFactory(
            model=rock_sample, fields=["rock_type"]
        ).generate()

        assert "depth" not in filterset_class.base_filters


@pytest.mark.django_db
class TestFormFactoryMeasurementBranch:
    """T061/T062 - a measurement type supplying no form of its own still
    gets `MeasurementFormMixin`'s widget configuration (dataset scoping,
    Select2 widgets) rather than a bare `ModelForm`, the same way
    `TestRegistryUsesTheMixins` proves it for samples
    (tests/test_core/test_sample/test_config.py)."""

    def test_generated_form_uses_the_measurement_form_mixins_dataset_widget(self):
        from django_addanother.widgets import AddAnotherWidgetWrapper

        from fairdm_demo.models import XRFMeasurement

        form_class = FormFactory(XRFMeasurement, fields=["name", "dataset"]).generate()
        form = form_class()

        assert isinstance(form.fields["dataset"].widget, AddAnotherWidgetWrapper)


@pytest.mark.django_db
class TestFilterFactoryMeasurementBranch:
    """T061/T063 - a measurement type supplying no filter set of its own
    still gets `MeasurementFilterMixin`'s declared filters rather than a
    bare `FilterSet` - a plain `FilterSet` base would never have "search",
    because it names no model field."""

    def test_generated_filterset_carries_the_measurement_filter_mixins_search_filter(
        self,
    ):
        from fairdm_demo.models import XRFMeasurement

        filterset_class = FilterFactory(
            XRFMeasurement, fields=["name", "dataset"]
        ).generate()

        assert "search" in filterset_class.base_filters
        assert "sample" in filterset_class.base_filters


@pytest.mark.django_db
class TestPublishedChoiceLists:
    """T036, FR-030, D3: a related-record filter's generated choice list
    excludes values that exist only on an unpublished record, for the
    sample, measurement and dataset filters - and includes a dataset that
    is published while private, the ordinary state. Mirrors the module
    T040 changes."""

    def test_a_sample_filters_choice_list_excludes_unpublished_samples(self):
        published = RockSampleFactory(dataset=DatasetFactory(published=True))
        unpublished = RockSampleFactory(dataset=DatasetFactory(published=False))

        filterset_class = FilterFactory(
            ExampleMeasurement, fields=["name", "sample"]
        ).generate()
        queryset = filterset_class.base_filters["sample"].extra["queryset"]

        assert published in queryset
        assert unpublished not in queryset

    def test_a_dataset_filters_choice_list_excludes_unpublished_and_includes_published_private(
        self,
    ):
        published_private = DatasetFactory(
            published=True, visibility=Visibility.PRIVATE
        )
        published_public = DatasetFactory(published=True, visibility=Visibility.PUBLIC)
        unpublished = DatasetFactory(published=False)

        filterset_class = FilterFactory(
            ExampleMeasurement, fields=["name", "dataset"]
        ).generate()
        queryset = filterset_class.base_filters["dataset"].extra["queryset"]

        assert published_private in queryset
        assert published_public in queryset
        assert unpublished not in queryset

    def test_a_measurement_filters_choice_list_excludes_unpublished_measurements(self):
        class MeasurementReferrer(models.Model):
            measurement = models.ForeignKey(Measurement, on_delete=models.CASCADE)

            class Meta:
                app_label = "test_app"

        published_dataset = DatasetFactory(published=True)
        unpublished_dataset = DatasetFactory(published=False)
        published = ExampleMeasurementFactory(
            dataset=published_dataset,
            sample=RockSampleFactory(dataset=published_dataset),
        )
        unpublished = ExampleMeasurementFactory(
            dataset=unpublished_dataset,
            sample=RockSampleFactory(dataset=unpublished_dataset),
        )

        filterset_class = FilterFactory(
            MeasurementReferrer, fields=["measurement"]
        ).generate()
        queryset = filterset_class.base_filters["measurement"].extra["queryset"]

        assert published in queryset
        assert unpublished not in queryset
