"""Tests for the collections app's navigation entries."""

import importlib
import sys
from pathlib import Path

import pytest
from django.apps import apps as django_apps
from django.urls import reverse
from flex_menu import Menu
from mvp.menus import MenuCollapse

import fairdm.apps
from fairdm.menus import AppMenu
from fairdm.registry import registry


def _entry_names(collapse_name):
    """The names of every child MenuItem under one of the Samples/Measurements headings."""
    return {child.name for child in AppMenu.get(collapse_name).children}


@pytest.mark.django_db
class TestSampleNavigationEntries:
    def test_every_registered_sample_type_has_an_entry_under_samples(self):
        assert registry.samples, "no sample types registered - nothing to test"
        expected = {
            registry.get_for_model(model).get_verbose_name_plural()
            for model in registry.samples
        }
        assert _entry_names("Samples") == expected


@pytest.mark.django_db
class TestMeasurementNavigationEntries:
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
    def _isolated_menu(self, monkeypatch):
        """Pre-create both headings the way the portal menu does."""
        from fairdm.contrib.collections import apps as apps_module
        from fairdm.menus.menus import _has_registered

        isolated_menu = Menu("IsolatedAppMenu")
        isolated_menu.parent = None
        MenuCollapse(
            name="Samples", check=_has_registered("samples"), parent=isolated_menu
        )
        MenuCollapse(
            name="Measurements",
            check=_has_registered("measurements"),
            parent=isolated_menu,
        )
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

    def test_the_declared_heading_hides_without_this_app_ever_running(
        self, monkeypatch, rf
    ):
        from fairdm.menus.menus import _has_registered

        monkeypatch.setattr(type(registry), "samples", property(lambda self: []))
        heading = MenuCollapse(name="Samples", check=_has_registered("samples"))

        assert heading.process(rf.get("/")).visible is False

    def test_a_heading_this_app_has_to_create_itself_also_hides(self, monkeypatch, rf):
        from fairdm.contrib.collections import apps as apps_module

        isolated_menu = Menu("IsolatedAppMenu")
        isolated_menu.parent = None
        monkeypatch.setattr(apps_module, "AppMenu", isolated_menu)
        monkeypatch.setattr(type(registry), "samples", property(lambda self: []))

        django_apps.get_app_config("collections").populate_data_collection_menu()
        processed = isolated_menu.get("Samples").process(rf.get("/"))

        assert processed.visible is False


@pytest.mark.django_db
class TestNavigationSurvivesAMissingMenuNode:
    def test_populate_data_collection_menu_recreates_missing_nodes_without_raising(
        self, monkeypatch
    ):
        from fairdm.contrib.collections import apps as apps_module

        isolated_menu = Menu("IsolatedAppMenu")
        isolated_menu.parent = None
        monkeypatch.setattr(apps_module, "AppMenu", isolated_menu)

        config = django_apps.get_app_config("collections")
        config.populate_data_collection_menu()

        assert isolated_menu.get("Samples") is not None
        assert isolated_menu.get("Measurements") is not None


class TestNavigationDoesNotDependOnThisApp:
    def test_the_framework_app_config_is_what_imports_the_menu(self):
        source = Path(fairdm.apps.__file__).read_text()
        assert "from fairdm import menus" in source, (
            "fairdm/apps.py no longer imports the menu module, so the navigation is "
            "back to depending on whichever optional app happens to import it"
        )

    def test_the_menu_module_is_loaded_once_the_framework_config_is(self):
        importlib.import_module("fairdm.apps")
        assert "fairdm.menus.menus" in sys.modules

    def test_the_core_headings_are_present(self):
        names = {str(child.name) for child in AppMenu.children}
        for expected in ("Home", "Projects", "Datasets"):
            assert expected in names
