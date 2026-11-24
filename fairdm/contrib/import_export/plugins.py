"""The import pages of a dataset.

``import/<type>/`` takes a file. ``imports/<job>/`` follows one file from its column
matches through the check to the import, and ``imports/`` lists every import into the
dataset. Every page answers a person who may not import into the dataset with a 404.
"""

import csv
import io

from django.contrib import messages
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse as django_reverse
from django.utils.http import content_disposition_header
from django.utils.text import capfirst, slugify
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from fairdm import plugins
from fairdm.contrib.plugins import reverse
from fairdm.contrib.plugins.access import has_perm
from fairdm.contrib.plugins.mixins import PrivateRecordNotFoundMixin
from fairdm.core.dataset.models import Dataset
from fairdm.registry import registry
from fairdm.views import FairDMTemplateView

from . import tasks
from .definitions import get_definition, import_definitions
from .exports import TableExport, format_for
from .forms import ImportOptionsForm, UploadForm
from .matching import HeadingMatcher
from .models import ImportJob, ImportRow
from .reader import FileProblem, FileReader
from .runner import ImportRun
from .undo import ImportUndo

STEPS = [
    ("file", _l("Choose a file")),
    ("columns", _l("Match columns")),
    ("check", _l("Check")),
    ("import", _l("Import")),
]


def can_import(request, dataset):
    """Say whether the request's user may import into a dataset.

    Args:
        request: The current request.
        dataset: The dataset, or None when no record has been resolved.

    Returns:
        True when the user holds the dataset's ``import_data`` permission.
    """
    if dataset is None or not request.user.is_authenticated:
        return False
    return has_perm(request, "dataset.import_data", dataset)


def import_chooser(dataset, kind=None):
    """Build the data of the dialog that lists the types a file can be imported as.

    Args:
        dataset: The dataset the file is imported into.
        kind: ``sample`` or ``measurement`` to offer one kind, or None to offer both.

    Returns:
        A dict with the dialog's ``id`` and ``title`` and its ``groups``, one for each
        kind with its ``kind``, ``title`` and ``entries``. Each entry holds the type's
        ``name``, ``count`` of records in the dataset, import page ``url``, the
        labels of the columns a new record ``required`` and the number of
        ``columns`` a file may carry besides the portal ID.
    """
    titles = {"sample": _("Samples"), "measurement": _("Measurements")}
    groups = []
    for key in [kind] if kind else ["sample", "measurement"]:
        entries = []
        for definition in import_definitions.all(key):
            schema = definition.table_schema()
            entries.append(
                {
                    "name": schema.name,
                    "count": definition.model.objects.filter(dataset=dataset).count(),
                    "url": reverse(dataset, "import", type=definition.name),
                    "required": [str(c.label) for c in schema.required],
                    "columns": len(schema.importable) - 1,
                }
            )
        groups.append({"kind": key, "title": titles[key], "entries": entries})
    title = {
        None: _("Import"),
        "sample": _("Import samples"),
        "measurement": _("Import measurements"),
    }[kind]
    return {"id": f"ie-import-{kind or 'all'}", "title": title, "groups": groups}


def records_url(dataset, definition):
    """Give the address of a dataset's records tab for a type.

    Args:
        dataset: The dataset.
        definition: The import definition of the type.

    Returns:
        The address.
    """
    return reverse(
        dataset,
        f"{definition.kind}s",
        type=registry.get_for_model(definition.model).get_slug(),
    )


class ImportPage(PrivateRecordNotFoundMixin, plugins.Plugin, FairDMTemplateView):
    """Shared by every import page: the permission, the step bar and the trail.

    Attributes:
        step: The key of the current step of ``STEPS``, or None for no step.
    """

    check = staticmethod(can_import)
    step = None

    def handle_no_permission(self):
        """Answer a person who may not import as if there were no such page.

        Raises:
            Http404: Always.
        """
        raise Http404(_("No import page here."))

    @property
    def dataset(self):
        """The dataset the page is under.

        Returns:
            The dataset.
        """
        return self.base_object

    def extra_crumbs(self):
        """List the trail entries between the dataset and the page itself.

        Returns:
            Breadcrumb dicts.
        """
        return []

    def get_breadcrumbs(self):
        """Build the trail from the dataset's records to this page.

        Returns:
            Breadcrumb dicts.
        """
        trail = super().get_breadcrumbs()
        trail.extend(self.extra_crumbs())
        trail.append({"text": str(self.get_page_title())})
        return trail

    def get_context_data(self, **kwargs):
        """Add the dataset, the steps and the address of the list of imports."""
        context = super().get_context_data(**kwargs)
        keys = [step[0] for step in STEPS]
        context["dataset"] = self.dataset
        context["steps"] = STEPS
        context["step_index"] = keys.index(self.step) if self.step in keys else -1
        context["imports_url"] = reverse(self.dataset, "imports")
        return context


class DefinitionMixin:
    """Reads the type named in the address and answers 404 when the portal has none.

    Attributes:
        definition: The import definition of the type.
    """

    def dispatch(self, request, *args, **kwargs):
        """Find the type's definition before the page is built."""
        self.definition = get_definition(kwargs.get("type"))
        if self.definition is None:
            raise Http404(_("The portal has no record type of that name."))
        return super().dispatch(request, *args, **kwargs)


@plugins.register(Dataset, menu=False)
class ImportStart(DefinitionMixin, ImportPage):
    """Take a file for one type: what it needs, the templates and the upload."""

    url_path = "import/<slug:type>"
    name = "import"
    template_name = "import_export/import_start.html"
    step = "file"

    def get_page_title(self):
        """Name the type the file is imported as."""
        return _("Import %(type)s") % {
            "type": self.definition.table_schema().name.lower()
        }

    def get_page_lead(self):
        """Name the dataset the file is imported into."""
        return _("into %(dataset)s") % {"dataset": self.dataset}

    def post(self, request, *args, **kwargs):
        """Read the uploaded file and, when it can be read, start its job.

        A file that cannot be read is shown on this page and saves no job. A job whose
        headings all match goes straight to the check and any other goes to matching.

        Args:
            request: The request.
            *args: Unused.
            **kwargs: The address's arguments.

        Returns:
            A redirect to the job or its matching page, or this page with the problem.
        """
        mode, empty = ImportOptionsForm(request.POST).chosen(
            ImportJob.Mode.BOTH, ImportJob.Empty.KEEP
        )
        try:
            job = self.new_job(UploadForm(request.POST, request.FILES), mode, empty)
        except FileProblem as problem:
            return self.render_to_response(
                self.get_context_data(upload_error=str(problem), mode=mode, empty=empty)
            )
        if job.status == ImportJob.Status.MATCHING:
            return redirect(reverse(self.dataset, "imports-columns", job=job.pk))
        tasks.start(tasks.check_job, job.pk)
        return redirect(job.get_absolute_url())

    def new_job(self, form, mode, empty):
        """Read the uploaded file and save the job that holds it.

        Args:
            form: The upload form, bound to the request.
            mode: What the file may do to the dataset's records.
            empty: What an empty cell means.

        Returns:
            The saved job, ``checking`` when every column is matched and ``matching``
            when the person has to look first.

        Raises:
            FileProblem: The file cannot be imported as this type.
        """
        if not form.is_valid():
            raise FileProblem(form.errors["file"][0], "format")
        upload = form.cleaned_data["file"]
        name, raw = upload.name, upload.read()
        fmt = FileReader.file_format(name)
        if fmt not in self.definition.formats:
            raise FileProblem(
                _("This portal does not read %(fmt)s files.") % {"fmt": fmt}, "format"
            )
        headings, rows = FileReader.parse(raw, fmt)[:2]
        named = [heading for heading in headings if heading]
        if len(set(named)) != len(named):
            raise FileProblem(
                _(
                    "Two columns have the same heading. "
                    "Give each column its own heading."
                ),
                "unreadable",
            )
        matcher = HeadingMatcher(self.definition.table_schema())
        job = ImportJob(
            dataset=self.dataset,
            definition_name=self.definition.name,
            created_by=self.request.user,
            filename=name[:255],
            file_format=fmt,
            file_size=len(raw),
            mode=mode,
            empty_cells=empty,
            headers=headings,
            samples=self.example_values(headings, rows),
            column_map=matcher.match_columns(headings),
            row_count=len(rows),
        )
        job.status = (
            ImportJob.Status.MATCHING
            if matcher.needs_matching(job)
            else ImportJob.Status.CHECKING
        )
        with transaction.atomic():
            job.file.save(name, ContentFile(raw), save=False)
            job.save()
        return job

    def example_values(self, headings, rows):
        """Take up to four values from each column, to show while matching.

        Args:
            headings: The file's headings.
            rows: The file's rows.

        Returns:
            The values by heading, each cut to 40 characters.
        """
        examples = {}
        for index, heading in enumerate(headings):
            values = []
            for row in rows:
                if not FileReader.blank(row[index]):
                    values.append(str(row[index]).strip()[:40])
                if len(values) == 4:
                    break
            examples[heading] = values
        return examples

    def get_context_data(self, **kwargs):
        """Add the type's guide, the downloads, the options and the recent imports."""
        context = super().get_context_data(**kwargs)
        schema = self.definition.table_schema()
        base = reverse(self.dataset, "import", type=self.definition.name)
        records = records_url(self.dataset, self.definition)
        count = self.definition.model.objects.filter(dataset=self.dataset).count()
        context["schema"] = schema
        context["count"] = count
        context["records_url"] = records
        context["template_links"] = [
            {
                "label": _("Excel template, with the column guide"),
                "url": f"{base}template.xlsx/",
                "icon": "file-earmark-excel",
            },
            {
                "label": _("CSV template"),
                "url": f"{base}template.csv/",
                "icon": "file-earmark-text",
            },
        ]
        context["current_links"] = [
            {
                "label": label,
                "url": f"{records}?export={key}&scope=all",
                "icon": "arrow-repeat",
            }
            for label, key in (("Excel", "xlsx"), ("CSV", "csv"))
        ]
        context["schema_url"] = django_reverse(
            "table_schema", kwargs={"name": self.definition.name}
        )
        context["options_form"] = ImportOptionsForm(
            initial={
                "mode": kwargs.get("mode", ImportJob.Mode.BOTH),
                "empty": kwargs.get("empty", ImportJob.Empty.KEEP),
            }
        )
        context["upload_error"] = kwargs.get("upload_error")
        context["formats"] = [fmt.upper() for fmt in self.definition.formats]
        context["recent"] = self.dataset.import_jobs.filter(
            definition_name=self.definition.name
        ).select_related("created_by")[:5]
        return context


class ImportTemplate(DefinitionMixin, ImportPage):
    """Download a file with a type's headings and nothing else."""

    url_path = "template.<str:fmt>"
    name = "template"

    def get(self, request, *args, **kwargs):
        """Answer with the type's template in one of the formats a template has.

        Args:
            request: The request.
            *args: Unused.
            **kwargs: The address's arguments.

        Returns:
            The file as a download.

        Raises:
            Http404: The format is not one the portal reads or has no template.
        """
        fmt = kwargs["fmt"]
        if fmt not in ("xlsx", "csv") or fmt not in self.definition.formats:
            raise Http404(_("No template in that format."))
        schema = self.definition.table_schema()
        if fmt == "xlsx":
            payload = TableExport(schema).workbook()
        else:
            buffer = io.StringIO(newline="")
            csv.writer(buffer).writerow(schema.headings)
            payload = ("﻿" + buffer.getvalue()).encode("utf-8")
        chosen = format_for(fmt)
        response = HttpResponse(payload, content_type=chosen.content_type)
        filename = f"{slugify(schema.name)}-template.{chosen.extension}"
        response["Content-Disposition"] = content_disposition_header(True, filename)
        return response


ImportStart.extra_views = [ImportTemplate]


@plugins.register(Dataset, menu=False)
class DatasetImports(ImportPage):
    """Every import into the dataset, newest first."""

    url_path = "imports"
    name = "imports"
    template_name = "import_export/import_history.html"

    def get_page_title(self):
        """Name the page."""
        return _("Past imports")

    def get_page_lead(self):
        """Say what the list holds."""
        return _("Every file imported into %(dataset)s, and what each one did.") % {
            "dataset": self.dataset
        }

    def get_context_data(self, **kwargs):
        """Add the dataset's jobs, newest first, and the dialog of types."""
        context = super().get_context_data(**kwargs)
        context["jobs"] = self.dataset.import_jobs.select_related(
            "created_by", "imported_by"
        )
        context["import_chooser"] = import_chooser(self.dataset)
        return context


class JobPage(ImportPage):
    """Shared by the pages of one job, which is read through its dataset only."""

    @property
    def job(self):
        """The job named in the address, found among the dataset's own.

        Returns:
            The job.

        Raises:
            Http404: The dataset has no such job.
        """
        if not hasattr(self, "found"):
            self.found = self.dataset.import_jobs.filter(pk=self.kwargs["job"]).first()
        if self.found is None:
            raise Http404(_("No such import."))
        return self.found

    def extra_crumbs(self):
        """Add the type's import page to the trail."""
        job = self.job
        return [
            {
                "text": capfirst(job.type_name),
                "href": reverse(self.dataset, "import", type=job.definition_name),
            }
        ]

    def get_context_data(self, **kwargs):
        """Add the job, its type's schema and the addresses the pages share."""
        context = super().get_context_data(**kwargs)
        job = self.job
        definition = job.definition
        context["job"] = job
        context["schema"] = definition.table_schema()
        context["start_url"] = reverse(self.dataset, "import", type=job.definition_name)
        context["columns_url"] = reverse(self.dataset, "imports-columns", job=job.pk)
        context["records_url"] = records_url(self.dataset, definition)
        return context

    def progress_of(self):
        """Read how far the job's run has got.

        Returns:
            The number of rows done and the share of the file that is, from 0 to 100.
        """
        job = self.job
        done = ImportRun(job).progress() or 0
        percent = min(100, int(100 * done / job.row_count)) if job.row_count else 0
        return done, percent


class JobColumns(JobPage):
    """Match the file's columns to the type's columns."""

    url_path = "<int:job>/columns"
    name = "columns"
    template_name = "import_export/import_columns.html"
    step = "columns"
    ALLOWED = (
        ImportJob.Status.MATCHING,
        ImportJob.Status.CHECKED,
        ImportJob.Status.PROBLEMS,
        ImportJob.Status.NOTHING,
    )

    def get_page_title(self):
        """Name the file whose columns are matched."""
        return _("Match the columns of %(file)s") % {"file": self.job.filename}

    def get_page_lead(self):
        """Say what matching does."""
        return _(
            "Each column of your file fills one field of a %(type)s, or is left out."
        ) % {"type": self.job.model._meta.verbose_name}

    def post(self, request, *args, **kwargs):
        """Keep the person's matches and start the check when the file can be checked.

        Only a job that has not been imported or set aside is matched. Matches that
        cannot be checked are kept and shown again with what is wrong.

        Args:
            request: The request.
            *args: Unused.
            **kwargs: The address's arguments.

        Returns:
            A redirect to the job, or this page again with the problems.
        """
        job = self.job
        if job.status not in self.ALLOWED:
            return redirect(job.get_absolute_url())
        schema = job.definition.table_schema()
        valid = {column.name for column in schema.importable}
        chosen = {}
        for index, heading in enumerate(job.headers):
            value = request.POST.get(f"col-{index}", "")
            chosen[heading] = value if value in valid else ""
        job.mode, job.empty_cells = ImportOptionsForm(request.POST).chosen(
            job.mode, job.empty_cells
        )
        job.column_map = chosen
        fields = {
            "column_map": chosen,
            "mode": job.mode,
            "empty_cells": job.empty_cells,
        }
        jobs = self.dataset.import_jobs.filter(pk=job.pk, status__in=self.ALLOWED)
        if HeadingMatcher(schema).problems(job):
            jobs.update(**fields)
            return self.render_to_response(self.get_context_data())
        if jobs.update(status=ImportJob.Status.CHECKING, summary={}, **fields):
            tasks.start(tasks.check_job, job.pk)
        return redirect(job.get_absolute_url())

    def get_context_data(self, **kwargs):
        """Add a row for each heading, the unfilled fields and the problems."""
        context = super().get_context_data(**kwargs)
        job = self.job
        schema = context["schema"]
        matcher = HeadingMatcher(schema)
        rows = []
        for index, heading in enumerate(job.headers):
            target = job.column_map.get(heading, "")
            found = matcher.match(heading)
            rows.append(
                {
                    "index": index,
                    "heading": heading or _("(no heading)"),
                    "values": job.samples.get(heading, []),
                    "target": target,
                    "auto": bool(found and found.name == target),
                }
            )
        mapped = {name for name in job.column_map.values() if name}
        context["rows"] = rows
        context["options"] = schema.importable
        context["unfilled"] = [c for c in schema.importable if c.name not in mapped]
        context["problems"] = matcher.problems(job)
        context["warnings"] = matcher.warnings(job)
        context["matched"] = len(mapped)
        context["options_form"] = ImportOptionsForm(
            initial={"mode": job.mode, "empty": job.empty_cells}, brief=True
        )
        return context


class JobDetail(JobPage):
    """One import: the check while it runs, its rows by outcome and the import.

    Attributes:
        per_page: How many rows a page lists.
        ACTIONS: For each action the statuses it may start from and the one it moves to.
    """

    url_path = "<int:job>"
    name = "job"
    template_name = "import_export/import_job.html"
    per_page = 100
    ACTIONS = {
        "import": ((ImportJob.Status.CHECKED,), ImportJob.Status.IMPORTING),
        "recheck": (
            (
                ImportJob.Status.CHECKED,
                ImportJob.Status.PROBLEMS,
                ImportJob.Status.NOTHING,
            ),
            ImportJob.Status.CHECKING,
        ),
        "discard": (
            (
                ImportJob.Status.MATCHING,
                ImportJob.Status.CHECKED,
                ImportJob.Status.PROBLEMS,
            ),
            ImportJob.Status.DISCARDED,
        ),
    }
    TITLES = {
        ImportJob.Status.CHECKING: _l("Checking %(file)s"),
        ImportJob.Status.CHECKED: _l("%(file)s is ready to import"),
        ImportJob.Status.NOTHING: _l("%(file)s matches what is stored"),
        ImportJob.Status.PROBLEMS: _l("%(file)s needs changes"),
        ImportJob.Status.IMPORTING: _l("Importing %(file)s"),
        ImportJob.Status.IMPORTED: _l("%(file)s was imported"),
        ImportJob.Status.UNDONE: _l("%(file)s was imported, then undone"),
        ImportJob.Status.FAILED: _l("%(file)s could not be read"),
        ImportJob.Status.DISCARDED: _l("%(file)s was not imported"),
        ImportJob.Status.MATCHING: _l("%(file)s: columns to match"),
    }

    @property
    def step(self):
        """The step the job is at: the import once it has begun, the check before."""
        if self.job.status in (
            ImportJob.Status.IMPORTING,
            ImportJob.Status.IMPORTED,
            ImportJob.Status.UNDONE,
        ):
            return "import"
        return "check"

    def get_page_title(self):
        """Say where the job stands, naming its file."""
        return self.TITLES[self.job.status] % {"file": self.job.filename}

    def get_page_lead(self):
        """Say how many rows of which type the file holds."""
        job = self.job
        return _("%(n)s rows of %(type)s for %(dataset)s") % {
            "n": job.row_count,
            "type": job.type_name,
            "dataset": self.dataset,
        }

    def get(self, request, *args, **kwargs):
        """Show the job, or send a job still matching to its matching page."""
        job = self.job
        if job.status == ImportJob.Status.MATCHING:
            return redirect(reverse(self.dataset, "imports-columns", job=job.pk))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Move the job on with one conditional update and queue the task it needs.

        An action the job's status does not allow changes nothing, so a second post of
        the same action finds the job already moved and queues no second task.

        Args:
            request: The request.
            *args: Unused.
            **kwargs: The address's arguments.

        Returns:
            A redirect to the job, or to the import page after a discard.
        """
        job = self.job
        action = request.POST.get("action")
        if action == "undo":
            return self.undo(request)
        rule = self.ACTIONS.get(action)
        if rule is None or (action == "import" and not job.writes):
            return redirect(job.get_absolute_url())
        allowed, target = rule
        moved = self.dataset.import_jobs.filter(pk=job.pk, status__in=allowed).update(
            status=target
        )
        if not moved:
            return redirect(job.get_absolute_url())
        if action == "import":
            tasks.start(tasks.import_job, job.pk, request.user.pk)
        elif action == "recheck":
            tasks.start(tasks.check_job, job.pk)
        else:
            ImportRun(job).delete_file()
            messages.info(
                request,
                _("Nothing from %(file)s was imported.") % {"file": job.filename},
            )
            return redirect(reverse(self.dataset, "import", type=job.definition_name))
        return redirect(job.get_absolute_url())

    def undo(self, request):
        """Undo the import, or show the records that stand in the way.

        The dataset is locked and the job's status read again inside the undo, so a
        second post of the action finds the job already undone and changes nothing.

        Args:
            request: The request.

        Returns:
            A redirect to the job once it is undone or when there is nothing to undo,
            otherwise the job's page with the records in the way listed.
        """
        job = self.job
        found = ImportUndo(job).undo(request.user)
        if found is None or not found["entries"]:
            if found is not None:
                messages.success(
                    request,
                    _("%(file)s was undone.") % {"file": job.filename},
                )
            return redirect(job.get_absolute_url())
        self.refusal = found
        return self.get(request)

    def rows_shown(self):
        """Choose the rows the page lists, by the outcome in ``?show=``.

        Returns:
            The outcome shown, empty for every row, and the rows of it.
        """
        job = self.job
        show = self.request.GET.get("show", "")
        if show not in ImportRow.Outcome.values and show != "all":
            show = (
                ImportRow.Outcome.PROBLEM
                if job.summary.get(ImportRow.Outcome.PROBLEM)
                else ""
            )
        rows = job.rows.all()
        if show in ImportRow.Outcome.values:
            rows = rows.filter(outcome=show)
        return show, rows

    def get_context_data(self, **kwargs):
        """Add the page of rows, the outcome tiles, the progress and the file facts."""
        context = super().get_context_data(**kwargs)
        job = self.job
        show, rows = self.rows_shown()
        try:
            page = max(1, int(self.request.GET.get("page", 1)))
        except ValueError:
            page = 1
        start = (page - 1) * self.per_page
        page_rows = list(rows[start : start + self.per_page + 1])
        labels = {
            column.name: str(column.label) for column in context["schema"].columns
        }
        for row in page_rows:
            row.problem_list = [
                {
                    "label": labels.get(p.get("column"), p.get("column", "")),
                    "message": p["message"],
                }
                for p in row.problems
            ]
        context["show"] = show
        context["page_rows"] = page_rows[: self.per_page]
        context["row_page"] = page
        context["has_next"] = len(page_rows) > self.per_page
        context["shown_total"] = rows.count()
        context["tiles"] = self.tiles(job)
        context["mapped_headings"] = [h for h in job.headers if job.column_map.get(h)]
        context["progress"], context["percent"] = self.progress_of()
        context["status_url"] = reverse(self.dataset, "imports-status", job=job.pk)
        context["problems_url"] = reverse(self.dataset, "imports-problems", job=job.pk)
        context["mode_label"] = ImportJob.Mode(job.mode).label
        context["empty_label"] = ImportJob.Empty(job.empty_cells).label
        context["written"] = job.status in (
            ImportJob.Status.IMPORTED,
            ImportJob.Status.UNDONE,
        )
        context["conflicts"] = getattr(self, "refusal", None)
        context["undo_blocked"] = job.status == ImportJob.Status.IMPORTED and bool(
            context["conflicts"] or ImportUndo(job).conflicts(None, limit=1)["entries"]
        )
        return context

    def tiles(self, job):
        """List the outcomes the job's rows fall in, each with its count.

        Args:
            job: The job.

        Returns:
            Dicts with the outcome's ``key``, ``label`` and ``count``. Outcomes with no
            rows are left out, except new and changed rows.
        """
        written = job.status in (ImportJob.Status.IMPORTED, ImportJob.Status.UNDONE)
        labels = {
            ImportRow.Outcome.PROBLEM: _("Need changes"),
            ImportRow.Outcome.NEW: _("Added") if written else _("New"),
            ImportRow.Outcome.UPDATE: _("Updated"),
            ImportRow.Outcome.UNCHANGED: _("Unchanged"),
            ImportRow.Outcome.SKIPPED: _("Skipped"),
        }
        return [
            {"key": key, "label": label, "count": job.summary.get(key, 0)}
            for key, label in labels.items()
            if job.summary.get(key, 0)
            or key in (ImportRow.Outcome.NEW, ImportRow.Outcome.UPDATE)
        ]


class JobStatus(JobPage):
    """The progress component, asked for every second while the job runs."""

    url_path = "<int:job>/status"
    name = "status"

    def get(self, request, *args, **kwargs):
        """Answer the progress, or a refresh of the page once the run is over.

        Args:
            request: The request.
            *args: Unused.
            **kwargs: The address's arguments.

        Returns:
            The progress component, or an empty response with ``HX-Refresh``.
        """
        job = self.job
        job.refresh_from_db()
        if not job.is_running:
            response = HttpResponse("")
            response["HX-Refresh"] = "true"
            return response
        done, percent = self.progress_of()
        return HttpResponse(
            render_to_string(
                "import_export/import_progress.html",
                {
                    "percent": percent,
                    "done": done,
                    "total": job.row_count,
                    "url": reverse(self.dataset, "imports-status", job=job.pk),
                    "importing": job.status == ImportJob.Status.IMPORTING,
                },
                request=request,
            )
        )


class JobProblems(JobPage):
    """The uploaded file back, with each row's problems written beside it."""

    url_path = "<int:job>/problems.xlsx"
    name = "problems"
    CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def get(self, request, *args, **kwargs):
        """Re-read the stored file and write it with a column of problems.

        Every heading, value and message is written as text, so a cell that starts with
        ``=`` is never a formula.

        Args:
            request: The request.
            *args: Unused.
            **kwargs: The address's arguments.

        Returns:
            The workbook as a download.

        Raises:
            Http404: The job has no problems or its file is no longer stored.
        """
        job = self.job
        if job.status != ImportJob.Status.PROBLEMS or not job.file:
            raise Http404(_("There is no file with problems to download."))
        try:
            with job.file.open("rb") as stored:
                headings, rows, lines = FileReader.parse(stored.read(), job.file_format)
        except (FileNotFoundError, FileProblem):
            raise Http404(_("The uploaded file is no longer stored.")) from None
        schema = job.definition.table_schema()
        problems = {
            row.line: row.problems
            for row in job.rows.filter(outcome=ImportRow.Outcome.PROBLEM)
        }
        export = TableExport(schema)
        book = Workbook()
        sheet = book.active
        sheet.title = _("Rows")[:31]
        for index, heading in enumerate(
            [_("Problems"), _("Row in your file"), *headings], 1
        ):
            export.write_text(sheet, 1, index, heading).font = Font(bold=True)
        red = PatternFill("solid", fgColor="F8D7DA")
        column_of = {name: heading for heading, name in job.column_map.items() if name}
        for number, (line, cells) in enumerate(zip(lines, rows, strict=True), start=2):
            found = problems.get(line, [])
            text = "\n".join(self.describe(schema, p) for p in found)
            note = export.write_text(sheet, number, 1, text)
            export.write_text(sheet, number, 2, line)
            for index, cell in enumerate(cells, start=3):
                export.write_text(sheet, number, index, cell)
            if found:
                note.fill = red
            for problem in found:
                heading = column_of.get(problem.get("column"))
                if heading in headings:
                    sheet.cell(
                        row=number, column=3 + headings.index(heading)
                    ).fill = red
        sheet.column_dimensions["A"].width = 60
        sheet.freeze_panes = "C2"
        buffer = io.BytesIO()
        book.save(buffer)
        stem = job.filename.rsplit(".", 1)[0]
        response = HttpResponse(buffer.getvalue(), content_type=self.CONTENT_TYPE)
        response["Content-Disposition"] = content_disposition_header(
            True, f"{slugify(stem) or 'import'}-problems.xlsx"
        )
        return response

    def describe(self, schema, problem):
        """Write one problem as a line, led by the label of its column.

        Args:
            schema: The type's table schema.
            problem: A dict with the problem's ``message`` and, when it has one,
                ``column``.

        Returns:
            The line.
        """
        column = schema.get(problem.get("column", ""))
        if column is None:
            return problem["message"]
        return f"{column.label}: {problem['message']}"


DatasetImports.extra_views = [JobColumns, JobStatus, JobProblems, JobDetail]
