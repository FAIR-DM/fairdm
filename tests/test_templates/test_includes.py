"""Tests for the includes the overview pages share: pending actions and the type badge."""

import pytest
from django_cotton import render_component

pytestmark = pytest.mark.django_db

INFO = {
    "description": "DESCRIPTION-MARKER",
    "keywords": ["KEYWORD-MARKER"],
    "authority": {"name": "AUTHORITY-MARKER", "website": "https://authority.test/"},
    "citation": {"text": "PROTOCOL-MARKER", "doi": "https://doi.org/10.1/p"},
}


class TestPendingAction:
    def _render(self, request_, **attributes):
        source = {
            "label": "Publish",
            "icon": "download",
            "reason": "REASON-MARKER",
            **attributes,
        }
        return render_component(request_, "actions.pending", **source)

    def test_the_button_is_disabled(self, request_, soup):
        button = soup(self._render(request_)).find("button")

        assert button.has_attr("disabled")

    def test_it_never_submits_or_links_anywhere(self, request_, soup):
        page = soup(self._render(request_))

        assert page.find("button")["type"] == "button"
        assert page.find("a") is None

    def test_it_says_why_to_a_pointer_and_to_a_screen_reader(self, request_, soup):
        button = soup(self._render(request_)).find("button")

        assert button["title"] == "REASON-MARKER"
        assert "REASON-MARKER" in button.find(class_="sr-only").get_text()


class TestTypeBadge:
    def _render(self, render_template, info=INFO):
        return render_template(
            "overview/includes/type_badge.html",
            {"label": "rock sample", "info": info, "id": "type-info"},
        )

    def test_a_described_type_opens_its_description_in_a_dialog(
        self, render_template, soup
    ):
        page = soup(self._render(render_template))

        button = page.find("button")
        dialog = page.find("dialog", id="type-info")
        assert button["aria-haspopup"] == "dialog"
        assert "type-info" in button["onclick"]
        assert "DESCRIPTION-MARKER" in dialog.get_text()

    def test_the_dialog_is_named_for_assistive_technology(self, render_template, soup):
        page = soup(self._render(render_template))

        dialog = page.find("dialog", id="type-info")
        named_by = dialog.get("aria-labelledby")
        assert dialog.get("aria-label") or (
            named_by and page.find(id=named_by).get_text(strip=True)
        )

    def test_the_dialog_can_be_closed_from_the_keyboard(self, render_template, soup):
        dialog = soup(self._render(render_template)).find("dialog")

        assert dialog.select("form[method=dialog] button")

    def test_the_dialog_carries_the_keywords_authority_and_protocol(
        self, render_template, soup
    ):
        dialog = soup(self._render(render_template)).find("dialog")

        text = dialog.get_text(" ", strip=True)
        assert "KEYWORD-MARKER" in text
        assert dialog.find("a", string="AUTHORITY-MARKER")["href"] == (
            "https://authority.test/"
        )
        assert dialog.find("a", string="PROTOCOL-MARKER")["href"] == (
            "https://doi.org/10.1/p"
        )

    def test_a_type_the_registry_does_not_describe_is_a_plain_badge(
        self, render_template, soup
    ):
        page = soup(self._render(render_template, info=None))

        assert page.find("button") is None
        assert page.find("dialog") is None
        assert page.find(class_="badge").get_text(strip=True) == "Rock sample"
