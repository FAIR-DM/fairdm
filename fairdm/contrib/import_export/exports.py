"""Write the rows of a record type as a file.

An export writes exactly the columns the type's table schema lists, so a file that goes
out can come back in.
"""

import io
import re
from dataclasses import dataclass

import tablib
from django.http import HttpResponse
from django.utils.http import content_disposition_header
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from .widgets import render_cell

SHEET_NAME_LIMIT = 31
"""The most characters Excel allows in a sheet's name."""

FORBIDDEN_IN_SHEET_NAME = re.compile(r"[\[\]:*?/\\]")
"""The characters Excel does not allow in a sheet's name."""

SAMPLE_COLUMNS = ("sample_name", "sample")
"""The columns that name a sample, written only for a sample the viewer may open."""

BYTE_ORDER_MARK = "﻿"
"""What starts a CSV file so Excel reads it as UTF-8."""

MIN_VALIDATED_ROWS = 5000
"""The fewest rows of a column a list validation covers."""

SPARE_VALIDATED_ROWS = 1000
"""How many rows past the data a list validation covers."""


@dataclass(frozen=True)
class ExportFormat:
    """One file format an export can be written in.

    Attributes:
        key: The short name the address and the menu use.
        label: What the menu calls the format.
        hint: The menu's one-line note about the format.
        content_type: The response's content type.
        extension: The file name's extension.
    """

    key: str
    label: str
    hint: str
    content_type: str
    extension: str


EXPORT_FORMATS: tuple[ExportFormat, ...] = (
    ExportFormat(
        "csv",
        "CSV",
        gettext_lazy("Opens anywhere"),
        "text/csv; charset=utf-8",
        "csv",
    ),
    ExportFormat(
        "xlsx",
        "Excel",
        gettext_lazy("With the column guide inside"),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xlsx",
    ),
    ExportFormat(
        "ods",
        "OpenDocument",
        gettext_lazy("LibreOffice, Numbers"),
        "application/vnd.oasis.opendocument.spreadsheet",
        "ods",
    ),
    ExportFormat(
        "tsv",
        "TSV",
        gettext_lazy("Tab-separated text"),
        "text/tab-separated-values; charset=utf-8",
        "tsv",
    ),
    ExportFormat(
        "json",
        "JSON",
        gettext_lazy("For scripts"),
        "application/json",
        "json",
    ),
)
"""Every format, in the order the menu lists them."""


def format_for(key: str) -> ExportFormat | None:
    """Find a format by its key.

    Args:
        key: The format's key, such as ``csv``.

    Returns:
        The format, or None when no format has the key.
    """
    return next((entry for entry in EXPORT_FORMATS if entry.key == key), None)


class TableExport:
    """Writes the rows of one record type in any export format.

    Attributes:
        schema: The type's table schema, which decides the columns.
    """

    def __init__(self, schema):
        """Keep the schema the files are written under.

        Args:
            schema: The type's table schema.
        """
        self.schema = schema

    def rows(self, queryset):
        """Write each record as a row of cells.

        The records are read in chunks, so a large table is never held in memory. A
        measurement's sample is named only when its ``sample_open`` annotation is true.

        Args:
            queryset: The records, in the order the rows should come out.

        Yields:
            A list of cells, one per column, for each record.
        """
        for record in queryset.iterator(chunk_size=500):
            hidden = not getattr(record, "sample_open", False)
            yield [
                ""
                if hidden and column.name in SAMPLE_COLUMNS
                else render_cell(column, record)
                for column in self.schema.columns
            ]

    def response(self, queryset, key, filename_stem):
        """Write the records as a file download.

        Args:
            queryset: The records to write.
            key: The key of one of ``EXPORT_FORMATS``.
            filename_stem: What the file's name starts with, before its extension.

        Returns:
            The response, with the format's content type and a file name made from the
            stem, in any script.

        Raises:
            ValueError: When no format has the key.
        """
        chosen = format_for(key)
        if chosen is None:
            raise ValueError(f"Unknown export format: {key!r}")
        rows = self.rows(queryset.order_by("pk"))
        if key == "xlsx":
            payload = self.workbook(rows)
        else:
            data = tablib.Dataset(headers=self.schema.headings)
            for row in rows:
                data.append(row)
            payload = data.export(key)
            if isinstance(payload, str):
                prefix = BYTE_ORDER_MARK if key == "csv" else ""
                payload = (prefix + payload).encode("utf-8")
        response = HttpResponse(payload, content_type=chosen.content_type)
        filename = f"{slugify(filename_stem, allow_unicode=True)}.{chosen.extension}"
        response["Content-Disposition"] = content_disposition_header(True, filename)
        return response

    def workbook(self, rows=()):
        """Write an Excel workbook of the rows, a column guide and the allowed values.

        Every string is written as text, so a name that starts with ``=`` is never a
        formula.

        Args:
            rows: Any iterable of rows of cells, none for an empty file.

        Returns:
            The workbook's bytes.
        """
        book = Workbook()
        data = book.active
        taken = set()
        data.title = self.sheet_title(self.schema.name, taken)
        count = self.write_data(data, rows)
        allowed = book.create_sheet(self.sheet_title(_("Allowed values"), taken))
        self.write_allowed(allowed, data, count)
        guide = book.create_sheet(self.sheet_title(_("Column guide"), taken), 1)
        self.write_guide(guide)
        buffer = io.BytesIO()
        book.save(buffer)
        return buffer.getvalue()

    def sheet_title(self, name, taken):
        """Make a name Excel accepts for a sheet and no other sheet has.

        Args:
            name: The name wanted.
            taken: The names already used. The new one is added to it.

        Returns:
            The name without the characters Excel forbids, cut to 31 characters, with
            `` (2)`` and so on before the cut when another sheet has it.
        """
        base = FORBIDDEN_IN_SHEET_NAME.sub("", str(name)).strip() or "Sheet"
        title, number = base[:SHEET_NAME_LIMIT], 1
        while title.casefold() in taken:
            number += 1
            suffix = f" ({number})"
            title = base[: SHEET_NAME_LIMIT - len(suffix)] + suffix
        taken.add(title.casefold())
        return title

    def write_text(self, sheet, row, column, value):
        """Write a cell as text, never as a formula.

        Args:
            sheet: The worksheet.
            row: The cell's row, from 1.
            column: The cell's column, from 1.
            value: The value to write.

        Returns:
            The cell.
        """
        cell = sheet.cell(row=row, column=column, value=value)
        if isinstance(value, str):
            cell.data_type = "s"
        return cell

    def write_data(self, sheet, rows):
        """Write the headings, their notes and the rows.

        Args:
            sheet: The first worksheet.
            rows: The rows of cells.

        Returns:
            How many rows were written.
        """
        plain = PatternFill("solid", fgColor="E8EEF5")
        needed = PatternFill("solid", fgColor="FBE7C6")
        export_only = PatternFill("solid", fgColor="EEEEEE")
        for index, column in enumerate(self.schema.columns, start=1):
            cell = self.write_text(sheet, 1, index, column.name)
            cell.font = Font(bold=True)
            cell.fill = (
                needed
                if column.required
                else export_only
                if not column.importable
                else plain
            )
            cell.comment = Comment(
                self.note_for(column), "FairDM", width=320, height=180
            )
            sheet.column_dimensions[get_column_letter(index)].width = max(
                12, min(40, len(column.name) + 4)
            )
        count = 0
        for count, row in enumerate(rows, start=1):
            for index, value in enumerate(row, start=1):
                self.write_text(sheet, count + 1, index, value)
        sheet.freeze_panes = "A2"
        return count

    def note_for(self, column):
        """Write the note that sits on a column's heading.

        Args:
            column: The column.

        Returns:
            The label, the kind and unit, how to write it, whether it is needed and
            what it holds.
        """
        lines = [str(column.label)]
        kind = str(column.kind_label)
        lines[0] += f"\n{kind}, {column.unit}" if column.unit else f"\n{kind}"
        lines.append(column.format_hint)
        if column.required:
            lines.append(_("Required for new records."))
        if not column.importable:
            lines.append(_("Not read on import."))
        if column.description:
            lines.append(f"\n{column.description}")
        return "\n".join(lines)

    def write_allowed(self, sheet, data, count):
        """Write the allowed values and the list validations that use them.

        Args:
            sheet: The worksheet of allowed values.
            data: The worksheet of rows, which gets the validations.
            count: How many rows the data sheet holds.
        """
        last_row = max(count + SPARE_VALIDATED_ROWS, MIN_VALIDATED_ROWS)
        position = 0
        for index, column in enumerate(self.schema.columns, start=1):
            values = [value for value, _meaning in column.allowed]
            if column.kind == "boolean":
                values = ["yes", "no"]
            if not values:
                continue
            position += 1
            self.write_text(sheet, 1, position, column.name).font = Font(bold=True)
            for row, value in enumerate(values, start=2):
                self.write_text(sheet, row, position, value)
            letter = get_column_letter(position)
            title = sheet.title.replace("'", "''")
            validation = DataValidation(
                type="list",
                formula1=f"='{title}'!${letter}$2:${letter}${len(values) + 1}",
                allow_blank=True,
                showErrorMessage=False,
            )
            target = get_column_letter(index)
            validation.add(f"{target}2:{target}{last_row}")
            data.add_data_validation(validation)

    def write_guide(self, sheet):
        """Write the column guide: a line about the portal ID and a row per column.

        Args:
            sheet: The guide's worksheet.
        """
        head = PatternFill("solid", fgColor="E8EEF5")
        self.write_text(
            sheet, 1, 1, _("Columns of %(type)s files") % {"type": self.schema.name}
        ).font = Font(bold=True, size=13)
        self.write_text(
            sheet,
            2,
            1,
            _(
                "Leave Portal ID empty for new records. Keep it when you edit an "
                "export, so the rows update the records they came from."
            ),
        )
        headings = [
            _("Heading"),
            _("Label"),
            _("Needed"),
            _("Type"),
            _("Unit"),
            _("How to write it"),
            _("Example"),
            _("What it holds"),
        ]
        for index, heading in enumerate(headings, start=1):
            cell = self.write_text(sheet, 4, index, heading)
            cell.font = Font(bold=True)
            cell.fill = head
        for row, column in enumerate(self.schema.columns, start=5):
            if column.required:
                needed = _("Required for new records")
            elif not column.importable:
                needed = _("Written on export, not read")
            else:
                needed = _("Optional")
            cells = [
                column.name,
                str(column.label),
                needed,
                str(column.kind_label),
                column.unit,
                column.format_hint,
                column.example,
                str(column.description),
            ]
            for index, value in enumerate(cells, start=1):
                cell = self.write_text(sheet, row, index, value)
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        for index, width in enumerate([22, 22, 24, 18, 8, 34, 22, 60], start=1):
            sheet.column_dimensions[get_column_letter(index)].width = width
