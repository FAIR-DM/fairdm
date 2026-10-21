"""Tests for Measurement filtering and search functionality."""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory

from demo.factories import RockSampleFactory
from demo.models import ICP_MS_Measurement, XRFMeasurement
from fairdm.contrib.autocomplete.filters import RecordMultipleFilter
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.measurement.filters import MeasurementFilter, MeasurementFilterMixin
from fairdm.core.measurement.models import (
    Measurement,
    MeasurementDate,
    MeasurementDescription,
)
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.registry import registry
from fairdm.utils.choices import Visibility
from tests.registry_models.models import ConcreteMeasurement, ConcreteSample

User = get_user_model()

pytestmark = pytest.mark.django_db


def _request_for(user):
    """A minimal request carrying an authenticated user."""
    request = RequestFactory().get("/")
    request.user = user
    return request


def _public_dataset():
    """A dataset a visitor can see, with the project it sits in."""
    return DatasetFactory(
        visibility=Visibility.PUBLIC,
        published=True,
        project=ProjectFactory(visibility=Visibility.PUBLIC),
    )


def _measurement(dataset, sample=None, **kwargs):
    return XRFMeasurement.objects.create(
        name=kwargs.pop("name", "XRF"),
        dataset=dataset,
        sample=sample or RockSampleFactory(dataset=dataset),
        element="Fe",
        concentration_ppm=25.5,
        **kwargs,
    )


class TestMeasurementFilterRecordFilters:
    def test_the_dataset_and_sample_filters_are_record_filters_at_public_scope(self):
        filters = MeasurementFilter().filters

        for name in ("dataset", "sample"):
            assert isinstance(filters[name], RecordMultipleFilter)
            assert filters[name].field.scope == "public"

    def test_a_signed_in_editor_is_offered_the_same_datasets_as_a_visitor(self):
        public = _public_dataset()
        editor = UserFactory()
        mine = DatasetFactory()
        ContributionFactory(
            content_object=mine, contributor=editor, level=ContributionLevel.EDIT
        )

        offered = set(
            MeasurementFilter(request=_request_for(editor))
            .form.fields["dataset"]
            .offered()
        )

        assert offered == {public}


class TestMeasurementFilterDatasetFiltering:
    def test_filter_by_dataset(self):
        dataset1, dataset2 = _public_dataset(), _public_dataset()
        measurement1 = _measurement(dataset1)
        measurement2 = _measurement(dataset2)

        filterset = MeasurementFilter(
            data={"dataset": [dataset1.id]},
            queryset=XRFMeasurement.objects.all(),
            request=_request_for(AnonymousUser()),
        )
        assert filterset.is_valid(), filterset.errors
        assert measurement1 in filterset.qs
        assert measurement2 not in filterset.qs

    def test_two_ticked_datasets_narrow_the_list_to_either(self):
        dataset1, dataset2, dataset3 = (_public_dataset() for _ in range(3))
        wanted = {_measurement(dataset1), _measurement(dataset2)}
        _measurement(dataset3)

        filterset = MeasurementFilter(
            data={"dataset": [dataset1.id, dataset2.id]},
            queryset=XRFMeasurement.objects.all(),
            request=_request_for(AnonymousUser()),
        )

        assert filterset.is_valid(), filterset.errors
        assert set(filterset.qs) == wanted


class TestMeasurementFilterSampleFiltering:
    def test_filter_by_sample(self):
        dataset = _public_dataset()
        sample1 = RockSampleFactory(dataset=dataset, name="Sample 1")
        sample2 = RockSampleFactory(dataset=dataset, name="Sample 2")
        measurement1 = _measurement(dataset, sample1)
        measurement2 = _measurement(dataset, sample2)

        filterset = MeasurementFilter(
            data={"sample": [sample1.id]},
            queryset=XRFMeasurement.objects.all(),
            request=_request_for(AnonymousUser()),
        )
        assert filterset.is_valid(), filterset.errors
        assert measurement1 in filterset.qs
        assert measurement2 not in filterset.qs

    def test_a_sample_of_a_private_dataset_is_refused(self):
        private = DatasetFactory(published=True)
        sample = RockSampleFactory(dataset=private)

        filterset = MeasurementFilter(
            data={"sample": [sample.id]},
            queryset=XRFMeasurement.objects.all(),
            request=_request_for(AnonymousUser()),
        )

        assert not filterset.is_valid()
        assert "sample" in filterset.errors


class TestMeasurementFilterPolymorphicTypeFiltering:
    def test_filter_by_polymorphic_type(self, user, project, dataset):
        from django.contrib.contenttypes.models import ContentType

        sample = RockSampleFactory(dataset=dataset)

        xrf_measurement = XRFMeasurement.objects.create(
            name="XRF Measurement",
            dataset=dataset,
            sample=sample,
            element="Fe",
            concentration_ppm=25.5,
        )
        icpms_measurement = ICP_MS_Measurement.objects.create(
            name="ICP-MS Measurement",
            dataset=dataset,
            sample=sample,
            isotope="207Pb",
            counts_per_second=1000.0,
        )

        xrf_ct = ContentType.objects.get_for_model(XRFMeasurement)
        icpms_ct = ContentType.objects.get_for_model(ICP_MS_Measurement)

        from fairdm.core.measurement.models import Measurement

        filterset = MeasurementFilter(
            data={"polymorphic_ctype": xrf_ct.id}, queryset=Measurement.objects.all()
        )
        assert filterset.is_valid()
        assert xrf_measurement in filterset.qs
        assert icpms_measurement not in filterset.qs

        filterset = MeasurementFilter(
            data={"polymorphic_ctype": icpms_ct.id}, queryset=Measurement.objects.all()
        )
        assert filterset.is_valid()
        assert icpms_measurement in filterset.qs
        assert xrf_measurement not in filterset.qs


class TestMeasurementFilterPolymorphicTypeChoices:
    def test_choices_are_exactly_the_registered_measurement_types(self, clean_registry):
        registry.register(ConcreteMeasurement)
        registry.register(ConcreteSample)

        filterset = MeasurementFilter()
        offered = set(filterset.filters["polymorphic_ctype"].queryset)

        assert offered == {
            ContentType.objects.get_for_model(model) for model in registry.measurements
        }
        assert ContentType.objects.get_for_model(XRFMeasurement) in offered
        assert ContentType.objects.get_for_model(ICP_MS_Measurement) in offered
        assert ContentType.objects.get_for_model(ConcreteMeasurement) in offered
        assert ContentType.objects.get_for_model(Measurement) not in offered
        assert ContentType.objects.get_for_model(ConcreteSample) not in offered

    def test_narrowing_by_a_registered_type_leaves_only_that_type(
        self, clean_registry, dataset
    ):
        registry.register(ConcreteMeasurement)
        sample = RockSampleFactory(dataset=dataset)

        concrete_measurement = ConcreteMeasurement.objects.create(
            name="Concrete Measurement",
            dataset=dataset,
            sample=sample,
            reading=1.0,
        )
        xrf_measurement = XRFMeasurement.objects.create(
            name="XRF Measurement",
            dataset=dataset,
            sample=sample,
            element="Fe",
            concentration_ppm=25.5,
        )

        concrete_ct = ContentType.objects.get_for_model(ConcreteMeasurement)
        filterset = MeasurementFilter(
            data={"polymorphic_ctype": concrete_ct.id},
            queryset=Measurement.objects.all(),
        )
        assert filterset.is_valid()
        assert concrete_measurement in filterset.qs
        assert xrf_measurement not in filterset.qs


class TestMeasurementFilterSearchFunctionality:
    def test_search_by_name_and_uuid(self, user, project, dataset):
        sample = RockSampleFactory(dataset=dataset)

        measurement1 = XRFMeasurement.objects.create(
            name="Iron Analysis XRF-001",
            dataset=dataset,
            sample=sample,
            element="Fe",
            concentration_ppm=25.5,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="Copper Sample Test",
            dataset=dataset,
            sample=sample,
            element="Cu",
            concentration_ppm=15.3,
        )
        measurement3 = XRFMeasurement.objects.create(
            name="Zinc Composition",
            dataset=dataset,
            sample=sample,
            element="Zn",
            concentration_ppm=8.7,
        )

        filterset = MeasurementFilter(
            data={"q": "Iron"}, queryset=XRFMeasurement.objects.all()
        )
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 not in filterset.qs
        assert measurement3 not in filterset.qs

        uuid_str = str(measurement2.uuid)[:8]
        filterset = MeasurementFilter(
            data={"q": uuid_str}, queryset=XRFMeasurement.objects.all()
        )
        assert filterset.is_valid()
        assert measurement2 in filterset.qs


class TestMeasurementFilterCrossRelationshipFiltering:
    def test_filter_by_description_text(self, user, project, dataset):
        dataset = _public_dataset()
        sample = RockSampleFactory(dataset=dataset)

        measurement1 = XRFMeasurement.objects.create(
            name="XRF-001",
            dataset=dataset,
            sample=sample,
            element="Fe",
            concentration_ppm=25.5,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="XRF-002",
            dataset=dataset,
            sample=sample,
            element="Cu",
            concentration_ppm=15.3,
        )

        MeasurementDescription.objects.create(
            related=measurement1,
            type="MeasurementSetup",
            value="High precision analysis using XRF",
        )
        MeasurementDescription.objects.create(
            related=measurement2,
            type="MeasurementSetup",
            value="Standard quality measurement",
        )

        filterset = MeasurementFilter(
            data={"description": "precision"},
            queryset=XRFMeasurement.objects.all(),
        )
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 not in filterset.qs

    def test_filter_by_date_range(self, user, project, dataset):

        dataset = _public_dataset()
        sample = RockSampleFactory(dataset=dataset)

        measurement1 = XRFMeasurement.objects.create(
            name="XRF-001",
            dataset=dataset,
            sample=sample,
            element="Fe",
            concentration_ppm=25.5,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="XRF-002",
            dataset=dataset,
            sample=sample,
            element="Cu",
            concentration_ppm=15.3,
        )
        measurement3 = XRFMeasurement.objects.create(
            name="XRF-003",
            dataset=dataset,
            sample=sample,
            element="Zn",
            concentration_ppm=8.7,
        )
        # A year-and-month-only date, well clear of the range boundaries used
        # below so its comparison is unambiguous at month precision.
        measurement_year_month = XRFMeasurement.objects.create(
            name="XRF-004",
            dataset=dataset,
            sample=sample,
            element="Pb",
            concentration_ppm=3.1,
        )
        # A year-only date, well clear of the range boundaries used below so
        # its comparison is unambiguous at year precision.
        measurement_year_only = XRFMeasurement.objects.create(
            name="XRF-005",
            dataset=dataset,
            sample=sample,
            element="Ni",
            concentration_ppm=6.2,
        )

        # Add dates ("Setup" is a real member of the Measurement date
        # vocabulary; PartialDateField accepts a string at any precision)
        MeasurementDate.objects.create(
            related=measurement1, type="Setup", value="2024-01-15"
        )
        MeasurementDate.objects.create(
            related=measurement2, type="Setup", value="2024-02-20"
        )
        MeasurementDate.objects.create(
            related=measurement3, type="Setup", value="2024-03-10"
        )
        MeasurementDate.objects.create(
            related=measurement_year_month, type="Setup", value="2024-06"
        )
        MeasurementDate.objects.create(
            related=measurement_year_only, type="Setup", value="2023"
        )

        filterset = MeasurementFilter(
            data={"date_after": "2024-02-01"},
            queryset=XRFMeasurement.objects.all(),
        )
        assert filterset.is_valid()
        assert measurement1 not in filterset.qs
        assert measurement2 in filterset.qs
        assert measurement3 in filterset.qs
        # June 2024 is after the February threshold, whatever day within
        # February is compared against.
        assert measurement_year_month in filterset.qs
        assert measurement_year_only not in filterset.qs

        filterset = MeasurementFilter(
            data={"date_before": "2024-02-28"},
            queryset=XRFMeasurement.objects.all(),
        )
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 in filterset.qs
        assert measurement3 not in filterset.qs
        # June 2024 is after the February threshold.
        assert measurement_year_month not in filterset.qs
        assert measurement_year_only in filterset.qs


class TestMeasurementFilterDateRangeValidation:
    @pytest.mark.parametrize("value", ["not-a-date", "2024-13-45"])
    # An invalid date string must be a form error, not a ValidationError raised when
    # the queryset is evaluated.
    def test_invalid_date_string_is_a_form_error_not_a_query_time_exception(
        self, value
    ):
        filterset = MeasurementFilter(
            data={"date_after": value}, queryset=Measurement.objects.all()
        )

        assert filterset.is_valid() is False
        assert "date_after" in filterset.errors

        list(filterset.qs)

    def test_empty_date_string_is_valid(self):
        filterset = MeasurementFilter(
            data={"date_after": ""}, queryset=Measurement.objects.all()
        )

        assert filterset.is_valid()


class TestMeasurementFilterCombinedFilters:
    def test_combined_filters_dataset_and_sample(self):
        dataset1, dataset2 = _public_dataset(), _public_dataset()

        sample1 = RockSampleFactory(dataset=dataset1, name="Sample 1")
        sample2 = RockSampleFactory(dataset=dataset1, name="Sample 2")

        measurement_both = XRFMeasurement.objects.create(
            name="XRF-both",
            dataset=dataset1,
            sample=sample1,
            element="Fe",
            concentration_ppm=25.5,
        )
        measurement_wrong_dataset = XRFMeasurement.objects.create(
            name="XRF-wrong-dataset",
            dataset=dataset2,
            sample=sample1,
            element="Cu",
            concentration_ppm=15.3,
        )
        measurement_wrong_sample = XRFMeasurement.objects.create(
            name="XRF-wrong-sample",
            dataset=dataset1,
            sample=sample2,
            element="Zn",
            concentration_ppm=8.7,
        )

        filterset = MeasurementFilter(
            data={"dataset": [dataset1.id], "sample": [sample1.id]},
            queryset=XRFMeasurement.objects.all(),
            request=_request_for(AnonymousUser()),
        )
        assert filterset.is_valid()
        assert measurement_both in filterset.qs
        assert measurement_wrong_dataset not in filterset.qs
        assert measurement_wrong_sample not in filterset.qs


class TestMeasurementFilterMixinInheritance:
    def test_inheriting_filter_set_carries_the_mixins_declared_filters(self):
        filterset = MeasurementFilter()

        assert "dataset" in filterset.filters
        assert "sample" in filterset.filters
        assert "polymorphic_ctype" in filterset.filters
        assert "q" in filterset.filters
        assert "description" in filterset.filters
        assert "date_after" in filterset.filters
        assert "date_before" in filterset.filters

    def test_mixin_declares_all_six(self):
        assert set(MeasurementFilterMixin.declared_filters) == {
            "dataset",
            "sample",
            "polymorphic_ctype",
            "q",
            "description",
            "date_after",
            "date_before",
        }


class TestMeasurementFilterMixinUsage:
    def test_custom_filter_inherits_from_mixin(self):
        import django_filters

        from fairdm.core.measurement.filters import MeasurementFilterMixin

        class CustomXRFFilter(MeasurementFilterMixin, django_filters.FilterSet):
            element = django_filters.CharFilter(
                field_name="element", lookup_expr="icontains"
            )

            class Meta(MeasurementFilterMixin.Meta):
                model = XRFMeasurement
                fields = [*MeasurementFilterMixin.Meta.fields, "element"]

        dataset = _public_dataset()
        sample = RockSampleFactory(dataset=dataset)

        measurement1 = XRFMeasurement.objects.create(
            name="XRF-001",
            dataset=dataset,
            sample=sample,
            element="Fe",
            concentration_ppm=25.5,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="XRF-002",
            dataset=dataset,
            sample=sample,
            element="Cu",
            concentration_ppm=15.3,
        )

        filterset = CustomXRFFilter(
            data={"dataset": [dataset.id]},
            queryset=XRFMeasurement.objects.all(),
            request=_request_for(AnonymousUser()),
        )
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 in filterset.qs
