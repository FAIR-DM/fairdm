"""Tests for the ``c-overview.*`` components the overview pages share.

Each component is rendered on its own, with only its documented attributes, and the tests read
what it delivers: the data it was given, the links it draws and the names it carries for
assistive technology. Wording is never asserted.
"""

import json
from datetime import date

import pytest
from django.utils import translation
from django.utils.formats import date_format

from fairdm.factories import OrganizationFactory, PersonFactory

pytestmark = pytest.mark.django_db


def _headings(page):
    return [h.get_text(strip=True) for h in page.select(".ov-panel__title")]


class TestEdit:
    def test_the_control_links_to_its_editing_page(self, render_overview, soup):
        page = soup(render_overview("edit", href="/edit/", label="Edit things"))

        link = page.find("a")
        assert link["href"] == "/edit/"
        assert link["aria-label"] == "Edit things"

    def test_without_an_editing_page_nothing_is_drawn(self, render_overview, soup):
        assert soup(render_overview("edit", href="")).find("a") is None


class TestPanel:
    def test_the_edit_control_and_the_full_list_sit_in_the_heading(
        self, render_overview, soup
    ):
        page = soup(
            render_overview("panel", title="T", edit_url="/edit/", more_url="/all/")
        )

        tools = page.select_one(".ov-panel__head")
        assert {a["href"] for a in tools.find_all("a")} == {"/edit/", "/all/"}

    def test_a_panel_without_either_has_no_links(self, render_overview, soup):
        page = soup(render_overview("panel", title="T"))

        assert page.find("a") is None


class TestSheet:
    @staticmethod
    def sheet(render_overview, **attributes):
        defaults = {"rows": [], "identifiers": [], "edit": {}, "api_url": ""}
        return render_overview("sheet", **{**defaults, **attributes})

    def test_a_record_row_links_to_the_record(self, render_overview, soup):
        organisation = OrganizationFactory()
        rows = [{"label": "Org", "icon": "organization", "record": organisation}]

        page = soup(self.sheet(render_overview, rows=rows))

        link = page.find("a", string=str(organisation))
        assert link["href"] == organisation.get_absolute_url()

    def test_a_row_with_a_url_links_its_text(self, render_overview, soup):
        rows = [{"label": "Licence", "text": "CC BY 4.0", "url": "https://x.test/l"}]

        page = soup(self.sheet(render_overview, rows=rows))

        assert page.find("a", string="CC BY 4.0")["href"] == "https://x.test/l"

    def test_a_row_note_is_shown_under_its_value(self, render_overview):
        rows = [{"label": "Licence", "text": "None", "note": "NOTE-MARKER"}]

        assert "NOTE-MARKER" in self.sheet(render_overview, rows=rows)

    def test_a_row_can_be_a_status_pill(self, render_overview, soup):
        rows = [{"label": "Status", "badge": "BADGE-MARKER", "badge_variant": "info"}]

        page = soup(self.sheet(render_overview, rows=rows))

        assert page.select_one(".badge").get_text(strip=True) == "BADGE-MARKER"

    def test_a_row_with_no_value_shows_a_dash_named_for_assistive_technology(
        self, render_overview, soup
    ):
        page = soup(self.sheet(render_overview, rows=[{"label": "Licence"}]))

        assert page.select_one("dd .sr-only").get_text(strip=True)

    def test_a_row_date_follows_the_active_locale(self, render_overview):
        when = date(2026, 3, 4)
        rows = [{"label": "Added", "icon": "calendar", "date": when}]

        with translation.override("de"):
            html = self.sheet(render_overview, rows=rows)
            expected = date_format(when, "SHORT_DATE_FORMAT")

        assert expected in html

    def test_the_api_address_is_offered_when_the_record_has_one(
        self, render_overview, soup
    ):
        page = soup(self.sheet(render_overview, api_url="/api/v1/thing/1/"))

        assert page.find("a", href="/api/v1/thing/1/") is not None

    def test_with_nothing_to_link_no_link_is_drawn(self, render_overview, soup):
        assert soup(self.sheet(render_overview)).find("a", href=True) is None

    def test_the_machine_metadata_downloads_are_disabled(self, render_overview, soup):
        page = soup(self.sheet(render_overview))

        assert page.find("button", disabled=True) is not None

    def test_each_part_the_viewer_may_edit_has_its_own_control(
        self, render_overview, soup
    ):
        edit = {"details": "/d/", "identifiers": "/i/", "delete": "/x/"}

        page = soup(self.sheet(render_overview, edit=edit, kind="project"))

        assert {a["href"] for a in page.find_all("a")} == {"/d/", "/i/", "/x/"}

    def test_each_identifier_is_listed_with_a_button_that_copies_it(
        self, render_overview, soup
    ):
        identifiers = [
            {"type": "DOI", "value": "10.1/x", "link": "https://doi.org/10.1/x"},
            {"type": "Grant", "value": "G-1", "link": None},
        ]

        page = soup(self.sheet(render_overview, identifiers=identifiers))

        assert page.find("a", string="10.1/x")["href"] == "https://doi.org/10.1/x"
        copied = [b["data-copy"] for b in page.select("button[data-copy]")]
        assert copied == ["https://doi.org/10.1/x", "G-1"]


class TestSheetFunding:
    AWARD = {
        "funderName": "FUNDER-NAME",
        "funderIdentifier": "https://ror.org/abc",
        "awardTitle": "AWARD-TITLE",
        "awardNumber": "AWARD-1",
        "awardURI": "https://grants.test/1",
    }

    @staticmethod
    def funding(render_overview, soup, funding, can_manage=False):
        html = render_overview(
            "sheet",
            rows=[],
            identifiers=[],
            edit={},
            funding=funding,
            can_manage=can_manage,
        )
        return soup(html).select_one('[data-card="funding"]')

    def test_each_award_shows_its_funder_title_and_number(self, render_overview, soup):
        section = self.funding(render_overview, soup, [self.AWARD])

        for value in ("FUNDER-NAME", "AWARD-TITLE", "AWARD-1"):
            assert value in section.get_text()

    def test_the_funder_and_the_award_link_where_the_award_records_a_link(
        self, render_overview, soup
    ):
        section = self.funding(render_overview, soup, [self.AWARD])

        assert section.find("a", string="FUNDER-NAME")["href"] == "https://ror.org/abc"
        assert section.find("a", string="AWARD-1")["href"] == "https://grants.test/1"

    def test_an_award_without_links_is_plain_text(self, render_overview, soup):
        award = {"funderName": "FUNDER-NAME", "awardNumber": "AWARD-1"}

        section = self.funding(render_overview, soup, [award])

        assert section.find("a") is None

    def test_with_no_funding_the_section_says_none_is_recorded(
        self, render_overview, soup
    ):
        for can_manage in (False, True):
            section = self.funding(render_overview, soup, [], can_manage)

            assert section.find("li") is None
            assert section.find("p").get_text(strip=True)

    def test_a_record_that_carries_no_funding_has_no_funding_section(
        self, render_overview, soup
    ):
        assert self.funding(render_overview, soup, None) is None


class TestCite:
    FORMATS = [
        {
            "key": "text",
            "label": "Text",
            "value": "CITE-TEXT",
            "url": None,
            "download": False,
        },
        {
            "key": "bibtex",
            "label": "BibTeX",
            "value": "@misc{key, title={BIB-TEXT}}",
            "url": "/record/cite/bibtex/",
            "download": True,
        },
        {
            "key": "ris",
            "label": "RIS",
            "value": "TY  - GEN\nER  - ",
            "url": "/record/cite/ris/",
            "download": True,
        },
    ]

    def test_the_citation_is_shown_and_the_panel_is_the_cite_buttons_target(
        self, render_overview, soup
    ):
        page = soup(render_overview("cite", formats=self.FORMATS))

        assert page.find(id="cite") is not None
        assert page.find(id="citation-text").get_text(strip=True) == "CITE-TEXT"

    def test_the_text_sits_in_a_pre_that_names_its_format(self, render_overview, soup):
        page = soup(render_overview("cite", formats=self.FORMATS))

        text = page.find(id="citation-text")
        assert text.name == "pre"
        assert text["data-format"] == "text"

    def test_there_is_one_tab_per_format_with_text_selected(
        self, render_overview, soup
    ):
        page = soup(render_overview("cite", formats=self.FORMATS))

        tabs = page.select("[role=tablist] [role=tab]")
        assert [t["data-format"] for t in tabs] == ["text", "bibtex", "ris"]
        assert [t["aria-selected"] for t in tabs] == ["true", "false", "false"]
        assert {t["aria-controls"] for t in tabs} == {"citation-text"}

    def test_the_formats_reach_the_script_as_json(self, render_overview, soup):
        page = soup(render_overview("cite", formats=self.FORMATS))

        carried = json.loads(page.find(id="cite-formats").string)
        assert carried == self.FORMATS

    def test_a_title_that_closes_the_script_tag_cannot_break_out_of_the_json(
        self, render_overview, soup
    ):
        hostile = [{**self.FORMATS[0], "value": "</script><b id='broken'>x</b>"}]

        page = soup(render_overview("cite", formats=hostile))

        assert page.find(id="broken") is None
        carried = json.loads(page.find(id="cite-formats").string)
        assert carried[0]["value"] == hostile[0]["value"]

    def test_a_hidden_link_waits_for_a_downloadable_format(self, render_overview, soup):
        page = soup(render_overview("cite", formats=self.FORMATS))

        link = page.select_one("a[data-download]")
        assert link.has_attr("hidden")
        assert link.has_attr("download")

    def test_a_button_copies_the_citation(self, render_overview, soup):
        page = soup(render_overview("cite", formats=self.FORMATS))

        assert page.select_one("button[data-copy-from]")["data-copy-from"] == (
            "citation-text"
        )

    def test_the_panel_is_marked_for_the_script(self, render_overview, soup):
        page = soup(render_overview("cite", formats=self.FORMATS))

        assert page.find(id="cite").has_attr("data-cite")

    def test_a_note_is_shown_under_the_citation(self, child_template, render_template):
        name = child_template(
            """<c-overview.cite :formats="formats">NOTE-MARKER</c-overview.cite>"""
        )

        assert "NOTE-MARKER" in render_template(name, {"formats": self.FORMATS})


class TestDescriptions:
    DESCRIPTIONS = [
        {"label": "Abstract", "value": "ABSTRACT-TEXT"},
        {"label": "Methods", "value": "METHODS-TEXT"},
    ]

    def test_with_several_descriptions_each_has_a_tab_named_for_its_label(
        self, render_overview, soup
    ):
        page = soup(
            render_overview("descriptions", descriptions=self.DESCRIPTIONS, group="g")
        )

        tabs = page.select('[role="tab"]')
        assert [t.get_text(strip=True) for t in tabs] == ["Abstract", "Methods"]

    def test_the_tab_set_is_named_for_assistive_technology(self, render_overview, soup):
        page = soup(
            render_overview("descriptions", descriptions=self.DESCRIPTIONS, group="g")
        )

        assert page.find(role="tablist")["aria-label"]

    def test_every_description_is_in_the_page_and_only_the_first_is_shown(
        self, render_overview, soup
    ):
        page = soup(
            render_overview("descriptions", descriptions=self.DESCRIPTIONS, group="g")
        )

        tabs = page.select('[role="tab"]')
        assert [t["aria-selected"] for t in tabs] == ["true", "false"]
        panels = page.select('[role="tabpanel"]')
        assert [p.has_attr("hidden") for p in panels] == [False, True]
        assert "ABSTRACT-TEXT" in page.get_text()
        assert "METHODS-TEXT" in page.get_text()

    def test_each_tab_controls_its_own_panel(self, render_overview, soup):
        page = soup(
            render_overview("descriptions", descriptions=self.DESCRIPTIONS, group="own")
        )

        for tab in page.select('[role="tab"]'):
            panel = page.find(id=tab["aria-controls"])
            assert panel["aria-labelledby"] == tab["id"]

    def test_one_description_is_titled_by_its_label_with_no_tabs(
        self, render_overview, soup
    ):
        page = soup(
            render_overview(
                "descriptions", descriptions=self.DESCRIPTIONS[:1], group="g"
            )
        )

        assert _headings(page) == ["Abstract"]
        assert page.select('[role="tab"]') == []

    def test_a_description_is_rendered_from_markdown_without_running_its_scripts(
        self, render_overview
    ):
        descriptions = [
            {"label": "Abstract", "value": "**bold** <script>alert(1)</script>"}
        ]

        html = render_overview("descriptions", descriptions=descriptions, group="g")

        assert "<strong>bold</strong>" in html
        assert "<script>alert(1)</script>" not in html

    def test_the_descriptions_are_edited_from_the_panel(self, render_overview, soup):
        for descriptions in (self.DESCRIPTIONS, self.DESCRIPTIONS[:1]):
            page = soup(
                render_overview(
                    "descriptions",
                    descriptions=descriptions,
                    group="g",
                    edit_url="/edit/",
                )
            )

            assert page.find("a", href="/edit/") is not None

    def test_with_none_it_shows_what_it_was_given_in_the_slot(
        self, child_template, render_template
    ):
        name = child_template(
            """<c-overview.descriptions :descriptions="descriptions" group="g">FIRST-RUN-MARKER</c-overview.descriptions>"""
        )

        assert "FIRST-RUN-MARKER" in render_template(name, {"descriptions": []})


class TestPeople:
    @staticmethod
    def people(named, faces=(), more=0):
        return {
            "named": [
                {"contributor": p, "roles": ["Creator"], "more_roles": 0} for p in named
            ],
            "faces": list(faces),
            "more": more,
            "total": len(named) + len(faces) + more,
        }

    def test_each_named_person_links_to_their_page(self, render_overview, soup):
        person = PersonFactory()

        page = soup(render_overview("people", people=self.people([person])))

        assert page.find("a", string=str(person))["href"] == person.get_absolute_url()

    def test_each_face_links_to_its_page_and_is_named_for_assistive_technology(
        self, render_overview, soup
    ):
        named, face = PersonFactory(), PersonFactory()

        page = soup(render_overview("people", people=self.people([named], [face])))

        link = page.select_one(".ov-faces a")
        assert link["href"] == face.get_absolute_url()
        assert link["aria-label"] == str(face)

    def test_the_rest_are_counted_and_the_count_links_to_the_full_list(
        self, render_overview, soup
    ):
        people = self.people([PersonFactory()], [PersonFactory()], more=3)

        page = soup(render_overview("people", people=people, all_url="/all/"))

        assert page.select_one(".ov-faces__more")["href"] == "/all/"

    def test_the_team_manages_who_is_credited_from_the_panel(
        self, render_overview, soup
    ):
        page = soup(
            render_overview(
                "people", people=self.people([PersonFactory()]), manage_url="/team/"
            )
        )

        assert page.select_one(".ov-panel__tools a")["href"] == "/team/"

    def test_with_nobody_credited_the_panel_still_shows(self, render_overview, soup):
        page = soup(render_overview("people", people=self.people([])))

        assert page.select_one('[data-card="people"]') is not None
        assert page.find("a") is None


class TestReadiness:
    READINESS = {
        "title": "T",
        "summary": "S",
        "done": 1,
        "total": 2,
        "ready": False,
        "items": [
            {"label": "MISSING", "done": False, "url": "/fix/"},
            {"label": "IN-PLACE", "done": True, "url": "/other/"},
        ],
    }

    def test_a_missing_item_links_to_where_it_is_fixed(self, render_overview, soup):
        page = soup(render_overview("readiness", readiness=self.READINESS))

        assert page.find("a", href="/fix/") is not None

    def test_the_items_in_place_are_folded_away_after_the_missing_ones(
        self, render_overview, soup
    ):
        page = soup(render_overview("readiness", readiness=self.READINESS))

        assert "IN-PLACE" in page.find("details").get_text()
        assert "MISSING" not in page.find("details").get_text()

    def test_the_ring_is_named_with_how_much_is_in_place(self, render_overview, soup):
        page = soup(render_overview("readiness", readiness=self.READINESS))

        assert page.find(role="img")["aria-label"]


class TestMix:
    def test_each_type_is_a_bar_drawn_against_the_largest_count(
        self, render_overview, soup
    ):
        mix = {"samples": [("Rocks", 4)], "measurements": [("XRF", 2)], "max": 4}

        page = soup(render_overview("mix", mix=mix))

        widths = [s["style"] for s in page.select(".ov-mix__track span")]
        assert widths == ["width: 100%", "width: 50%"]


class TestResult:
    def test_the_value_is_shown_with_its_unit(self, render_overview, soup):
        page = soup(render_overview("result", label="L", value="12.5", unit="ppm Fe"))

        value = page.select_one(".ov-result__value").get_text(" ", strip=True)
        assert value == "12.5 ppm Fe"

    def test_notes_given_in_the_slot_sit_beside_the_value(
        self, child_template, render_template, soup
    ):
        name = child_template(
            """<c-overview.result label="L" value="1">NOTE-MARKER</c-overview.result>"""
        )

        page = soup(render_template(name))

        assert "NOTE-MARKER" in page.select_one(".ov-result__aside").get_text()

    def test_without_notes_no_aside_is_drawn(self, render_overview, soup):
        page = soup(render_overview("result", label="L", value="1"))

        assert page.select_one(".ov-result__aside") is None


class TestCoverage:
    @pytest.fixture
    def located(self):
        """The ``sample_map`` a page hands the panel when samples have locations."""
        return {
            "located": 1234,
            "missing": 5,
            "bounds": [7.9, 48.9, 8.1, 49.0],
            "area": "48.9 N to 49.0 N, 7.9 E to 8.1 E",
            "points_url": "/abc/sample-points/",
            "datasets": 3,
        }

    def render(self, render_overview, map_, **attributes):
        return render_overview(
            "coverage", map=map_, id="cov", more_url="/abc/samples/", **attributes
        )

    def test_the_map_element_carries_where_to_fetch_the_points_and_what_to_fit(
        self, render_overview, soup, located
    ):
        page = soup(self.render(render_overview, located))

        element = page.select_one("[data-map]")
        assert element["data-points-url"] == "/abc/sample-points/"
        assert json.loads(element["data-bounds"]) == [7.9, 48.9, 8.1, 49.0]
        assert element["role"] == "img"

    def test_the_maps_accessible_name_holds_the_number_mapped_and_the_area(
        self, render_overview, soup, located
    ):
        page = soup(self.render(render_overview, located))

        label = page.select_one("[data-map]")["aria-label"]
        assert "1,234" in label
        assert located["area"] in label

    def test_the_legend_counts_the_samples_with_and_without_a_location(
        self, render_overview, soup, located
    ):
        page = soup(self.render(render_overview, located))

        legend = page.select_one(".ov-map-legend")
        assert [s.get_text() for s in legend.select("strong")][:2] == ["1,234", "5"]

    def test_the_legend_leaves_out_the_count_without_a_location_when_none_is_missing(
        self, render_overview, soup, located
    ):
        page = soup(self.render(render_overview, {**located, "missing": 0}))

        legend = page.select_one(".ov-map-legend")
        assert "5" not in [s.get_text() for s in legend.select("strong")]

    def test_the_legend_counts_the_datasets_only_when_given(
        self, render_overview, soup, located
    ):
        with_datasets = soup(self.render(render_overview, located))
        without = {k: v for k, v in located.items() if k != "datasets"}
        without_datasets = soup(self.render(render_overview, without))

        def figures(page):
            return [s.get_text() for s in page.select(".ov-map-legend strong")]

        assert "3" in figures(with_datasets)
        assert len(figures(without_datasets)) == len(figures(with_datasets)) - 1

    def test_the_legend_names_the_area_covered(self, render_overview, soup, located):
        page = soup(self.render(render_overview, located))

        assert located["area"] in page.select_one(".ov-map-legend").get_text()

    def test_the_see_all_link_is_the_samples_list_given(
        self, render_overview, soup, located
    ):
        page = soup(self.render(render_overview, located))

        assert page.select_one(".ov-panel__more")["href"] == "/abc/samples/"

    def test_the_panel_has_no_edit_control(self, render_overview, soup, located):
        page = soup(self.render(render_overview, located))

        assert page.select_one(".ov-panel__tools a:not(.ov-panel__more)") is None

    def test_the_panel_is_the_coverage_card(self, render_overview, soup, located):
        page = soup(self.render(render_overview, located))

        assert page.select_one("[data-card=coverage]") is not None

    def test_with_none_located_there_is_no_map_element(
        self, render_overview, soup, located
    ):
        none_located = {**located, "located": 0, "bounds": None, "area": None}

        page = soup(self.render(render_overview, none_located))

        assert page.select_one("[data-map]") is None
        assert page.select_one(".ov-map-legend") is None
        assert page.select_one(".ov-empty") is not None

    def test_the_empty_line_can_be_replaced(self, render_overview, soup, located):
        none_located = {**located, "located": 0, "bounds": None, "area": None}

        page = soup(self.render(render_overview, none_located, empty="EMPTY-MARKER"))

        assert page.select_one(".ov-empty").get_text() == "EMPTY-MARKER"

    def test_located_samples_without_bounds_give_the_legend_and_no_map(
        self, render_overview, soup, located
    ):
        page = soup(self.render(render_overview, {**located, "bounds": None}))

        assert page.select_one("[data-map]") is None
        assert page.select_one(".ov-map-legend") is not None
