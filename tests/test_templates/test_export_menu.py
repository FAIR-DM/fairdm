"""Tests for the ``c-import.export-menu`` component, the menu that downloads a table.

The component is rendered for a menu like the one the export mixin builds, and the
tests read its structure: the links, their ``download`` attribute and the element the
script binds to. Wording and look are never asserted.
"""

import pytest
from django_cotton import render_component

from fairdm.contrib.import_export.exports import EXPORT_FORMATS


@pytest.fixture
def build_menu():
    """Return a function building a menu as the export mixin describes one."""

    def build(filtered):
        """Build the menu.

        Args:
            filtered: Whether a search narrows the rows.

        Returns:
            The menu, a dict with a shown and an every-row address per format.
        """
        return {
            "filtered": filtered,
            "shown": 3,
            "type_name": "rock samples",
            "formats": [
                {
                    "label": entry.label,
                    "hint": entry.hint,
                    "shown_url": f"?q=basalt&export={entry.key}",
                    "all_url": f"?export={entry.key}&scope=all",
                }
                for entry in EXPORT_FORMATS
            ],
        }

    return build


@pytest.fixture
def render_menu(request_, soup):
    """Return a function rendering the menu and parsing the HTML."""

    def render(menu):
        """Render the menu.

        Args:
            menu: The menu to draw, or None.

        Returns:
            The parsed HTML.
        """
        return soup(render_component(request_, "import.export-menu", menu=menu))

    return render


def hrefs(page):
    """Return the address of every link in the page, in order."""
    return [link["href"] for link in page.select("a")]


@pytest.mark.django_db
class TestExportMenuComponent:
    def test_an_unfiltered_menu_links_every_format_once(self, render_menu, build_menu):
        menu = build_menu(filtered=False)

        page = render_menu(menu)

        assert hrefs(page) == [entry["all_url"] for entry in menu["formats"]]

    def test_a_filtered_menu_links_every_format_for_each_choice(
        self, render_menu, build_menu
    ):
        menu = build_menu(filtered=True)

        page = render_menu(menu)

        assert sorted(hrefs(page)) == sorted(
            [entry["shown_url"] for entry in menu["formats"]]
            + [entry["all_url"] for entry in menu["formats"]]
        )

    @pytest.mark.parametrize("filtered", [False, True])
    def test_every_link_downloads(self, render_menu, build_menu, filtered):
        page = render_menu(build_menu(filtered=filtered))

        assert page.select("a")
        assert all(link.has_attr("download") for link in page.select("a"))

    def test_the_details_element_carries_the_hook_of_the_script(
        self, render_menu, build_menu
    ):
        page = render_menu(build_menu(filtered=False))

        assert len(page.select("details[data-ie-menu]")) == 1
        assert page.select_one("details[data-ie-menu] > summary")

    @pytest.mark.parametrize("menu", [None, {}])
    def test_nothing_is_drawn_without_a_menu(self, render_menu, menu):
        page = render_menu(menu)

        assert not page.select("details, a")
