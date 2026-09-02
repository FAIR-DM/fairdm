"""T042-T046: the navigation entries `CollectionsConfig.populate_data_collection_menu()`
builds under Samples and Measurements (US4), and the crash-safety and empty-heading
rules the menu tree needs to honour them."""

import pytest

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
