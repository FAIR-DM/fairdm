"""Tests for the location input in ``fairdm.contrib.location.forms``."""

import pytest
from bs4 import BeautifulSoup
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.http import QueryDict
from django.test import RequestFactory

from demo.factories import RockSampleFactory
from demo.models import RockSample
from fairdm.contrib.contributors.choices import ContributionLevel

from fairdm.contrib.location.forms import (
    Location,
    LocationField,
    LocationWidget,
    parse_coordinate,
)
from fairdm.factories import ContributionFactory, UserFactory
from fairdm.registry.config import ModelConfiguration
from tests.test_core.test_editing import form_payload

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


def clean(field, *parts):
    """Clean one submission, given as the field's values in input order."""
    return field.clean(list(parts))


def refusal(field, *parts):
    """Return the code of the error a submission is refused with."""
    with pytest.raises(ValidationError) as caught:
        clean(field, *parts)
    return caught.value.code


class TestLocationField:
    def test_decimal_degrees_in_wgs84_clean_to_that_point(self):
        field = LocationField()

        location = clean(field, "49.0094", "8.4115", "", "")

        assert isinstance(location, Location)
        assert location.point.srid == 4326
        assert (location.point.x, location.point.y) == (8.4115, 49.0094)

    def test_latitude_and_longitude_are_each_read_in_their_own_notation(self):
        location = clean(LocationField(), "49 0 33.84 N", "8 24.69", "", "")

        assert location.point.y == pytest.approx(49.0094, abs=1e-5)
        assert location.point.x == pytest.approx(8.4115, abs=1e-5)

    def test_elevation_and_uncertainty_are_kept_as_given(self):
        location = clean(LocationField(), "49.0094", "8.4115", "-12.5", "3")

        assert (location.elevation, location.uncertainty) == (-12.5, 3.0)

    def test_elevation_and_uncertainty_may_be_left_out(self):
        location = clean(LocationField(), "49.0094", "8.4115", "", "")

        assert (location.elevation, location.uncertainty) == (None, None)

    @pytest.mark.parametrize(
        "parts",
        [("49.0094", ""), ("", "8.4115")],
    )
    def test_one_coordinate_without_the_other_is_refused(self, parts):
        assert refusal(LocationField(), *parts, "", "") == "incomplete"

    @pytest.mark.parametrize("parts", [("5", ""), ("", "2"), ("5", "2")])
    def test_elevation_or_uncertainty_without_coordinates_is_refused(self, parts):
        assert refusal(LocationField(), "", "", *parts) == "no_point"

    def test_a_negative_uncertainty_is_refused(self):
        assert refusal(LocationField(), "49.0094", "8.4115", "", "-1") == "negative_uncertainty"

    def test_an_uncertainty_of_zero_is_accepted(self):
        location = clean(LocationField(), "49.0094", "8.4115", "", "0")

        assert location.uncertainty == 0

    def test_a_latitude_beyond_ninety_is_refused_with_the_coordinate_error(self):
        assert refusal(LocationField(), "91", "8.4115", "", "") == "out_of_range"

    def test_a_hemisphere_of_the_other_axis_is_refused(self):
        assert refusal(LocationField(), "49.0094 E", "8.4115", "", "") == "wrong_axis"

    @pytest.mark.parametrize("position", [0, 1])
    def test_an_input_of_more_than_64_characters_is_refused(self, position):
        parts = ["49.0094", "8.4115", "", ""]
        parts[position] = "49.".ljust(65, "0")

        with pytest.raises(ValidationError) as caught:
            clean(LocationField(), *parts)

        assert "max_length" in [error.code for error in caught.value.error_list]

    def test_an_empty_submission_cleans_to_none(self):
        assert clean(LocationField(), "", "", "", "") is None

    def test_a_required_field_refuses_an_empty_submission(self):
        assert refusal(LocationField(required=True), "", "", "", "", "") == "required"


class TestLocationFieldPointOnly:
    def test_two_coordinates_clean_to_a_wgs84_point(self):
        location = clean(LocationField(full=False), "49.0094", "8.4115")

        assert location.point.srid == 4326
        assert (location.point.x, location.point.y) == (8.4115, 49.0094)
        assert (location.elevation, location.uncertainty) == (None, None)

    def test_it_asks_for_no_elevation_or_uncertainty(self):
        field = LocationField(full=False)

        assert len(field.fields) == 2
        assert len(field.widget.widgets) == 2

    def test_empty_cleans_to_none(self):
        assert clean(LocationField(full=False), "", "") is None

    def test_one_coordinate_without_the_other_is_refused(self):
        assert refusal(LocationField(full=False), "49.0094", "") == "incomplete"


class TestLocationWidget:
    def test_a_stored_location_decompresses_to_decimal_degrees_in_wgs84(self):
        widget = LocationWidget()
        location = Location(Point(8.4115, 49.0094, srid=4326), 112.0, 5.0)

        assert widget.decompress(location) == ["49.0094", "8.4115", 112.0, 5.0]

    def test_a_stored_point_alone_decompresses_for_the_point_only_input(self):
        widget = LocationWidget(full=False)

        assert widget.decompress(Point(8.4115, 49.0094, srid=4326)) == ["49.0094", "8.4115"]

    def test_decompressing_a_value_and_cleaning_it_again_gives_the_same_point(self):
        point = Point(8.411500000123, 49.009400000456, srid=4326)
        field = LocationField()

        again = field.clean(field.widget.decompress(Location(point, None, None)))

        assert (again.point.x, again.point.y) == (point.x, point.y)

    def test_nothing_stored_decompresses_to_empty_parts(self):
        assert LocationWidget().decompress(None) == [None, None, None, None]


def rendered(widget, value=None):
    """Render a widget the way a form does and parse the result."""
    html = widget.render("location", value, attrs={"id": "id_location"})
    return BeautifulSoup(html, "html.parser")


class TestLocationWidgetRendering:
    def test_each_part_is_an_input_named_after_the_field(self):
        page = rendered(LocationWidget())

        names = {control["name"] for control in page.select("input[name]")}
        assert names == {
            "location_first",
            "location_second",
            "location_elevation",
            "location_uncertainty",
        }

    def test_the_point_only_input_has_two_coordinates_and_nothing_else(self):
        page = rendered(LocationWidget(full=False))

        names = {control["name"] for control in page.select("input[name]")}
        assert names == {"location_first", "location_second"}

    def test_a_stored_location_fills_the_inputs(self):
        location = Location(Point(8.4115, 49.0094, srid=4326), 112.0, 5.0)

        page = rendered(LocationWidget(), location)

        values = {c["name"]: c["value"] for c in page.select("input[name]")}
        assert values == {
            "location_first": "49.0094",
            "location_second": "8.4115",
            "location_elevation": "112.0",
            "location_uncertainty": "5.0",
        }

    def test_a_typed_latitude_is_escaped_in_the_value_and_nowhere_else(self):
        typed = "49');alert(1);//<b>x</b>"
        widget = LocationWidget()

        html = widget.render("location", [typed, "8", None, None], attrs={"id": "id_location"})

        page = BeautifulSoup(html, "html.parser")
        assert page.select_one("input[name='location_first']")["value"] == typed
        assert "alert(1)" not in page.select_one("[x-data]")["x-data"]
        assert "<b>" not in html
        assert not any("alert(1)" in (script.string or "") for script in page.select("script"))


def browser_submission(page, **typed):
    """What a browser sends for a rendered form, with a value typed into the first control of a name.

    A name that appears on several controls is sent once for each, in page order.
    """
    data = QueryDict(mutable=True)
    for name, value in form_payload(page).items():
        data.setlist(name, value if isinstance(value, list) else [value])
    for name, value in typed.items():
        values = [control.get("value", "") for control in page.select(f"[name='{name}']")]
        values[0] = value
        data.setlist(name, values)
    return data


@pytest.mark.django_db
class TestLocationFormMixin:
    """A registration that lists no fields still gets one input for each part of the location."""

    @pytest.fixture
    def form_for_unlisted_fields(self):
        sample = RockSampleFactory()
        editor = UserFactory()
        ContributionFactory(content_object=sample, contributor=editor, level=ContributionLevel.EDIT)
        request = RequestFactory().get("/")
        request.user = editor
        form_class = ModelConfiguration(model=RockSample).get_form_class()
        return form_class, sample, request

    def test_each_part_of_the_location_has_one_input(self, form_for_unlisted_fields):
        form_class, sample, request = form_for_unlisted_fields

        page = BeautifulSoup(form_class(instance=sample, request=request).as_div(), "html.parser")

        names = [control["name"] for control in page.select("input[name]")]
        assert names.count("location_elevation") == 1
        assert names.count("location_uncertainty") == 1

    def test_an_elevation_typed_in_the_location_input_is_saved(self, form_for_unlisted_fields):
        form_class, sample, request = form_for_unlisted_fields
        page = BeautifulSoup(form_class(instance=sample, request=request).as_div(), "html.parser")
        data = browser_submission(
            page, location_first="49.0094", location_second="8.4115", location_elevation="112.5"
        )
        data["status"] = sample.status

        form = form_class(data, instance=sample, request=request)

        assert form.is_valid(), form.errors
        assert form.save().location_elevation == 112.5
