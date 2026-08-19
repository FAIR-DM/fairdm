"""Tests for Measurement filtering and search functionality (T021 - Phase 7).

This module tests the MeasurementFilter and MeasurementFilterMixin classes that provide
comprehensive filtering capabilities for Measurement models including:
- Dataset filtering
- Sample filtering
- Polymorphic type filtering
- Generic search (name, uuid)
- Cross-relationship filtering (descriptions, dates)
- Combined filters
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory
from guardian.shortcuts import assign_perm

from fairdm.core.measurement.filters import MeasurementFilter, MeasurementFilterMixin
from fairdm.core.measurement.models import (
    Measurement,
    MeasurementDate,
    MeasurementDescription,
)
from fairdm.factories import DatasetFactory, UserFactory
from fairdm.registry import registry
from fairdm_demo.factories import RockSampleFactory
from fairdm_demo.models import ICP_MS_Measurement, XRFMeasurement
from tests.registry_models.models import ConcreteMeasurement, ConcreteSample

User = get_user_model()

pytestmark = pytest.mark.django_db


def _request_for(user):
    """A minimal request carrying an authenticated user.

    `MeasurementFilterMixin` narrows the dataset choices to what the request's
    user may change, and leaves them at the privacy-first default when no
    request is given (T115) - the same contract `MeasurementFormMixin` already
    holds for forms.
    """
    request = RequestFactory().get("/")
    request.user = user
    return request


class TestMeasurementFilterDatasetFiltering:
    """Test dataset filtering functionality."""

    def test_filter_by_dataset(self, user, project):
        """Test filtering measurements by dataset relationship."""
        # Left private, which is the model's default and the ordinary case: the
        # filter's "dataset" choices come from `Dataset.all_objects`, so filtering
        # by one works.
        dataset1 = DatasetFactory(project=project)
        dataset2 = DatasetFactory(project=project)

        sample1 = RockSampleFactory(dataset=dataset1)
        sample2 = RockSampleFactory(dataset=dataset2)

        # Create measurements in different datasets
        measurement1 = XRFMeasurement.objects.create(
            name="XRF in Dataset 1",
            dataset=dataset1,
            sample=sample1,
            element="Fe",
            concentration_ppm=25.5,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="XRF in Dataset 2",
            dataset=dataset2,
            sample=sample2,
            element="Cu",
            concentration_ppm=15.3,
        )

        # The reader is entitled to both datasets, so both are offered as choices
        # even though each is private (T115).
        assign_perm("dataset.change_dataset", user, dataset1)
        assign_perm("dataset.change_dataset", user, dataset2)

        # Filter by dataset1
        filterset = MeasurementFilter(
            data={"dataset": dataset1.id},
            queryset=XRFMeasurement.objects.all(),
            request=_request_for(user),
        )
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 not in filterset.qs


class TestMeasurementFilterSampleFiltering:
    """Test sample filtering functionality."""

    def test_filter_by_sample(self, user, project, dataset):
        """Test filtering measurements by sample relationship."""
        # Create two samples
        sample1 = RockSampleFactory(dataset=dataset, name="Sample 1")
        sample2 = RockSampleFactory(dataset=dataset, name="Sample 2")

        # Create measurements for different samples
        measurement1 = XRFMeasurement.objects.create(
            name="XRF for Sample 1",
            dataset=dataset,
            sample=sample1,
            element="Fe",
            concentration_ppm=25.5,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="XRF for Sample 2",
            dataset=dataset,
            sample=sample2,
            element="Cu",
            concentration_ppm=15.3,
        )

        # Filter by sample1
        filterset = MeasurementFilter(
            data={"sample": sample1.id}, queryset=XRFMeasurement.objects.all()
        )
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 not in filterset.qs


class TestMeasurementFilterPolymorphicTypeFiltering:
    """Test polymorphic type filtering functionality."""

    def test_filter_by_polymorphic_type(self, user, project, dataset):
        """Test filtering measurements by polymorphic content type."""
        from django.contrib.contenttypes.models import ContentType

        sample = RockSampleFactory(dataset=dataset)

        # Create measurements of different types
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

        # Get content types
        xrf_ct = ContentType.objects.get_for_model(XRFMeasurement)
        icpms_ct = ContentType.objects.get_for_model(ICP_MS_Measurement)

        # Filter by XRFMeasurement type
        from fairdm.core.measurement.models import Measurement

        filterset = MeasurementFilter(
            data={"polymorphic_ctype": xrf_ct.id}, queryset=Measurement.objects.all()
        )
        assert filterset.is_valid()
        assert xrf_measurement in filterset.qs
        assert icpms_measurement not in filterset.qs

        # Filter by ICP_MS_Measurement type
        filterset = MeasurementFilter(
            data={"polymorphic_ctype": icpms_ct.id}, queryset=Measurement.objects.all()
        )
        assert filterset.is_valid()
        assert icpms_measurement in filterset.qs
        assert xrf_measurement not in filterset.qs


class TestMeasurementFilterPolymorphicTypeChoices:
    """T066/T067 - the `polymorphic_ctype` filter's choices are exactly the
    registered measurement types, drawn from `registry.measurements` rather
    than a hardcoded application list. `ConcreteMeasurement`
    (`tests.registry_models`) stands in for a type registered from outside
    the framework, the way `TestAdminOffersExactlyRegisteredMeasurementTypes`
    proves the same shape for the admin (test_admin_registry.py)."""

    def test_choices_are_exactly_the_registered_measurement_types(
        self, clean_registry
    ):
        """The polymorphic base, every registered sample type and every
        non-measurement record are absent - only registered measurement
        types, named individually, are offered."""
        registry.register(ConcreteMeasurement)
        registry.register(ConcreteSample)

        filterset = MeasurementFilter()
        offered = set(filterset.filters["polymorphic_ctype"].queryset)

        assert offered == {
            ContentType.objects.get_for_model(model)
            for model in registry.measurements
        }
        assert ContentType.objects.get_for_model(XRFMeasurement) in offered
        assert ContentType.objects.get_for_model(ICP_MS_Measurement) in offered
        assert ContentType.objects.get_for_model(ConcreteMeasurement) in offered
        assert ContentType.objects.get_for_model(Measurement) not in offered
        assert ContentType.objects.get_for_model(ConcreteSample) not in offered

    def test_narrowing_by_a_registered_type_leaves_only_that_type(
        self, clean_registry, dataset
    ):
        """Narrowing by one of the offered choices - including the type
        registered from outside the framework - leaves only measurements of
        that type."""
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
    """Test generic search functionality."""

    def test_search_by_name_and_uuid(self, user, project, dataset):
        """Test generic search across name and uuid fields."""
        sample = RockSampleFactory(dataset=dataset)

        # Create measurements with distinct names
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

        # Search by name
        filterset = MeasurementFilter(
            data={"search": "Iron"}, queryset=XRFMeasurement.objects.all()
        )
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 not in filterset.qs
        assert measurement3 not in filterset.qs

        # Search by UUID (partial match)
        uuid_str = str(measurement2.uuid)[:8]
        filterset = MeasurementFilter(
            data={"search": uuid_str}, queryset=XRFMeasurement.objects.all()
        )
        assert filterset.is_valid()
        assert measurement2 in filterset.qs


class TestMeasurementFilterCrossRelationshipFiltering:
    """Test cross-relationship filtering for descriptions and dates."""

    def test_filter_by_description_text(self, user, project, dataset):
        """Test filtering measurements by description text content."""
        sample = RockSampleFactory(dataset=dataset)

        # Create measurements
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

        # Add descriptions
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

        # Filter by description content
        filterset = MeasurementFilter(
            data={"description": "precision"},
            queryset=XRFMeasurement.objects.all(),
        )
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 not in filterset.qs

    def test_filter_by_date_range(self, user, project, dataset):
        """Test filtering measurements by associated date ranges - full dates,
        a year and month only, and a year only (T072). `MeasurementDate.value`
        accepts all three precisions (`fairdm.db.fields.PartialDateField`); a
        partial date is compared on the part it records rather than being
        dropped from the range or raising (T073, plan.md R2)."""

        sample = RockSampleFactory(dataset=dataset)

        # Create measurements
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

        # Filter by date_after
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
        # The whole of 2023 is before the February 2024 threshold.
        assert measurement_year_only not in filterset.qs

        # Filter by date_before
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
        # The whole of 2023 is before the February 2024 threshold.
        assert measurement_year_only in filterset.qs


class TestMeasurementFilterDateRangeValidation:
    """T073 follow-up - the `CharFilter` swap that let `date_after`/
    `date_before` accept a year or a year-and-month (T072/T073) also let any
    string through unvalidated: `is_valid()` reported `True` for junk input,
    and the request then died with an unhandled `ValidationError` when the
    queryset was evaluated, rather than a form error a reader could see and
    correct. A public filter form must never do that - the field now
    validates the string at clean time, using the same parser
    (`partial_date.PartialDate.parseDate`) the model field itself uses, so
    the accepted/rejected shapes cannot drift between the two."""

    @pytest.mark.parametrize("value", ["not-a-date", "2024-13-45"])
    def test_invalid_date_string_is_a_form_error_not_a_query_time_exception(
        self, value
    ):
        """Junk input fails `is_valid()` and is reported on the `date_after`
        field - and, critically, evaluating `.qs` on the invalid filter set
        does not raise. django-filter excludes an invalid field from
        `form.cleaned_data`, so `filter_queryset` never reaches it once the
        field itself refuses the value."""
        filterset = MeasurementFilter(
            data={"date_after": value}, queryset=Measurement.objects.all()
        )

        assert filterset.is_valid() is False
        assert "date_after" in filterset.errors

        # Must not raise.
        list(filterset.qs)

    def test_empty_date_string_is_valid(self):
        """An empty value is the ordinary "no filter applied" case, not
        invalid input."""
        filterset = MeasurementFilter(
            data={"date_after": ""}, queryset=Measurement.objects.all()
        )

        assert filterset.is_valid()


class TestMeasurementFilterCombinedFilters:
    """T076 - each filter in a combination narrows independently. Reopened at
    design review: the previous version proved only the sample half - the one
    row the dataset filter would remove was bound to a discarded name and
    never asserted, so deleting "dataset" from the filter data left the test
    green."""

    def test_combined_filters_dataset_and_sample(self, user, project):
        """`measurement_wrong_dataset` shares `sample1` with `measurement_both`
        but is linked to `dataset2` (US-2 cross-dataset linking: a
        measurement's own `dataset` need not match its sample's) - only the
        `dataset` filter removes it. Symmetrically, `measurement_wrong_sample`
        shares `dataset1` with `measurement_both` but uses `sample2` - only
        the `sample` filter removes it. Filtering by both together leaves
        only the measurement matching both, and each exclusion is the work of
        a different filter - confirmed by removing each filter from the data
        in turn and watching its corresponding assertion fail."""
        dataset1 = DatasetFactory(project=project)
        dataset2 = DatasetFactory(project=project)

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

        assign_perm("dataset.change_dataset", user, dataset1)

        # Filter by dataset AND sample
        filterset = MeasurementFilter(
            data={"dataset": dataset1.id, "sample": sample1.id},
            queryset=XRFMeasurement.objects.all(),
            request=_request_for(user),
        )
        assert filterset.is_valid()
        assert measurement_both in filterset.qs
        assert measurement_wrong_dataset not in filterset.qs  # the dataset filter's work
        assert measurement_wrong_sample not in filterset.qs  # the sample filter's work


class TestMeasurementFilterMixinInheritance:
    """T052 - a filter set inheriting MeasurementFilterMixin carries every
    filter the mixin declares, named one by one rather than merely
    established by a query that an empty filter set would also satisfy."""

    def test_inheriting_filter_set_carries_the_mixins_declared_filters(self):
        """MeasurementFilter inherits MeasurementFilterMixin, so its own
        filters must include every filter the mixin declares, named
        individually."""
        filterset = MeasurementFilter()

        assert "dataset" in filterset.filters
        assert "sample" in filterset.filters
        assert "polymorphic_ctype" in filterset.filters
        assert "search" in filterset.filters
        assert "description" in filterset.filters
        assert "date_after" in filterset.filters
        assert "date_before" in filterset.filters

    def test_mixin_declares_all_six(self):
        """Confirms the mixin's own declared filters are exactly the ones
        its docstring advertises, not merely inherited from the concrete
        MeasurementFilter below it."""
        assert set(MeasurementFilterMixin.declared_filters) == {
            "dataset",
            "sample",
            "polymorphic_ctype",
            "search",
            "description",
            "date_after",
            "date_before",
        }


class TestMeasurementFilterMixinDatasetPrivacy:
    """T115 - the filter mixin's dataset choices are scoped to what the
    requesting reader may see, not every dataset in the portal. Mirrors
    `MeasurementFormMixin`'s own dataset scoping (T054/T056): an entitled
    reader can narrow by a private dataset, and a reader with no
    entitlement is offered none - not merely the ones already public."""

    def test_entitled_reader_may_narrow_by_a_private_dataset(self):
        """A reader holding `change_dataset` on a private dataset finds it
        among the mixin's own choices, and not a private dataset they hold
        no rights over."""
        user = UserFactory()
        allowed = DatasetFactory()  # private by default
        other = DatasetFactory()
        assign_perm("change_dataset", user, allowed)

        filterset = MeasurementFilter(request=_request_for(user))

        offered = set(filterset.filters["dataset"].queryset)
        assert offered == {allowed}
        assert other not in offered

    def test_reader_with_no_entitlement_is_offered_no_private_dataset(self):
        """With no request at all, the mixin is left holding the
        privacy-first default manager rather than `all_objects` - the
        fixture below is private (the factory default), so it is not
        offered."""
        DatasetFactory()

        filterset = MeasurementFilter()

        assert set(filterset.filters["dataset"].queryset) == set()


class TestMeasurementFilterRegistryGeneratedDatasetPrivacy:
    """T074 - the dataset-choices widening T115 proves on `MeasurementFilter`
    directly (`TestMeasurementFilterMixinDatasetPrivacy` above) also holds on
    the filter set the registry generates for a registered measurement type.
    Built the way the registry builds it -
    `fairdm.registry.factories.FilterFactory`, matching
    `TestFilterFactoryMeasurementBranch`
    (tests/test_registry/test_factories.py) - because a hand-built stand-in
    would prove nothing about the wiring itself."""

    def test_entitled_reader_finds_a_private_dataset_on_the_registry_generated_filterset(
        self,
    ):
        """A reader holding `change_dataset` on a private dataset finds it
        among the registry-generated filter set's dataset choices too, and
        not a private dataset they hold no rights over."""
        from fairdm.registry.factories import FilterFactory

        user = UserFactory()
        allowed = DatasetFactory()  # private by default
        other = DatasetFactory()
        assign_perm("change_dataset", user, allowed)

        filterset_class = FilterFactory(XRFMeasurement, fields=["dataset"]).generate()
        filterset = filterset_class(request=_request_for(user))

        offered = set(filterset.filters["dataset"].queryset)
        assert offered == {allowed}
        assert other not in offered


class TestMeasurementFilterMixinUsage:
    """Test MeasurementFilterMixin for custom filters."""

    def test_custom_filter_inherits_from_mixin(self, user, project, dataset):
        """Test that custom filters can inherit from MeasurementFilterMixin."""
        import django_filters

        from fairdm.core.measurement.filters import MeasurementFilterMixin

        # Create a custom filter class that inherits from the mixin
        class CustomXRFFilter(MeasurementFilterMixin, django_filters.FilterSet):
            element = django_filters.CharFilter(
                field_name="element", lookup_expr="icontains"
            )

            class Meta(MeasurementFilterMixin.Meta):
                model = XRFMeasurement
                fields = [*MeasurementFilterMixin.Meta.fields, "element"]

        sample = RockSampleFactory(dataset=dataset)

        # Create XRF measurements
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

        assign_perm("dataset.change_dataset", user, dataset)

        # Use custom filter
        filterset = CustomXRFFilter(
            data={"dataset": dataset.id},
            queryset=XRFMeasurement.objects.all(),
            request=_request_for(user),
        )
        assert filterset.is_valid()
        assert measurement1 in filterset.qs
        assert measurement2 in filterset.qs
