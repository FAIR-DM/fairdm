"""Fixtures for the contributor pages: a way to request and read a page as a given viewer."""

import pytest
from allauth.socialaccount.models import SocialAccount
from bs4 import BeautifulSoup
from django.test import Client


@pytest.fixture
def get_page():
    """Request a path as a viewer and return the response and its parsed HTML.

    The viewer is a contributor to sign in as, or None for a visitor.
    """

    def get(path, viewer=None):
        browser = Client()
        if viewer is not None:
            browser.force_login(viewer)
        response = browser.get(path)
        return response, BeautifulSoup(response.content.decode(), "html.parser")

    return get


@pytest.fixture
def orcid_signed_in():
    """Record that a person has signed in with ORCID."""

    def connect(person):
        return SocialAccount.objects.create(
            user=person, provider="orcid", uid=f"orcid-{person.pk}"
        )

    return connect
