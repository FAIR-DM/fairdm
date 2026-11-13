"""Tests for the shared overview page skeleton, ``overview/page.html``."""

import json
from urllib.parse import quote

import pytest
from bs4 import BeautifulSoup
from django.contrib.gis.geos import Point

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.core.vocabularies import IDENTIFIER_TYPES
from fairdm.factories import (
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.utils.choices import Visibility

SIDE_COLUMN_MARKERS = [
    "READINESS-MARKER",
    "CITATION-MARKER",
    "DETAILS-MARKER",
    "IDENTIFIER-MARKER",
    "FUNDER-MARKER",
    "TIMELINE-MARKER",
    "PEOPLE-MARKER",
    "FACTS-MARKER",
]


@pytest.fixture
def page_context(db):
    """Everything the skeleton reads from the context, with a marker on each side-column card."""
    person = PersonFactory(name="PEOPLE-MARKER")
    return {
        "record": ProjectFactory(),
        "overview_icon": "project",
        "can_manage": True,
        "readiness": {
            "items": [{"label": "an item", "done": False, "url": None}],
            "done": 0,
            "total": 1,
            "ready": False,
            "title": "READINESS-MARKER",
            "summary": "nothing yet",
            "about": "why it matters",
        },
        "details": [{"label": "DETAILS-MARKER", "icon": "info", "text": "a value"}],
        "people": {
            "named": [{"contributor": person, "roles": [], "more_roles": 0}],
            "faces": [],
            "more": 0,
            "total": 1,
        },
        "identifiers": [
            {
                "type": f"{IDENTIFIER_TYPES}/doi",
                "value": "10.1234/IDENTIFIER-MARKER",
                "link": None,
            }
        ],
        "funding": [{"funderName": "FUNDER-MARKER"}],
        "citation": {
            "title": "Citation",
            "formats": [
                {
                    "key": "text",
                    "label": "Text",
                    "value": "CITATION-MARKER",
                    "url": None,
                    "download": False,
                }
            ],
        },
    }


def _positions(html, markers):
    return [html.index(marker) for marker in markers]


@pytest.mark.django_db
class TestSideColumn:
    def test_the_cards_come_in_the_documented_order(
        self, child_template, render_template, page_context
    ):
        name = child_template(
            """{% extends "overview/page.html" %}
            {% block overview.timeline %}<p>TIMELINE-MARKER</p>{% endblock %}
            {% block overview.record_facts %}<p>FACTS-MARKER</p>{% endblock %}"""
        )

        html = render_template(name, page_context)

        positions = _positions(html, SIDE_COLUMN_MARKERS)
        assert positions == sorted(positions)

    def test_a_record_without_a_readiness_checklist_gets_no_readiness_card(
        self, render_template, page_context
    ):
        del page_context["readiness"]

        html = render_template("overview/page.html", page_context)

        assert "READINESS-MARKER" not in html

    def test_the_people_card_shows_when_nobody_is_credited(
        self, render_template, page_context
    ):
        page_context["people"] = {"named": [], "faces": [], "more": 0, "total": 0}

        html = render_template("overview/page.html", page_context)

        assert 'data-card="people"' in html
        assert "PEOPLE-MARKER" not in html

    def test_the_side_column_is_one_block_a_template_can_replace(
        self, child_template, render_template, page_context
    ):
        name = child_template(
            """{% extends "overview/page.html" %}
            {% block overview.side %}<p>ONLY-THIS</p>{% endblock %}"""
        )

        html = render_template(name, page_context)

        assert "ONLY-THIS" in html
        assert "CITATION-MARKER" not in html


@pytest.mark.django_db
class TestABlockThatWrapsOthersKeepsItsContent:
    def test_adding_to_the_side_column_keeps_its_cards(
        self, child_template, render_template, page_context
    ):
        name = child_template(
            """{% extends "overview/page.html" %}
            {% block overview.side %}{{ block.super }}<p>EXTRA-CARD</p>{% endblock %}"""
        )

        html = render_template(name, page_context)

        assert "EXTRA-CARD" in html
        assert "DETAILS-MARKER" in html
        assert "CITATION-MARKER" in html

    def test_adding_to_the_details_card_keeps_its_rows(
        self, child_template, render_template, page_context
    ):
        name = child_template(
            """{% extends "overview/page.html" %}
            {% block overview.details %}{{ block.super }}<p>AFTER-DETAILS</p>{% endblock %}"""
        )

        html = render_template(name, page_context)

        assert "DETAILS-MARKER" in html
        assert html.index("DETAILS-MARKER") < html.index("AFTER-DETAILS")

    def test_a_section_added_inside_details_sits_beside_its_rows(
        self, child_template, render_template, page_context
    ):
        name = child_template(
            """{% extends "overview/page.html" %}
            {% block overview.details_extra %}<p>SECTION-INSIDE</p>{% endblock %}"""
        )

        html = render_template(name, page_context)

        assert html.index("DETAILS-MARKER") < html.index("SECTION-INSIDE")
        assert html.index("SECTION-INSIDE") < html.index("IDENTIFIER-MARKER")

    def test_a_page_that_fills_the_wide_column_can_be_added_to_by_a_type_template(
        self, child_template, render_template, page_context
    ):
        child_template(
            """{% extends "overview/page.html" %}
            {% block overview.main %}<p>RECORD-CONTENT</p>{% endblock %}""",
            name="record.html",
        )
        name = child_template(
            """{% extends "record.html" %}
            {% block overview.main %}{{ block.super }}<p>TYPE-CONTENT</p>{% endblock %}""",
            name="type.html",
        )

        html = render_template(name, page_context)

        assert html.index("RECORD-CONTENT") < html.index("TYPE-CONTENT")


@pytest.mark.django_db
class TestHeader:
    def test_the_people_row_names_each_person_linked_to_their_page(
        self, render_template, page_context
    ):
        leader = PersonFactory(name="Leader Person")
        page_context["header_people"] = [leader]
        page_context["header_people_label"] = "Leaders"

        html = render_template("overview/page.html", page_context)

        assert f'href="{leader.get_absolute_url()}"' in html
        assert str(leader) in html

    def test_the_people_row_is_left_out_when_the_record_names_nobody(
        self, render_template, page_context
    ):
        html = render_template("overview/page.html", page_context)

        assert 'aria-label="Leaders"' not in html

    def test_a_template_can_replace_the_people_row_by_its_block_name(
        self, child_template, render_template, page_context
    ):
        page_context["header_people"] = [PersonFactory()]
        page_context["header_people_label"] = "Leaders"
        name = child_template(
            """{% extends "overview/page.html" %}
            {% block overview.byline %}<p>OWN-BYLINE</p>{% endblock %}"""
        )

        html = render_template(name, page_context)

        assert "OWN-BYLINE" in html
        assert 'aria-label="Leaders"' not in html


@pytest.mark.django_db
class TestHeaderImage:
    def test_a_record_with_an_image_opens_it_at_full_size(
        self, render_template, page_context, soup
    ):
        record = ProjectFactory(with_image=True)
        page_context.update(record=record, cover_image=record.image)

        page = soup(render_template("overview/page.html", page_context))

        opener = page.select_one("button[data-opens]")
        dialog = page.find(id=opener["data-opens"])
        assert dialog.name == "dialog"
        assert dialog.find("img")["src"] == record.image.url

    def test_a_record_without_an_image_has_nothing_to_open(
        self, render_template, page_context, soup
    ):
        page = soup(render_template("overview/page.html", page_context))

        assert page.select_one("button[data-opens]") is None
        assert page.find("dialog") is None


@pytest.mark.django_db
class TestHeaderEditing:
    def test_the_header_edits_the_details_and_the_keywords(
        self, render_template, page_context, soup
    ):
        page_context["edit"] = {"details": "/details/", "keywords": "/keywords/"}

        page = soup(render_template("overview/page.html", page_context))

        header = page.find("header")
        assert {"/details/", "/keywords/"} <= {a["href"] for a in header("a")}

    def test_a_record_with_no_keywords_offers_its_team_a_way_to_add_them(
        self, render_template, page_context, soup
    ):
        page_context["edit"] = {"keywords": "/keywords/"}

        page = soup(render_template("overview/page.html", page_context))

        keywords = page.select_one("header ul[aria-label]:has(a[href='/keywords/'])")
        assert keywords is not None
        assert keywords.select(".badge") == []

    def test_a_viewer_who_may_not_edit_gets_no_editing_link(
        self, render_template, page_context, soup
    ):
        page_context["edit"] = {}

        page = soup(render_template("overview/page.html", page_context))

        assert page.select(".ov-edit") == []


@pytest.mark.django_db
class TestChartLibrary:
    def test_the_page_loads_the_chart_library_only_when_it_has_a_chart(
        self, render_template, page_context
    ):
        without = render_template("overview/page.html", page_context)
        with_chart = render_template(
            "overview/page.html", {**page_context, "has_charts": True}
        )

        assert "echarts@" not in without
        assert "echarts@" in with_chart

    def test_a_template_can_serve_the_chart_library_itself(
        self, child_template, render_template, page_context
    ):
        name = child_template(
            """{% extends "overview/page.html" %}
            {% block overview.chart_library %}<script src="/own/echarts.js"></script>{% endblock %}"""
        )

        html = render_template(name, {**page_context, "has_charts": True})

        assert "/own/echarts.js" in html
        assert "echarts@" not in html


@pytest.mark.django_db
class TestMapLibrary:
    def test_the_page_loads_the_map_library_only_when_it_has_a_map(
        self, render_template, page_context
    ):
        without = render_template("overview/page.html", page_context)
        with_map = render_template(
            "overview/page.html", {**page_context, "has_map": True}
        )

        assert "maplibre-gl@" not in without
        assert "maplibre-gl@" in with_map

    def test_a_template_can_serve_the_map_library_itself(
        self, child_template, render_template, page_context
    ):
        name = child_template(
            """{% extends "overview/page.html" %}
            {% block overview.map_library %}
              <script src="/own/maplibre.js"></script>
            {% endblock %}"""
        )

        html = render_template(name, {**page_context, "has_map": True})

        assert "/own/maplibre.js" in html
        assert "maplibre-gl@" not in html


def _public_dataset():
    return DatasetFactory(
        project=ProjectFactory(visibility=Visibility.PUBLIC),
        visibility=Visibility.PUBLIC,
        published=True,
    )


def _public_sample():
    return RockSampleFactory(dataset=_public_dataset())


def _public_measurement():
    dataset = _public_dataset()
    return ExampleMeasurementFactory(
        dataset=dataset, sample=RockSampleFactory(dataset=dataset)
    )


RECORDS = {
    "project": lambda: ProjectFactory(visibility=Visibility.PUBLIC),
    "dataset": _public_dataset,
    "sample": _public_sample,
    "measurement": _public_measurement,
    "person": lambda: PersonFactory(is_active=True, is_claimed=True),
    "organization": OrganizationFactory,
}


@pytest.mark.django_db
class TestPermalinkOnEveryOverviewPage:
    @pytest.fixture(params=RECORDS)
    def shown(self, request, client):
        """A record of one kind, its absolute permalink and its overview page."""
        record = RECORDS[request.param]()
        response = client.get(record.get_absolute_url())
        assert response.status_code == 200
        permalink = f"http://testserver/{record.uuid}/"
        return permalink, BeautifulSoup(response.content, "html.parser")

    def test_the_identifiers_card_lists_the_permalink_and_copies_it(self, shown):
        permalink, page = shown

        card = page.select_one("[data-card=identifiers]")

        assert card.select_one(f"a[href='{permalink}']") is not None
        copies = [b.get("data-copy", "") + b.get("onclick", "") for b in card("button")]
        assert any(permalink in copy for copy in copies)

    def test_every_choice_in_the_share_menu_carries_the_permalink(self, shown):
        permalink, page = shown

        copy_link = page.select_one("a[onclick*=clipboard]")
        choices = copy_link.find_parent("ul").select("a")

        assert len(choices) > 1
        for choice in choices:
            address = choice.get("href", "") + choice.get("onclick", "")
            assert permalink in address or quote(permalink) in address


@pytest.mark.django_db
class TestSampleMapOnTheOverviewPage:
    @pytest.fixture(params=["project", "dataset"])
    def kind(self, request):
        return request.param

    def page_of(self, kind, client, *, located):
        """Open a public record's overview; its dataset holds one sample if asked."""
        dataset = _public_dataset()
        record = dataset.project if kind == "project" else dataset
        if located is not None:
            RockSampleFactory(
                dataset=dataset,
                location=Point(7.9, 48.9, srid=4326) if located else None,
            )
        response = client.get(record.get_absolute_url())
        assert response.status_code == 200
        return BeautifulSoup(response.content, "html.parser"), record

    def test_a_record_without_samples_shows_no_coverage_panel(self, kind, client):
        page, _ = self.page_of(kind, client, located=None)

        assert page.select_one("[data-card=coverage]") is None

    def test_located_samples_give_the_map_and_load_the_map_library(self, kind, client):
        page, record = self.page_of(kind, client, located=True)

        element = page.select_one("[data-card=coverage] [data-map]")
        assert (
            element["data-points-url"] == f"{record.get_absolute_url()}sample-points/"
        )
        assert any("maplibre-gl@" in (s.get("src") or "") for s in page("script"))

    def test_samples_none_of_which_is_located_give_the_panel_without_a_map(
        self, kind, client
    ):
        page, _ = self.page_of(kind, client, located=False)

        assert page.select_one("[data-card=coverage]") is not None
        assert page.select_one("[data-map]") is None
        assert not any("maplibre-gl@" in (s.get("src") or "") for s in page("script"))


class TestCitePanelOnEveryRecordPage:
    @pytest.fixture(params=["project", "dataset", "sample", "measurement"])
    def shown(self, request, client):
        """A record of one kind, its overview page, and the app it belongs to."""
        record = RECORDS[request.param]()
        response = client.get(record.get_absolute_url())
        assert response.status_code == 200
        return record, BeautifulSoup(response.content, "html.parser")

    def test_the_panel_offers_text_bibtex_and_ris(self, shown):
        _, page = shown

        tabs = page.select("#cite [role=tablist] [role=tab]")

        assert [t["data-format"] for t in tabs] == ["text", "bibtex", "ris"]

    def test_each_format_carries_the_address_that_serves_it(self, shown):
        record, page = shown
        page_address = record.get_absolute_url()

        formats = json.loads(page.find(id="cite-formats").string)

        assert [f["key"] for f in formats] == ["text", "bibtex", "ris"]
        by_key = {f["key"]: f for f in formats}
        for key in ("bibtex", "ris"):
            assert by_key[key]["download"] is True
            assert by_key[key]["url"] == f"{page_address}cite/{key}/"
        assert by_key["text"]["download"] is False
