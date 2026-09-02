"""T042-T046: the navigation entries `CollectionsConfig.populate_data_collection_menu()`
builds under Samples and Measurements (US4), and the crash-safety and empty-heading
rules the menu tree needs to honour them."""

import pytest
from django.apps import apps as django_apps
from django.urls import reverse
from flex_menu import Menu
from mvp.menus import MenuCollapse

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


@pytest.mark.django_db
class TestEmptyRegistryHidesItsHeading:
    """T045, FR-040, Acceptance Scenario 5: a portal with no registered types of one
    kind shows no heading for it. Asserted against an empty registry, not the
    populated demo, where it would pass without exercising anything.

    The Samples/Measurements node is pre-created empty, mirroring how
    `fairdm/menus/menus.py` declares it unconditionally, at import, before
    `populate_data_collection_menu()` ever runs - an isolated `Menu` stands in for the
    real `AppMenu` so no other test observes the mutation."""

    def _isolated_menu(self, monkeypatch):
        """Both headings pre-created empty, so whichever kind's registry this test
        does not empty still finds a node to append its real entries to."""
        from fairdm.contrib.collections import apps as apps_module

        isolated_menu = Menu("IsolatedAppMenu")
        isolated_menu.parent = None
        MenuCollapse(name="Samples", parent=isolated_menu)
        MenuCollapse(name="Measurements", parent=isolated_menu)
        monkeypatch.setattr(apps_module, "AppMenu", isolated_menu)
        return isolated_menu

    def test_samples_heading_is_invisible_when_no_sample_types_are_registered(
        self, monkeypatch, rf
    ):
        isolated_menu = self._isolated_menu(monkeypatch)
        monkeypatch.setattr(type(registry), "samples", property(lambda self: []))

        django_apps.get_app_config("collections").populate_data_collection_menu()
        processed = isolated_menu.get("Samples").process(rf.get("/"))

        assert processed.visible is False

    def test_measurements_heading_is_invisible_when_no_measurement_types_are_registered(
        self, monkeypatch, rf
    ):
        isolated_menu = self._isolated_menu(monkeypatch)
        monkeypatch.setattr(type(registry), "measurements", property(lambda self: []))

        django_apps.get_app_config("collections").populate_data_collection_menu()
        processed = isolated_menu.get("Measurements").process(rf.get("/"))

        assert processed.visible is False
