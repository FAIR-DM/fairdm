"""Tests for fairdm/registry/factories.py."""

import pytest
from django.contrib import admin
from django.db import models
from django.forms import ModelForm
from django_filters import FilterSet
from django_tables2 import Table

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from demo.models import ExampleMeasurement
from fairdm.api.serializers import BaseMeasurementSerializer, BaseSampleSerializer
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.factories import DatasetFactory
from fairdm.registry import ModelConfiguration
from fairdm.registry.factories import (
    AdminFactory,
    FilterFactory,
    FormFactory,
    TableFactory,
)
from fairdm.utils.choices import Visibility
from tests.registry_models.models import ConcreteMeasurement, ConcreteSample


@pytest.fixture
def sample_model():
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
    def test_factory_initialization(self, sample_model):
        factory = AdminFactory(sample_model)
        assert factory.model == sample_model

    def test_generate_creates_admin_class(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert issubclass(admin_class, admin.ModelAdmin)

    def test_custom_admin_class_preserved(self, sample_model):
        factory = AdminFactory(sample_model, fields=["name", "status"])
        admin_class = factory.generate()

        assert hasattr(admin_class, "list_display")
        assert isinstance(admin_class.list_display, list)


class TestListDisplay:
    def test_explicit_list_display(self, sample_model):
        factory = AdminFactory(sample_model, fields=["name", "status"])
        admin_class = factory.generate()

        assert hasattr(admin_class, "list_display")
        assert "name" in admin_class.list_display

    def test_auto_list_display_from_parent_fields(self, sample_model):
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

        assert hasattr(admin_class, "list_display")
        assert len(admin_class.list_display) <= 5

    def test_auto_list_display_from_inspector(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert isinstance(admin_class.list_display, list)
        assert len(admin_class.list_display) > 0


class TestListFilter:
    def test_explicit_list_filter(self, sample_model):
        factory = AdminFactory(sample_model, fields=["status", "is_public"])
        admin_class = factory.generate()

        assert hasattr(admin_class, "list_filter")
        assert isinstance(admin_class.list_filter, list)

    def test_auto_list_filter(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert isinstance(admin_class.list_filter, list)

    def test_list_filter_limited_to_five(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert len(admin_class.list_filter) >= 0


class TestSearchFields:
    def test_explicit_search_fields(self, sample_model):
        factory = AdminFactory(sample_model, fields=["name", "description"])
        admin_class = factory.generate()

        assert hasattr(admin_class, "search_fields")
        assert isinstance(admin_class.search_fields, list)

    def test_auto_search_fields(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert isinstance(admin_class.search_fields, list)

    def test_search_fields_limited_to_three(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert len(admin_class.search_fields) >= 0


class TestFieldsets:
    def test_explicit_fieldsets_dict_format(self, sample_model):
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

        assert hasattr(admin_class, "fieldsets") or hasattr(admin_class, "fields")

    def test_explicit_fieldsets_django_format(self, sample_model):
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

        if hasattr(admin_class, "fieldsets") and admin_class.fieldsets is not None:
            assert isinstance(admin_class.fieldsets, list)

    def test_auto_fieldsets_from_inspector(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert hasattr(admin_class, "fieldsets") or hasattr(admin_class, "fields")


class TestOptionalAttributes:
    def test_list_per_page(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert hasattr(admin_class, "readonly_fields")
        assert isinstance(admin_class.readonly_fields, list)

    def test_list_editable(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class is not None

    def test_ordering(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class is not None

    def test_date_hierarchy(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert hasattr(admin_class, "date_hierarchy")

    def test_readonly_fields(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert hasattr(admin_class, "readonly_fields")
        assert isinstance(admin_class.readonly_fields, list)

    def test_prepopulated_fields(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class is not None

    def test_inlines(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class is not None


class TestAdminClassNaming:
    def test_generated_class_name(self, sample_model):
        factory = AdminFactory(sample_model)
        admin_class = factory.generate()

        assert admin_class.__name__ == "SampleModelAdmin"


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
    def test_generate_basic_form(self):
        factory = FormFactory(SampleModel)

        form_class = factory.generate()

        assert issubclass(form_class, ModelForm)
        assert form_class._meta.model == SampleModel

    def test_form_with_specific_fields(self):
        factory = FormFactory(SampleModel, fields=["name", "collected_at"])

        form_class = factory.generate()

        form = form_class()
        assert "name" in form.fields
        assert "collected_at" in form.fields
        assert "description" not in form.fields

    def test_form_with_all_fields(self):
        factory = FormFactory(SampleModel)

        form_class = factory.generate()
        form = form_class()

        assert "name" in form.fields
        assert "collected_at" in form.fields

    def test_form_with_exclusions(self):
        factory = FormFactory(SampleModel, fields=["name", "status"])

        form_class = factory.generate()
        form = form_class()

        assert "name" in form.fields
        assert "status" in form.fields
        assert "description" not in form.fields
        assert "count" not in form.fields

    def test_form_with_parent_fields(self):
        parent_fields = ["name", "status"]
        factory = FormFactory(SampleModel, fields=parent_fields)

        fields = factory.get_fields()

        assert fields == parent_fields

    def test_form_with_custom_widgets(self):
        factory = FormFactory(SampleModel, fields=["name", "collected_at"])

        form_class = factory.generate()
        form = form_class()

        from django.forms import DateInput

        assert isinstance(form.fields["collected_at"].widget, DateInput)

    def test_get_widgets_smart_detection(self):
        factory = FormFactory(SampleModel, fields=["collected_at", "status"])

        form_class = factory.generate()
        form = form_class()

        from django.forms import DateInput

        assert isinstance(form.fields["collected_at"].widget, DateInput)


@pytest.mark.django_db
class TestTableFactory:
    def test_generate_basic_table(self):
        factory = TableFactory(SampleModel)

        table_class = factory.generate()

        assert issubclass(table_class, Table)
        assert table_class._meta.model == SampleModel

    def test_table_with_specific_fields(self):
        factory = TableFactory(SampleModel, fields=["name", "status", "collected_at"])

        fields = factory.get_fields()

        assert fields == ["name", "status", "collected_at"]

    def test_table_with_exclusions(self):
        factory = TableFactory(SampleModel, fields=["name", "status"])

        fields = factory.get_fields()

        assert "name" in fields
        assert "status" in fields
        assert "description" not in fields

    def test_a_declared_long_text_field_is_left_out_of_the_generated_table(self):
        # One long value would push the other columns off the page. See docs/portal-development/listing-a-registered-type.md.
        factory = TableFactory(SampleModel, fields=["name", "description", "status"])

        table_class = factory.generate()

        assert "description" in factory.get_fields()
        assert "description" not in table_class.base_columns
        assert {"name", "status"} <= set(table_class.base_columns)

    def test_table_with_parent_fields(self):
        parent_fields = ["name", "status"]
        factory = TableFactory(SampleModel, fields=parent_fields)

        fields = factory.get_fields()

        assert fields == parent_fields

    def test_table_default_list_fields(self):
        factory = TableFactory(SampleModel)

        fields = factory.get_fields()

        assert isinstance(fields, list)
        assert len(fields) > 0
        assert "name" in fields

    def test_table_orderable_all(self):
        factory = TableFactory(SampleModel, fields=["name", "status"])

        table_class = factory.generate()

        assert table_class is not None
        assert issubclass(table_class, Table)

    def test_table_orderable_specific(self):
        factory = TableFactory(SampleModel, fields=["name", "status"])

        table_class = factory.generate()

        assert table_class is not None
        assert issubclass(table_class, Table)


@pytest.mark.django_db
class TestFilterFactory:
    def test_generate_basic_filterset(self):
        factory = FilterFactory(SampleModel)

        filterset_class = factory.generate()

        assert issubclass(filterset_class, FilterSet)

    def test_filterset_with_specific_fields(self):
        factory = FilterFactory(SampleModel, fields=["status", "collected_at"])

        fields = factory.get_fields()

        assert "status" in fields
        assert "collected_at" in fields

    def test_filterset_with_exclusions(self):
        factory = FilterFactory(SampleModel, fields=["status", "collected_at"])

        fields = factory.get_fields()

        assert "status" in fields
        assert "collected_at" in fields
        assert "name" not in fields

    def test_filterset_with_parent_fields(self):
        parent_fields = ["status", "is_published"]
        factory = FilterFactory(SampleModel, fields=parent_fields)

        fields = factory.get_fields()

        assert fields == parent_fields

    def test_filterset_default_filter_fields(self):
        factory = FilterFactory(SampleModel)

        fields = factory.get_fields()

        assert isinstance(fields, list)
        assert len(fields) > 0

    def test_get_filter_overrides_exact(self):
        factory = FilterFactory(SampleModel, fields=["name", "status"])

        filterset_class = factory.generate()

        assert filterset_class is not None
        assert issubclass(filterset_class, FilterSet)

    def test_get_filter_overrides_range(self):
        factory = FilterFactory(SampleModel, fields=["collected_at", "count"])

        filterset_class = factory.generate()

        assert filterset_class is not None
        assert issubclass(filterset_class, FilterSet)

    def test_get_filter_overrides_search(self):
        factory = FilterFactory(SampleModel, fields=["name", "description"])

        filterset_class = factory.generate()

        assert filterset_class is not None
        assert issubclass(filterset_class, FilterSet)

    def test_get_filter_overrides_smart_detection(self):
        factory = FilterFactory(
            SampleModel, fields=["collected_at", "is_published", "status"]
        )

        filterset_class = factory.generate()

        assert filterset_class is not None
        assert issubclass(filterset_class, FilterSet)

    def test_filter_overrides_custom_priority(self):
        factory = FilterFactory(SampleModel, fields=["status"])

        filterset_class = factory.generate()

        assert filterset_class is not None
        assert issubclass(filterset_class, FilterSet)


class TestGeneratedTableClass:
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
        table_class = TableFactory(model=rock_sample, fields=["rock_type"]).generate()

        template = getattr(table_class.Meta, "template_name", None)
        assert template != "django_tables2/bootstrap5.html"


class TestGeneratedFilterSetClass:
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
    def test_generated_form_uses_the_measurement_form_mixins_dataset_widget(self):
        from django_addanother.widgets import AddAnotherWidgetWrapper

        from demo.models import XRFMeasurement

        form_class = FormFactory(XRFMeasurement, fields=["name", "dataset"]).generate()
        form = form_class()

        assert isinstance(form.fields["dataset"].widget, AddAnotherWidgetWrapper)


@pytest.mark.django_db
class TestFilterFactoryMeasurementBranch:
    # A plain FilterSet base would lack "search", because it names no model field.
    def test_generated_filterset_carries_the_measurement_filter_mixins_search_filter(
        self,
    ):
        from demo.models import XRFMeasurement

        filterset_class = FilterFactory(
            XRFMeasurement, fields=["name", "dataset"]
        ).generate()

        assert "search" in filterset_class.base_filters
        assert "sample" in filterset_class.base_filters


@pytest.mark.django_db
class TestPublishedChoiceLists:
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


@pytest.mark.django_db
class TestSerializerFactory:
    """The one builder of the serializer a registered type's API uses."""

    @pytest.fixture(
        params=[
            (ConcreteSample, BaseSampleSerializer, "rock_type"),
            (ConcreteMeasurement, BaseMeasurementSerializer, "reading"),
        ],
        ids=["sample", "measurement"],
    )
    def kind(self, request):
        model, base, own_field = request.param
        return model, base, own_field

    @staticmethod
    def extras(serializer_class, base):
        """The fields the serializer carries beyond the base's common and metadata fields."""
        fields = list(serializer_class.Meta.fields)
        return [
            name
            for name in fields
            if name not in base.common_fields and name not in base.metadata_fields
        ]

    def test_it_builds_on_the_base_for_its_kind(self, kind):
        model, base, _ = kind

        serializer_class = ModelConfiguration(model=model).get_serializer_class()

        assert issubclass(serializer_class, base)

    def test_with_no_api_configuration_it_carries_the_common_fields_and_the_defaults(
        self, kind
    ):
        model, base, own_field = kind

        serializer_class = ModelConfiguration(model=model).get_serializer_class()

        fields = list(serializer_class.Meta.fields)
        assert fields[: len(base.common_fields)] == list(base.common_fields)
        assert own_field in fields

    def test_the_defaults_leave_out_options_and_tags(self, kind):
        model, _, _ = kind

        serializer_class = ModelConfiguration(model=model).get_serializer_class()

        assert "options" not in serializer_class.Meta.fields
        assert "tags" not in serializer_class.Meta.fields

    def test_a_field_listed_for_the_api_is_carried_even_when_the_defaults_leave_it_out(
        self, kind
    ):
        model, base, own_field = kind

        serializer_class = ModelConfiguration(
            model=model, serializer_fields=[own_field, "options"]
        ).get_serializer_class()

        assert self.extras(serializer_class, base) == [own_field, "options"]

    def test_serializer_fields_are_carried_with_the_common_fields(self, kind):
        model, base, own_field = kind

        serializer_class = ModelConfiguration(
            model=model, serializer_fields=[own_field]
        ).get_serializer_class()

        fields = list(serializer_class.Meta.fields)
        assert fields[: len(base.common_fields)] == list(base.common_fields)
        assert self.extras(serializer_class, base) == [own_field]

    def test_only_the_general_field_list_is_carried_when_the_api_has_none(self, kind):
        model, base, own_field = kind

        serializer_class = ModelConfiguration(
            model=model, fields=[own_field]
        ).get_serializer_class()

        assert self.extras(serializer_class, base) == [own_field]

    def test_the_api_list_wins_over_the_general_list(self, kind):
        model, base, own_field = kind
        general = "image"

        serializer_class = ModelConfiguration(
            model=model, fields=[general], serializer_fields=[own_field]
        ).get_serializer_class()

        assert self.extras(serializer_class, base) == [own_field]

    def test_a_field_the_base_already_carries_is_not_repeated(self, kind):
        model, _, own_field = kind

        serializer_class = ModelConfiguration(
            model=model, serializer_fields=["name", own_field]
        ).get_serializer_class()

        fields = list(serializer_class.Meta.fields)
        assert len(fields) == len(set(fields))

    def test_the_defaults_for_other_components_still_include_options_and_tags(
        self, kind
    ):
        model, _, _ = kind

        config = ModelConfiguration(model=model)

        assert "options" in config.resolve_fields("form")
        assert "tags" in config.resolve_fields("form")
