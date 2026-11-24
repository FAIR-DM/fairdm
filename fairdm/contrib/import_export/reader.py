"""Reading a file into headings and rows."""

import csv
import io
import zipfile
from pathlib import PurePath

from django.utils.translation import gettext_lazy as _


class FileProblem(Exception):
    """A file that cannot be imported, with the reason a person can act on.

    Args:
        message: The reason, in the active language.
        code: A short name for the reason: ``format``, ``too_large``,
            ``too_large_unpacked``, ``unreadable``, ``empty``, ``no_rows`` or
            ``too_many_rows``.

    Attributes:
        code: The short name of the reason.
    """

    def __init__(self, message, code):
        """Keep the reason and its short name."""
        super().__init__(message)
        self.code = code


class FileReader:
    """Turns the bytes of a CSV, TSV, Excel or OpenDocument file into rows.

    Nothing is kept between calls, so every method is a class method.

    Attributes:
        FORMATS: The formats that are read, as file extensions without the dot.
        MAX_BYTES: The largest file read.
        MAX_ROWS: The most data rows a file may hold.
        MAX_COLUMNS: The most cells kept of a row. Cells past it are never read.
        MAX_UNCOMPRESSED: The largest a workbook's first sheet may be once unpacked.
        MAX_UNCOMPRESSED_ODS: The largest an OpenDocument spreadsheet's content may
            be once unpacked. odfpy builds the whole document in memory at about
            twenty times the size of the XML, so this is far below
            ``MAX_UNCOMPRESSED``.
        MAX_REPEAT: The most empty cells one repeated cell of an OpenDocument row
            is expanded to.
    """

    FORMATS = ("csv", "tsv", "xlsx", "ods")
    MAX_BYTES = 20 * 1024 * 1024
    MAX_ROWS = 50_000
    MAX_COLUMNS = 1024
    MAX_UNCOMPRESSED = 200 * 1024 * 1024
    MAX_UNCOMPRESSED_ODS = 24 * 1024 * 1024
    MAX_REPEAT = 1024
    SHEET_ENTRIES = {"xlsx": "xl/worksheets/sheet1.xml", "ods": "content.xml"}
    ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")

    @classmethod
    def file_format(cls, name):
        """Name the format of a file by its extension.

        Args:
            name: The file's name.

        Returns:
            One of ``FORMATS``.

        Raises:
            FileProblem: With code ``format`` when the extension is not one read.
        """
        extension = PurePath(name).suffix.lower().lstrip(".")
        if extension not in cls.FORMATS:
            raise FileProblem(
                _(
                    "“%(name)s” is not a file this page reads. Use CSV, Excel "
                    "(.xlsx), OpenDocument (.ods) or tab-separated (.tsv) text."
                )
                % {"name": name},
                "format",
            )
        return extension

    @classmethod
    def blank(cls, cell):
        """Say whether a cell holds nothing.

        Args:
            cell: A cell as read.

        Returns:
            True for no value or text of only spaces.
        """
        return cell is None or (isinstance(cell, str) and not cell.strip())

    @classmethod
    def decode(cls, raw):
        """Read the bytes of a text file.

        Args:
            raw: The file's bytes.

        Returns:
            The text, read as UTF-8 with or without a byte order mark, then as
            Windows-1252.
        """
        for encoding in cls.ENCODINGS:
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise FileProblem(_("The file's text could not be read."), "unreadable")

    @classmethod
    def too_many_rows(cls):
        """Build the problem of a file with more rows than the limit.

        Returns:
            A ``FileProblem`` with code ``too_many_rows``.
        """
        return FileProblem(
            _("The file has more than %(max)s rows. Split it into smaller files.")
            % {"max": cls.MAX_ROWS},
            "too_many_rows",
        )

    @classmethod
    def limited(cls, rows):
        """Pass rows on until one more than the limit has been read.

        Args:
            rows: An iterable of rows, the first of which holds the headings.

        Yields:
            Rows up to the headings and ``MAX_ROWS + 1`` rows with a value. Blank rows
            are passed on so a row keeps its line number, up to twice the limit.

        Raises:
            FileProblem: With code ``too_many_rows`` when the file goes on past the
                blank rows passed, so rows after them would be left out unseen.
        """
        wanted = cls.MAX_ROWS + 2
        filled = 0
        rows = iter(rows)
        for count, row in enumerate(rows, start=1):
            yield row
            filled += not all(cls.blank(cell) for cell in row)
            if filled >= wanted:
                return
            if count >= 2 * wanted:
                if next(rows, None) is not None:
                    raise cls.too_many_rows()
                return

    @classmethod
    def trimmed(cls, row):
        """Cut a row to ``MAX_COLUMNS`` cells and drop its empty cells at the end.

        Args:
            row: A row as read.

        Returns:
            The row's cells as a list.
        """
        cells = list(row[: cls.MAX_COLUMNS])
        while cells and cls.blank(cells[-1]):
            cells.pop()
        return cells

    @classmethod
    def check_unpacked(cls, raw, fmt):
        """Refuse a workbook or spreadsheet whose first sheet unpacks too large.

        The size is read from the archive's index, so nothing is unpacked.

        Args:
            raw: The file's bytes.
            fmt: ``xlsx`` or ``ods``.

        Raises:
            FileProblem: With code ``unreadable`` when the file is not an archive and
                ``too_large_unpacked`` when the sheet is over ``MAX_UNCOMPRESSED``, or
                ``MAX_UNCOMPRESSED_ODS`` for an OpenDocument file.
        """
        ceiling = cls.MAX_UNCOMPRESSED
        if fmt == "ods":
            ceiling = min(ceiling, cls.MAX_UNCOMPRESSED_ODS)
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                names = archive.namelist()
                entry = cls.SHEET_ENTRIES[fmt]
                if entry not in names:
                    sheets = sorted(n for n in names if n.startswith("xl/worksheets/"))
                    entry = sheets[0] if sheets else entry
                size = archive.getinfo(entry).file_size
        except (zipfile.BadZipFile, KeyError):
            raise FileProblem(
                _("The file is not a spreadsheet this page can open."), "unreadable"
            ) from None
        if size > ceiling:
            raise FileProblem(
                _("The file's first sheet is too large to open."), "too_large_unpacked"
            )

    @classmethod
    def read_csv(cls, raw, fmt):
        """Read a comma, semicolon or tab separated file.

        Args:
            raw: The file's bytes.
            fmt: ``csv`` or ``tsv``. A tab is never the delimiter of a ``csv``.

        Returns:
            An iterator of rows of text.
        """
        text = cls.decode(raw)
        if fmt == "tsv":
            delimiter = "\t"
        else:
            try:
                delimiter = csv.Sniffer().sniff(text[:4096], delimiters=",;").delimiter
            except csv.Error:
                delimiter = ","
        return csv.reader(io.StringIO(text, newline=""), delimiter=delimiter)

    @classmethod
    def read_xlsx(cls, raw):
        """Read the first sheet of an Excel workbook.

        Args:
            raw: The file's bytes.

        Returns:
            An iterator of rows of cells.
        """
        from openpyxl import load_workbook

        cls.check_unpacked(raw, "xlsx")
        try:
            book = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
            sheet = book.worksheets[0]
        except Exception:
            raise FileProblem(
                _("The file is not an Excel workbook this page can open."),
                "unreadable",
            ) from None
        return (list(row) for row in sheet.iter_rows(values_only=True))

    @classmethod
    def read_ods(cls, raw):
        """Read the first sheet of an OpenDocument spreadsheet with odfpy.

        A repeated cell is read once for each repeat, and a repeated row likewise.
        Repeated empty cells are cut at ``MAX_REPEAT`` and a row at ``MAX_COLUMNS``.

        Args:
            raw: The file's bytes.

        Returns:
            An iterator of rows of cells.
        """
        from odf.opendocument import load
        from odf.table import Table, TableRow

        cls.check_unpacked(raw, "ods")
        try:
            tables = load(io.BytesIO(raw)).spreadsheet.getElementsByType(Table)
        except Exception:
            raise FileProblem(
                _("The file is not an OpenDocument spreadsheet this page can open."),
                "unreadable",
            ) from None
        if not tables:
            return iter(())
        return cls.ods_rows(tables[0].getElementsByType(TableRow))

    @classmethod
    def ods_rows(cls, table_rows):
        """Expand the repeats of an OpenDocument table's rows.

        Args:
            table_rows: The table's row elements.

        Yields:
            One list of cells for each row, repeated rows as many times as repeated.
        """
        for table_row in table_rows:
            cells = cls.ods_cells(table_row)
            repeat = int(table_row.getAttribute("numberrowsrepeated") or 1)
            yield from (list(cells) for number in range(repeat))

    @classmethod
    def ods_cells(cls, table_row):
        """Read the cells of an OpenDocument row, repeats expanded.

        Args:
            table_row: The row element.

        Returns:
            The cells' values: text, a number, a date as text or None.
        """
        from odf.teletype import extractText

        cells = []
        for cell in table_row.childNodes:
            if cell.qname[1] not in ("table-cell", "covered-table-cell"):
                continue
            kind = cell.getAttribute("valuetype")
            if kind in ("float", "percentage", "currency"):
                number = float(cell.getAttribute("value"))
                value = int(number) if number.is_integer() else number
            elif kind == "boolean":
                value = cell.getAttribute("booleanvalue") == "true"
            elif kind == "date":
                value = cell.getAttribute("datevalue")
            elif kind == "string" or cell.childNodes:
                value = "".join(extractText(p) for p in cell.childNodes) or None
            else:
                value = None
            repeat = int(cell.getAttribute("numbercolumnsrepeated") or 1)
            if value is None:
                repeat = min(repeat, cls.MAX_REPEAT)
            cells.extend([value] * min(repeat, cls.MAX_COLUMNS - len(cells)))
            if len(cells) >= cls.MAX_COLUMNS:
                break
        return cells

    @classmethod
    def read_grid(cls, raw, fmt):
        """Read every row of a file, as lists of cells.

        Reading stops at the headings and ``MAX_ROWS + 1`` rows, so a file over the
        limit is never read to its end. Each row is cut to ``MAX_COLUMNS`` cells with
        its empty cells at the end dropped as it is read.

        Args:
            raw: The file's bytes.
            fmt: One of ``FORMATS``.

        Returns:
            The rows, headings first.

        Raises:
            FileProblem: With code ``unreadable``, ``too_large_unpacked`` or
                ``too_many_rows``. Any error a parser raises while it reads is
                ``unreadable``.
        """
        if fmt in ("csv", "tsv"):
            rows = cls.read_csv(raw, fmt)
        elif fmt == "xlsx":
            rows = cls.read_xlsx(raw)
        elif fmt == "ods":
            rows = cls.read_ods(raw)
        else:
            raise FileProblem(_("Unknown format."), "format")
        try:
            return list(cls.limited(cls.trimmed(row) for row in rows))
        except FileProblem:
            raise
        except Exception:
            raise FileProblem(
                _("The file is not a spreadsheet this page can open."), "unreadable"
            ) from None

    @classmethod
    def parse(cls, raw, fmt):
        """Read a file's headings and its rows.

        Args:
            raw: The file's bytes.
            fmt: One of ``FORMATS``.

        Returns:
            The headings as trimmed text with empty ones at the end dropped, the rows
            as lists of cells cut or filled to the headings' length with blank rows
            left out, and the line of the file each row came from, counting from 1.

        Raises:
            FileProblem: With code ``too_large``, ``unreadable``, ``empty``,
                ``no_rows`` or ``too_many_rows``.
        """
        if len(raw) > cls.MAX_BYTES:
            raise FileProblem(
                _("The file is larger than %(mb)s MB.")
                % {"mb": cls.MAX_BYTES // (1024 * 1024)},
                "too_large",
            )
        grid = cls.read_grid(raw, fmt)
        start = next(
            (i for i, row in enumerate(grid) if not all(map(cls.blank, row))), None
        )
        if start is None:
            raise FileProblem(_("The file is empty."), "empty")
        headings = ["" if cls.blank(c) else str(c).strip() for c in grid[start]]
        while headings and not headings[-1]:
            headings.pop()
        rows, lines = [], []
        for line, row in enumerate(grid[start + 1 :], start=start + 2):
            cells = list(row[: len(headings)])
            cells += [None] * (len(headings) - len(cells))
            if not all(map(cls.blank, cells)):
                rows.append(cells)
                lines.append(line)
        if not rows:
            raise FileProblem(_("The file has headings but no rows."), "no_rows")
        if len(rows) > cls.MAX_ROWS:
            raise cls.too_many_rows()
        return headings, rows, lines
