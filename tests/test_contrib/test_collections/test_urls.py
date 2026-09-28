"""Smoke tests for every generated collection listing address."""

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from demo.models import RockSample, WaterSample
from fairdm.contrib.collections.views import DataTableView
from fairdm.registry import registry


@pytest.mark.django_db
class TestListingAddresses:
    def test_every_generated_listing_returns_200_and_reverses_by_its_list_name(
        self, client
    ):
        assert registry.samples, "no sample types registered - nothing to test"
        assert registry.measurements, (
            "no measurement types registered - nothing to test"
        )

        for model_class in [*registry.samples, *registry.measurements]:
            slug = registry.get_for_model(model_class).get_slug()
            url = reverse(f"{slug}-list")
            response = client.get(url)
            assert response.status_code == 200, (
                f"{model_class.__name__}'s listing ({url}) returned "
                f"{response.status_code}"
            )


@pytest.mark.django_db
class TestDuplicateListingAddress:
    def test_two_sample_types_with_the_same_slug_raise_improperly_configured_naming_both(
        self, monkeypatch
    ):
        rock_config = registry.get_for_model(RockSample)
        water_config = registry.get_for_model(WaterSample)
        monkeypatch.setattr(rock_config, "get_slug", lambda: "duplicate-slug")
        monkeypatch.setattr(water_config, "get_slug", lambda: "duplicate-slug")

        with pytest.raises(ImproperlyConfigured) as excinfo:
            DataTableView.get_urls()

        assert "RockSample" in str(excinfo.value)
        assert "WaterSample" in str(excinfo.value)
