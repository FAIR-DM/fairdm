"""Tests for fairdm/contrib/import_export/widgets.py."""

import datetime as dt
from decimal import Decimal

import pytest
from controlled_vocabularies.models import Record
from django.contrib.auth.models import AnonymousUser
from django.db import models

from demo.factories import RockSampleFactory
from demo.models import (
    CustomSample,
    ExampleMeasurement,
    ICP_MS_Measurement,
    RockSample,
    XRFMeasurement,
)
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.import_export.widgets import (
    ConceptCellWidget,
    SampleCellWidget,
    widget_for,
)
from fairdm.factories import ContributionFactory, DatasetFactory, PersonFactory
from fairdm.utils.choices import Visibility

pytestmark = pytest.mark.django_db

UTC = dt.UTC
ROCK_TYPE = (RockSample, "rock_type")
WEIGHT = (RockSample, "weight_grams")
HARDNESS = (RockSample, "hardness_mohs")
COLLECTED = (RockSample, "collection_date")
LATITUDE = (RockSample, "latitude")
LONGITUDE = (RockSample, "longitude")
WHOLE = (CustomSample, "integer_field")
FLAG = (CustomSample, "boolean_field")
MOMENT = (ICP_MS_Measurement, "analysis_date")
CLOCK = (ExampleMeasurement, "time_field")
COUNT = (ExampleMeasurement, "positive_integer_field")


class TestRoundTrip:
    """A cell an export writes reads back as the value it was written from."""

    @pytest.mark.parametrize(
        ("where", "value"),
        [
            (ROCK_TYPE, "basalt"),
            (WHOLE, 42),
            (WEIGHT, 12.5),
            (HARDNESS, Decimal("6.5")),
            (HARDNESS, Decimal(7)),
            (FLAG, True),
            (FLAG, False),
            (COLLECTED, dt.date(2024, 6, 30)),
            (MOMENT, dt.datetime(2024, 6, 30, 14, 5, 42, tzinfo=UTC)),
            (CLOCK, dt.time(14, 5, 42)),
            (LATITUDE, 48.9165),
            (LONGITUDE, -7.8436),
        ],
    )
    def test_a_value_reads_back_as_it_was_written(self, column_of, where, value):
        widget = column_of(*where).widget()

        assert widget.clean(widget.render(value)) == value

    def test_a_datetime_with_seconds_keeps_its_seconds(self, column_of):
        widget = column_of(*MOMENT).widget()
        value = dt.datetime(2024, 6, 30, 14, 5, 42, tzinfo=UTC)

        assert widget.clean(widget.render(value)).second == value.second

    def test_a_time_with_seconds_keeps_its_seconds(self, column_of):
        widget = column_of(*CLOCK).widget()

        assert widget.clean(widget.render(dt.time(14, 5, 42))).second == 42

    def test_a_partial_date_reads_back_as_it_was_written(self, make_column):
        widget = make_column("partial_date").widget()

        for value in ("2024", "2024-06", "2024-06-30"):
            assert widget.clean(widget.render(value)) == value

    def test_a_choice_reads_back_as_it_was_written(self, make_column):
        column = make_column("choice", allowed=[("igneous", "Igneous rock")])
        widget = column.widget()

        assert widget.clean(widget.render("igneous")) == "igneous"

    def test_a_choice_reads_by_its_meaning(self, make_column):
        column = make_column("choice", allowed=[("igneous", "Igneous rock")])

        assert column.widget().clean("igneous ROCK") == "igneous"

    def test_a_concept_reads_back_as_it_was_written(self, column_of):
        column = column_of(RockSample, "status")
        record = Record.objects.filter(column.model_field.resolve_restriction()).first()
        widget = column.widget()

        assert widget.clean(widget.render(record)) == record

    def test_a_sample_reads_back_as_it_was_written(self, column_of):
        sample = RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )
        widget = column_of(XRFMeasurement, "sample").widget(
            dataset=sample.dataset, user=AnonymousUser()
        )

        assert widget.clean(widget.render(sample)) == sample

    def test_a_quantity_reads_back_as_it_was_written(self, column_of):
        column = column_of(ICP_MS_Measurement, "value")
        widget = column.widget()
        value = widget.clean("12.5")

        assert widget.clean(widget.render(value)) == value

    @pytest.mark.parametrize(
        ("where", "text"),
        [
            (COLLECTED, "2024-06-30"),
            (MOMENT, "2024-06-30 14:05:42"),
            (CLOCK, "14:05:42"),
        ],
    )
    def test_a_spreadsheets_own_object_reads_as_the_text_does(
        self, column_of, where, text
    ):
        widget = column_of(*where).widget()
        objects = {
            COLLECTED: dt.datetime(2024, 6, 30, 0, 0),
            MOMENT: dt.datetime(2024, 6, 30, 14, 5, 42),
            CLOCK: dt.time(14, 5, 42),
        }

        assert widget.clean(objects[where]) == widget.clean(text)

    def test_a_spreadsheets_date_object_reads_as_a_date(self, column_of):
        widget = column_of(*COLLECTED).widget()

        assert widget.clean(dt.date(2024, 6, 30)) == dt.date(2024, 6, 30)

    @pytest.mark.parametrize(
        ("where", "cell", "value"),
        [
            (ROCK_TYPE, "  basalt  ", "basalt"),
            (WEIGHT, " 12.5 ", 12.5),
            (WHOLE, " 42 ", 42),
            (FLAG, "  yes ", True),
            (COLLECTED, " 2024-06-30 ", dt.date(2024, 6, 30)),
            (CLOCK, " 14:05:42 ", dt.time(14, 5, 42)),
        ],
    )
    def test_spaces_around_a_cell_are_stripped(self, column_of, where, cell, value):
        assert column_of(*where).widget().clean(cell) == value

    @pytest.mark.parametrize(
        "where",
        [WHOLE, WEIGHT, HARDNESS, FLAG, COLLECTED, MOMENT, CLOCK, LATITUDE, COUNT],
    )
    @pytest.mark.parametrize("cell", ["", "   ", None])
    def test_an_empty_cell_is_none(self, column_of, where, cell):
        assert column_of(*where).widget().clean(cell) is None

    @pytest.mark.parametrize("cell", ["", "   ", None])
    def test_an_empty_cell_of_a_text_field_that_cannot_be_null_is_empty_text(
        self, column_of, cell
    ):
        assert column_of(*ROCK_TYPE).widget().clean(cell) == ""

    def test_an_empty_cell_of_a_text_field_that_can_be_null_is_none(
        self, make_column
    ):
        column = make_column("text", model_field=models.CharField(null=True))

        assert column.widget().clean("  ") is None

    def test_a_concept_sample_and_quantity_read_an_empty_cell_as_none(self, column_of):
        for column in (
            column_of(RockSample, "status"),
            column_of(XRFMeasurement, "sample"),
            column_of(ICP_MS_Measurement, "value"),
        ):
            assert column.widget().clean("") is None


class TestRefusals:
    """A cell that cannot be read is refused with a reason, as a ValueError."""

    @pytest.mark.parametrize(
        ("where", "cell"),
        [
            (WEIGHT, "heavy"),
            (WHOLE, "forty-two"),
            (WHOLE, "1.5"),
            (COUNT, "-1"),
            (LATITUDE, "91"),
            (LONGITUDE, "-181"),
            (LATITUDE, "nan"),
            (LONGITUDE, "inf"),
            (HARDNESS, "5.55"),
            (FLAG, "maybe"),
            (COLLECTED, "30 June 2024"),
            (COLLECTED, "06/30/2024"),
            (MOMENT, "yesterday"),
            (CLOCK, "half past two"),
        ],
    )
    def test_a_cell_the_column_cannot_read_is_refused(self, column_of, where, cell):
        with pytest.raises(ValueError):  # noqa: PT011
            column_of(*where).widget().clean(cell)

    def test_text_over_the_longest_allowed_is_refused(self, column_of):
        column = column_of(*ROCK_TYPE)

        with pytest.raises(ValueError):  # noqa: PT011
            column.widget().clean("x" * (column.max_length + 1))

    def test_a_value_not_in_the_list_is_refused(self, make_column):
        column = make_column("choice", allowed=[("igneous", "Igneous rock")])

        with pytest.raises(ValueError):  # noqa: PT011
            column.widget().clean("purple")

    def test_a_partial_date_in_another_form_is_refused(self, make_column):
        for cell in ("June 2024", "2024-13", "2024-02-30"):
            with pytest.raises(ValueError):  # noqa: PT011
                make_column("partial_date").widget().clean(cell)

    def test_a_decimal_comma_is_refused_with_the_number_written_with_a_point(
        self, column_of
    ):
        with pytest.raises(ValueError) as refusal:  # noqa: PT011
            column_of(*WEIGHT).widget().clean("12,5")

        assert "12.5" in str(refusal.value)

    def test_a_decimal_comma_in_a_quantity_is_refused_with_a_point(self, column_of):
        with pytest.raises(ValueError) as refusal:  # noqa: PT011
            column_of(ICP_MS_Measurement, "value").widget().clean("12,5 ppm")

        assert "12.5" in str(refusal.value)

    def test_a_number_at_the_edge_of_the_range_is_read(self, column_of):
        assert column_of(*LATITUDE).widget().clean("90") == 90


class TestConceptWidget:
    """A concept is read by label, code or address."""

    @pytest.fixture
    def column(self, column_of):
        """The sample status column, which lists a vocabulary."""
        return column_of(RockSample, "status")

    @pytest.fixture
    def record(self, column):
        """One concept of the vocabulary, with a label in German."""
        found = Record.objects.filter(column.model_field.resolve_restriction()).first()
        found.data = {
            **found.data,
            "skos:altLabel": [{"@value": "Verfügbar", "@language": "de"}],
        }
        found.save()
        return found

    def test_a_concept_is_read_by_its_preferred_label(self, column, record):
        assert column.widget().clean(record.pref_label) == record

    def test_a_label_is_matched_ignoring_case(self, column, record):
        assert column.widget().clean(record.pref_label.upper()) == record

    def test_a_concept_is_read_by_a_label_in_another_language(self, column, record):
        assert column.widget().clean("Verfügbar") == record

    def test_a_concept_is_read_by_its_code(self, column, record):
        assert column.widget().clean(record.slug) == record

    def test_a_concept_is_read_by_its_address(self, column, record):
        assert column.widget().clean(record.uri) == record

    def test_a_cell_is_written_as_the_preferred_label(self, column, record):
        assert column.widget().render(record) == record.pref_label

    def test_a_label_not_in_the_list_is_refused(self, column, record):
        with pytest.raises(ValueError):  # noqa: PT011
            column.widget().clean("no such concept")

    def test_an_empty_vocabulary_refuses_every_cell(self, column, record):
        Record.objects.filter(column.model_field.resolve_restriction()).delete()
        widget = column.widget()

        for cell in (record.pref_label, record.slug, record.uri, "anything"):
            with pytest.raises(ValueError):  # noqa: PT011
                widget.clean(cell)

    def test_the_lookup_is_built_once_per_widget(
        self, column, record, django_assert_num_queries
    ):
        widget = column.widget()
        widget.clean(record.pref_label)

        with django_assert_num_queries(0):
            widget.clean(record.slug)

    def test_widget_for_a_concept_column_is_the_concept_widget(self, column):
        assert isinstance(widget_for(column), ConceptCellWidget)


class TestSampleWidget:
    """A sample is read from the ones the person may see, and nothing says which."""

    @pytest.fixture
    def target(self):
        """The dataset the file is imported into."""
        return DatasetFactory(visibility=Visibility.PUBLIC, published=True)

    @pytest.fixture
    def column(self, column_of):
        """The sample column of a measurement."""
        return column_of(XRFMeasurement, "sample")

    @pytest.fixture
    def public(self):
        """A sample in another dataset that anyone may see."""
        return RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        )

    @pytest.fixture
    def private(self):
        """A sample in a dataset that only its team may see."""
        return RockSampleFactory(
            dataset=DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        )

    @pytest.fixture
    def outsider(self):
        """A person with no level on the private dataset."""
        return PersonFactory(is_active=True)

    @pytest.fixture
    def insider(self, private):
        """A person who may see the private dataset."""
        person = PersonFactory(is_active=True)
        ContributionFactory(
            content_object=private.dataset,
            contributor=person,
            level=ContributionLevel.VIEW,
        )
        return person

    def refusal(self, column, target, user, cell):
        """Return the message a cell is refused with."""
        with pytest.raises(ValueError) as refused:  # noqa: PT011
            column.widget(dataset=target, user=user).clean(cell)
        return str(refused.value)

    def test_a_visible_samples_portal_id_in_another_dataset_is_read(
        self, column, target, outsider, public
    ):
        widget = column.widget(dataset=target, user=outsider)

        assert widget.clean(public.uuid) == public

    def test_a_portal_id_is_read_by_a_visitor_when_the_sample_is_public(
        self, column, target, public
    ):
        assert column.widget(dataset=target, user=None).clean(public.uuid) == public

    def test_a_private_samples_portal_id_is_read_by_someone_who_may_see_it(
        self, column, target, insider, private
    ):
        assert column.widget(dataset=target, user=insider).clean(private.uuid) == (
            private
        )

    def test_a_private_sample_is_refused_like_a_portal_id_nobody_holds(
        self, column, target, outsider, private
    ):
        nobody = self.refusal(column, target, outsider, "sNOBODYHOLDSTHISID123456")

        assert self.refusal(column, target, outsider, private.uuid) == nobody

    def test_a_private_sample_is_refused_a_visitor_like_a_portal_id_nobody_holds(
        self, column, target, private
    ):
        nobody = self.refusal(column, target, None, "sNOBODYHOLDSTHISID123456")

        assert self.refusal(column, target, None, private.uuid) == nobody

    def test_the_local_id_of_a_sample_in_the_dataset_is_read(
        self, column, target, outsider
    ):
        sample = RockSampleFactory(dataset=target, local_id="CORE-7")

        assert column.widget(dataset=target, user=outsider).clean("CORE-7") == sample

    def test_a_unique_name_in_the_dataset_is_read(self, column, target, outsider):
        sample = RockSampleFactory(dataset=target, name="Granite block")

        widget = column.widget(dataset=target, user=outsider)

        assert widget.clean("Granite block") == sample

    def test_a_local_id_in_another_dataset_is_not_read(
        self, column, target, outsider, public
    ):
        nobody = self.refusal(column, target, outsider, "sNOBODYHOLDSTHISID123456")

        assert self.refusal(column, target, outsider, public.local_id) == nobody

    def test_a_local_id_in_a_dataset_the_person_may_not_see_is_not_read(
        self, column, outsider
    ):
        hidden = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        RockSampleFactory(dataset=hidden, local_id="CORE-9")
        nobody = self.refusal(column, hidden, outsider, "sNOBODYHOLDSTHISID123456")

        assert self.refusal(column, hidden, outsider, "CORE-9") == nobody

    def test_a_local_id_shared_by_two_samples_asks_for_the_portal_id(
        self, column, target, outsider
    ):
        RockSampleFactory.create_batch(2, dataset=target, local_id="CORE-1")

        message = self.refusal(column, target, outsider, "CORE-1")

        assert "portal ID" in message

    def test_a_name_shared_by_two_samples_asks_for_the_portal_id(
        self, column, target, outsider
    ):
        RockSampleFactory.create_batch(2, dataset=target, name="Twin")

        message = self.refusal(column, target, outsider, "Twin")

        assert "portal ID" in message

    def test_a_cell_is_written_as_the_portal_id(self, column, public):
        assert column.widget().render(public) == public.uuid

    def test_widget_for_a_sample_column_passes_on_the_dataset_and_person(
        self, column, target, outsider
    ):
        widget = widget_for(column, dataset=target, user=outsider)

        assert isinstance(widget, SampleCellWidget)
        assert (widget.dataset, widget.user) == (target, outsider)


class TestQuantityWidget:
    """A number with a unit is converted to the column's unit."""

    @pytest.fixture
    def column(self, column_of):
        """A column of a quantity field."""
        return column_of(ICP_MS_Measurement, "value")

    @pytest.fixture
    def base(self, column):
        """The unit the column stores."""
        return column.model_field.base_units

    def test_a_bare_number_is_read_in_the_columns_unit(self, column, base):
        value = column.widget().clean("12.5")

        assert value.magnitude == Decimal("12.5")
        assert value.units == column.model_field.ureg.Unit(base)

    def test_a_number_with_a_compatible_unit_is_converted(self, column, base):
        value = column.widget().clean("12.5 milligram / liter")

        assert value.to(base).magnitude == Decimal("12500.0")

    def test_a_number_with_no_space_before_its_unit_is_converted(self, column, base):
        value = column.widget().clean("2mg/l")

        assert value.to(base).magnitude == 2000

    def test_a_number_a_spreadsheet_holds_is_read_in_the_columns_unit(self, column):
        assert column.widget().clean(3).magnitude == 3

    def test_a_unit_that_does_not_convert_is_refused(self, column):
        with pytest.raises(ValueError):  # noqa: PT011
            column.widget().clean("12 meter")

    def test_a_unit_nobody_knows_is_refused(self, column):
        with pytest.raises(ValueError):  # noqa: PT011
            column.widget().clean("12 zorp")

    def test_text_that_is_not_a_number_is_refused(self, column):
        with pytest.raises(ValueError):  # noqa: PT011
            column.widget().clean("lots")

    def test_a_cell_is_written_as_the_number_in_the_columns_unit(self, column):
        value = column.widget().clean("12.5 milligram / liter")

        assert column.widget().render(value) == "12500"
