"""T042-T046: the navigation entries `CollectionsConfig.populate_data_collection_menu()`
builds under Samples and Measurements (US4), and the crash-safety and empty-heading
rules the menu tree needs to honour them."""

import pytest
from django.urls import reverse

from fairdm.menus import AppMenu
from fairdm.registry import registry


def _entry_names(collapse_name):
    """The names of every child MenuItem under one of the Samples/Measurements headings."""
    return {child.name for child in AppMenu.get(collapse_name).children}


@pytest.mark.django_db
class TestSampleNavigationEntries:
    """T042, FR-039, Acceptance Scenarios 1 and 3: every `registry.samples` model has
    an entry under Samples, named by its plural verbose name."""

    def test_every_registered_sample_type_has_an_entry_under_samples(self):
        assert registry.samples, "no sample types registered - nothing to test"
        expected = {
            registry.get_for_model(model).get_verbose_name_plural()
            for model in registry.samples
        }
        assert _entry_names("Samples") == expected


@pytest.mark.django_db
class TestMeasurementNavigationEntries:
    """T043, Acceptance Scenario 2: every `registry.measurements` model has an entry
    under Measurements, named the same way."""

    def test_every_registered_measurement_type_has_an_entry_under_measurements(self):
        assert registry.measurements, (
            "no measurement types registered - nothing to test"
        )
        expected = {
            registry.get_for_model(model).get_verbose_name_plural()
            for model in registry.measurements
        }
        assert _entry_names("Measurements") == expected


@pytest.mark.django_db
class TestNavigationEntryUrls:
    """T044, Acceptance Scenario 4: selecting a navigation entry opens that type's
    listing. Red until T047 replaces the "-collection" view names T028 retired with
    "-list" - flex_menu's `resolve_url()` swallows the `NoReverseMatch` and logs a
    warning rather than raising, so nothing else fails loudly without this test."""

    def test_a_sample_entrys_url_resolves_to_its_listing(self, rf):
        model_class = registry.samples[0]
        config = registry.get_for_model(model_class)
        entry = AppMenu.get("Samples").get(config.get_verbose_name_plural())

        processed = entry.process(rf.get("/"))

        assert processed.visible
        assert processed.url == reverse(f"{config.get_slug()}-list")

    def test_a_measurement_entrys_url_resolves_to_its_listing(self, rf):
        model_class = registry.measurements[0]
        config = registry.get_for_model(model_class)
        entry = AppMenu.get("Measurements").get(config.get_verbose_name_plural())

        processed = entry.process(rf.get("/"))

        assert processed.visible
        assert processed.url == reverse(f"{config.get_slug()}-list")
