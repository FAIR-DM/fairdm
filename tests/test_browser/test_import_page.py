"""Tests for ``fairdm/static/js/import.js``, the page where a file is chosen for import.

The script shows the chosen file in the drop zone and lets the upload form be sent once.
Both happen in the browser only.
"""

import pytest
from playwright.sync_api import expect

from demo.models import RockSample  # noqa: F401
from fairdm.contrib.plugins import reverse
from tests.conftest import requires_browser, wait_until_still

pytestmark = requires_browser

ROCKS = b"name,rock_type,collection_date\nGranite A,granite,2024-06-30\n"


@pytest.fixture
def import_page(page, live_server, sign_in, editor, open_dataset):
    """The import page of rock samples, signed in as an editor of the dataset."""
    sign_in(editor)
    page.goto(live_server.url + reverse(open_dataset, "import", type="rocksample"))
    wait_until_still(page)
    return page


def choose_file(page):
    page.set_input_files(
        "[data-ie-file]",
        files=[{"name": "rocks.csv", "mimeType": "text/csv", "buffer": ROCKS}],
    )


class TestDropZone:
    def test_choosing_a_file_shows_its_name_and_size_in_place_of_the_prompt(
        self, import_page
    ):
        choose_file(import_page)

        chosen = import_page.locator("[data-ie-chosen]")
        expect(chosen).to_have_text("rocks.csv · 1 KB")
        expect(import_page.locator("[data-ie-drop-text]")).to_be_hidden()


class TestUploadForm:
    def test_a_second_submit_while_the_first_is_sent_posts_nothing(self, import_page):
        posts = []
        import_page.on(
            "request", lambda r: posts.append(r.url) if r.method == "POST" else None
        )
        choose_file(import_page)

        import_page.evaluate(
            """() => {
              const form = document.querySelector('form[data-ie-upload]');
              form.requestSubmit();
              form.requestSubmit();
            }"""
        )
        import_page.wait_for_url("**/imports/**")

        assert len(posts) == 1
