"""Tests for the ``c-card.*`` components the overview pages share.

Each component is rendered on its own, with only its documented attributes, and the tests read
what it delivers: the data it was given, the links it draws and the names it carries for
assistive technology. Wording is never asserted.
"""

from datetime import date
from decimal import Decimal

import pytest
from django.utils import translation
from django.utils.formats import date_format
from partial_date import PartialDate

from fairdm.factories import OrganizationFactory, PersonFactory, PointFactory


def _card_titles(soup):
    return [h2.get_text(strip=True) for h2 in soup.select("h2.card-title")]


@pytest.mark.django_db
class TestDetailsCard:
    def test_a_record_row_links_to_the_record(self, render_card, soup):
        organisation = OrganizationFactory()
        rows = [{"label": "Org", "icon": "organization", "record": organisation}]

        page = soup(render_card("details", rows=rows, api_url=""))

        link = page.find("a", string=str(organisation))
        assert link["href"] == organisation.get_absolute_url()

    def test_a_row_with_a_url_links_its_text(self, render_card, soup):
        rows = [{"label": "Licence", "text": "CC BY 4.0", "url": "https://x.test/l"}]

        page = soup(render_card("details", rows=rows, api_url=""))

        assert page.find("a", string="CC BY 4.0")["href"] == "https://x.test/l"

    def test_a_row_note_is_shown_under_its_value(self, render_card):
        rows = [{"label": "Licence", "text": "None", "note": "NOTE-MARKER"}]

        assert "NOTE-MARKER" in render_card("details", rows=rows, api_url="")

    def test_a_row_can_be_a_badge(self, render_card, soup):
        rows = [{"label": "Status", "badge": "BADGE-MARKER", "badge_variant": "info"}]

        page = soup(render_card("details", rows=rows, api_url=""))

        assert page.select_one(".badge").get_text(strip=True) == "BADGE-MARKER"

    def test_the_api_address_is_offered_when_the_record_has_one(
        self, render_card, soup
    ):
        page = soup(render_card("details", rows=[], api_url="/api/v1/thing/1/"))

        assert page.find("a", href="/api/v1/thing/1/") is not None

    def test_no_api_link_is_drawn_when_the_record_has_none(self, render_card, soup):
        page = soup(render_card("details", rows=[], api_url=""))

        assert page.find("a", href=True) is None

    def test_a_row_date_follows_the_active_locale(self, render_card):
        when = date(2026, 3, 4)
        rows = [{"label": "Added", "icon": "calendar", "date": when}]

        with translation.override("de"):
            html = render_card("details", rows=rows, api_url="")
            expected = date_format(when, "SHORT_DATE_FORMAT")

        assert expected in html

    def test_the_machine_metadata_downloads_are_disabled(self, render_card, soup):
        page = soup(render_card("details", rows=[], api_url=""))

        assert page.find("button", disabled=True) is not None


@pytest.mark.django_db
class TestPeopleCard:
    def test_each_person_links_to_their_page_and_is_named_for_assistive_technology(
        self, render_card, soup
    ):
        person = PersonFactory(name="Avatar Person")
        people = {"shown": [person], "more": 0, "total": 1}

        page = soup(render_card("people", people=people, all_url=""))

        link = page.find("a", href=person.get_absolute_url())
        assert link["aria-label"] == "Avatar Person"

    def test_the_name_is_available_on_hover(self, render_card, soup):
        person = PersonFactory(name="Hover Person")
        people = {"shown": [person], "more": 0, "total": 1}

        page = soup(render_card("people", people=people, all_url=""))

        assert page.find(attrs={"data-tip": "Hover Person"}) is not None

    def test_the_rest_are_counted_and_the_count_links_to_the_full_list(
        self, render_card, soup
    ):
        people = {"shown": [PersonFactory()], "more": 7, "total": 8}

        page = soup(render_card("people", people=people, all_url="/all/"))

        counted = [a for a in page.find_all("a", href="/all/") if "7" in a.text]
        assert counted

    def test_the_count_is_plain_text_when_there_is_no_full_list(
        self, render_card, soup
    ):
        people = {"shown": [PersonFactory()], "more": 7, "total": 8}

        page = soup(render_card("people", people=people, all_url=""))

        assert "7" in page.get_text()
        assert page.find("a", href="") is None

    def test_no_count_is_shown_when_everyone_fits(self, render_card):
        people = {"shown": [PersonFactory()], "more": 0, "total": 1}

        assert "and 0" not in render_card("people", people=people, all_url="/all/")


@pytest.mark.django_db
class TestIdentifiersCard:
    def test_each_identifier_is_listed_and_a_linked_one_links(self, render_card, soup):
        identifiers = [
            {"type": "DOI", "value": "10.1/x", "link": "https://doi.org/10.1/x"},
            {"type": "GRANT_NUMBER", "value": "G-1", "link": None},
        ]

        page = soup(
            render_card(
                "identifiers", identifiers=identifiers, portal_id="", local_id=""
            )
        )

        assert page.find("a", string="10.1/x")["href"] == "https://doi.org/10.1/x"
        assert page.find("td", string=lambda t: t and t.strip() == "G-1") is not None
        assert page.find("a", string="G-1") is None

    def test_the_teams_own_id_is_listed(self, render_card):
        html = render_card(
            "identifiers", identifiers=[], portal_id="", local_id="LOCAL-MARKER"
        )

        assert "LOCAL-MARKER" in html

    def test_the_portal_id_is_listed_with_a_button_that_copies_it(
        self, render_card, soup
    ):
        page = soup(
            render_card("identifiers", identifiers=[], portal_id="PORTALONE", local_id="")
        )

        assert "PORTALONE" in page.get_text()
        assert "PORTALONE" in page.find("button")["onclick"]
        assert page.find("button")["aria-label"]

    def test_the_table_is_named_for_assistive_technology(self, render_card, soup):
        page = soup(
            render_card("identifiers", identifiers=[], portal_id="P", local_id="")
        )

        assert page.find("table").find("caption").get_text(strip=True)


@pytest.mark.django_db
class TestFundingCard:
    AWARD = {
        "funderName": "FUNDER-NAME",
        "funderIdentifier": "https://ror.org/abc",
        "awardTitle": "AWARD-TITLE",
        "awardNumber": "AWARD-1",
        "awardURI": "https://grants.test/1",
    }

    def test_each_award_shows_its_funder_title_and_number(self, render_card):
        html = render_card("funding", funding=[self.AWARD], can_manage=False)

        for value in ("FUNDER-NAME", "AWARD-TITLE", "AWARD-1"):
            assert value in html

    def test_the_funder_and_the_award_link_where_the_award_records_a_link(
        self, render_card, soup
    ):
        page = soup(render_card("funding", funding=[self.AWARD], can_manage=False))

        assert page.find("a", string="FUNDER-NAME")["href"] == "https://ror.org/abc"
        assert page.find("a", string="AWARD-1")["href"] == "https://grants.test/1"

    def test_an_award_without_links_is_plain_text(self, render_card, soup):
        award = {"funderName": "FUNDER-NAME", "awardNumber": "AWARD-1"}

        page = soup(render_card("funding", funding=[award], can_manage=False))

        assert page.find("a") is None

    def test_with_no_funding_a_visitor_gets_no_card(self, render_card):
        assert render_card("funding", funding=[], can_manage=False).strip() == ""

    def test_with_no_funding_the_team_gets_a_card_that_says_none_is_recorded(
        self, render_card, soup
    ):
        page = soup(render_card("funding", funding=[], can_manage=True))

        assert len(_card_titles(page)) == 1
        assert page.find("li") is None
        assert page.find("p").get_text(strip=True)


@pytest.mark.django_db
class TestCitationCard:
    def test_the_citation_text_is_shown_and_the_card_is_the_target_of_the_cite_button(
        self, render_card, soup
    ):
        page = soup(render_card("citation", title="Citation", text="CITE-TEXT"))

        assert page.find(id="cite") is not None
        assert page.find(id="citation-text").get_text(strip=True) == "CITE-TEXT"

    def test_a_button_copies_the_citation(self, render_card, soup):
        page = soup(render_card("citation", title="Citation", text="CITE-TEXT"))

        copy = next(b for b in page.find_all("button") if not b.has_attr("disabled"))
        assert "citation-text" in copy["onclick"]

    def test_exporting_the_citation_is_disabled_and_says_why(self, render_card, soup):
        page = soup(render_card("citation", title="Citation", text="CITE-TEXT"))

        disabled = page.find("button", disabled=True)
        assert disabled["title"]
        assert disabled.find(class_="sr-only").get_text(strip=True)

    def test_a_note_is_shown_under_the_citation(self, child_template, render_template):
        name = child_template(
            '''<c-card.citation title="Citation" text="CITE-TEXT">NOTE-MARKER</c-card.citation>'''
        )

        assert "NOTE-MARKER" in render_template(name)


@pytest.mark.django_db
class TestDescriptionsCard:
    DESCRIPTIONS = [
        {"label": "Abstract", "value": "ABSTRACT-TEXT"},
        {"label": "Methods", "value": "METHODS-TEXT"},
    ]

    def test_with_several_descriptions_each_has_a_tab_named_for_its_label(
        self, render_card, soup
    ):
        page = soup(
            render_card("descriptions", descriptions=self.DESCRIPTIONS, group="g")
        )

        tabs = page.select('input[role="tab"]')
        assert [t["aria-label"] for t in tabs] == ["Abstract", "Methods"]

    def test_the_tab_set_is_named_for_assistive_technology(self, render_card, soup):
        page = soup(
            render_card("descriptions", descriptions=self.DESCRIPTIONS, group="g")
        )

        assert page.find(role="tablist")["aria-label"]

    def test_every_description_is_in_the_page_and_the_first_tab_is_selected(
        self, render_card, soup
    ):
        page = soup(
            render_card("descriptions", descriptions=self.DESCRIPTIONS, group="g")
        )

        tabs = page.select('input[role="tab"]')
        assert tabs[0].has_attr("checked")
        assert not tabs[1].has_attr("checked")
        assert "ABSTRACT-TEXT" in page.get_text()
        assert "METHODS-TEXT" in page.get_text()

    def test_the_tabs_of_one_set_share_a_group(self, render_card, soup):
        page = soup(
            render_card("descriptions", descriptions=self.DESCRIPTIONS, group="own")
        )

        assert {t["name"] for t in page.select('input[role="tab"]')} == {"own"}

    def test_one_description_is_titled_by_its_label_with_no_tabs(
        self, render_card, soup
    ):
        page = soup(
            render_card("descriptions", descriptions=self.DESCRIPTIONS[:1], group="g")
        )

        assert _card_titles(page) == ["Abstract"]
        assert page.select('input[role="tab"]') == []

    def test_a_description_is_rendered_from_markdown_without_running_its_scripts(
        self, render_card
    ):
        descriptions = [
            {"label": "Abstract", "value": "**bold** <script>alert(1)</script>"}
        ]

        html = render_card("descriptions", descriptions=descriptions, group="g")

        assert "<strong>bold</strong>" in html
        assert "<script>alert(1)</script>" not in html

    def test_with_none_it_shows_what_it_was_given_in_the_slot(
        self, child_template, render_template
    ):
        name = child_template(
            '''<c-card.descriptions :descriptions="descriptions" group="g">FIRST-RUN-MARKER</c-card.descriptions>'''
        )

        assert "FIRST-RUN-MARKER" in render_template(name, {"descriptions": []})


@pytest.mark.django_db
class TestTimelineCard:
    def test_each_step_is_listed_in_the_order_given(self, render_card, soup):
        steps = [
            {"label": "FIRST", "date": PartialDate("2020"), "day": None},
            {"label": "SECOND", "date": PartialDate("2021-05-06"), "day": date(2021, 5, 6)},
        ]

        page = soup(render_card("timeline", title="History", steps=steps, empty=""))

        items = [li.get_text(" ", strip=True) for li in page.select("ol > li")]
        assert "FIRST" in items[0]
        assert "SECOND" in items[1]

    def test_a_date_recorded_only_to_the_year_is_shown_as_recorded(self, render_card):
        steps = [{"label": "Step", "date": PartialDate("2020"), "day": None}]

        html = render_card("timeline", title="History", steps=steps, empty="")

        assert "2020" in html
        assert "Jan" not in html

    def test_a_full_day_follows_the_active_locale(self, render_card):
        when = date(2021, 5, 6)
        steps = [{"label": "Step", "date": PartialDate("2021-05-06"), "day": when}]

        with translation.override("de"):
            html = render_card("timeline", title="History", steps=steps, empty="")
            expected = date_format(when, "SHORT_DATE_FORMAT")

        assert expected in html

    def test_each_person_credited_on_a_step_links_to_their_page(
        self, render_card, soup
    ):
        person = PersonFactory()
        steps = [
            {"label": "Step", "date": None, "day": None, "people": [person]},
        ]

        page = soup(render_card("timeline", title="History", steps=steps, empty=""))

        assert page.find("a", href=person.get_absolute_url()) is not None

    def test_a_step_note_is_rendered(self, render_card):
        steps = [{"label": "Step", "date": None, "day": None, "note": "NOTE-MARKER"}]

        assert "NOTE-MARKER" in render_card(
            "timeline", title="History", steps=steps, empty=""
        )

    def test_with_no_steps_the_card_says_what_it_was_told_to(self, render_card, soup):
        page = soup(
            render_card("timeline", title="History", steps=[], empty="EMPTY-MARKER")
        )

        assert page.find("ol") is None
        assert "EMPTY-MARKER" in page.get_text()


@pytest.mark.django_db
class TestLocationCard:
    def test_the_coordinates_are_in_the_page_as_text(self, render_card, soup):
        point = PointFactory(x=Decimal("8.541"), y=Decimal("47.376"))

        page = soup(render_card("location", location=point))

        text = page.get_text(" ", strip=True)
        assert "8.541" in text
        assert "47.376" in text

    def test_the_map_is_named_with_the_coordinates_and_carries_them_for_the_script(
        self, render_card, soup
    ):
        point = PointFactory(x=Decimal("8.541"), y=Decimal("47.376"))

        page = soup(render_card("location", location=point))

        surface = page.find(class_="overview-map")
        assert surface["role"] == "img"
        assert "8.541" in surface["aria-label"]
        assert "47.376" in surface["aria-label"]
        assert surface["data-lon"] == "8.541"
        assert surface["data-lat"] == "47.376"

    def test_with_no_location_the_card_is_left_out(self, render_card):
        assert render_card("location", location=None).strip() == ""

    def test_with_no_location_and_an_empty_message_the_card_shows_it(
        self, render_card, soup
    ):
        page = soup(render_card("location", location=None, empty="EMPTY-MARKER"))

        assert page.find(class_="overview-map") is None
        assert "EMPTY-MARKER" in page.get_text()


@pytest.mark.django_db
class TestReadinessCard:
    READINESS = {
        "items": [
            {"label": "MISSING-ONE", "done": False, "url": "/fix/one/"},
            {"label": "DONE-ONE", "done": True, "url": None},
            {"label": "MISSING-TWO", "done": False, "url": None},
        ],
        "done": 1,
        "total": 3,
        "ready": False,
    }

    def _render(self, render_card, **overrides):
        attributes = {
            "title": "Ready?",
            "summary": "1 of 3",
            "about": "",
            "readiness": self.READINESS,
        }
        return render_card("readiness", **{**attributes, **overrides})

    def test_missing_items_come_before_the_ones_in_place(self, render_card):
        html = self._render(render_card)

        assert html.index("MISSING-ONE") < html.index("MISSING-TWO")
        assert html.index("MISSING-TWO") < html.index("DONE-ONE")

    def test_a_missing_item_links_to_where_it_is_fixed_when_such_a_page_exists(
        self, render_card, soup
    ):
        page = soup(self._render(render_card))

        assert page.find("a", href="/fix/one/") is not None
        assert len(page.find_all("a")) == 1

    def test_every_item_says_whether_it_is_missing_or_done_to_assistive_technology(
        self, render_card, soup
    ):
        page = soup(self._render(render_card))

        for item in page.select("ul > li"):
            assert item.find(class_="sr-only").get_text(strip=True)

    def test_the_progress_bar_is_named_and_carries_the_counts(self, render_card, soup):
        bar = soup(self._render(render_card)).find("progress")

        assert bar["aria-label"]
        assert (bar["value"], bar["max"]) == ("1", "3")


@pytest.mark.django_db
class TestPlaceholderCard:
    def test_it_carries_the_title_and_the_message_it_was_given(self, render_card, soup):
        page = soup(
            render_card(
                "placeholder", title="TITLE-MARKER", icon="map", message="MESSAGE-MARKER"
            )
        )

        assert _card_titles(page) == ["TITLE-MARKER"]
        assert "MESSAGE-MARKER" in page.get_text()

    def test_it_offers_nothing_to_press(self, render_card, soup):
        page = soup(
            render_card("placeholder", title="T", icon="map", message="M")
        )

        assert page.find("button") is None
        assert page.find("a") is None
