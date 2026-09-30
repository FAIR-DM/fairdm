"""Tests for the pure helpers the overview pages share."""

import json
from datetime import date

import pytest
from partial_date import PartialDate

from fairdm.core.overview import as_date, format_authors, json_ld
from fairdm.factories import OrganizationFactory, PersonFactory


@pytest.mark.django_db
class TestFormatAuthors:
    def test_no_creators_gives_an_empty_string(self):
        assert format_authors([]) == ""

    def test_one_creator_is_surname_and_initial(self):
        person = PersonFactory(first_name="Anna", last_name="Keller")

        assert format_authors([person]) == "Keller, A."

    def test_two_creators_are_joined_by_an_ampersand(self):
        first = PersonFactory(first_name="Anna", last_name="Keller")
        second = PersonFactory(first_name="Tomas", last_name="Oliveira")

        assert format_authors([first, second]) == "Keller, A. & Oliveira, T."

    def test_several_creators_are_comma_separated_with_an_ampersand_before_the_last(
        self,
    ):
        people = [
            PersonFactory(first_name="Anna", last_name="Keller"),
            PersonFactory(first_name="Tomas", last_name="Oliveira"),
            PersonFactory(first_name="Lena", last_name="Brandt"),
        ]

        assert format_authors(people) == "Keller, A., Oliveira, T. & Brandt, L."

    def test_an_organisation_is_written_by_its_name(self):
        organisation = OrganizationFactory(name="Geothermal Institute")
        person = PersonFactory(first_name="Anna", last_name="Keller")

        assert format_authors([person, organisation]) == (
            "Keller, A. & Geothermal Institute"
        )

    def test_a_person_without_a_first_name_is_written_by_their_name(self):
        person = PersonFactory(first_name="", last_name="Keller", name="Keller")

        assert format_authors([person]) == str(person)


class TestJsonLd:
    def test_the_characters_that_could_end_the_script_element_are_escaped(self):
        data = {"name": "</script><script>alert(1)</script> & <b>"}

        encoded = json_ld(data)

        assert "<" not in encoded
        assert ">" not in encoded
        assert "&" not in encoded

    def test_the_escaped_output_decodes_to_the_original_data(self):
        data = {"name": "</script> & <b>", "n": 3}

        assert json.loads(json_ld(data)) == data

    def test_a_value_json_cannot_encode_is_written_as_its_string_form(self):
        assert json.loads(json_ld({"when": date(2026, 3, 4)})) == {"when": "2026-03-04"}


class TestAsDate:
    @pytest.mark.parametrize("recorded", ["2020", "2020-03", "2020-03-04"])
    def test_a_partial_date_of_any_precision_gives_a_date(self, recorded):
        assert isinstance(as_date(PartialDate(recorded)), date)

    def test_a_year_only_date_gives_the_first_day_of_that_year(self):
        assert as_date(PartialDate("2020")) == date(2020, 1, 1)

    def test_a_month_only_date_gives_the_first_day_of_that_month(self):
        assert as_date(PartialDate("2020-03")) == date(2020, 3, 1)

    def test_the_recorded_precision_is_left_on_the_partial_date(self):
        recorded = PartialDate("2020-03")

        as_date(recorded)

        assert str(recorded) == "2020-03"

    def test_nothing_recorded_gives_nothing(self):
        assert as_date(None) is None

    def test_a_plain_date_passes_through(self):
        assert as_date(date(2020, 3, 4)) == date(2020, 3, 4)
