"""Fixtures for the browser tests: a live server, a database it can see and a sign-in."""

import pytest
from django.test import Client
from django.urls import reverse
from pytest_django.plugin import blocking_manager_key

from demo.factories import RockSampleFactory
from demo.models import RockSample
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.factories import ContributionFactory, DatasetFactory, PersonFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility
from tests.conftest import seed_session_data

@pytest.hookimpl(wrapper=True)
def pytest_runtest_teardown(item, nextitem):
    """Write the licences and vocabularies back after a browser test's database is flushed.

    A browser test runs against a database that commits, because the live server's threads
    cannot see a transaction the test has not committed. It is emptied when the test ends,
    and the tests that run after it on the same worker still expect the seed data.
    pytest-django empties it when the test's own fixtures end, and the teardown hook
    returns after that, whichever order the fixtures were set up in.
    """
    try:
        return (yield)
    finally:
        if "live_server" in item.fixturenames:
            with item.config.stash[blocking_manager_key].unblock():
                seed_session_data()


@pytest.fixture
def open_dataset():
    """A published dataset anyone may see."""
    return DatasetFactory(visibility=Visibility.PUBLIC, published=True)


@pytest.fixture
def rock_listing_url(open_dataset):
    """The portal's list of rock samples, with one rock in it."""
    RockSampleFactory(dataset=open_dataset)
    return reverse(f"{registry.get_for_model(RockSample).get_slug()}-list")


@pytest.fixture
def sign_in(page, live_server):
    """Return a function that signs a user into the test's browser page."""

    def sign_in(user):
        """Give the page's browser the session of ``user``.

        Args:
            user: The user to sign in.
        """
        client = Client()
        client.force_login(user)
        cookie = client.cookies["sessionid"]
        page.context.add_cookies(
            [{"name": "sessionid", "value": cookie.value, "url": live_server.url}]
        )

    return sign_in


@pytest.fixture
def editor(open_dataset):
    """A person who may import into the open dataset."""
    person = PersonFactory()
    ContributionFactory(
        content_object=open_dataset, contributor=person, level=ContributionLevel.EDIT
    )
    return person
