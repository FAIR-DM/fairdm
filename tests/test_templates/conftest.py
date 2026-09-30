"""Fixtures for rendering the shared overview templates and their components."""

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django_cotton import render_component


@pytest.fixture
def request_(rf):
    """A request from a visitor, for templates that read ``request``."""
    request = rf.get("/")
    request.user = AnonymousUser()
    return request


@pytest.fixture
def render_card(request_):
    """Render one ``c-card.*`` component with the given attributes and return its HTML."""

    def render(name, **attributes):
        return render_component(request_, f"card.{name}", **attributes)

    return render


@pytest.fixture
def render_template(request_):
    """Render a template by name with a context and return its HTML."""

    def render(name, context=None):
        return render_to_string(name, context or {}, request=request_)

    return render


@pytest.fixture
def child_template(settings, tmp_path):
    """Write a template into a directory the template engine searches, and return its name."""
    settings.TEMPLATES = [
        {
            **settings.TEMPLATES[0],
            "DIRS": [*settings.TEMPLATES[0]["DIRS"], tmp_path],
        }
    ]

    def write(source, name="child.html"):
        (tmp_path / name).write_text(source)
        return name

    return write


@pytest.fixture
def soup():
    """Parse rendered HTML for structural assertions."""
    return lambda html: BeautifulSoup(html, "html.parser")
