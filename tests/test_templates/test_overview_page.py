"""Tests for the shared overview page skeleton, ``overview/page.html``."""

import pytest
from fairdm.factories import PersonFactory, ProjectFactory

SIDE_COLUMN_MARKERS = [
    "READINESS-MARKER",
    "DETAILS-MARKER",
    "TIMELINE-MARKER",
    "PEOPLE-MARKER",
    "IDENTIFIER-MARKER",
    "FUNDER-MARKER",
    "CITATION-MARKER",
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
        "people": {"shown": [person], "more": 0, "total": 1},
        "identifiers": [
            {"type": "DOI", "value": "10.1234/IDENTIFIER-MARKER", "link": None}
        ],
        "funding": [{"funderName": "FUNDER-MARKER"}],
        "citation": {"title": "Citation", "text": "CITATION-MARKER"},
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

    def test_a_card_with_nobody_to_show_is_left_out(
        self, render_template, page_context
    ):
        page_context["people"] = {"shown": [], "more": 0, "total": 0}

        html = render_template("overview/page.html", page_context)

        assert "PEOPLE-MARKER" not in html
        assert "Everyone credited" not in html

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

