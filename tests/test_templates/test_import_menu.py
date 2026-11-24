"""Tests for the ``c-import.import-menu`` component, the button and its dialog of types.

The component is rendered for the data ``import_chooser`` builds, and the tests read its
structure: the button that opens the dialog, the dialog's id and one link to each type's
import page. Wording and look are never asserted.
"""

import pytest
from django_cotton import render_component

from fairdm.contrib.import_export.definitions import import_definitions
from fairdm.contrib.import_export.plugins import import_chooser
from fairdm.factories import DatasetFactory


@pytest.fixture
def render_menu(request_, soup):
    """Return a function rendering the menu and parsing the HTML."""

    def render(chooser):
        """Render the menu.

        Args:
            chooser: The dialog's data, as ``import_chooser`` builds it.

        Returns:
            The parsed HTML.
        """
        return soup(
            render_component(
                request_, "import.import-menu", chooser=chooser, label="Import"
            )
        )

    return render


@pytest.mark.django_db
class TestImportMenuComponent:
    def test_each_type_is_linked_once_to_its_import_page(self, render_menu):
        dataset = DatasetFactory()
        chooser = import_chooser(dataset)

        page = render_menu(chooser)

        hrefs = [a["href"] for a in page.select("dialog a")]
        expected = [e["url"] for g in chooser["groups"] for e in g["entries"]]
        assert hrefs == expected
        assert len(expected) == len(import_definitions.all())

    @pytest.mark.parametrize("kind", ["sample", "measurement"])
    def test_a_kind_lists_only_its_own_types(self, render_menu, kind):
        chooser = import_chooser(DatasetFactory(), kind)

        page = render_menu(chooser)

        hrefs = [a["href"] for a in page.select("dialog a")]
        assert hrefs == [e["url"] for e in chooser["groups"][0]["entries"]]
        assert len(hrefs) == len(import_definitions.all(kind))

    def test_the_dialog_carries_the_choosers_id(self, render_menu):
        chooser = import_chooser(DatasetFactory(), "sample")

        page = render_menu(chooser)

        dialog = page.select_one("dialog")
        assert dialog["id"] == chooser["id"]

    def test_the_button_opens_the_dialog_by_its_id(self, render_menu):
        chooser = import_chooser(DatasetFactory(), "sample")

        page = render_menu(chooser)

        button = page.select_one("button[aria-haspopup=dialog]")
        assert chooser["id"] in button["onclick"]
