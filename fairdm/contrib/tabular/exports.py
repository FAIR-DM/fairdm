"""Files that go out: exports, templates, the column guide and a file with its problems marked.

An export writes exactly the columns an import reads, so a file that goes out comes back in.
"""

from __future__ import annotations

import io
import json

import tablib
from django.http import HttpResponse
from django.utils.text import slugify
from django.utils.translation import gettext as _

from .resources import render_cell
from .schema import TableSchema

FORMATS = {
    "csv": ("CSV", "text/csv; charset=utf-8", "csv"),
    "xlsx": ("Excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"),
    "ods": ("OpenDocument", "application/vnd.oasis.opendocument.spreadsheet", "ods"),
    "tsv": ("Tab-separated", "text/tab-separated-values; charset=utf-8", "tsv"),
    "json": ("JSON", "application/json", "json"),
}


def rows_for(schema: TableSchema, queryset):
    for instance in queryset.iterator(chunk_size=500):
        yield [render_cell(c, instance) for c in schema.columns]


def export_response(schema: TableSchema, queryset, fmt: str, basename: str):
    label, content_type, ext = FORMATS[fmt]
    if fmt == "xlsx":
        payload = workbook(schema, rows_for(schema, queryset))
    else:
        data = tablib.Dataset(headers=schema.headings)
        for row in rows_for(schema, queryset):
            data.append(row)
        if fmt == "json":
            payload = json.dumps(data.dict, ensure_ascii=False, indent=1).encode()
        elif fmt == "csv":
            payload = ("﻿" + data.export("csv")).encode()
        else:
            payload = data.export(fmt)
            if isinstance(payload, str):
                payload = payload.encode()
    response = HttpResponse(payload, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{slugify(basename)}.{ext}"'
    return response


def guide_rows(schema: TableSchema):
    for column in schema.columns:
        allowed = "; ".join(v for v, _m in column.allowed)
        if column.allowed_total:
            allowed += _(" … and %(n)s more") % {"n": column.allowed_total - len(column.allowed)}
        yield [
            column.name,
            str(column.label),
            _("Required for new records")
            if column.required
            else (_("Written on export, not read") if column.role == "export" else _("Optional")),
            str(column.kind_label),
            column.unit,
            str(column.format_hint),
            allowed,
            column.example,
            str(column.description),
        ]


GUIDE_HEADINGS = [
    "Heading",
    "Label",
    "Needed",
    "Type",
    "Unit",
    "How to write it",
    "Allowed values",
    "Example",
    "What it holds",
]


def workbook(schema: TableSchema, rows, example=False):
    """An Excel workbook: the data sheet first, then the column guide and the allowed lists."""
    from openpyxl import Workbook
    from openpyxl.comments import Comment
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    book = Workbook()
    sheet = book.active
    sheet.title = schema.name[:31]
    sheet.append(schema.headings)
    head_fill = PatternFill("solid", fgColor="E8EEF5")
    need_fill = PatternFill("solid", fgColor="FBE7C6")
    export_fill = PatternFill("solid", fgColor="EEEEEE")
    for index, column in enumerate(schema.columns, start=1):
        cell = sheet.cell(row=1, column=index)
        cell.font = Font(bold=True)
        cell.fill = need_fill if column.required else (export_fill if column.role == "export" else head_fill)
        text = f"{column.label}\n{column.kind_label}"
        if column.unit:
            text += f", {column.unit}"
        text += f"\n{column.format_hint}"
        if column.required:
            text += "\n" + _("Required for new records.")
        if column.role == "export":
            text += "\n" + _("Not read on import.")
        if column.description:
            text += f"\n\n{column.description}"
        cell.comment = Comment(text, "FairDM", width=320, height=180)
        sheet.column_dimensions[get_column_letter(index)].width = max(12, min(40, len(column.name) + 4))
    count = 0
    for row in rows:
        sheet.append(row)
        count += 1
    if example and not count:
        sheet.append([c.example if c.role != "key" else "" for c in schema.columns])
    sheet.freeze_panes = "A2"

    lists = book.create_sheet(_("Allowed values")[:31])
    list_column = 0
    for index, column in enumerate(schema.columns, start=1):
        options = [v for v, _m in column.allowed]
        if column.kind == "boolean":
            options = ["yes", "no"]
        if not options:
            continue
        list_column += 1
        letter = get_column_letter(list_column)
        lists.cell(row=1, column=list_column, value=column.name).font = Font(bold=True)
        for r, option in enumerate(options, start=2):
            lists.cell(row=r, column=list_column, value=option)
        validation = DataValidation(
            type="list",
            formula1=f"='{lists.title}'!${letter}$2:${letter}${len(options) + 1}",
            allow_blank=True,
            showErrorMessage=False,
        )
        sheet.add_data_validation(validation)
        target = get_column_letter(index)
        validation.add(f"{target}2:{target}5000")

    guide = book.create_sheet(_("Column guide")[:31])
    guide.append([_("Columns of %(type)s files") % {"type": schema.name}])
    guide["A1"].font = Font(bold=True, size=13)
    guide.append([_("Leave Portal ID empty for new records. Keep it when you edit an export, so the rows update the records they came from.")])
    guide.append([])
    guide.append(GUIDE_HEADINGS)
    for cell in guide[4]:
        cell.font = Font(bold=True)
        cell.fill = head_fill
    for row in guide_rows(schema):
        guide.append(row)
    widths = [22, 22, 22, 18, 8, 34, 34, 22, 60]
    for i, width in enumerate(widths, start=1):
        guide.column_dimensions[get_column_letter(i)].width = width
    for row in guide.iter_rows(min_row=5):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


def template_response(schema: TableSchema, fmt: str):
    label, content_type, ext = FORMATS[fmt]
    if fmt == "xlsx":
        payload = workbook(schema, [], example=True)
    else:
        data = tablib.Dataset(headers=schema.headings)
        if fmt == "json":
            payload = json.dumps([{c.name: "" for c in schema.columns}], indent=1).encode()
        else:
            payload = data.export(fmt)
            payload = payload.encode() if isinstance(payload, str) else payload
            if fmt == "csv":
                payload = "﻿".encode() + payload
    response = HttpResponse(payload, content_type=content_type)
    response["Content-Disposition"] = f'attachment; filename="{slugify(schema.name)}-template.{ext}"'
    return response


def schema_response(schema: TableSchema):
    response = HttpResponse(
        json.dumps(schema.as_frictionless(), indent=2, ensure_ascii=False),
        content_type="application/json",
    )
    response["Content-Disposition"] = f'attachment; filename="{slugify(schema.name)}-schema.json"'
    return response


def problems_response(job):
    """The uploaded file back, with each row's problems beside it and the cells marked."""
    from openpyxl import Workbook
    from openpyxl.comments import Comment
    from openpyxl.styles import Font, PatternFill

    headers = job.headers
    reverse_map = {v: k for k, v in job.column_map.items() if v}
    book = Workbook()
    sheet = book.active
    sheet.title = _("Rows")[:31]
    sheet.append([_("Problems"), _("Row in your file"), *headers])
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    red = PatternFill("solid", fgColor="F8D7DA")
    for entry in job.rows:
        problems = entry.get("problems", [])
        text = "\n".join(
            (f"{p['column']}: " if p.get("column") else "") + p["message"] for p in problems
        )
        sheet.append([text, entry["line"], *[entry["values"].get(h, "") for h in headers]])
        r = sheet.max_row
        if problems:
            sheet.cell(row=r, column=1).fill = red
        for p in problems:
            heading = reverse_map.get(p.get("column"))
            if heading in headers:
                cell = sheet.cell(row=r, column=3 + headers.index(heading))
                cell.fill = red
                cell.comment = Comment(p["message"], "FairDM")
    sheet.column_dimensions["A"].width = 60
    sheet.freeze_panes = "C2"
    buffer = io.BytesIO()
    book.save(buffer)
    response = HttpResponse(buffer.getvalue(), content_type=FORMATS["xlsx"][1])
    stem = job.filename.rsplit(".", 1)[0]
    response["Content-Disposition"] = f'attachment; filename="{slugify(stem)}-problems.xlsx"'
    return response
