"""Tests for the contributor overview's cards and the ``c-missing`` notice.

Each component is rendered on its own with only its documented attributes. The tests read where
each entry links, what is counted and which card shows its empty state, found by the card's
``data-card`` attribute and the alert role, never by a sentence.
"""

import pytest
from django_cotton import render_component

from fairdm.factories import (
    AffiliationFactory,
    DatasetFactory,
    OrganizationFactory,
    ProjectFactory,
)
from fairdm.utils.choices import Visibility

ALL_URL = "/all/"


def _records(shown, more=0, total=None):
    return {"shown": shown, "more": more, "total": len(shown) + more if total is None else total}


@pytest.fixture
def render_with(child_template, render_template):
    """Render a template source with a context and return its HTML."""

    def render(source, **context):
        return render_template(child_template(source), context)

    return render


def _empty_state(card):
    return card.select_one("[role=alert]")


@pytest.mark.django_db
class TestMissing:
    def test_it_draws_its_text_in_an_alert(self, render_with, soup):
        html = render_with("<c-missing><span>SLOT-MARKER</span></c-missing>")

        alert = soup(html).select_one("[role=alert]")
        assert "SLOT-MARKER" in alert.get_text()


@pytest.mark.django_db
class TestRecordsCard:
    def _render(self, request_, records, kind="project", **overrides):
        attributes = {
            "title": "Records",
            "records": records,
            "kind": kind,
            "variant": "info",
            "all_url": ALL_URL,
            "empty": "EMPTY-MARKER",
            **overrides,
        }
        return render_component(request_, "card.records", **attributes)

    def test_each_project_links_to_its_page(self, request_, soup):
        projects = [ProjectFactory(visibility=Visibility.PUBLIC) for _ in range(2)]
        shown = [{"record": project, "owned": False} for project in projects]

        card = soup(self._render(request_, _records(shown))).select_one("[data-card]")

        hrefs = {a["href"] for a in card.select("ul a")}
        assert hrefs == {project.get_absolute_url() for project in projects}

    def test_each_dataset_links_to_its_page(self, request_, soup):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        shown = [{"record": dataset, "owned": False}]

        card = soup(
            self._render(request_, _records(shown), kind="dataset")
        ).select_one("[data-card]")

        assert card["data-card"] == "datasets"
        assert card.select_one("ul a")["href"] == dataset.get_absolute_url()

    def test_the_card_counts_all_the_records_not_only_those_shown(self, request_, soup):
        shown = [{"record": ProjectFactory(), "owned": False}]

        card = soup(self._render(request_, _records(shown, more=6))).select_one(
            "[data-card]"
        )

        assert card.select_one(".badge").get_text(strip=True) == "7"

    def test_it_offers_the_full_list_and_says_how_many_more(self, request_, soup):
        shown = [{"record": ProjectFactory(), "owned": False}]

        card = soup(self._render(request_, _records(shown, more=6))).select_one(
            "[data-card]"
        )

        to_all = card.find_all("a", href=ALL_URL)
        assert len(to_all) == 2
        assert "6" in to_all[-1].get_text()

    def test_without_more_records_it_offers_the_full_list_once(self, request_, soup):
        shown = [{"record": ProjectFactory(), "owned": False}]

        card = soup(self._render(request_, _records(shown))).select_one("[data-card]")

        assert len(card.find_all("a", href=ALL_URL)) == 1

    def test_with_nothing_it_shows_its_empty_state_and_no_list(self, request_, soup):
        card = soup(self._render(request_, _records([]))).select_one("[data-card]")

        assert "EMPTY-MARKER" in _empty_state(card).get_text()
        assert card.select_one("ul") is None
        assert card.find("a", href=ALL_URL) is None

    def test_with_nothing_it_is_not_given_a_count(self, request_, soup):
        card = soup(self._render(request_, _records([]))).select_one("[data-card]")

        assert card.select_one(".badge") is None


@pytest.mark.django_db
class TestRolesCard:
    def test_each_role_shows_its_name_and_count(self, request_, soup):
        roles = [
            {"label": "ROLE-ONE", "count": 3, "percent": 100},
            {"label": "ROLE-TWO", "count": 1, "percent": 33},
        ]

        card = soup(render_component(request_, "card.roles", roles=roles)).select_one(
            "[data-card=roles]"
        )

        assert [dt.get_text(strip=True) for dt in card.select("dt")] == [
            "ROLE-ONE",
            "ROLE-TWO",
        ]
        assert [dd.get_text() for dd in card.select("dd")][0].count("3") == 1

    def test_each_role_carries_its_share_of_the_most_held_role(self, request_, soup):
        roles = [
            {"label": "ROLE-ONE", "count": 3, "percent": 100},
            {"label": "ROLE-TWO", "count": 1, "percent": 33},
        ]

        card = soup(render_component(request_, "card.roles", roles=roles)).select_one(
            "[data-card=roles]"
        )

        assert [bar["value"] for bar in card.select("progress")] == ["100", "33"]
        assert [bar["max"] for bar in card.select("progress")] == ["100", "100"]

    def test_with_no_roles_it_shows_its_empty_state(self, request_, soup):
        card = soup(render_component(request_, "card.roles", roles=[])).select_one(
            "[data-card=roles]"
        )

        assert _empty_state(card) is not None
        assert card.select_one("dl") is None


@pytest.mark.django_db
class TestLinksCard:
    LINKS = [
        {"url": "https://github.com/someone", "host": "github.com"},
        {"url": "https://example.org/me", "host": "example.org"},
    ]

    def test_each_link_points_at_its_address_and_is_named_by_its_site(
        self, request_, soup
    ):
        card = soup(
            render_component(request_, "card.links", links=self.LINKS)
        ).select_one("[data-card=links]")

        anchors = card.select("ul a")
        assert [a["href"] for a in anchors] == [link["url"] for link in self.LINKS]
        assert [a.get_text(strip=True) for a in anchors] == ["github.com", "example.org"]

    def test_an_outside_link_does_not_hand_over_the_opener_or_the_ranking(
        self, request_, soup
    ):
        card = soup(
            render_component(request_, "card.links", links=self.LINKS)
        ).select_one("[data-card=links]")

        for anchor in card.select("ul a"):
            assert {"noopener", "nofollow"} <= set(anchor["rel"])

    def test_with_no_links_it_shows_its_empty_state(self, request_, soup):
        card = soup(render_component(request_, "card.links", links=[])).select_one(
            "[data-card=links]"
        )

        assert _empty_state(card) is not None
        assert card.select_one("ul") is None


@pytest.mark.django_db
class TestAffiliationsCard:
    def _render(self, request_, current=(), past=()):
        affiliations = {"current": list(current), "past": list(past)}
        return render_component(request_, "card.affiliations", affiliations=affiliations)

    def test_each_affiliation_links_to_its_organization(self, request_, soup):
        current = AffiliationFactory(organization=OrganizationFactory(), is_primary=True)
        past = AffiliationFactory(
            organization=OrganizationFactory(), start_date="2010", end_date="2014"
        )

        card = soup(self._render(request_, [current], [past])).select_one(
            "[data-card=affiliations]"
        )

        hrefs = [a["href"] for a in card.select("ul a")]
        assert current.organization.get_absolute_url() in hrefs
        assert past.organization.get_absolute_url() in hrefs

    def test_current_affiliations_come_before_past_ones(self, request_, soup):
        current = AffiliationFactory(organization=OrganizationFactory())
        past = AffiliationFactory(
            organization=OrganizationFactory(), start_date="2010", end_date="2014"
        )

        card = soup(self._render(request_, [current], [past])).select_one(
            "[data-card=affiliations]"
        )

        lists = card.select("ul")
        assert len(lists) == 2
        assert lists[0].select_one("a")["href"] == current.organization.get_absolute_url()
        assert lists[1].select_one("a")["href"] == past.organization.get_absolute_url()

    def test_the_period_is_shown_as_precisely_as_it_was_recorded(self, request_, soup):
        past = AffiliationFactory(start_date="2010", end_date="2014")
        past.refresh_from_db()

        card = soup(self._render(request_, past=[past])).select_one(
            "[data-card=affiliations]"
        )

        text = card.select_one("ul").get_text()
        assert past.start_display == "2010"
        assert "2010" in text
        assert "2014" in text

    def test_with_none_it_shows_its_empty_state(self, request_, soup):
        card = soup(self._render(request_)).select_one("[data-card=affiliations]")

        assert _empty_state(card) is not None
        assert card.select_one("ul") is None
