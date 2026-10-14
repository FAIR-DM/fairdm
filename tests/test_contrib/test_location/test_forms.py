"""Tests for the location input in ``fairdm.contrib.location.forms``."""

import pytest
from django.core.exceptions import ValidationError

from fairdm.contrib.location.forms import parse_coordinate

# One place, 48 degrees 56 minutes 7 seconds north, written every way the input accepts.
LATITUDE_FORMS = [
    "48.93528",
    "48.93528°",
    "+48.93528",
    "48 56.117",
    "48° 56.117′",
    "48 56.117 N",
    "N 48 56.117",
    "48 56 7",
    "48°56'7\"N",
    "48° 56′ 7″ N",
    "N48 56 7",
    "48 56 7 North",
    "north 48 56 7",
    "48d56'7\"",
    "48,93528",
]

# One place, 8 degrees 24 minutes 41.4 seconds east.
LONGITUDE_FORMS = [
    "8.41150",
    "8.4115°",
    "8 24.69",
    "8° 24.69′ E",
    "E 8 24.69",
    "8 24 41.4",
    "8°24'41.4\"E",
    "E8 24 41.4",
    "8 24 41.4 East",
]


@pytest.mark.parametrize("text", LATITUDE_FORMS)
class TestParseCoordinateLatitude:
    def test_every_notation_of_one_latitude_agrees(self, text):
        assert parse_coordinate(text, "lat") == pytest.approx(48.93528, abs=1e-5)


@pytest.mark.parametrize("text", LONGITUDE_FORMS)
class TestParseCoordinateLongitude:
    def test_every_notation_of_one_longitude_agrees(self, text):
        assert parse_coordinate(text, "lon") == pytest.approx(8.4115, abs=1e-5)


class TestParseCoordinate:
    @pytest.mark.parametrize(
        ("text", "axis", "expected"),
        [
            ("48 56 7 S", "lat", -48.93528),
            ("48.93528 South", "lat", -48.93528),
            ("S 48.93528", "lat", -48.93528),
            ("-48.93528", "lat", -48.93528),
            ("8 24 41.4 W", "lon", -8.4115),
            ("West 8.4115", "lon", -8.4115),
            ("-8.4115", "lon", -8.4115),
        ],
    )
    def test_southern_and_western_hemispheres_are_negative(
        self, text, axis, expected
    ):
        assert parse_coordinate(text, axis) == pytest.approx(expected, abs=1e-5)

    @pytest.mark.parametrize(
        ("text", "axis"),
        [("90", "lat"), ("-90", "lat"), ("180", "lon"), ("-180", "lon"), ("0", "lat")],
    )
    def test_the_limits_of_each_axis_are_accepted(self, text, axis):
        assert parse_coordinate(text, axis) == float(text)

    @pytest.mark.parametrize(
        ("text", "axis"),
        [
            ("91", "lat"),
            ("-90.00001", "lat"),
            ("90 30 0", "lat"),
            ("181", "lon"),
            ("-180.5", "lon"),
        ],
    )
    def test_a_value_beyond_its_axis_is_refused(self, text, axis):
        with pytest.raises(ValidationError) as caught:
            parse_coordinate(text, axis)

        assert caught.value.code == "out_of_range"

    @pytest.mark.parametrize(
        ("text", "axis"),
        [
            ("48.9353 E", "lat"),
            ("48 56 7 W", "lat"),
            ("East 48.9353", "lat"),
            ("8.4115 N", "lon"),
            ("8 24 41.4 S", "lon"),
            ("North 8.4115", "lon"),
        ],
    )
    def test_a_hemisphere_of_the_other_axis_is_refused(self, text, axis):
        with pytest.raises(ValidationError) as caught:
            parse_coordinate(text, axis)

        assert caught.value.code == "wrong_axis"

    @pytest.mark.parametrize("text", ["48d 56m 7s", "48 56m", "48° 56m 7″ N"])
    def test_minutes_written_with_the_letter_m_are_refused(self, text):
        with pytest.raises(ValidationError) as caught:
            parse_coordinate(text, "lat")

        assert caught.value.code == "minutes_letter"

    @pytest.mark.parametrize(
        "text",
        ["", "   ", "abc", "nan", "inf", "1e3", "0x10", "48 70 7", "12 34 56 78"],
    )
    def test_text_that_is_not_a_coordinate_is_refused(self, text):
        with pytest.raises(ValidationError) as caught:
            parse_coordinate(text, "lat")

        assert caught.value.code == "invalid"

    def test_the_message_names_the_value_that_was_typed(self):
        with pytest.raises(ValidationError) as caught:
            parse_coordinate("somewhere", "lat")

        assert "somewhere" in str(caught.value.messages[0])
