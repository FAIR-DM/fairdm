"""
Integration tests for demo app admin views.

This module tests that all demo measurement model admin interfaces work correctly,
including list views, add views, and edit views. These tests catch common admin
configuration errors like:
- Missing fields referenced in fieldsets
- Incorrect field names in list_display/list_filter
- Foreign key/autocomplete configuration issues
- Custom admin methods that fail at runtime

Tests follow the pattern:
1. Create test data (authenticated user, samples, measurements)
2. Make HTTP requests to admin URLs
3. Assert successful response (200 OK) and no errors
4. Verify expected content appears in response

These tests complement the core admin tests by verifying the actual demo
implementations used as examples for portal developers.
"""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from fairdm.factories import DatasetFactory, SampleFactory
from fairdm_demo.models import ExampleMeasurement, ICP_MS_Measurement, RockSample, WaterSample, XRFMeasurement

User = get_user_model()


@pytest.fixture
def admin_user(db):
    """Create a superuser for admin access."""
    return User.objects.create_superuser(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="admin123",
    )


@pytest.fixture
def sample(db):
    """Create a sample for measurement tests."""
    return SampleFactory()


@pytest.fixture
def rock_sample(db):
    """Create a rock sample for admin tests."""
    dataset = DatasetFactory()
    return RockSample.objects.create(
        name="Test Rock Sample",
        dataset=dataset,
        rock_type="Igneous",
        mineral_content="Quartz, Feldspar",
        weight_grams=150.0,
        collection_date="2024-01-15",
        hardness_mohs=7.0,
    )


@pytest.fixture
def water_sample(db):
    """Create a water sample for admin tests."""
    dataset = DatasetFactory()
    return WaterSample.objects.create(
        name="Test Water Sample",
        dataset=dataset,
        water_source="River",
        temperature_celsius=18.5,
        ph_level=7.2,
        turbidity_ntu=3.5,
        dissolved_oxygen_mg_l=8.2,
        conductivity_us_cm=450.0,
    )


@pytest.fixture
def example_measurement(db, sample):
    """Create an example measurement for admin tests."""
    return ExampleMeasurement.objects.create(
        name="Test Example Measurement",
        sample=sample,
        dataset=sample.dataset,
        char_field="Test Value",
        text_field="Test Description",
        integer_field=42,
        boolean_field=True,
    )


@pytest.fixture
def xrf_measurement(db, sample):
    """Create an XRF measurement for admin tests."""
    return XRFMeasurement.objects.create(
        name="Test XRF Measurement",
        sample=sample,
        dataset=sample.dataset,
        element="Si",
        concentration_ppm=250000.0,
        detection_limit_ppm=5.0,
        instrument_model="Bruker Tracer",
        measurement_conditions="30kV, 10µA, vacuum",
    )


@pytest.fixture
def icp_ms_measurement(db, sample):
    """Create an ICP-MS measurement for admin tests."""
    return ICP_MS_Measurement.objects.create(
        name="Test ICP-MS Measurement",
        sample=sample,
        dataset=sample.dataset,
        isotope="207Pb",
        counts_per_second=15000.0,
        concentration_ppb=120.5,
        uncertainty_percent=2.5,
        dilution_factor=100.0,
        internal_standard="115In",
    )


# ============================================================================
# Sample Admin View Tests
# ============================================================================


@pytest.mark.django_db
class TestRockSampleAdminViews:
    """Test RockSample admin views load correctly."""

    def test_list_view_loads(self, admin_user, client, rock_sample):
        """Test that RockSample list view loads without errors."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_rocksample_changelist")
        response = client.get(url)

        assert response.status_code == 200
        assert "Test Rock Sample" in str(response.content)

    def test_add_view_loads(self, admin_user, client):
        """Test that RockSample add view loads without errors."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_rocksample_add")
        response = client.get(url)

        assert response.status_code == 200

    def test_change_view_loads(self, admin_user, client, rock_sample):
        """Test that RockSample change view loads without errors."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_rocksample_change", args=[rock_sample.pk])
        response = client.get(url)

        assert response.status_code == 200
        assert "Test Rock Sample" in str(response.content)
        assert "Geological Properties" in str(response.content)

    def test_list_view_search_works(self, admin_user, client, rock_sample):
        """Test that RockSample search functionality works."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_rocksample_changelist")
        response = client.get(url, {"q": "Test Rock"})

        assert response.status_code == 200
        assert "Test Rock Sample" in str(response.content)

    def test_list_view_filter_works(self, admin_user, client, rock_sample):
        """Test that RockSample filtering works."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_rocksample_changelist")
        response = client.get(url, {"rock_type": "Igneous"})

        assert response.status_code == 200


@pytest.mark.django_db
class TestWaterSampleAdminViews:
    """Test WaterSample admin views load correctly."""

    def test_list_view_loads(self, admin_user, client, water_sample):
        """Test that WaterSample list view loads without errors."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_watersample_changelist")
        response = client.get(url)

        assert response.status_code == 200
        assert "Test Water Sample" in str(response.content)

    def test_add_view_loads(self, admin_user, client):
        """Test that WaterSample add view loads without errors."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_watersample_add")
        response = client.get(url)

        assert response.status_code == 200

    def test_change_view_loads(self, admin_user, client, water_sample):
        """Test that WaterSample change view loads without errors."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_watersample_change", args=[water_sample.pk])
        response = client.get(url)

        assert response.status_code == 200
        assert "Test Water Sample" in str(response.content)
        assert "Water Quality Parameters" in str(response.content)


# ============================================================================
# Measurement Admin View Tests
# ============================================================================


@pytest.mark.django_db
class TestExampleMeasurementAdminViews:
    """Test ExampleMeasurement admin views load correctly."""

    def test_list_view_loads(self, admin_user, client, example_measurement):
        """Test that ExampleMeasurement list view loads without errors."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_examplemeasurement_changelist")
        response = client.get(url)

        assert response.status_code == 200
        assert "Test Example Measurement" in str(response.content)

    def test_add_view_loads(self, admin_user, client):
        """Test that ExampleMeasurement add view loads without errors."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_examplemeasurement_add")
        response = client.get(url)

        assert response.status_code == 200

    def test_change_view_loads(self, admin_user, client, example_measurement):
        """Test that ExampleMeasurement change view loads without errors."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_examplemeasurement_change", args=[example_measurement.pk])
        response = client.get(url)

        assert response.status_code == 200
        assert "Test Example Measurement" in str(response.content)
        assert "Example Properties" in str(response.content)

    def test_list_view_displays_custom_fields(self, admin_user, client, example_measurement):
        """Test that list view displays custom char_field and integer_field."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_examplemeasurement_changelist")
        response = client.get(url)

        assert response.status_code == 200
        content = str(response.content)
        assert "Test Value" in content  # char_field value
        assert "42" in content  # integer_field value


@pytest.mark.django_db
class TestXRFMeasurementAdminViews:
    """Test XRFMeasurement admin views load correctly."""

    def test_list_view_loads(self, admin_user, client, xrf_measurement):
        """Test that XRFMeasurement list view loads without errors."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_xrfmeasurement_changelist")
        response = client.get(url)

        assert response.status_code == 200
        assert "Test XRF Measurement" in str(response.content)

    def test_add_view_loads(self, admin_user, client):
        """Test that XRFMeasurement add view loads without errors."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_xrfmeasurement_add")
        response = client.get(url)

        assert response.status_code == 200

    def test_change_view_loads(self, admin_user, client, xrf_measurement):
        """Test that XRFMeasurement change view loads without errors."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_xrfmeasurement_change", args=[xrf_measurement.pk])
        response = client.get(url)

        assert response.status_code == 200
        assert "Test XRF Measurement" in str(response.content)
        assert "XRF Analysis Parameters" in str(response.content)

    def test_list_view_displays_element_and_concentration(self, admin_user, client, xrf_measurement):
        """Test that list view displays element and concentration fields."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_xrfmeasurement_changelist")
        response = client.get(url)

        assert response.status_code == 200
        content = str(response.content)
        assert "Si" in content  # element value

    def test_list_view_filter_by_element_works(self, admin_user, client, xrf_measurement):
        """Test that filtering by element works."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_xrfmeasurement_changelist")
        response = client.get(url, {"element": "Si"})

        assert response.status_code == 200


@pytest.mark.django_db
class TestICPMSMeasurementAdminViews:
    """Test ICP_MS_Measurement admin views load correctly.

    CRITICAL: This test class specifically addresses the bug reported where
    the ICP-MS edit view was showing an error. The issue was that the admin
    fieldsets referenced 'detection_limit_ppb' which doesn't exist on the model.
    """

    def test_list_view_loads(self, admin_user, client, icp_ms_measurement):
        """Test that ICP_MS_Measurement list view loads without errors."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_icp_ms_measurement_changelist")
        response = client.get(url)

        assert response.status_code == 200
        assert "Test ICP-MS Measurement" in str(response.content)

    def test_add_view_loads(self, admin_user, client):
        """Test that ICP_MS_Measurement add view loads without errors."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_icp_ms_measurement_add")
        response = client.get(url)

        assert response.status_code == 200

    def test_change_view_loads_without_error(self, admin_user, client, icp_ms_measurement):
        """Test that ICP_MS_Measurement change view loads without errors.

        This is the critical test case that catches the bug where the admin
        referenced non-existent fields. Previously this would fail with a
        FieldError when the admin tried to render fields that don't exist
        on the model.
        """
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_icp_ms_measurement_change", args=[icp_ms_measurement.pk])
        response = client.get(url)

        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Check admin fieldsets."
        assert "Test ICP-MS Measurement" in str(response.content)
        assert "ICP-MS Analysis Parameters" in str(response.content)

    def test_change_view_displays_all_configured_fields(self, admin_user, client, icp_ms_measurement):
        """Test that all fields in admin fieldsets are actually on the model."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_icp_ms_measurement_change", args=[icp_ms_measurement.pk])
        response = client.get(url)

        assert response.status_code == 200
        content = str(response.content)

        # Verify all fields from fieldsets are displayed
        assert "Isotope" in content
        assert "207Pb" in content  # isotope value
        assert "Counts per Second" in content
        assert "15000" in content  # counts_per_second value
        assert "Concentration (ppb)" in content
        assert "120.5" in content  # concentration_ppb value
        assert "Uncertainty (%)" in content
        assert "Dilution Factor" in content
        assert "100" in content  # dilution_factor value
        assert "Internal Standard" in content
        assert "115In" in content  # internal_standard value

    def test_list_view_displays_isotope_and_concentration(self, admin_user, client, icp_ms_measurement):
        """Test that list view displays isotope and concentration fields."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_icp_ms_measurement_changelist")
        response = client.get(url)

        assert response.status_code == 200
        content = str(response.content)
        assert "207Pb" in content  # isotope value

    def test_list_view_filter_by_isotope_works(self, admin_user, client, icp_ms_measurement):
        """Test that filtering by isotope works."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_icp_ms_measurement_changelist")
        response = client.get(url, {"isotope": "207Pb"})

        assert response.status_code == 200

    def test_search_by_isotope_works(self, admin_user, client, icp_ms_measurement):
        """Test that searching by isotope works."""
        client.force_login(admin_user)
        url = reverse("admin:fairdm_demo_icp_ms_measurement_changelist")
        response = client.get(url, {"q": "207Pb"})

        assert response.status_code == 200
        assert "Test ICP-MS Measurement" in str(response.content)


# ============================================================================
# Cross-Model Admin Tests
# ============================================================================


@pytest.mark.django_db
class TestAllMeasurementAdminViewsWork:
    """Integration test to ensure ALL demo measurement admins work.

    This test class provides a safety net to catch any admin configuration
    errors across all demo measurement models. If any admin view fails to
    load, this will catch it.
    """

    def test_all_measurement_list_views_load(
        self,
        admin_user,
        client,
        example_measurement,
        xrf_measurement,
        icp_ms_measurement,
    ):
        """Test that all measurement list views load successfully."""
        client.force_login(admin_user)

        measurement_models = [
            ("fairdm_demo_examplemeasurement", "Example Measurement"),
            ("fairdm_demo_xrfmeasurement", "XRF Measurement"),
            ("fairdm_demo_icp_ms_measurement", "ICP-MS Measurement"),
        ]

        for model_name, display_name in measurement_models:
            url = reverse(f"admin:{model_name}_changelist")
            response = client.get(url)

            assert response.status_code == 200, f"{display_name} list view failed to load"

    def test_all_measurement_add_views_load(self, admin_user, client):
        """Test that all measurement add views load successfully."""
        client.force_login(admin_user)

        measurement_models = [
            ("fairdm_demo_examplemeasurement", "Example Measurement"),
            ("fairdm_demo_xrfmeasurement", "XRF Measurement"),
            ("fairdm_demo_icp_ms_measurement", "ICP-MS Measurement"),
        ]

        for model_name, display_name in measurement_models:
            url = reverse(f"admin:{model_name}_add")
            response = client.get(url)

            assert response.status_code == 200, f"{display_name} add view failed to load"

    def test_all_measurement_change_views_load(
        self,
        admin_user,
        client,
        example_measurement,
        xrf_measurement,
        icp_ms_measurement,
    ):
        """Test that all measurement change views load successfully."""
        client.force_login(admin_user)

        measurements = [
            (example_measurement, "Example Measurement", "fairdm_demo_examplemeasurement"),
            (xrf_measurement, "XRF Measurement", "fairdm_demo_xrfmeasurement"),
            (icp_ms_measurement, "ICP-MS Measurement", "fairdm_demo_icp_ms_measurement"),
        ]

        for measurement, display_name, model_name in measurements:
            url = reverse(f"admin:{model_name}_change", args=[measurement.pk])
            response = client.get(url)

            assert response.status_code == 200, f"{display_name} change view failed to load"
            assert measurement.name in str(response.content)


@pytest.mark.django_db
class TestAllSampleAdminViewsWork:
    """Integration test to ensure ALL demo sample admins work."""

    def test_all_sample_list_views_load(self, admin_user, client, rock_sample, water_sample):
        """Test that all sample list views load successfully."""
        client.force_login(admin_user)

        sample_models = [
            ("fairdm_demo_rocksample", "Rock Sample"),
            ("fairdm_demo_watersample", "Water Sample"),
        ]

        for model_name, display_name in sample_models:
            url = reverse(f"admin:{model_name}_changelist")
            response = client.get(url)

            assert response.status_code == 200, f"{display_name} list view failed to load"

    def test_all_sample_change_views_load(self, admin_user, client, rock_sample, water_sample):
        """Test that all sample change views load successfully."""
        client.force_login(admin_user)

        samples = [
            (rock_sample, "Rock Sample", "fairdm_demo_rocksample"),
            (water_sample, "Water Sample", "fairdm_demo_watersample"),
        ]

        for sample, display_name, model_name in samples:
            url = reverse(f"admin:{model_name}_change", args=[sample.pk])
            response = client.get(url)

            assert response.status_code == 200, f"{display_name} change view failed to load"
            assert sample.name in str(response.content)
