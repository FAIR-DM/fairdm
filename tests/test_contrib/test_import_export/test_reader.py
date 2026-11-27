"""The reader turns a file into headings and rows, or says why it cannot."""

import pytest

from fairdm.contrib.import_export.reader import FileProblem, FileReader

from .conftest import ods_of

HEADINGS = ["Name", "Local ID", "Rock type"]
ROWS = [["Granite 1", "G-1", "granite"], ["Basalt 2", "B-2", "basalt"]]
KINDS = ["csv", "semicolon", "tsv", "xlsx", "ods"]
NAMES = {
    "csv": "rocks.csv",
    "semicolon": "rocks.csv",
    "tsv": "rocks.tsv",
    "xlsx": "rocks.xlsx",
    "ods": "rocks.ods",
}


def code_of(raw, name="rocks.csv"):
    """Return the code of the problem reading the file raises."""
    with pytest.raises(FileProblem) as caught:
        FileReader.parse(raw, FileReader.file_format(name))
    return caught.value.code


class TestFileReader:
    """What a file is read as."""

    class TestFileFormat:
        """Which files are read at all."""

        def test_a_read_format_is_named_by_its_extension(self):
            names = {
                "a.csv": "csv",
                "A.CSV": "csv",
                "a.tsv": "tsv",
                "a.xlsx": "xlsx",
                "a.ods": "ods",
            }

            assert {name: FileReader.file_format(name) for name in names} == names

        def test_another_format_is_refused(self):
            accepted = []
            for name in ["a.json", "a.txt", "a.xls", "a"]:
                try:
                    FileReader.file_format(name)
                except FileProblem as caught:
                    assert caught.code == "format"
                else:
                    accepted.append(name)

            assert accepted == []

    class TestParse:
        """Headings, rows and line numbers."""

        @pytest.mark.parametrize("kind", KINDS)
        def test_every_format_gives_the_same_headings_and_rows(self, file_of, kind):
            raw = file_of(kind, [HEADINGS, *ROWS])

            headings, rows, lines = FileReader.parse(
                raw, FileReader.file_format(NAMES[kind])
            )

            assert headings == HEADINGS
            assert rows == ROWS
            assert lines == [2, 3]

        def test_a_semicolon_file_is_not_split_on_commas(self, file_of):
            raw = file_of("semicolon", [["Name", "Note"], ["a", "x, y"]])

            headings, rows, _lines = FileReader.parse(raw, "csv")

            assert headings == ["Name", "Note"]
            assert rows == [["a", "x, y"]]

        def test_a_tab_is_never_a_csv_delimiter(self):
            raw = b"Name\tNote\na\tb\n"

            headings, _rows, _lines = FileReader.parse(raw, "csv")

            assert headings == ["Name\tNote"]

        def test_a_blank_first_line_is_skipped_and_lines_still_count_it(self):
            raw = b"\nName,Rock type\nGranite,granite\n"

            headings, rows, lines = FileReader.parse(raw, "csv")

            assert headings == ["Name", "Rock type"]
            assert rows == [["Granite", "granite"]]
            assert lines == [3]

        def test_blank_rows_are_dropped_and_the_others_keep_their_line(self):
            raw = b"Name\na\n\n,\nb\n"

            _headings, rows, lines = FileReader.parse(raw, "csv")

            assert rows == [["a"], ["b"]]
            assert lines == [2, 5]

        def test_short_rows_are_filled_and_long_rows_cut_to_the_headings(self):
            raw = b"A,B\n1\n1,2,3\n"

            _headings, rows, _lines = FileReader.parse(raw, "csv")

            assert rows == [["1", None], ["1", "2"]]

        def test_empty_headings_at_the_end_are_dropped(self):
            raw = b"A,B,,\n1,2,,\n"

            headings, rows, _lines = FileReader.parse(raw, "csv")

            assert headings == ["A", "B"]
            assert rows == [["1", "2"]]

        def test_a_workbook_reads_its_first_sheet_only(self):
            from openpyxl import Workbook

            book = Workbook()
            book.active.append(["A"])
            book.active.append(["first"])
            book.create_sheet().append(["B"])
            import io

            out = io.BytesIO()
            book.save(out)

            headings, rows, _lines = FileReader.parse(out.getvalue(), "xlsx")

            assert headings == ["A"]
            assert rows == [["first"]]

    class TestOpenDocument:
        """A spreadsheet read with odfpy, never tablib."""

        def test_a_repeated_cell_reads_as_the_csv_row_does(self, ods_file):
            raw = ods_file([[["A", "B", "C"], ["x", "y"]]], repeated=(0, 1, 1, 2))

            headings, rows, _lines = FileReader.parse(raw, "ods")

            assert headings == ["A", "B", "C"]
            assert rows == [["x", "y", "y"]]

        def test_three_sheets_read_the_first_only(self, ods_file):
            raw = ods_file([[["A"], ["one"]], [["B"], ["two"]], [["C"], ["three"]]])

            headings, rows, _lines = FileReader.parse(raw, "ods")

            assert headings == ["A"]
            assert rows == [["one"]]

        def test_a_repeated_row_is_read_once_per_repeat(self):
            import io

            from odf.opendocument import OpenDocumentSpreadsheet
            from odf.table import Table, TableCell, TableRow
            from odf.text import P

            doc = OpenDocumentSpreadsheet()
            table = Table(name="Sheet1")
            for text, repeat in (("A", 1), ("same", 3)):
                row = TableRow()
                if repeat > 1:
                    row.setAttribute("numberrowsrepeated", str(repeat))
                cell = TableCell(valuetype="string")
                cell.addElement(P(text=text))
                row.addElement(cell)
                table.addElement(row)
            doc.spreadsheet.addElement(table)
            out = io.BytesIO()
            doc.write(out)

            _headings, rows, lines = FileReader.parse(out.getvalue(), "ods")

            assert rows == [["same"]] * 3
            assert lines == [2, 3, 4]

        def test_a_file_that_is_not_a_spreadsheet_is_refused(self):
            assert code_of(b"not a zip", "rocks.ods") == "unreadable"

    class TestRefusals:
        """A file that cannot be imported, and why."""

        def test_a_file_with_no_content_has_no_headings(self):
            assert code_of(b"\n\n") == "empty"

        def test_a_file_with_headings_and_no_rows_is_refused(self):
            assert code_of(b"Name,Rock type\n") == "no_rows"

        def test_a_file_of_only_blank_rows_has_no_rows(self):
            assert code_of(b"Name\n,\n\n") == "no_rows"

        def test_a_file_over_the_size_limit_is_refused(self):
            raw = b"x" * (FileReader.MAX_BYTES + 1)

            assert code_of(raw) == "too_large"

        def test_a_file_over_the_row_limit_is_refused(self, monkeypatch):
            monkeypatch.setattr(FileReader, "MAX_ROWS", 3)
            raw = b"A\n" + b"1\n" * 4

            assert code_of(raw) == "too_many_rows"

        def test_a_file_at_the_row_limit_is_read(self, monkeypatch):
            monkeypatch.setattr(FileReader, "MAX_ROWS", 3)
            raw = b"A\n" + b"1\n" * 3

            _headings, rows, _lines = FileReader.parse(raw, "csv")

            assert len(rows) == 3

        def test_the_row_limit_counts_rows_after_a_blank_first_line(self, monkeypatch):
            monkeypatch.setattr(FileReader, "MAX_ROWS", 3)
            raw = b"\nA\n" + b"1\n" * 3

            _headings, rows, _lines = FileReader.parse(raw, "csv")

            assert len(rows) == 3

    class TestEncoding:
        """The text of a CSV, whichever way it was saved."""

        def test_utf8_is_read(self):
            raw = "Name\nGrüner Schiefer\n".encode()

            _headings, rows, _lines = FileReader.parse(raw, "csv")

            assert rows == [["Grüner Schiefer"]]

        def test_a_byte_order_mark_is_not_part_of_the_first_heading(self):
            raw = "﻿Name\nx\n".encode()

            headings, _rows, _lines = FileReader.parse(raw, "csv")

            assert headings == ["Name"]

        def test_windows_1252_is_read(self):
            raw = "Name\nGrüner Schiefer\n".encode("cp1252")

            _headings, rows, _lines = FileReader.parse(raw, "csv")

            assert rows == [["Grüner Schiefer"]]

    class TestBoundedReading:
        """A large file is not read to its end, or opened when it is too big."""

        @pytest.mark.parametrize("kind", ["csv", "xlsx", "ods"])
        def test_reading_stops_one_row_past_the_limit(self, monkeypatch, file_of, kind):
            monkeypatch.setattr(FileReader, "MAX_ROWS", 3)
            raw = file_of(kind, [["A"]] + [[str(n)] for n in range(20)])

            grid = FileReader.read_grid(raw, FileReader.file_format(NAMES[kind]))

            assert len(grid) == 3 + 2

        @pytest.mark.parametrize("kind", ["xlsx", "ods"])
        def test_a_sheet_larger_uncompressed_than_the_limit_is_refused_unopened(
            self, monkeypatch, file_of, kind
        ):
            monkeypatch.setattr(FileReader, "MAX_UNCOMPRESSED", 100)
            raw = file_of(kind, [HEADINGS, *ROWS])

            assert code_of(raw, NAMES[kind]) == "too_large_unpacked"


def xlsx_claiming(rows, dimension):
    """Build a workbook whose sheet declares ``dimension`` as its used range."""
    import io
    import re
    import zipfile

    from openpyxl import Workbook

    book = Workbook()
    for row in rows:
        book.active.append(list(row))
    plain = io.BytesIO()
    book.save(plain)
    out = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(plain.getvalue())) as source,
        zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target,
    ):
        for entry in source.namelist():
            data = source.read(entry)
            if entry == "xl/worksheets/sheet1.xml":
                data = re.sub(
                    rb'<dimension ref="[^"]*"',
                    b'<dimension ref="%s"' % dimension.encode(),
                    data,
                )
            target.writestr(entry, data)
    return out.getvalue()


def ods_with_cell(cell_xml):
    """Build an OpenDocument file whose second row holds the given cell markup."""
    import io
    import zipfile

    plain = ods_of([[["h"], ["x"]]])
    out = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(plain)) as source,
        zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target,
    ):
        for entry in source.namelist():
            data = source.read(entry)
            if entry == "content.xml":
                marker = (
                    b'<table:table-cell office:value-type="string">'
                    b"<text:p>x</text:p></table:table-cell>"
                )
                assert marker in data
                data = data.replace(marker, cell_xml.encode())
            target.writestr(entry, data)
    return out.getvalue()


class TestReaderBounds:
    """A small file never costs more memory than its real cells."""

    def test_a_value_repeated_across_many_columns_is_cut_while_it_is_read(self):
        raw = ods_of([[["h"], ["x"]]], repeated=(0, 1, 0, 3_000_000))
        assert len(raw) < 2000

        grid = FileReader.read_grid(raw, "ods")

        assert max(len(row) for row in grid) <= 1024

    def test_a_workbook_claiming_the_last_column_is_not_padded_to_it(self):
        raw = xlsx_claiming([["h"], ["x"], ["y"]], "A1:XFD3")

        grid = FileReader.read_grid(raw, "xlsx")

        assert max(len(row) for row in grid) <= 1024
        assert FileReader.parse(raw, "xlsx")[1] == [["x"], ["y"]]

    def test_trailing_empty_cells_are_dropped_from_a_row_read(self):
        raw = xlsx_claiming([["h", "i"], ["x"]], "A1:ZZ2")

        grid = FileReader.read_grid(raw, "xlsx")

        assert grid == [["h", "i"], ["x"]]

    def test_an_ods_sheet_over_its_ceiling_is_refused_before_it_is_loaded(self):
        import io
        import zipfile

        size = FileReader.MAX_UNCOMPRESSED_ODS + 1024
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("content.xml", b" " * size)

        assert code_of(out.getvalue(), "rocks.ods") == "too_large_unpacked"


class TestMalformedSheets:
    """A spreadsheet that breaks while it is read is refused, never a crash."""

    @pytest.mark.parametrize(
        "cell",
        [
            '<table:table-cell office:value-type="float"/>',
            '<table:table-cell office:value-type="float" office:value="abc"/>',
            '<table:table-cell office:value-type="string" '
            'table:number-columns-repeated="many"><text:p>x</text:p>'
            "</table:table-cell>",
        ],
    )
    def test_an_ods_cell_that_is_not_readable_is_unreadable(self, cell):
        assert code_of(ods_with_cell(cell), "rocks.ods") == "unreadable"

    def test_a_workbook_whose_sheet_breaks_part_way_is_unreadable(self):
        import io
        import zipfile

        raw = xlsx_claiming([["h"]] + [[str(n)] for n in range(200)], "A1:A201")
        out = io.BytesIO()
        with (
            zipfile.ZipFile(io.BytesIO(raw)) as source,
            zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as target,
        ):
            for entry in source.namelist():
                data = source.read(entry)
                if entry == "xl/worksheets/sheet1.xml":
                    data = data[: len(data) // 2]
                target.writestr(entry, data)

        assert code_of(out.getvalue(), "rocks.xlsx") == "unreadable"

    def test_a_file_cut_by_the_blank_row_cap_is_refused(self, monkeypatch):
        monkeypatch.setattr(FileReader, "MAX_ROWS", 3)
        raw = b"A\n" + b"\n" * 30 + b"late\n"

        assert code_of(raw) == "too_many_rows"

    def test_a_file_of_blank_rows_ending_at_the_cap_is_not_cut(self, monkeypatch):
        monkeypatch.setattr(FileReader, "MAX_ROWS", 3)
        raw = b"A\nx\n" + b"\n" * 4

        headings, rows, _lines = FileReader.parse(raw, "csv")

        assert (headings, rows) == (["A"], [["x"]])
