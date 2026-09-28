"""Integration tests for demo app admin views."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from demo.factories import RockSampleFactory
from demo.models import (
    ExampleMeasurement,
    ICP_MS_Measurement,
    RockSample,
    WaterSample,
    XRFMeasurement,
)
from fairdm.factories import DatasetFactory

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="admin123",
    )


@pytest.fixture
def sample(db):
    return RockSampleFactory()


@pytest.fixture
def rock_sample(db):
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


@pytest.mark.django_db
class TestRockSampleAdminViews:
    def test_list_view_loads(self, admin_user, client, rock_sample):
        client.force_login(admin_user)
        url = reverse("admin:demo_rocksample_changelist")
        response = client.get(url)

        assert response.status_code == 200
        assert "Test Rock Sample" in str(response.content)

    def test_add_view_loads(self, admin_user, client):
        client.force_login(admin_user)
        url = reverse("admin:demo_rocksample_add")
        response = client.get(url)

        assert response.status_code == 200

    def test_change_view_loads(self, admin_user, client, rock_sample):
        client.force_login(admin_user)
        url = reverse("admin:demo_rocksample_change", args=[rock_sample.pk])
        response = client.get(url)

        assert response.status_code == 200
        assert "Test Rock Sample" in str(response.content)

    def test_list_view_search_works(self, admin_user, client, rock_sample):
        client.force_login(admin_user)
        url = reverse("admin:demo_rocksample_changelist")
        response = client.get(url, {"q": "Test Rock"})

        assert response.status_code == 200
        assert "Test Rock Sample" in str(response.content)

    def test_list_view_filter_works(self, admin_user, client, rock_sample):
        client.force_login(admin_user)
        url = reverse("admin:demo_rocksample_changelist")
        response = client.get(url, {"rock_type": "Igneous"})

        assert response.status_code == 200


@pytest.mark.django_db
class TestWaterSampleAdminViews:
    def test_list_view_loads(self, admin_user, client, water_sample):
        client.force_login(admin_user)
        url = reverse("admin:demo_watersample_changelist")
        response = client.get(url)

        assert response.status_code == 200
        assert "Test Water Sample" in str(response.content)

    def test_add_view_loads(self, admin_user, client):
        client.force_login(admin_user)
        url = reverse("admin:demo_watersample_add")
        response = client.get(url)

        assert response.status_code == 200

    def test_change_view_loads(self, admin_user, client, water_sample):
        client.force_login(admin_user)
        url = reverse("admin:demo_watersample_change", args=[water_sample.pk])
        response = client.get(url)

        assert response.status_code == 200
        assert "Test Water Sample" in str(response.content)


@pytest.mark.django_db
class TestExampleMeasurementAdminViews:
    def test_list_view_loads(self, admin_user, client, example_measurement):
        client.force_login(admin_user)
        url = reverse("admin:demo_examplemeasurement_changelist")
        response = client.get(url)

        assert response.status_code == 200
        assert "Test Example Measurement" in str(response.content)

    def test_add_view_loads(self, admin_user, client):
        client.force_login(admin_user)
        url = reverse("admin:demo_examplemeasurement_add")
        response = client.get(url)

        assert response.status_code == 200

    def test_change_view_loads(self, admin_user, client, example_measurement):
        client.force_login(admin_user)
        url = reverse(
            "admin:demo_examplemeasurement_change", args=[example_measurement.pk]
        )
        response = client.get(url)

        assert response.status_code == 200
        assert "Test Example Measurement" in str(response.content)

    def test_list_view_displays_custom_fields(
        self, admin_user, client, example_measurement
    ):
        client.force_login(admin_user)
        url = reverse("admin:demo_examplemeasurement_changelist")
        response = client.get(url)

        assert response.status_code == 200
        content = str(response.content)
        assert "Test Value" in content
        assert "42" in content


@pytest.mark.django_db
class TestXRFMeasurementAdminViews:
    def test_list_view_loads(self, admin_user, client, xrf_measurement):
        client.force_login(admin_user)
        url = reverse("admin:demo_xrfmeasurement_changelist")
        response = client.get(url)

        assert response.status_code == 200
        assert "Test XRF Measurement" in str(response.content)

    def test_add_view_loads(self, admin_user, client):
        client.force_login(admin_user)
        url = reverse("admin:demo_xrfmeasurement_add")
        response = client.get(url)

        assert response.status_code == 200

    def test_change_view_loads(self, admin_user, client, xrf_measurement):
        client.force_login(admin_user)
        url = reverse("admin:demo_xrfmeasurement_change", args=[xrf_measurement.pk])
        response = client.get(url)

        assert response.status_code == 200
        assert "Test XRF Measurement" in str(response.content)

    def test_list_view_displays_element_and_concentration(
        self, admin_user, client, xrf_measurement
    ):
        client.force_login(admin_user)
        url = reverse("admin:demo_xrfmeasurement_changelist")
        response = client.get(url)

        assert response.status_code == 200
        content = str(response.content)
        assert "Si" in content

    def test_list_view_filter_by_element_works(
        self, admin_user, client, xrf_measurement
    ):
        client.force_login(admin_user)
        url = reverse("admin:demo_xrfmeasurement_changelist")
        response = client.get(url, {"element": "Si"})

        assert response.status_code == 200


@pytest.mark.django_db
class TestICPMSMeasurementAdminViews:
    # The fieldsets once named a field the model lacks (detection_limit_ppb), which broke the edit view.
    def test_list_view_loads(self, admin_user, client, icp_ms_measurement):
        client.force_login(admin_user)
        url = reverse("admin:demo_icp_ms_measurement_changelist")
        response = client.get(url)

        assert response.status_code == 200
        assert "Test ICP-MS Measurement" in str(response.content)

    def test_add_view_loads(self, admin_user, client):
        client.force_login(admin_user)
        url = reverse("admin:demo_icp_ms_measurement_add")
        response = client.get(url)

        assert response.status_code == 200

    def test_change_view_loads_without_error(
        self, admin_user, client, icp_ms_measurement
    ):
        client.force_login(admin_user)
        url = reverse(
            "admin:demo_icp_ms_measurement_change", args=[icp_ms_measurement.pk]
        )
        response = client.get(url)

        assert response.status_code == 200, (
            f"Expected 200 OK, got {response.status_code}. Check admin fieldsets."
        )
        assert "Test ICP-MS Measurement" in str(response.content)

    def test_change_view_displays_all_configured_fields(
        self, admin_user, client, icp_ms_measurement
    ):
        client.force_login(admin_user)
        url = reverse(
            "admin:demo_icp_ms_measurement_change", args=[icp_ms_measurement.pk]
        )
        response = client.get(url)

        assert response.status_code == 200
        content = str(response.content)

        assert "207Pb" in content
        assert "15000" in content
        assert "120.5" in content
        assert "100" in content
        assert "115In" in content

    def test_list_view_displays_isotope_and_concentration(
        self, admin_user, client, icp_ms_measurement
    ):
        client.force_login(admin_user)
        url = reverse("admin:demo_icp_ms_measurement_changelist")
        response = client.get(url)

        assert response.status_code == 200
        content = str(response.content)
        assert "207Pb" in content

    def test_list_view_filter_by_isotope_works(
        self, admin_user, client, icp_ms_measurement
    ):
        client.force_login(admin_user)
        url = reverse("admin:demo_icp_ms_measurement_changelist")
        response = client.get(url, {"isotope": "207Pb"})

        assert response.status_code == 200

    def test_search_by_isotope_works(self, admin_user, client, icp_ms_measurement):
        client.force_login(admin_user)
        url = reverse("admin:demo_icp_ms_measurement_changelist")
        response = client.get(url, {"q": "207Pb"})

        assert response.status_code == 200
        assert "Test ICP-MS Measurement" in str(response.content)


@pytest.mark.django_db
class TestAllMeasurementAdminViewsWork:
    def test_all_measurement_list_views_load(
        self,
        admin_user,
        client,
        example_measurement,
        xrf_measurement,
        icp_ms_measurement,
    ):
        client.force_login(admin_user)

        measurement_models = [
            ("demo_examplemeasurement", "Example Measurement"),
            ("demo_xrfmeasurement", "XRF Measurement"),
            ("demo_icp_ms_measurement", "ICP-MS Measurement"),
        ]

        for model_name, display_name in measurement_models:
            url = reverse(f"admin:{model_name}_changelist")
            response = client.get(url)

            assert response.status_code == 200, (
                f"{display_name} list view failed to load"
            )

    def test_all_measurement_add_views_load(self, admin_user, client):
        client.force_login(admin_user)

        measurement_models = [
            ("demo_examplemeasurement", "Example Measurement"),
            ("demo_xrfmeasurement", "XRF Measurement"),
            ("demo_icp_ms_measurement", "ICP-MS Measurement"),
        ]

        for model_name, display_name in measurement_models:
            url = reverse(f"admin:{model_name}_add")
            response = client.get(url)

            assert response.status_code == 200, (
                f"{display_name} add view failed to load"
            )

    def test_all_measurement_change_views_load(
        self,
        admin_user,
        client,
        example_measurement,
        xrf_measurement,
        icp_ms_measurement,
    ):
        client.force_login(admin_user)

        measurements = [
            (
                example_measurement,
                "Example Measurement",
                "demo_examplemeasurement",
            ),
            (xrf_measurement, "XRF Measurement", "demo_xrfmeasurement"),
            (
                icp_ms_measurement,
                "ICP-MS Measurement",
                "demo_icp_ms_measurement",
            ),
        ]

        for measurement, display_name, model_name in measurements:
            url = reverse(f"admin:{model_name}_change", args=[measurement.pk])
            response = client.get(url)

            assert response.status_code == 200, (
                f"{display_name} change view failed to load"
            )
            assert measurement.name in str(response.content)


@pytest.mark.django_db
class TestAllSampleAdminViewsWork:
    def test_all_sample_list_views_load(
        self, admin_user, client, rock_sample, water_sample
    ):
        client.force_login(admin_user)

        sample_models = [
            ("demo_rocksample", "Rock Sample"),
            ("demo_watersample", "Water Sample"),
        ]

        for model_name, display_name in sample_models:
            url = reverse(f"admin:{model_name}_changelist")
            response = client.get(url)

            assert response.status_code == 200, (
                f"{display_name} list view failed to load"
            )

    def test_all_sample_change_views_load(
        self, admin_user, client, rock_sample, water_sample
    ):
        client.force_login(admin_user)

        samples = [
            (rock_sample, "Rock Sample", "demo_rocksample"),
            (water_sample, "Water Sample", "demo_watersample"),
        ]

        for sample, display_name, model_name in samples:
            url = reverse(f"admin:{model_name}_change", args=[sample.pk])
            response = client.get(url)

            assert response.status_code == 200, (
                f"{display_name} change view failed to load"
            )
            assert sample.name in str(response.content)
