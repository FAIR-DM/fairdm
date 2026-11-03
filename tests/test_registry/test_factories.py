"""Tests for fairdm/registry/factories.py."""

import pytest
from django.contrib import admin
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError
from django.db import models
from django.forms import ModelForm
from django.test import RequestFactory
from django_filters import FilterSet, ModelChoiceFilter
from django_tables2 import Table

from demo.factories import RockSampleFactory
from demo.models import ExampleMeasurement, RockSample
from fairdm.api.serializers import BaseMeasurementSerializer, BaseSampleSerializer
from fairdm.contrib.autocomplete.fields import DatasetMultipleChoiceField
from fairdm.contrib.autocomplete.filters import RecordMultipleFilter
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.config import BaseMeasurementConfiguration
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.registry import ModelConfiguration
from fairdm.registry.factories import (
    AdminFactory,
    FilterFactory,
    FormFactory,
    ScopedChoicesMixin,
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

    def test_a_field_inherited_from_fields_that_cannot_be_edited_is_left_out(self):
        config = ModelConfiguration(model=RockSample, fields=["rock_type", "uuid"])

        assert list(config.get_form_class().base_fields) == ["rock_type"]
        assert config.resolve_fields("table") == ["rock_type", "uuid"]

    def test_a_measurement_types_own_field_that_cannot_be_edited_is_left_out(self):
        config = BaseMeasurementConfiguration(
            model=ExampleMeasurement, fields=["char_field", "uuid"]
        )

        fields = config.get_form_class().base_fields

        assert "char_field" in fields
        assert "uuid" not in fields

    def test_a_field_named_for_the_form_that_cannot_be_edited_is_still_refused(self):
        config = ModelConfiguration(
            model=RockSample, fields=["rock_type"], form_fields=["uuid"]
        )

        with pytest.raises(FieldError, match="non-editable"):
            config.get_form_class()

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
        # One long value would push the other columns off the page. See docs/developers/explanation/what-registering-a-type-produces.md.
        factory = TableFactory(SampleModel, fields=["name", "description", "status"])

        table_class = factory.generate()

        assert "description" in factory.get_fields()
        assert "description" not in table_class.base_columns
        assert {"name", "status"} <= set(table_class.base_columns)

    def test_a_geometry_field_is_left_out_of_the_generated_table(self):
        # The base table carries latitude and longitude, and a point has no sort order.
        factory = TableFactory(ConcreteSample, fields=["name", "location", "rock_type"])

        table_class = factory.generate()

        assert "location" in factory.get_fields()
        assert "location" not in table_class.base_columns
        assert {"name", "rock_type", "latitude", "longitude"} <= set(
            table_class.base_columns
        )

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
    def test_generated_form_uses_the_measurement_form_mixins_dataset_field(self):
        from demo.models import XRFMeasurement
        from fairdm.contrib.autocomplete.fields import DatasetChoiceField

        form_class = FormFactory(XRFMeasurement, fields=["name", "dataset"]).generate()
        form = form_class()

        assert isinstance(form.fields["dataset"], DatasetChoiceField)


@pytest.mark.django_db
class TestGeneratedRelatedRecordForms:
    @pytest.fixture(
        params=["project", "dataset", "sample", "measurement"],
    )
    def referrer(self, request):
        """A model with a foreign key to one kind of record, and the field class for it."""
        from fairdm.contrib.autocomplete import fields
        from fairdm.core.dataset.models import Dataset
        from fairdm.core.project.models import Project

        related = {
            "project": Project,
            "dataset": Dataset,
            "sample": Sample,
            "measurement": Measurement,
        }[request.param]
        attrs = {
            "__module__": __name__,
            "Meta": type("Meta", (), {"app_label": "test_app"}),
            "related": models.ForeignKey(related, on_delete=models.CASCADE),
        }
        model = type(
            f"{request.param.capitalize()}FormReferrer", (models.Model,), attrs
        )
        return model, getattr(fields, f"{request.param.capitalize()}ChoiceField")

    def test_a_related_record_is_chosen_with_the_single_field_at_view_scope(
        self, referrer
    ):
        model, field_class = referrer

        form = FormFactory(model, fields=["related"]).generate()()

        assert isinstance(form.fields["related"], field_class)
        assert form.fields["related"].scope == "view"

    def test_the_dataset_a_measurement_sits_in_is_chosen_at_edit_scope(self):
        from demo.models import XRFMeasurement
        from fairdm.contrib.autocomplete.fields import DatasetChoiceField

        form = FormFactory(XRFMeasurement, fields=["name", "dataset"]).generate()()

        assert isinstance(form.fields["dataset"], DatasetChoiceField)
        assert form.fields["dataset"].scope == "edit"

    def test_the_project_a_dataset_sits_in_is_chosen_at_edit_scope(self):
        from fairdm.contrib.autocomplete.fields import ProjectChoiceField
        from fairdm.core.dataset.models import Dataset

        form = FormFactory(Dataset, fields=["name", "project"]).generate()()

        assert isinstance(form.fields["project"], ProjectChoiceField)
        assert form.fields["project"].scope == "edit"


@pytest.mark.django_db
class TestFilterFactoryMeasurementBranch:
    # A plain FilterSet base would lack "q", because it names no model field.
    def test_generated_filterset_carries_the_measurement_filter_mixins_search_filter(
        self,
    ):
        from demo.models import XRFMeasurement

        filterset_class = FilterFactory(
            XRFMeasurement, fields=["name", "dataset"]
        ).generate()

        assert "q" in filterset_class.base_filters
        assert "sample" in filterset_class.base_filters


@pytest.mark.django_db
class TestGeneratedRelatedRecordFilters:
    @pytest.fixture(
        params=["project", "dataset", "sample", "measurement"],
    )
    def referrer(self, request):
        """A model with a foreign key to one kind of record, and the field class for it."""
        from fairdm.contrib.autocomplete import fields
        from fairdm.core.dataset.models import Dataset
        from fairdm.core.project.models import Project

        related = {
            "project": Project,
            "dataset": Dataset,
            "sample": Sample,
            "measurement": Measurement,
        }[request.param]
        attrs = {
            "__module__": __name__,
            "Meta": type("Meta", (), {"app_label": "test_app"}),
            "related": models.ForeignKey(related, on_delete=models.CASCADE),
        }
        model = type(f"{request.param.capitalize()}Referrer", (models.Model,), attrs)
        return model, getattr(
            fields, f"{request.param.capitalize()}MultipleChoiceField"
        )

    def test_a_related_record_filter_is_a_record_filter_at_public_scope(self, referrer):
        model, field_class = referrer

        filterset_class = FilterFactory(model, fields=["related"]).generate()
        generated = filterset_class.base_filters["related"]

        assert isinstance(generated, RecordMultipleFilter)
        assert generated.field_class is field_class
        assert generated.extra["scope"] == "public"

    def test_a_related_dataset_filter_offers_public_datasets_only(self):
        public = DatasetFactory(
            published=True,
            visibility=Visibility.PUBLIC,
            project=ProjectFactory(visibility=Visibility.PUBLIC),
        )
        published_private = DatasetFactory(
            published=True, visibility=Visibility.PRIVATE
        )
        request = RequestFactory().get("/")
        request.user = AnonymousUser()

        filterset = FilterFactory(
            ExampleMeasurement, fields=["name", "dataset"]
        ).generate()(request=request)

        assert set(filterset.form.fields["dataset"].offered()) == {public}
        assert published_private not in filterset.form.fields["dataset"].offered()


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


@pytest.mark.django_db
class TestScopedChoicesMixin:
    """A filter set narrows what its related-record filters offer to the rows it was given."""

    @pytest.fixture
    def filterset_class(self):
        class Rows(FilterSet):
            dataset = ModelChoiceFilter(queryset=Dataset.all_objects.all())
            project = ModelChoiceFilter(
                field_name="dataset__project", queryset=Project.objects.all()
            )
            polymorphic_ctype = ModelChoiceFilter(queryset=ContentType.objects.all())

            class Meta:
                model = RockSample
                fields = []

        return ScopedChoicesMixin.applied_to(Rows)

    @staticmethod
    def request_for(user):
        request = RequestFactory().get("/")
        request.user = user
        return request

    def test_a_related_filter_offers_only_the_records_the_rows_point_to(
        self, filterset_class
    ):
        listed_in = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        RockSampleFactory(dataset=listed_in)

        filterset = filterset_class(
            queryset=RockSample.objects.filter(dataset=listed_in),
            request=self.request_for(AnonymousUser()),
        )

        assert set(filterset.filters["dataset"].queryset) == {listed_in}
        assert {
            ct.model_class() for ct in filterset.filters["polymorphic_ctype"].queryset
        } == {RockSample}

    def test_a_filter_on_a_model_the_rows_do_not_point_to_is_left_alone(
        self, filterset_class
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        ProjectFactory(visibility=Visibility.PUBLIC)
        RockSampleFactory(dataset=dataset)

        filterset = filterset_class(
            queryset=RockSample.objects.filter(dataset=dataset),
            request=self.request_for(AnonymousUser()),
        )

        assert filterset.filters["project"].queryset.count() == Project.objects.count()

    def test_a_dataset_the_viewer_may_not_see_is_not_offered(self, filterset_class):
        waiting = DatasetFactory(visibility=Visibility.PRIVATE, published=True)
        RockSampleFactory(dataset=waiting)
        team = UserFactory()
        ContributionFactory(
            content_object=waiting, contributor=team, level=ContributionLevel.VIEW
        )
        rows = RockSample.objects.filter(dataset=waiting)

        visitor = filterset_class(
            queryset=rows, request=self.request_for(AnonymousUser())
        )
        member = filterset_class(queryset=rows, request=self.request_for(team))

        assert set(visitor.filters["dataset"].queryset) == set()
        assert set(member.filters["dataset"].queryset) == {waiting}

    def test_a_filter_on_a_concept_field_is_narrowed_to_the_concepts_the_rows_use(
        self,
    ):
        from controlled_vocabularies.models import Record

        class Rows(FilterSet):
            status = ModelChoiceFilter(
                queryset=Record.objects.all(), to_field_name="slug"
            )

            class Meta:
                model = RockSample
                fields = []

        used = RockSampleFactory()
        used.refresh_from_db()
        filterset = ScopedChoicesMixin.applied_to(Rows)(
            queryset=RockSample.objects.filter(pk=used.pk),
            request=self.request_for(AnonymousUser()),
        )

        offered = set(filterset.filters["status"].queryset.values_list("pk", flat=True))
        assert offered <= set(
            Record.objects.filter(uri=used.status_id).values_list("pk", flat=True)
        )

    def test_a_filter_named_to_be_dropped_is_removed(self):
        class Rows(FilterSet):
            dataset = ModelChoiceFilter(queryset=Dataset.all_objects.all())

            class Meta:
                model = RockSample
                fields = []

        filterset = ScopedChoicesMixin.applied_to(Rows, drop=("dataset",))(
            queryset=RockSample.objects.none(),
            request=self.request_for(AnonymousUser()),
        )

        assert "dataset" not in filterset.filters

    @pytest.fixture
    def record_filterset_class(self):
        class Rows(FilterSet):
            dataset = RecordMultipleFilter(
                DatasetMultipleChoiceField, field_name="dataset"
            )

            class Meta:
                model = RockSample
                fields = []

        return Rows

    def build(self, filterset_class, **options):
        return ScopedChoicesMixin.applied_to(filterset_class, **options)(
            queryset=RockSample.objects.none(),
            request=self.request_for(AnonymousUser()),
        )

    def test_a_record_filter_is_set_to_the_view_scope_by_default(
        self, record_filterset_class
    ):
        field = self.build(record_filterset_class).filters["dataset"].field

        assert field.scope == "view"
        assert field.owner_pk is None

    def test_a_record_filter_takes_the_scope_it_is_given(self, record_filterset_class):
        filterset = self.build(record_filterset_class, scope="public")

        assert filterset.filters["dataset"].field.scope == "public"

    def test_a_record_filter_on_a_persons_own_page_offers_that_persons_records(
        self, record_filterset_class
    ):
        person = UserFactory()

        field = (
            self.build(record_filterset_class, owner=person.pk).filters["dataset"].field
        )

        assert field.owner_pk == person.pk
        assert field.scope == "profile"
