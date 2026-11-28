"""Tests for ``fairdm/static/js/export-menu.js``, the Export menu of a records table.

The menu is a ``<details>`` element. The script closes it on a click outside it and on
Escape, and puts focus back on its button. Only a browser runs that script, so the
rendered markup is tested with the test client elsewhere.
"""

import pytest
from playwright.sync_api import expect

from tests.conftest import requires_browser

pytestmark = requires_browser


@pytest.fixture
def menu(page, live_server, rock_listing_url):
    """The Export menu of the rock list, opened."""
    page.goto(live_server.url + rock_listing_url)
    menu = page.locator("details[data-ie-menu]")
    menu.locator("summary").click()
    expect(menu).to_have_attribute("open", "")
    return menu


class TestExportMenuClosing:
    def test_escape_closes_the_menu_and_returns_focus_to_its_button(self, page, menu):
        menu.locator("a").first.focus()

        page.keyboard.press("Escape")

        expect(menu).not_to_have_attribute("open", "")
        expect(menu.locator("summary")).to_be_focused()

    def test_a_click_outside_the_menu_closes_it(self, page, menu):
        address = page.url

        page.locator("body").click(position={"x": 1, "y": 1})

        expect(menu).not_to_have_attribute("open", "")
        assert page.url == address

    def test_a_click_inside_the_menu_keeps_it_open(self, page, menu):
        menu.locator(".ie-menu__title").first.click()

        expect(menu).to_have_attribute("open", "")
