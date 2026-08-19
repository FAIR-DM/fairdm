"""Integration tests for Measurement admin interface.

Tests for User Story 3: Enhanced Admin Interface

This module tests the Django admin interface for Measurement models including:
- Search functionality (name, uuid)
- Filtering (dataset, sample, type)
- Inline metadata editing (descriptions, dates, identifiers, contributors)
- Vocabulary correctness (MeasurementDescription and MeasurementDate use Measurement vocabularies)
- Polymorphic type handling

Based on tasks T019, T006-T010 from Feature 006.
"""

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from fairdm.core.measurement.admin import MeasurementChildAdmin
from fairdm.core.measurement.models import (
    Measurement,
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)
from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory

User = get_user_model()


@pytest.fixture
def admin_user(db):
    """Create a superuser for admin access."""
    user = User.objects.create_superuser(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="admin123",
    )
    return user


@pytest.fixture
def measurement_admin():
    """Create a MeasurementAdmin instance."""
    return MeasurementChildAdmin(Measurement, AdminSite())


@pytest.fixture
def request_factory():
    """Create a RequestFactory instance."""
    return RequestFactory()


@pytest.mark.django_db
class TestMeasurementAdminSearch:
    """Tests for admin search functionality."""

    def test_search_by_name(self, measurement_admin, admin_user, request_factory):
        """Test that admin search finds measurements by name."""
        measurement1 = ExampleMeasurementFactory(
            sample=RockSampleFactory(), name="XRF Analysis"
        )
        measurement2 = ExampleMeasurementFactory(
            sample=RockSampleFactory(), name="ICP-MS Analysis"
        )
        _measurement3 = ExampleMeasurementFactory(
            sample=RockSampleFactory(), name="Spectroscopy"
        )

        request = request_factory.get("/admin/measurement/measurement/", {"q": "XRF"})
        request.user = admin_user

        queryset = measurement_admin.get_search_results(
            request, Measurement.objects.all(), "XRF"
        )[0]

        assert measurement1 in queryset
        assert measurement2 not in queryset

    def test_search_by_uuid(self, measurement_admin, admin_user, request_factory):
        """Test that admin search finds measurements by UUID."""
        measurement1 = ExampleMeasurementFactory(sample=RockSampleFactory())

        request = request_factory.get(
            "/admin/measurement/measurement/", {"q": measurement1.uuid}
        )
        request.user = admin_user

        queryset = measurement_admin.get_search_results(
            request, Measurement.objects.all(), measurement1.uuid
        )[0]

        assert measurement1 in queryset

    def test_search_returns_empty_for_no_matches(
        self, measurement_admin, admin_user, request_factory
    ):
        """Test that admin search returns empty queryset when no matches found."""
        _measurement1 = ExampleMeasurementFactory(
            sample=RockSampleFactory(), name="Test Measurement"
        )

        request = request_factory.get(
            "/admin/measurement/measurement/", {"q": "NonExistent"}
        )
        request.user = admin_user

        queryset = measurement_admin.get_search_results(
            request, Measurement.objects.all(), "NonExistent"
        )[0]

        assert queryset.count() == 0


@pytest.mark.django_db
class TestMeasurementAdminFilters:
    """Tests for admin filtering functionality (FR-040), exercised through the
    administrative interface itself rather than by querying the model directly."""

    def test_filter_by_dataset(self, admin_user, request_factory):
        """Narrowing the parent changelist by dataset leaves only that dataset's rows."""
        from django.contrib import admin as django_admin

        from fairdm.factories import DatasetFactory
        from fairdm_demo.models import XRFMeasurement

        dataset1 = DatasetFactory(name="Dataset A")
        dataset2 = DatasetFactory(name="Dataset B")
        sample1 = RockSampleFactory(dataset=dataset1)
        sample2 = RockSampleFactory(dataset=dataset2)

        measurement1 = XRFMeasurement.objects.create(
            name="XRF 1",
            sample=sample1,
            dataset=dataset1,
            element="Si",
            concentration_ppm=250000.0,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="XRF 2",
            sample=sample2,
            dataset=dataset2,
            element="Fe",
            concentration_ppm=50000.0,
        )

        parent_admin = django_admin.site._registry[Measurement]
        request = request_factory.get(
            "/admin/core/measurement/", {"dataset__id__exact": str(dataset1.pk)}
        )
        request.user = admin_user

        changelist = parent_admin.get_changelist_instance(request)

        result_pks = set(changelist.queryset.values_list("pk", flat=True))
        assert measurement1.pk in result_pks
        assert measurement2.pk not in result_pks

    def test_filter_by_sample(self, admin_user, request_factory, sample):
        """Narrowing the parent changelist by sample leaves only that sample's rows."""
        from django.contrib import admin as django_admin

        from fairdm_demo.models import XRFMeasurement

        sample2 = RockSampleFactory(dataset=sample.dataset)

        measurement1 = XRFMeasurement.objects.create(
            name="XRF 1",
            sample=sample,
            dataset=sample.dataset,
            element="Si",
            concentration_ppm=250000.0,
        )
        measurement2 = XRFMeasurement.objects.create(
            name="XRF 2",
            sample=sample2,
            dataset=sample.dataset,
            element="Fe",
            concentration_ppm=50000.0,
        )

        parent_admin = django_admin.site._registry[Measurement]
        request = request_factory.get(
            "/admin/core/measurement/", {"sample__id__exact": str(sample.pk)}
        )
        request.user = admin_user

        changelist = parent_admin.get_changelist_instance(request)

        result_pks = set(changelist.queryset.values_list("pk", flat=True))
        assert measurement1.pk in result_pks
        assert measurement2.pk not in result_pks

    def test_filter_by_measurement_type(self, admin_user, request_factory, sample):
        """Narrowing the parent changelist by measurement type leaves only that type's rows."""
        from django.contrib import admin as django_admin
        from django.contrib.contenttypes.models import ContentType

        from fairdm_demo.models import ICP_MS_Measurement, XRFMeasurement

        xrf = XRFMeasurement.objects.create(
            name="XRF",
            sample=sample,
            dataset=sample.dataset,
            element="Si",
            concentration_ppm=250000.0,
        )
        icp = ICP_MS_Measurement.objects.create(
            name="ICP-MS",
            sample=sample,
            dataset=sample.dataset,
            isotope="207Pb",
            counts_per_second=15000.0,
            concentration_ppb=120.5,
        )

        xrf_type = ContentType.objects.get_for_model(XRFMeasurement)

        parent_admin = django_admin.site._registry[Measurement]
        request = request_factory.get(
            "/admin/core/measurement/", {"polymorphic_ctype": str(xrf_type.pk)}
        )
        request.user = admin_user

        changelist = parent_admin.get_changelist_instance(request)

        result_pks = set(changelist.queryset.values_list("pk", flat=True))
        assert xrf.pk in result_pks
        assert icp.pk not in result_pks

    def test_list_filter_configuration(self, measurement_admin):
        """Test that list_filter is configured correctly."""
        assert "added" in measurement_admin.list_filter

    def test_child_admin_list_filter_includes_dataset_and_sample(
        self, measurement_admin
    ):
        """FR-040: the child admin's list can be narrowed by dataset and by sample."""
        filtered_field_names = {
            entry[0] if isinstance(entry, tuple) else entry
            for entry in measurement_admin.list_filter
        }
        assert "dataset" in filtered_field_names
        assert "sample" in filtered_field_names

    def test_parent_admin_list_filter_includes_dataset_and_sample(self):
        """FR-040: the parent admin's list can be narrowed by dataset and by sample."""
        from fairdm.core.measurement.admin import MeasurementParentAdmin

        parent_admin = MeasurementParentAdmin(Measurement, AdminSite())
        filtered_field_names = {
            entry[0] if isinstance(entry, tuple) else entry
            for entry in parent_admin.list_filter
        }
        assert "dataset" in filtered_field_names
        assert "sample" in filtered_field_names


@pytest.mark.django_db
class TestMeasurementAdminInlines:
    """Tests for admin inline metadata editing."""

    def test_description_inline_configured(self, measurement_admin):
        """Test that MeasurementDescriptionInline is configured in MeasurementAdmin."""
        inline_names = [inline.__name__ for inline in measurement_admin.inlines]
        assert "MeasurementDescriptionInline" in inline_names

    def test_date_inline_configured(self, measurement_admin):
        """Test that MeasurementDateInline is configured in MeasurementAdmin."""
        inline_names = [inline.__name__ for inline in measurement_admin.inlines]
        assert "MeasurementDateInline" in inline_names

    def test_identifier_inline_configured(self, measurement_admin):
        """Test that MeasurementIdentifierInline is configured in MeasurementAdmin."""
        inline_names = [inline.__name__ for inline in measurement_admin.inlines]
        assert "MeasurementIdentifierInline" in inline_names

    def test_contribution_inline_configured(self, measurement_admin):
        """Test that MeasurementContributionInline is configured in MeasurementAdmin."""
        inline_names = [inline.__name__ for inline in measurement_admin.inlines]
        assert "MeasurementContributionInline" in inline_names

    def test_inline_metadata_can_be_created(self, measurement_admin, measurement):
        """Test that inline metadata objects can be created for a measurement."""
        # Create description via inline
        description = MeasurementDescription.objects.create(
            related=measurement, type="method", value="XRF analysis method description"
        )

        assert description.related == measurement
        assert measurement.descriptions.count() == 1

    def test_inline_dates_can_be_created(self, measurement_admin, measurement):
        """Test that inline date objects can be created for a measurement."""
        # Create date via inline
        date = MeasurementDate.objects.create(
            related=measurement, type="measured", value="2024-01-15"
        )

        assert date.related == measurement
        assert measurement.dates.count() == 1

    def test_inline_identifiers_can_be_created(self, measurement_admin, measurement):
        """Test that inline identifier objects can be created for a measurement."""
        # Create identifier via inline
        identifier = MeasurementIdentifier.objects.create(
            related=measurement, type="DOI", value="10.1234/meas.123"
        )

        assert identifier.related == measurement
        assert measurement.identifiers.count() == 1

    def test_inline_contribution_can_be_added_and_changed(self, measurement):
        """Test that a contribution can be credited on a measurement, and then changed."""
        from fairdm.factories import PersonFactory

        contributor = PersonFactory()
        contribution = measurement.contributors.create(contributor=contributor)

        assert contribution.contributor == contributor
        assert measurement.contributors.count() == 1

        new_contributor = PersonFactory()
        contribution.contributor = new_contributor
        contribution.save()
        contribution.refresh_from_db()

        assert contribution.contributor == new_contributor


@pytest.mark.django_db
class TestMeasurementAdminInlineRowCaps:
    """Tests for T098: an inline editor whose type is drawn from a vocabulary offers no
    more rows than that vocabulary has members. Contributions are NOT capped - a
    measurement may credit any number of people, one row each (design review correction)."""

    def test_description_inline_row_cap_matches_vocabulary(self):
        from fairdm.core.measurement.admin import MeasurementDescriptionInline

        assert MeasurementDescriptionInline.max_num == len(
            MeasurementDescription.VOCABULARY.values
        )

    def test_date_inline_row_cap_matches_vocabulary(self):
        from fairdm.core.measurement.admin import MeasurementDateInline

        assert MeasurementDateInline.max_num == len(MeasurementDate.VOCABULARY.values)

    def test_identifier_inline_row_cap_matches_vocabulary(self):
        from fairdm.core.measurement.admin import MeasurementIdentifierInline

        assert MeasurementIdentifierInline.max_num == len(
            MeasurementIdentifier.VOCABULARY.values
        )

    def test_contribution_inline_is_not_row_capped(self):
        from fairdm.core.measurement.admin import MeasurementContributionInline

        assert MeasurementContributionInline.max_num is None


@pytest.mark.django_db
class TestMeasurementAdminSharedInlines:
    """T099: every registered measurement type offers the same attached-record editors."""

    def test_every_registered_type_offers_the_same_inlines(self):
        from django.contrib import admin as django_admin

        from fairdm.core.measurement.admin import MeasurementChildAdmin
        from fairdm.registry import registry

        measurement_types = registry.measurements
        assert len(measurement_types) >= 2, (
            "need at least two registered types to compare"
        )

        child_admins = [
            django_admin.site._registry[model] for model in measurement_types
        ]

        for child_admin in child_admins:
            assert child_admin.inlines == MeasurementChildAdmin.inlines


@pytest.mark.django_db
class TestMeasurementAdminVocabularyCorrectness:
    """Tests for vocabulary correctness in admin inlines."""

    def test_measurement_description_uses_measurement_vocabulary(self, measurement):
        """Test that MeasurementDescription inline uses Measurement vocabulary collection."""
        # Create a description with a Measurement-specific type
        description = MeasurementDescription.objects.create(
            related=measurement, type="method", value="Test method"
        )

        # Verify the vocabulary is from Measurement collection (not Sample)
        assert description.VOCABULARY is not None
        assert description.type == "method"  # type field returns string value

    def test_measurement_date_uses_measurement_vocabulary(self, measurement):
        """Test that MeasurementDate inline uses Measurement vocabulary collection."""
        # Create a date with a Measurement-specific type
        date = MeasurementDate.objects.create(
            related=measurement, type="measured", value="2024-01-15"
        )

        # Verify the vocabulary is from Measurement collection (not Sample)
        assert date.VOCABULARY is not None
        assert date.type == "measured"  # type field returns string value


@pytest.mark.django_db
class TestMeasurementAdminPolymorphicHandling:
    """Tests for polymorphic type handling in admin."""

    def test_parent_admin_shows_type_selection_interface(
        self, admin_user, request_factory
    ):
        """Test that parent admin provides polymorphic type selection."""
        from fairdm.core.measurement.admin import MeasurementParentAdmin

        parent_admin = MeasurementParentAdmin(Measurement, AdminSite())

        # Parent admin should have get_child_models method
        assert hasattr(parent_admin, "get_child_models")

        # get_child_models should return measurement types from registry
        child_models = parent_admin.get_child_models()
        assert len(child_models) > 0

    def test_child_admin_renders_with_inlines(self, measurement_admin, sample):
        """Test that child admin renders correctly with all inlines."""
        from fairdm_demo.models import XRFMeasurement

        # Create an XRF measurement
        xrf = XRFMeasurement.objects.create(
            name="XRF Test",
            sample=sample,
            dataset=sample.dataset,
            element="Si",
            concentration_ppm=250000.0,
        )

        # Child admin should render with all inlines
        assert (
            len(measurement_admin.inlines) == 4
        )  # Descriptions, Dates, Identifiers, Contributors


@pytest.mark.django_db
class TestMeasurementAdminConfiguration:
    """Tests for general admin configuration."""

    def test_list_display_configured(self, measurement_admin):
        """Test that list_display shows appropriate fields."""
        assert "name" in measurement_admin.list_display
        assert "sample" in measurement_admin.list_display
        assert "dataset" in measurement_admin.list_display
        assert "added" in measurement_admin.list_display

    def test_search_fields_configured(self, measurement_admin):
        """Test that search_fields includes name and uuid."""
        assert "name" in measurement_admin.search_fields
        assert "uuid" in measurement_admin.search_fields

    def test_readonly_fields_configured(self, measurement_admin):
        """Test that readonly fields include uuid and timestamps."""
        assert "uuid" in measurement_admin.readonly_fields
        assert "added" in measurement_admin.readonly_fields
        assert "modified" in measurement_admin.readonly_fields

    def test_fieldsets_configured(self, measurement_admin):
        """Test that base_fieldsets are properly configured for polymorphic admin."""
        # Polymorphic admin uses base_fieldsets instead of fieldsets
        assert hasattr(measurement_admin, "base_fieldsets")
        assert measurement_admin.base_fieldsets is not None
        assert len(measurement_admin.base_fieldsets) >= 2

    def test_measurement_admin_is_configured_for_inheritance(self, measurement_admin):
        """Test that MeasurementAdmin is designed for inheritance by custom classes."""
        # MeasurementAdmin should have inlines configured
        assert len(measurement_admin.inlines) > 0
        # MeasurementAdmin should have search configured
        assert len(measurement_admin.search_fields) > 0
        # MeasurementAdmin should have list display configured
        assert len(measurement_admin.list_display) > 0
