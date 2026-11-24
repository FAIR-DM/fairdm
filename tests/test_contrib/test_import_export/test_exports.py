"""Tests for the files an export writes."""

import csv
import io
import json
import zipfile
from dataclasses import replace
from urllib.parse import unquote

import pytest
import tablib
from django.http import HttpResponse
from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string, get_column_letter

from demo.models import RockSample, XRFMeasurement
from fairdm.contrib.import_export.exports import (
    EXPORT_FORMATS,
    TableExport,
    format_for,
)
from fairdm.registry import registry

TYPES = [*registry.samples, *registry.measurements]
KEYS = [export_format.key for export_format in EXPORT_FORMATS]


@pytest.fixture
def export_of():
    """Return a function writing a queryset of one type in a format."""

    def write(model, queryset, key, stem="records"):
        """Export the rows.

        Args:
            model: The registered type the rows belong to.
            queryset: The records to write.
            key: The format's key.
            stem: The start of the file's name.

        Returns:
            The response and the type's table schema.
        """
        schema = registry.get_for_model(model).get_table_schema()
        return TableExport(schema).response(queryset, key, stem), schema

    return write


@pytest.fixture
def read_back():
    """Return a function reading an export's body back as headings and rows."""

    def read(response, key):
        """Read the file.

        Args:
            response: The export's response.
            key: The format's key.

        Returns:
            The headings and the rows, every cell as text.
        """
        body = response.content
        if key in ("csv", "tsv"):
            text = body.decode("utf-8-sig")
            delimiter = "," if key == "csv" else "\t"
            lines = list(csv.reader(io.StringIO(text, newline=""), delimiter=delimiter))
            return lines[0], lines[1:]
        if key == "json":
            records = json.loads(body.decode("utf-8"))
            headings = list(records[0]) if records else []
            return headings, [[str(v) for v in record.values()] for record in records]
        if key == "xlsx":
            sheet = load_workbook(io.BytesIO(body)).worksheets[0]
            lines = [
                ["" if v is None else str(v) for v in row]
                for row in sheet.iter_rows(values_only=True)
            ]
            return lines[0], lines[1:]
        data = tablib.Dataset().load(body, format="ods")
        return list(data.headers), [
            ["" if v is None else str(v) for v in row] for row in data
        ]

    return read


class TestExportFormats:
    def test_the_formats_come_in_the_menus_order(self):
        assert KEYS == ["csv", "xlsx", "ods", "tsv", "json"]

    @pytest.mark.parametrize("key", KEYS)
    def test_a_key_finds_its_format(self, key):
        assert format_for(key).key == key

    @pytest.mark.parametrize("key", ["xls", "", "CSV", "pdf"])
    def test_a_key_that_is_not_a_format_finds_none(self, key):
        assert format_for(key) is None


@pytest.mark.django_db
class TestExportResponse:
    @pytest.mark.parametrize("key", KEYS)
    @pytest.mark.parametrize("model", TYPES, ids=lambda m: m.__name__)
    def test_every_type_writes_its_headings_and_rows_in_every_format(
        self, model, key, make_record, export_of, read_back
    ):
        records = [make_record(model) for _ in range(2)]
        response, schema = export_of(model, model.objects.order_by("pk"), key)
        headings, rows = read_back(response, key)
        assert headings == schema.headings
        assert headings[0] == "portal_id"
        assert [row[0] for row in rows] == [str(r.uuid) for r in records]

    @pytest.mark.parametrize("key", KEYS)
    def test_the_content_type_and_extension_are_the_formats(
        self, key, make_record, export_of
    ):
        make_record(RockSample)
        response, _schema = export_of(RockSample, RockSample.objects.all(), key)
        chosen = format_for(key)
        assert isinstance(response, HttpResponse)
        assert response.status_code == 200
        assert response["Content-Type"] == chosen.content_type
        disposition = response["Content-Disposition"]
        assert disposition.startswith("attachment")
        assert f'filename="records.{chosen.extension}"' in disposition

    def test_a_name_in_any_script_still_names_the_file(self, make_record, export_of):
        make_record(RockSample)
        response, _schema = export_of(
            RockSample, RockSample.objects.all(), "csv", stem="Dünnschliff 東京"
        )
        assert "dünnschliff-東京.csv" in unquote(response["Content-Disposition"])

    @pytest.mark.parametrize("key", ["csv", "tsv", "xlsx", "json"])
    def test_a_value_with_a_delimiter_a_quote_and_a_line_break_stays_one_cell(
        self, key, make_record, export_of, read_back
    ):
        name = 'a,b\t"c"\nd'
        make_record(RockSample, name=name)
        response, _schema = export_of(RockSample, RockSample.objects.all(), key)
        headings, rows = read_back(response, key)
        assert len(rows) == 1
        assert rows[0][headings.index("name")] == name

    @pytest.mark.parametrize("key", KEYS)
    def test_text_in_any_script_survives_every_format(
        self, key, make_record, export_of, read_back
    ):
        name = "Dünnschliff 東京 ☃"
        make_record(RockSample, name=name)
        response, _schema = export_of(RockSample, RockSample.objects.all(), key)
        headings, rows = read_back(response, key)
        assert rows[0][headings.index("name")] == name

    def test_json_is_a_list_of_objects_keyed_by_the_headings(
        self, make_record, export_of
    ):
        make_record(RockSample)
        make_record(RockSample)
        response, schema = export_of(RockSample, RockSample.objects.all(), "json")
        records = json.loads(response.content)
        assert len(records) == 2
        assert all(list(record) == schema.headings for record in records)

    def test_a_csv_file_starts_with_a_byte_order_mark(self, make_record, export_of):
        make_record(RockSample)
        response, _schema = export_of(RockSample, RockSample.objects.all(), "csv")
        assert response.content.startswith(b"\xef\xbb\xbf")

    @pytest.mark.parametrize("key", KEYS)
    def test_an_empty_optional_value_and_a_missing_location_give_empty_cells(
        self, key, make_record, export_of, read_back
    ):
        make_record(RockSample, location=None, local_id="")
        response, _schema = export_of(RockSample, RockSample.objects.all(), key)
        headings, rows = read_back(response, key)
        for heading in ("local_id", "latitude", "longitude"):
            assert rows[0][headings.index(heading)] == ""
        assert rows[0][headings.index("latitude")] == ""

    @pytest.mark.parametrize("key", ["csv", "xlsx", "ods", "tsv"])
    def test_no_rows_write_the_headings_alone(self, key, export_of, read_back):
        response, schema = export_of(RockSample, RockSample.objects.none(), key)
        headings, rows = read_back(response, key)
        assert headings == schema.headings
        assert rows == []

    def test_no_rows_write_an_empty_json_list(self, export_of):
        response, _schema = export_of(RockSample, RockSample.objects.none(), "json")
        assert json.loads(response.content) == []


@pytest.mark.django_db
class TestExportOrder:
    def test_rows_come_out_in_primary_key_order_whatever_the_queryset_sorts_by(
        self, make_record, export_of, read_back
    ):
        records = [make_record(RockSample, name=name) for name in ("c", "a", "b")]
        queryset = RockSample.objects.order_by("-name")
        response, _schema = export_of(RockSample, queryset, "csv")
        _headings, rows = read_back(response, "csv")
        assert [row[0] for row in rows] == [
            str(r.uuid) for r in sorted(records, key=lambda r: r.pk)
        ]


@pytest.mark.django_db
class TestSampleName:
    def annotated(self, make_record, is_open):
        record = make_record(XRFMeasurement)
        record.sample_open = is_open
        return record

    @pytest.fixture
    def writer(self):
        """Return a function writing the rows of one measurement type."""
        schema = registry.get_for_model(XRFMeasurement).get_table_schema()
        return schema, TableExport(schema)

    def cells(self, writer, record):
        schema, table = writer
        row = next(table.rows(FakeQuerySet([record])))
        return dict(zip(schema.headings, row, strict=True))

    def test_a_sample_the_viewer_may_open_is_named(self, make_record, writer):
        record = self.annotated(make_record, True)
        cells = self.cells(writer, record)
        assert cells["sample_name"] == record.sample.name
        assert cells["sample"] == str(record.sample.uuid)

    @pytest.mark.parametrize("is_open", [False, None])
    def test_a_sample_the_viewer_may_not_open_is_left_empty(
        self, make_record, writer, is_open
    ):
        record = self.annotated(make_record, is_open)
        if is_open is None:
            del record.sample_open
        cells = self.cells(writer, record)
        assert cells["sample_name"] == ""
        assert cells["sample"] == ""

    def test_a_sample_type_keeps_a_column_that_is_named_like_the_sample_one(
        self, make_record
    ):
        schema = registry.get_for_model(RockSample).get_table_schema()
        renamed = [
            replace(c, name="sample", attribute="name") if c.name == "name" else c
            for c in schema.columns
        ]
        schema = replace(schema, columns=renamed)
        record = make_record(RockSample)
        cells = self.cells((schema, TableExport(schema)), record)
        assert cells["sample"] == record.name


class FakeQuerySet:
    """Hold records a test has already annotated, and hand them out like a queryset."""

    def __init__(self, records):
        self.records = records

    def iterator(self, chunk_size=None):
        """Yield the records, as ``QuerySet.iterator`` does."""
        return iter(self.records)


@pytest.mark.django_db
class TestWorkbook:
    @pytest.fixture
    def schema(self):
        return registry.get_for_model(RockSample).get_table_schema()

    @pytest.fixture
    def measured(self):
        """The schema of a type with a column that has a unit."""
        return registry.get_for_model(XRFMeasurement).get_table_schema()

    def book(self, schema, rows=()):
        return load_workbook(io.BytesIO(TableExport(schema).workbook(rows)))

    def test_it_has_the_rows_the_guide_and_the_allowed_values(
        self, schema, make_record
    ):
        book = self.book(schema, [["x"] * len(schema.columns)])
        assert len(book.worksheets) == 3
        data, guide, allowed = book.worksheets
        assert [c.value for c in data[1]] == schema.headings
        assert data.max_row == 2
        assert guide.max_row >= len(schema.columns)
        listed = [c.value for c in allowed[1] if c.value]
        assert listed
        assert set(listed) <= set(schema.headings)

    def test_the_guide_has_a_row_per_column(self, schema):
        guide = self.book(schema).worksheets[1]
        names = {row[0] for row in guide.iter_rows(values_only=True)}
        assert set(schema.headings) <= names

    def test_a_control_character_a_spreadsheet_cannot_hold_is_left_out(self, schema):
        row = [""] * len(schema.columns)
        row[schema.headings.index("name")] = "a\x0bb"
        data = self.book(schema, [row]).worksheets[0]
        assert data.cell(row=2, column=schema.headings.index("name") + 1).value == "ab"

    def test_a_heading_note_carries_the_label_kind_and_unit(self, measured):
        data = self.book(measured).worksheets[0]
        column = next(c for c in measured.columns if c.unit and c.role == "field")
        note = data.cell(row=1, column=measured.headings.index(column.name) + 1).comment
        assert str(column.label) in note.text
        assert str(column.kind_label) in note.text
        assert column.unit in note.text
        assert str(column.format_hint) in note.text

    def test_a_required_column_says_so_and_an_export_column_is_not_read(self, measured):
        data = self.book(measured).worksheets[0]
        required = next(c for c in measured.columns if c.required)
        export = next(c for c in measured.columns if c.role == "export")
        index = {name: i + 1 for i, name in enumerate(measured.headings)}
        assert (
            "Required for new records."
            in data.cell(row=1, column=index[required.name]).comment.text
        )
        assert (
            "Not read on import."
            in data.cell(row=1, column=index[export.name]).comment.text
        )

    def test_each_listed_column_has_a_list_validation_pointing_at_its_range(
        self, schema
    ):
        book = self.book(schema)
        data, _guide, allowed = book.worksheets
        validations = data.data_validations.dataValidation
        listed = [c.value for c in allowed[1] if c.value]
        assert listed
        assert len(validations) == len(listed)
        for validation in validations:
            assert validation.type == "list"
            assert validation.allow_blank
            assert not validation.showErrorMessage
            assert allowed.title in validation.formula1
            assert str(validation.sqref).endswith("5000")
            column = column_index_from_string(str(validation.sqref).split(":")[0][:-1])
            heading = data.cell(row=1, column=column).value
            position = listed.index(heading) + 1
            letter = get_column_letter(position)
            values = next(allowed.iter_cols(min_col=position, max_col=position))[1:]
            last = 1 + len([c for c in values if c.value is not None])
            assert validation.formula1.endswith(f"!${letter}$2:${letter}${last}")

    def test_the_validation_reaches_a_thousand_rows_past_the_data(self, schema):
        rows = [[""] * len(schema.columns) for _ in range(5000)]
        data = self.book(schema, rows).worksheets[0]
        validation = data.data_validations.dataValidation[0]
        assert str(validation.sqref).endswith("6000")

    @pytest.mark.parametrize("name", ["x" * 60, "a/b", "[a]:b*c?d\\e"])
    def test_a_type_name_excel_cannot_hold_still_gives_a_workbook_that_opens(
        self, schema, name, monkeypatch
    ):
        monkeypatch.setattr(type(schema), "name", name)
        titles = [sheet.title for sheet in self.book(schema).worksheets]
        assert len(titles) == len(set(titles)) == 3
        assert all(len(t) <= 31 for t in titles)
        assert not set("[]:*?/\\") & set("".join(titles))

    def test_a_name_that_repeats_another_sheets_gets_a_number(
        self, schema, monkeypatch
    ):
        monkeypatch.setattr(type(schema), "name", "Column guide")
        titles = [sheet.title for sheet in self.book(schema).worksheets]
        assert len(set(titles)) == 3

    def test_a_column_with_three_hundred_values_keeps_them_all(
        self, schema, monkeypatch
    ):
        column = next(c for c in schema.columns if c.name == "status")
        monkeypatch.setattr(column, "allowed", [(f"v{n}", "") for n in range(300)])
        allowed = self.book(schema).worksheets[2]
        position = next(c.column for c in allowed[1] if c.value == "status")
        values = [
            allowed.cell(row=r, column=position).value
            for r in range(2, allowed.max_row + 1)
        ]
        assert values == [f"v{n}" for n in range(300)]

    def test_a_name_that_looks_like_a_formula_is_read_back_as_text(
        self, schema, make_record
    ):
        row = [""] * len(schema.columns)
        row[schema.headings.index("name")] = "=1+1"
        data = self.book(schema, [row]).worksheets[0]
        cell = data.cell(row=2, column=schema.headings.index("name") + 1)
        assert cell.value == "=1+1"
        assert cell.data_type == "s"

    def test_no_rows_write_the_same_sheets_and_headings(self, schema):
        empty = self.book(schema)
        full = self.book(schema, [[""] * len(schema.columns)])
        assert [s.title for s in empty.worksheets] == [s.title for s in full.worksheets]
        assert [c.value for c in empty.worksheets[0][1]] == schema.headings
        assert empty.worksheets[0].max_row == 1

    def test_the_file_is_a_zip_of_sheets(self, schema):
        payload = TableExport(schema).workbook()
        assert zipfile.is_zipfile(io.BytesIO(payload))
