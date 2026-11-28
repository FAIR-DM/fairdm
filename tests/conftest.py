"""Root-level pytest configuration for FairDM tests."""

import importlib.util
import os
import re
import threading
import time
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from django.core.management import call_command
from django.core.signals import request_finished, request_started

from fairdm.factories import DatasetFactory, ProjectFactory, UserFactory
from tests.test_contrib.test_autocomplete.conftest import in_request  # noqa: F401


def pytest_collection_modifyitems(items):
    """Mark every browser test ``e2e``, then queue the slow and browser tests first.

    A test is a browser test when its fixtures reach Playwright's ``browser``. Marking
    it here means a new browser test cannot miss the marker, and
    ``pytest -m "not e2e and not slow"`` is the whole suite without them.

    ``--dist=loadscope`` hands out one class or module at a time in collection order. A
    slow test collected late starts late and sets the suite's wall time.
    """
    for item in items:
        if "browser" in item.fixturenames:
            item.add_marker(pytest.mark.e2e)
    items.sort(
        key=lambda item: (
            item.get_closest_marker("slow") is None
            and item.get_closest_marker("e2e") is None
        )
    )


def seed_session_data():
    """Write the data every test may rely on: the licences and FairDM's vocabularies."""
    # Seed the recommended licences through the real deployment path
    # (`fairdm/management/commands/seed_licenses.py`), the route a portal takes.
    call_command("seed_licenses", verbosity=0)
    # Read from the copies `CONTROLLED_VOCABULARIES` declares, never over the network.
    call_command("sync_vocabularies", verbosity=0)


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        seed_session_data()


@pytest.fixture
def reseeded_after_flush(django_db_blocker):
    """Write the session's data again once a transactional test has flushed it.

    A transactional test empties every table when it ends, and the tests that run after
    it on the same worker still expect the licences and vocabularies. Request this
    before ``transactional_db``, so its teardown runs after the flush.
    """
    yield
    with django_db_blocker.unblock():
        seed_session_data()


@pytest.fixture
def filter_placement():
    """Return a function sorting a list page's filter fields into toolbar and panel."""

    def place(response):
        """Return the field names drawn in the toolbar and those in the filter panel.

        Args:
            response: The rendered list or table page.

        Returns:
            A ``(toolbar, panel)`` pair of sets of field names.
        """
        soup = BeautifulSoup(response.content, "html.parser")
        form = soup.select_one("form#filterForm")
        panel = soup.select_one("#filters")
        in_panel = {tag["name"] for tag in panel.select("[name]")} if panel else set()
        in_form = {tag["name"] for tag in form.select("[name]")}
        return in_form - in_panel, in_panel

    return place


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def authenticated_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture
def project(user):
    return ProjectFactory(owner=user)


@pytest.fixture
def disconnect_shipped_role_guard():
    # The guard refuses to delete or rename a shipped role, bulk deletes included. Tests that need
    # a shipped role missing switch it off.
    from django.contrib.auth.models import Group
    from django.db.models.signals import pre_delete, pre_save

    from fairdm.contrib.contributors.receivers import (
        refuse_shipped_role_deletion,
        refuse_shipped_role_rename,
    )

    pre_delete.disconnect(
        refuse_shipped_role_deletion,
        sender=Group,
        dispatch_uid="contributors.refuse_shipped_role_deletion",
    )
    pre_save.disconnect(
        refuse_shipped_role_rename,
        sender=Group,
        dispatch_uid="contributors.refuse_shipped_role_rename",
    )
    try:
        yield
    finally:
        pre_delete.connect(
            refuse_shipped_role_deletion,
            sender=Group,
            dispatch_uid="contributors.refuse_shipped_role_deletion",
        )
        pre_save.connect(
            refuse_shipped_role_rename,
            sender=Group,
            dispatch_uid="contributors.refuse_shipped_role_rename",
        )


@pytest.fixture
def project_with_datasets():
    project = ProjectFactory()
    datasets = DatasetFactory.create_batch(3, project=project)
    return project, datasets


# Browser tests -------------------------------------------------------------------


def _browser_is_installed():
    """True when Playwright is importable and its browser is downloaded.

    Installing the package is one step and downloading the browser is another, so a
    machine that has the dependency but never ran ``playwright install`` would error at
    launch instead of skipping.
    """
    if importlib.util.find_spec("playwright") is None:
        return False

    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            return Path(p.chromium.executable_path).exists()
    except Exception:
        return False


def _should_skip_browser_tests(has_browser, env):
    """Decide whether browser tests skip, given the browser and the environment.

    Locally a missing browser is ordinary: a contributor who has not run
    ``playwright install chromium`` sees skips, not a wall of errors. In CI it is a
    failure, because the workflow installs the browser, and skipping there would read
    as a pass on the checks page.

    Args:
        has_browser: Whether Playwright's Chromium is downloaded.
        env: The environment variables.

    Returns:
        True when the tests should skip.
    """
    if has_browser:
        return False
    return env.get("CI", "").lower() not in {"1", "true"}


requires_browser = pytest.mark.skipif(
    _should_skip_browser_tests(_browser_is_installed(), os.environ),
    reason="playwright browser not installed (run: playwright install chromium)",
)

#: How long a browser action, a navigation or an ``expect`` waits.
BROWSER_TIMEOUT_MS = 20_000

VENDORED = Path(__file__).resolve().parent / "fixtures" / "vendor"

_ICONS = r"https://cdn\.jsdelivr\.net/npm/bootstrap-icons@1\.13\.1/font/"

#: What the browser tests serve in place of the hosts a page asks for, so no browser
#: test needs the network: ``(address pattern, file to send, content type)``. The
#: pattern matches the whole URL. Each file is a copy of the published release, and
#: the page's integrity hash is checked against it.
STAND_INS = (
    (
        re.compile(
            r"https://cdn\.jsdelivr\.net/npm/htmx\.org@2\.0\.10/dist/htmx\.min\.js"
        ),
        VENDORED / "htmx.min.js",
        "application/javascript",
    ),
    (
        re.compile(_ICONS + r"bootstrap-icons\.min\.css"),
        VENDORED / "bootstrap-icons.min.css",
        "text/css",
    ),
    (
        re.compile(_ICONS + r"fonts/bootstrap-icons\.woff2(?:\?.*)?"),
        VENDORED / "bootstrap-icons.woff2",
        "font/woff2",
    ),
)

#: Every web address that is not on this machine. Only these go through Python: a
#: test that waits with ``wait_until`` does not run Playwright, so a request held for
#: Python's answer would stall until the test's next browser call.
OFF_THIS_MACHINE = re.compile(
    r"^https?://(?!(?:localhost|127\.0\.0\.1|\[::1\])(?::\d+)?(?:/|$))"
)


def wait_until(condition, timeout=5.0, interval=0.02):
    """Poll ``condition`` until it is true, for state on the server side.

    A browser event reaches the test only during a Playwright call, so this never sees
    one. Wait for those with ``page.expect_event``.

    Args:
        condition: A callable returning a truthy value once the state is reached.
        timeout: Seconds to wait before failing.
        interval: Seconds between looks.
    """
    deadline = time.monotonic() + timeout
    while not condition():
        assert time.monotonic() < deadline, "the state was never reached"
        time.sleep(interval)


def wait_until_still(page):
    """Wait until no htmx request is in flight and nothing is moving.

    No htmx request is in flight, no swap is settling and no CSS transition is running,
    for two animation frames in a row. A swap is settled only then: htmx scrolls the
    page back to the top as it finishes. This is the state a fixed pause after a
    gesture would stand in for.

    Args:
        page: The Playwright page.

    Raises:
        AssertionError: If the page is still busy after about 600 frames.
    """
    still = page.evaluate(
        """async () => {
          const frame = () => new Promise(done => requestAnimationFrame(done));
          const busy = () => document.querySelector(
            '.htmx-request, .htmx-swapping, .htmx-settling, .htmx-added'
          ) || document.getAnimations().some(a => a instanceof CSSTransition);
          let quiet = 0;
          for (let tries = 0; tries < 600 && quiet < 2; tries++) {
            await frame();
            quiet = busy() ? 0 : quiet + 1;
          }
          return quiet >= 2;
        }"""
    )
    assert still, "the page never came to rest"


def answer_request(route, request, external):
    """Answer one request a browser context makes.

    Only requests to other machines reach this function (see ``OFF_THIS_MACHINE``).
    One to an address in ``STAND_INS`` is answered from the repository. Any other is
    refused and recorded in ``external``, which fails the test when it ends, so a page
    cannot reach the network without a test noticing.

    Args:
        route: The Playwright route for the request.
        request: The Playwright request.
        external: A list that collects ``"METHOD url"`` for each refused request.
    """
    url = request.url
    for pattern, path, content_type in STAND_INS:
        if pattern.fullmatch(url):
            try:
                body = path.read_bytes()
            except OSError as error:
                # An unanswered route hangs the page until its timeout and hides why.
                external.append(
                    f"{request.method} {url} (stand-in unreadable: {error})"
                )
                route.abort("failed")
                return
            route.fulfill(
                body=body,
                content_type=content_type,
                headers={"access-control-allow-origin": "*"},
            )
            return
    external.append(f"{request.method} {url}")
    route.abort("blockedbyclient")


def _configure_context(context, external):
    """Apply the suite's timeouts to a browser context and keep it off the network.

    Args:
        context: The Playwright browser context.
        external: The list that ``answer_request`` records refused requests in.
    """
    context.set_default_timeout(BROWSER_TIMEOUT_MS)
    context.set_default_navigation_timeout(BROWSER_TIMEOUT_MS)
    # Routing turns the browser's HTTP cache off for the context.
    context.route(
        OFF_THIS_MACHINE,
        lambda route, request: answer_request(route, request, external),
    )


class RequestsInFlight:
    """Count the requests the live server is answering at this moment.

    The live server answers in threads of its own, and a setting a test changed is read
    by them. A value put back while a request is still being answered is read half-way,
    and the next test inherits the last one's page. Waiting for this count to reach zero
    is what puts it back between requests.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._count = 0

    def _started(self, **kwargs):
        with self._lock:
            self._count += 1

    def _finished(self, **kwargs):
        with self._lock:
            # A request that began before ``watch`` still finishes after it.
            self._count = max(0, self._count - 1)

    def watch(self):
        """Start counting."""
        request_started.connect(self._started, weak=False)
        request_finished.connect(self._finished, weak=False)

    def stop(self):
        """Stop counting."""
        request_started.disconnect(self._started)
        request_finished.disconnect(self._finished)

    def wait_until_idle(self):
        """Wait until the live server has finished every request it was sent."""
        wait_until(lambda: self._count == 0, timeout=15)


@pytest.fixture
def requests_in_flight():
    """The live server's request count, and an idle server before the test ends.

    A browser test's pages are closed before this fixture ends, and the test's
    ``monkeypatch`` undoes after it, so a value the test set with ``monkeypatch`` is put
    back only once no request can still be reading it. Settings changed through the
    ``settings`` fixture are put back earlier and are not covered.
    """
    counter = RequestsInFlight()
    counter.watch()
    yield counter
    try:
        counter.wait_until_idle()
    finally:
        counter.stop()


@pytest.fixture(autouse=True)
def _browser_defaults(request, monkeypatch):
    """Give every browser context a timeout that survives a loaded runner, keep it off
    the network, and fail the test that reached out to it.

    The contexts a test opens itself through ``browser.new_context`` or
    ``browser.new_page`` are configured the same way as the ``page`` fixture's. This
    fixture is set up before the others a test asks for, so it ends after them: the
    pages are closed by the time it checks.
    """
    if "browser" not in request.fixturenames:
        yield
        return
    from playwright.sync_api import expect

    expect.set_options(timeout=BROWSER_TIMEOUT_MS)
    external = []
    request.getfixturevalue("requests_in_flight")
    browser = request.getfixturevalue("browser")
    new_context, new_page = browser.new_context, browser.new_page

    def configured_context(*args, **kwargs):
        context = new_context(*args, **kwargs)
        _configure_context(context, external)
        return context

    def configured_page(*args, **kwargs):
        page = new_page(*args, **kwargs)
        _configure_context(page.context, external)
        return page

    monkeypatch.setattr(browser, "new_context", configured_context)
    monkeypatch.setattr(browser, "new_page", configured_page)
    yield
    assert not external, (
        "the browser test reached the network. Vendor what the page asks for "
        "(see STAND_INS in tests/conftest.py): " + ", ".join(external)
    )
