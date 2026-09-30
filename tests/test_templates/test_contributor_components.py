"""Tests for the ``c-contributor.*`` display components.

Each component is rendered through a small template that uses it the way a portal would, and the
tests read what it delivers: which contributors appear, where they link, what a missing value
falls back to, and the markup and slots a caller can rely on. Wording is never asserted.
"""

import pytest

from fairdm.factories import PersonFactory


@pytest.fixture
def render_with(child_template, render_template):
    """Render a template source with a context and return its HTML."""

    def render(source, **context):
        return render_template(child_template(source), context)

    return render


@pytest.mark.django_db
class TestNames:
    def test_a_list_of_people_renders_every_name(self, render_with):
        people = PersonFactory.create_batch(2)

        html = render_with('<c-contributor.names :contributors="people" />', people=people)

        assert all(person.name in html for person in people)


@pytest.mark.django_db
class TestAvatar:
    def test_the_avatar_is_the_daisyui_avatar_component(self, render_with, soup):
        person = PersonFactory()

        html = render_with('<c-contributor.avatar :contributor="person" />', person=person)

        assert soup(html).select_one(".avatar") is not None

    def test_a_person_without_a_photo_shows_their_initials(self, render_with, soup):
        person = PersonFactory(first_name="Ada", last_name="Lovelace", name="Ada Lovelace")

        html = render_with('<c-contributor.avatar :contributor="person" />', person=person)

        assert soup(html).get_text(strip=True) == "AL"


@pytest.mark.django_db
class TestName:
    def test_a_person_links_to_their_page(self, render_with, soup):
        person = PersonFactory()

        html = render_with('<c-contributor.name :contributor="person" />', person=person)

        assert soup(html).find("a", string=person.name)["href"] == person.get_absolute_url()
