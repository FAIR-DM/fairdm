"""Tests for the browser-test support in ``tests/conftest.py``.

The browser fixtures fail quietly when they are wrong. A guard that skips in CI turns
every browser test into a green skip, and an offline guard that lets a request through
makes a test depend on the network without anyone noticing.
"""

import pytest
from playwright.sync_api import expect

from tests.conftest import (
    OFF_THIS_MACHINE,
    STAND_INS,
    RequestsInFlight,
    _should_skip_browser_tests,
    answer_request,
    requires_browser,
    wait_until,
    wait_until_still,
)


class TestShouldSkipBrowserTests:
    @pytest.mark.parametrize(
        ("has_browser", "env", "skips"),
        [
            (True, {}, False),
            (False, {}, True),
            (False, {"CI": "true"}, False),
            (False, {"CI": ""}, True),
        ],
        ids=["browser present", "missing locally", "missing in CI", "empty CI variable"],
    )
    def test_a_missing_browser_skips_only_outside_ci(self, has_browser, env, skips):
        assert _should_skip_browser_tests(has_browser, env) is skips


class FakeRoute:
    """The answers a Playwright route can give, recorded."""

    def __init__(self):
        self.answer = None
        self.body = None

    def abort(self, reason):
        self.answer = "abort"

    def fulfill(self, body, content_type, headers):
        self.answer = "fulfill"
        self.body = body


class FakeRequest:
    method = "GET"

    def __init__(self, url):
        self.url = url


def answer(url):
    route, external = FakeRoute(), []
    answer_request(route, FakeRequest(url), external)
    return route, external


class TestAnswerRequest:
    def test_a_request_to_any_other_host_is_refused_and_recorded(self):
        route, external = answer("https://example.com/tracker.js")

        assert route.answer == "abort"
        assert external == ["GET https://example.com/tracker.js"]

    def test_a_stand_in_is_answered_from_its_file_and_not_recorded(self):
        pattern, path, _ = STAND_INS[0]
        url = "https://cdn.jsdelivr.net/npm/htmx.org@2.0.10/dist/htmx.min.js"
        assert pattern.fullmatch(url)

        route, external = answer(url)

        assert (route.answer, route.body, external) == ("fulfill", path.read_bytes(), [])


class TestOffThisMachine:
    def test_only_addresses_on_other_machines_match(self):
        addresses = {
            "http://localhost:8123/datasets/": False,
            "http://127.0.0.1:41233/": False,
            "http://[::1]:8000/x": False,
            "https://example.com/localhost/": True,
            "http://localhost.example.com/": True,
            "https://cdn.jsdelivr.net/npm/htmx.org@2.0.10/dist/htmx.min.js": True,
        }

        matched = {url: bool(OFF_THIS_MACHINE.match(url)) for url in addresses}

        assert matched == addresses


class TestRequestsInFlight:
    def test_the_server_is_idle_once_every_request_it_started_has_finished(self):
        counter = RequestsInFlight()

        counter._started()
        counter._started()
        counter._finished()
        with pytest.raises(AssertionError):
            wait_until(lambda: counter._count == 0, timeout=0.05)
        counter._finished()

        counter.wait_until_idle()

    def test_a_request_that_began_before_counting_does_not_count_below_zero(self):
        counter = RequestsInFlight()

        counter._finished()

        assert counter._count == 0


@requires_browser
class TestWaitUntilStill:
    def test_it_returns_only_after_an_htmx_request_has_finished(self, page):
        page.set_content(
            """<body class="htmx-request"><script>
              setTimeout(() => document.body.classList.remove('htmx-request'), 300);
            </script></body>"""
        )

        wait_until_still(page)

        expect(page.locator("body")).not_to_have_class("htmx-request")
