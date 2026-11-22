"""Reading a file, checking it, importing it and undoing an import."""

from __future__ import annotations

import csv
import io
import json
from collections import defaultdict

import tablib
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import ImportJob
from .resources import RowProblem, blank, build_resource, clean_text
from .schema import schema_for

READABLE = {
    "csv": _("CSV"),
    "tsv": _("Tab-separated text"),
    "txt": _("Tab-separated text"),
    "xlsx": _("Excel workbook"),
    "ods": _("OpenDocument spreadsheet"),
    "json": _("JSON"),
}
MAX_BYTES = 20 * 1024 * 1024
MAX_ROWS = 50_000


class FileProblem(Exception):
    pass


# Reading --------------------------------------------------------------------------------------


def file_format(name: str) -> str:
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext == "txt":
        return "tsv"
    if ext not in READABLE:
        raise FileProblem(
            _("“%(name)s” is not a file this page reads. Use CSV, Excel (.xlsx), OpenDocument (.ods), tab-separated text or JSON.")
            % {"name": name}
        )
    return ext


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise FileProblem(_("The file's text could not be read."))


def read_grid(raw: bytes, fmt: str) -> list[list]:
    """Every row of the file, as lists of cells."""
    if fmt in ("csv", "tsv"):
        text = decode(raw)
        if fmt == "tsv":
            delimiter = "\t"
        else:
            sample = text[:4096]
            try:
                delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
            except csv.Error:
                delimiter = ","
        return [list(r) for r in csv.reader(io.StringIO(text), delimiter=delimiter)]
    if fmt == "xlsx":
        from openpyxl import load_workbook

        try:
            book = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
        except Exception:  # noqa: BLE001
            raise FileProblem(_("The file is not an Excel workbook this page can open.")) from None
        sheet = book.worksheets[0]
        return [list(r) for r in sheet.iter_rows(values_only=True)]
    if fmt == "ods":
        try:
            data = tablib.Dataset().load(raw, format="ods", headers=False)
        except Exception:  # noqa: BLE001
            raise FileProblem(_("The file is not an OpenDocument spreadsheet this page can open.")) from None
        return [list(r) for r in data]
    if fmt == "json":
        try:
            records = json.loads(decode(raw))
        except json.JSONDecodeError:
            raise FileProblem(_("The file is not valid JSON.")) from None
        if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
            raise FileProblem(_("A JSON file must be a list of objects, one per record."))
        headers = []
        for record in records:
            for key in record:
                if key not in headers:
                    headers.append(key)
        return [headers] + [[r.get(h) for h in headers] for r in records]
    raise FileProblem(_("Unknown format."))


def parse(raw: bytes, fmt: str):
    """Return (headings, rows, line numbers) with empty rows dropped."""
    grid = read_grid(raw, fmt)
    header_at = None
    for index, row in enumerate(grid):
        if any(not blank(c) for c in row):
            header_at = index
            break
    if header_at is None:
        raise FileProblem(_("The file is empty."))
    headers = [clean_text(c) for c in grid[header_at]]
    while headers and not headers[-1]:
        headers.pop()
    rows, lines = [], []
    for index, row in enumerate(grid[header_at + 1 :], start=header_at + 2):
        cells = list(row[: len(headers)]) + [None] * (len(headers) - len(row))
        if all(blank(c) for c in cells):
            continue
        rows.append(cells)
        lines.append(index)
    if not rows:
        raise FileProblem(_("The file has headings but no rows."))
    if len(rows) > MAX_ROWS:
        raise FileProblem(_("The file has %(n)s rows. Split it into files of at most %(max)s.") % {"n": len(rows), "max": MAX_ROWS})
    return headers, rows, lines


def start_job(dataset, model, uploaded, user, mode, empty) -> ImportJob:
    """Read the uploaded file far enough to match its columns. Raises FileProblem."""
    fmt = file_format(uploaded.name)
    if uploaded.size > MAX_BYTES:
        raise FileProblem(_("The file is larger than 20 MB."))
    raw = uploaded.read()
    headers, rows, _lines = parse(raw, fmt)
    seen = set()
    for h in headers:
        if h and h.lower() in seen:
            raise FileProblem(_("Two columns are headed “%(h)s”. Give each column its own heading.") % {"h": h})
        seen.add(h.lower())
    schema = schema_for(model)
    column_map = {}
    taken = set()
    for heading in headers:
        column = schema.match(heading)
        if column and column.name not in taken:
            column_map[heading] = column.name
            taken.add(column.name)
        else:
            column_map[heading] = ""
    samples = {}
    for i, heading in enumerate(headers):
        values = []
        for row in rows:
            cell = row[i]
            if not blank(cell):
                values.append(clean_text(cell)[:40])
            if len(values) == 4:
                break
        samples[heading] = values
    from django.contrib.contenttypes.models import ContentType
    from django.core.files.base import ContentFile

    job = ImportJob(
        dataset=dataset,
        content_type=ContentType.objects.get_for_model(model, for_concrete_model=True),
        created_by=user,
        filename=uploaded.name,
        file_format=fmt,
        file_size=len(raw),
        mode=mode,
        empty_cells=empty,
        headers=headers,
        samples=samples,
        column_map=column_map,
        row_count=len(rows),
    )
    job.file.save(uploaded.name, ContentFile(raw), save=False)
    job.save()
    return job


def mapping_problems(job: ImportJob, schema=None) -> list[str]:
    """What stops the matched columns from being checked."""
    schema = schema or schema_for(job.model)
    mapped = {v for v in job.column_map.values() if v}
    problems = []
    if not mapped:
        problems.append(_("No column in the file is matched to a field."))
    if job.mode != ImportJob.Mode.UPDATE:
        missing = [c for c in schema.required if c.name not in mapped]
        if missing:
            problems.append(
                _("New records need %(cols)s, and no column is matched to %(them)s.")
                % {
                    "cols": ", ".join(str(c.label) for c in missing),
                    "them": _("it") if len(missing) == 1 else _("them"),
                }
            )
    if job.mode == ImportJob.Mode.UPDATE and not ({"portal_id", "local_id"} & mapped):
        problems.append(_("Updating needs a Portal ID or Local ID column to find each record."))
    return problems


def mapping_warnings(job: ImportJob) -> list[str]:
    mapped = {v for v in job.column_map.values() if v}
    warnings = []
    if job.mode == ImportJob.Mode.BOTH and not ({"portal_id", "local_id"} & mapped):
        warnings.append(
            _("The file has no Portal ID or Local ID column, so every row will be added as a new record. Importing it a second time would add every row again.")
        )
    if ("latitude" in mapped) != ("longitude" in mapped):
        warnings.append(_("Only one of latitude and longitude is matched. A location needs both."))
    return warnings


# Checking and importing -----------------------------------------------------------------------


def progress_key(job_id):
    return f"tabular:{job_id}:progress"


def progress(job: ImportJob) -> int:
    return cache.get(progress_key(job.pk), 0)


def mapped_dataset(job: ImportJob):
    raw = job.file.open("rb").read()
    job.file.close()
    headers, rows, lines = parse(raw, job.file_format)
    keep = [(i, job.column_map.get(h)) for i, h in enumerate(headers) if job.column_map.get(h)]
    data = tablib.Dataset(headers=[name for _i, name in keep])
    for row in rows:
        data.append([row[i] if not isinstance(row[i], str) else row[i].strip() for i, _n in keep])
    return headers, rows, lines, data


def duplicate_problems(data: tablib.Dataset, lines) -> dict[int, dict]:
    """Rows of one file that point at the same record."""
    seen = defaultdict(list)
    shown = {}
    for index, row in enumerate(data.dict):
        pid = clean_text(row.get("portal_id"))
        lid = clean_text(row.get("local_id"))
        if pid:
            seen[("portal_id", pid)].append(index)
            shown[("portal_id", pid)] = pid
        elif lid:
            seen[("local_id", lid.lower())].append(index)
            shown[("local_id", lid.lower())] = lid
    problems = {}
    for key, indexes in seen.items():
        if len(indexes) < 2:
            continue
        column = key[0]
        what = _("portal ID") if column == "portal_id" else _("Local ID")
        for index in indexes:
            others = [str(lines[i]) for i in indexes if i != index]
            if len(others) == 1:
                message = _("Row %(row)s has the same %(what)s, %(v)s. A record may appear once in a file.")
            else:
                message = _("Rows %(row)s have the same %(what)s, %(v)s. A record may appear once in a file.")
            problems[index] = {
                "column": column,
                "message": message % {"row": ", ".join(others), "what": what, "v": shown[key]},
            }
    return problems


def friendly(message: str, code: str | None) -> str:
    if code in ("blank", "null", "required") or message in ("This field cannot be blank.", "This field cannot be null."):
        return _("Required for a new record.")
    return message


def run(job: ImportJob, dry_run: bool):
    """Check or import a job's file and keep the outcome of every row on the job."""
    schema = schema_for(job.model)
    headers, raw_rows, lines, data = mapped_dataset(job)
    columns = [h for h in data.headers]
    attribute_to_column = {c.attribute: c.name for c in schema.importable if c.attribute}
    attribute_to_column["location"] = "latitude"
    resource_class = build_resource(schema, job.dataset, columns=columns)
    resource = resource_class(job.dataset, mode=job.mode, empty=job.empty_cells, user=job.created_by)
    key = progress_key(job.pk)
    cache.set(key, 0, 3600)

    def on_row(n):
        if n % 10 == 0 or n == len(lines):
            cache.set(key, n, 3600)

    resource.on_row = on_row
    duplicates = duplicate_problems(data, lines)
    blocked = bool(duplicates) and not dry_run
    if blocked:
        dry_run = True
    result = resource.import_data(
        data,
        dry_run=dry_run,
        raise_errors=False,
        use_transactions=True,
        rollback_on_validation_errors=True,
        retain_instance_in_row_result=True,
    )
    cache.set(key, len(lines), 3600)

    entries = []
    summary = {"new": 0, "update": 0, "unchanged": 0, "skipped": 0, "problem": 0}
    undo = {"created": [], "updated": {}}
    errors_by_row = {}
    for number, row_errors in result.row_errors():
        errors_by_row[number] = row_errors
    for index, row_result in enumerate(result.rows):
        number = index + 1
        line = lines[index]
        values = {h: clean_text(raw_rows[index][i]) for i, h in enumerate(headers)}
        entry = {
            "line": line,
            "outcome": "",
            "label": "",
            "url": "",
            "changes": [],
            "note": "",
            "problems": [],
            "values": values,
        }
        note = resource.row_notes.get(number)
        instance = getattr(row_result, "instance", None)
        if instance is not None:
            entry["label"] = instance.name or instance.local_id or ""
            if instance.pk and getattr(instance, "uuid", None):
                entry["portal_id"] = instance.uuid
                if not (dry_run and row_result.import_type == "new"):
                    try:
                        entry["url"] = instance.get_absolute_url()
                    except Exception:  # noqa: BLE001
                        entry["url"] = ""
        if not entry["label"]:
            entry["label"] = values.get(next((h for h, c in job.column_map.items() if c == "name"), ""), "") or ""
        kind = row_result.import_type
        if kind == "invalid":
            for attribute, messages in row_result.validation_error.message_dict.items():
                column = attribute_to_column.get(attribute, attribute)
                if column == "__all__":
                    column = ""
                for message in messages:
                    entry["problems"].append({"column": column, "message": friendly(message, None)})
        elif kind == "error":
            for error in errors_by_row.get(number, row_result.errors):
                exc = getattr(error, "error", error)
                if isinstance(exc, RowProblem):
                    entry["problems"].append({"column": exc.column, "message": exc.message})
                else:
                    entry["problems"].append({"column": "", "message": _("This row could not be read: %(e)s") % {"e": exc}})
        if index in duplicates:
            entry["problems"].append(duplicates[index])
        if entry["problems"]:
            entry["outcome"] = "problem"
        elif kind == "new":
            entry["outcome"] = "new"
            entry["changes"] = []
        elif kind == "update":
            entry["outcome"] = "update"
            entry["changes"] = note if isinstance(note, list) else []
        elif kind == "skip":
            if isinstance(note, str):
                entry["outcome"] = "skipped"
                entry["note"] = note
            else:
                entry["outcome"] = "unchanged"
        summary[entry["outcome"]] += 1
        if not dry_run and instance is not None and instance.pk:
            if entry["outcome"] == "new":
                undo["created"].append(instance.pk)
            elif entry["outcome"] == "update":
                original = getattr(row_result, "original", None)
                if original is not None:
                    undo["updated"][str(instance.pk)] = snapshot(schema, original, entry["changes"])
        entries.append(entry)
    return summary, entries, undo, result


def snapshot(schema, original, changes):
    """The stored values an undo puts back, for the attributes that changed."""
    out = {}
    for change in changes:
        column = schema.get(change["column"])
        if column is None:
            continue
        if column.kind in ("latitude", "longitude"):
            out["location"] = original.location.wkt if original.location else None
            continue
        field = column.model_field or original._meta.get_field(column.attribute)
        out[field.attname] = jsonable(getattr(original, field.attname))
    return out


def jsonable(value):
    import datetime as dt
    from decimal import Decimal

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (dt.date, dt.datetime, dt.time)):
        return value.isoformat()
    if hasattr(value, "magnitude"):
        return str(value.magnitude)
    return str(value)


def check(job: ImportJob):
    try:
        summary, entries, _undo, _result = run(job, dry_run=True)
    except FileProblem as e:
        job.status = ImportJob.Status.FAILED
        job.error = str(e)
        job.save()
        return
    except Exception as e:  # noqa: BLE001
        job.status = ImportJob.Status.FAILED
        job.error = _("The file could not be checked: %(e)s") % {"e": e}
        job.save()
        raise
    job.summary = summary
    job.rows = entries
    job.checked_at = timezone.now()
    job.status = ImportJob.Status.PROBLEMS if summary["problem"] else ImportJob.Status.CHECKED
    job.save()


def perform(job: ImportJob, user):
    summary, entries, undo, result = run(job, dry_run=False)
    if summary["problem"]:
        job.summary = summary
        job.rows = entries
        job.status = ImportJob.Status.PROBLEMS
        job.error = _("Something changed since the check, and some rows can no longer be imported. Nothing was written.")
        job.save()
        return
    job.summary = summary
    job.rows = entries
    job.undo = undo
    job.imported_at = timezone.now()
    job.imported_by = user
    job.status = ImportJob.Status.IMPORTED
    job.error = ""
    job.save()


# Undo -----------------------------------------------------------------------------------------


def undo_conflicts(job: ImportJob) -> list[dict]:
    """Records the import touched that have changed since, which stop an undo."""
    from fairdm.core.measurement.models import Measurement

    model = job.model
    conflicts = []
    ids = list(job.undo.get("created", [])) + [int(k) for k in job.undo.get("updated", {})]
    stamp = job.imported_at
    for obj in model.objects.filter(pk__in=ids):
        modified = getattr(obj, "modified", None)
        if modified and stamp and modified > stamp:
            conflicts.append({"label": obj.name, "url": obj.get_absolute_url(), "reason": _("changed since the import")})
    created = job.undo.get("created", [])
    if created and model._meta.get_field("dataset") and hasattr(model, "type_of") and model.type_of.__name__ == "Sample":
        used = Measurement.objects.filter(sample_id__in=created).values_list("sample_id", flat=True).distinct()
        for obj in model.objects.filter(pk__in=list(used)):
            conflicts.append({"label": obj.name, "url": obj.get_absolute_url(), "reason": _("has measurements recorded on it")})
    return conflicts


def undo(job: ImportJob, user):
    model = job.model
    with transaction.atomic():
        for obj in model.objects.filter(pk__in=job.undo.get("created", [])):
            obj.delete()
        for pk, values in job.undo.get("updated", {}).items():
            obj = model.objects.filter(pk=int(pk)).first()
            if obj is None:
                continue
            for attname, value in values.items():
                if attname == "location":
                    from django.contrib.gis.geos import GEOSGeometry

                    obj.location = GEOSGeometry(value, srid=4326) if value else None
                    continue
                field = next(f for f in model._meta.concrete_fields if f.attname == attname)
                setattr(obj, attname, None if value is None else field.to_python(value))
            obj.save()
        job.status = ImportJob.Status.UNDONE
        job.undone_at = timezone.now()
        job.undone_by = user
        job.save()
