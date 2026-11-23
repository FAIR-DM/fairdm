"""The import pages of a dataset.

``/datasets/<uuid>/import/<type>/`` takes a file, and
``/imports/<job>/`` follows one file from its column matches through the check to the import
and, if it comes to that, its undo. ``/imports/`` lists every import into the dataset.
"""

from __future__ import annotations

from django.contrib import messages
from django.db.models import Count
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l

from fairdm import plugins
from fairdm.contrib.plugins import Plugin, reverse
from fairdm.contrib.plugins.access import has_perm
from fairdm.contrib.plugins.mixins import PrivateRecordNotFoundMixin
from fairdm.core.dataset.models import Dataset
from fairdm.views import FairDMTemplateView

from . import engine, exports, tasks
from .models import ImportJob
from .definitions import definitions, get_definition

FORMAT_NAMES = {
    "csv": "CSV",
    "xlsx": "Excel (.xlsx)",
    "ods": "OpenDocument (.ods)",
    "tsv": "TSV",
    "json": "JSON",
}

STEPS = [
    ("file", _l("Choose a file")),
    ("columns", _l("Match columns")),
    ("check", _l("Check")),
    ("import", _l("Import")),
]


def can_import(request, dataset) -> bool:
    if dataset is None or not request.user.is_authenticated:
        return False
    return has_perm(request, "dataset.import_data", dataset)


def records_tab_url(dataset, definition):
    name = "measurements" if definition.kind == "measurement" else "samples"
    return reverse(dataset, name, type=definition.model._meta.model_name)


def count_in(dataset, model):
    return model.objects.filter(dataset=dataset).count()


def import_chooser(dataset, kind=None):
    """The types a dialog offers to import into ``dataset``: one kind, or samples and measurements.

    Returns the dialog's id and title, and one group per kind, each with its types: name,
    column count, the columns a new record needs, how many the dataset holds and the import page.
    """
    titles = {"sample": _("Samples"), "measurement": _("Measurements")}
    groups = []
    for key in [kind] if kind else ["sample", "measurement"]:
        entries = []
        for definition in definitions(key):
            schema = definition.columns()
            entries.append(
                {
                    "name": schema.name,
                    "count": count_in(dataset, definition.model),
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
    return {"id": f"tx-import-{kind or 'all'}", "title": title, "groups": groups}


class ImportPage(PrivateRecordNotFoundMixin, Plugin, FairDMTemplateView):
    """Shared by every import page: the permission, the step bar and the trail."""

    check = staticmethod(can_import)
    step = None

    def handle_no_permission(self):
        raise Http404(_("No import page here."))

    @property
    def dataset(self):
        return self.base_object

    def extra_crumbs(self):
        return []

    def get_breadcrumbs(self):
        trail = super().get_breadcrumbs()
        home = self.dataset.get_absolute_url()
        at = next((i for i, c in enumerate(trail) if c.get("href") == home), len(trail) - 1)
        head = trail[: at + 1]
        head.extend(self.extra_crumbs())
        head.append({"text": str(self.get_page_title())})
        return head

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dataset"] = self.dataset
        context["steps"] = STEPS
        context["step"] = self.step
        step_keys = [k for k, _label in STEPS]
        context["step_index"] = step_keys.index(self.step) if self.step in step_keys else -1
        context["imports_url"] = reverse(self.dataset, "imports")
        return context


@plugins.register(Dataset, menu=False)
class ImportStart(ImportPage):
    """Take a file for one type: what it needs, the templates, and the upload."""

    url_path = "import/<slug:type>"
    name = "import"
    template_name = "tabular/start.html"
    step = "file"

    def dispatch(self, request, *args, **kwargs):
        self.definition = get_definition(kwargs.get("type"))
        if self.definition is None:
            raise Http404(_("The portal has no record type of that name."))
        self.schema = self.definition.columns()
        return super().dispatch(request, *args, **kwargs)

    def get_page_title(self):
        return _("Import %(type)s") % {"type": self.schema.name.lower()}

    def get_page_lead(self):
        return _("into %(dataset)s") % {"dataset": self.dataset}

    def post(self, request, *args, **kwargs):
        uploaded = request.FILES.get("file")
        mode = request.POST.get("mode", ImportJob.Mode.BOTH)
        empty = request.POST.get("empty", ImportJob.Empty.KEEP)
        if mode not in ImportJob.Mode.values:
            mode = ImportJob.Mode.BOTH
        if empty not in ImportJob.Empty.values:
            empty = ImportJob.Empty.KEEP
        if not uploaded:
            return self.render_to_response(self.get_context_data(upload_error=_("Choose a file to import."), mode=mode, empty=empty))
        try:
            job = engine.start_job(self.dataset, self.definition, uploaded, request.user, mode, empty)
        except engine.FileProblem as e:
            return self.render_to_response(self.get_context_data(upload_error=str(e), mode=mode, empty=empty))
        unmatched = [h for h, c in job.column_map.items() if not c]
        if unmatched or engine.mapping_problems(job, self.schema) or engine.mapping_warnings(job):
            return redirect(reverse(self.dataset, "imports-columns", job=job.pk))
        job.status = ImportJob.Status.CHECKING
        job.save()
        tasks.start(tasks.check_job, job.pk)
        return redirect(job.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        schema = self.schema
        context["schema"] = schema
        context["count"] = count_in(self.dataset, self.definition.model)
        context["records_url"] = records_tab_url(self.dataset, self.definition)
        base = reverse(self.dataset, "import", type=self.definition.name)
        context["template_urls"] = [
            (_("Excel template, with the column guide"), f"{base}template.xlsx/", "xlsx"),
            (_("CSV template"), f"{base}template.csv/", "csv"),
        ]
        context["schema_url"] = f"{base}schema.json/"
        context["current_urls"] = [
            ("Excel", f"{context['records_url']}?export=xlsx&scope=all"),
            ("CSV", f"{context['records_url']}?export=csv&scope=all"),
        ]
        context["modes"] = ImportJob.Mode.choices
        context["mode"] = kwargs.get("mode", ImportJob.Mode.BOTH)
        context["empty"] = kwargs.get("empty", ImportJob.Empty.KEEP)
        context["upload_error"] = kwargs.get("upload_error")
        context["formats"] = [FORMAT_NAMES[f] for f in self.definition.formats if f in FORMAT_NAMES]
        context["recent"] = self.dataset.import_jobs.filter(
            definition_name=self.definition.name
        ).select_related("created_by")[:5]
        return context


class ImportTemplate(ImportPage):
    url_path = "template.<str:fmt>"
    name = "template"

    def get(self, request, *args, **kwargs):
        definition = get_definition(kwargs["type"])
        if definition is None or kwargs["fmt"] not in definition.formats:
            raise Http404
        return exports.template_response(definition.columns(), kwargs["fmt"])


class ImportSchema(ImportPage):
    url_path = "schema.json"
    name = "schema"

    def get(self, request, *args, **kwargs):
        definition = get_definition(kwargs["type"])
        if definition is None:
            raise Http404
        return exports.schema_response(definition.columns())


ImportStart.extra_views = [ImportTemplate, ImportSchema]


@plugins.register(Dataset, menu=False)
class DatasetImports(ImportPage):
    """Every import into the dataset, newest first."""

    url_path = "imports"
    name = "imports"
    template_name = "tabular/history.html"
    page_title = _l("Past imports")

    def get_page_lead(self):
        return _("Every file imported into %(dataset)s, and what each one did.") % {"dataset": self.dataset}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["jobs"] = self.dataset.import_jobs.select_related("created_by", "imported_by")
        context["import_chooser"] = import_chooser(self.dataset)
        return context


class JobPage(ImportPage):
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @property
    def job(self):
        if not hasattr(self, "_job"):
            dataset = self.dataset
            self._job = ImportJob.objects.filter(dataset=dataset, pk=self.kwargs["job"]).first()
            if self._job is None:
                raise Http404(_("No such import."))
        return self._job

    def extra_crumbs(self):
        job = self.job
        return [
            {"text": capfirst(job.type_name), "href": reverse(self.dataset, "import", type=job.definition_name)},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.job
        schema = job.definition.columns()
        context["job"] = job
        context["schema"] = schema
        context["start_url"] = reverse(self.dataset, "import", type=job.definition_name)
        context["columns_url"] = reverse(self.dataset, "imports-columns", job=job.pk)
        context["records_url"] = records_tab_url(self.dataset, job.definition)
        return context


class JobColumns(JobPage):
    """Match the file's columns to the type's columns."""

    url_path = "<int:job>/columns"
    name = "columns"
    template_name = "tabular/columns.html"
    step = "columns"

    def get_page_title(self):
        return _("Match the columns of %(file)s") % {"file": self.job.filename}

    def get_page_lead(self):
        return _("Each column of your file fills one field of a %(type)s, or is left out.") % {
            "type": self.job.model._meta.verbose_name
        }

    def post(self, request, *args, **kwargs):
        job = self.job
        if job.status not in (ImportJob.Status.MATCHING, ImportJob.Status.CHECKED, ImportJob.Status.PROBLEMS, ImportJob.Status.NOTHING):
            return redirect(job.get_absolute_url())
        schema = job.definition.columns()
        valid = {c.name for c in schema.importable}
        chosen = {}
        used = {}
        for index, heading in enumerate(job.headers):
            value = request.POST.get(f"col-{index}", "")
            if value and value not in valid:
                value = ""
            chosen[heading] = value
            if value:
                used.setdefault(value, []).append(heading)
        mode = request.POST.get("mode", job.mode)
        empty = request.POST.get("empty", job.empty_cells)
        job.mode = mode if mode in ImportJob.Mode.values else job.mode
        job.empty_cells = empty if empty in ImportJob.Empty.values else job.empty_cells
        job.column_map = chosen
        clashes = {k: v for k, v in used.items() if len(v) > 1}
        if clashes:
            job.save()
            column, headings = next(iter(clashes.items()))
            return self.render_to_response(
                self.get_context_data(
                    clash=_("“%(a)s” and “%(b)s” both fill %(col)s. Choose one.")
                    % {"a": headings[0], "b": headings[1], "col": schema.get(column).label}
                )
            )
        problems = engine.mapping_problems(job, schema)
        if problems:
            job.save()
            return self.render_to_response(self.get_context_data())
        job.status = ImportJob.Status.CHECKING
        job.summary, job.rows = {}, []
        job.save()
        tasks.start(tasks.check_job, job.pk)
        return redirect(job.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.job
        schema = context["schema"]
        rows = []
        for index, heading in enumerate(job.headers):
            target = job.column_map.get(heading, "")
            auto = schema.match(heading)
            rows.append(
                {
                    "index": index,
                    "heading": heading or _("(no heading)"),
                    "values": job.samples.get(heading, []),
                    "target": target,
                    "auto": bool(auto and auto.name == target),
                }
            )
        mapped = {v for v in job.column_map.values() if v}
        context["rows"] = rows
        context["options"] = schema.importable
        context["unfilled"] = [c for c in schema.importable if c.name not in mapped]
        context["problems"] = engine.mapping_problems(job, schema)
        context["warnings"] = engine.mapping_warnings(job)
        context["clash"] = kwargs.get("clash")
        context["matched"] = len(mapped)
        context["modes"] = ImportJob.Mode.choices
        return context


class JobDetail(JobPage):
    """One import: the check while it runs, its outcome row by row, the import, and undo."""

    url_path = "<int:job>"
    name = "job"
    template_name = "tabular/job.html"
    per_page = 100

    @property
    def step(self):
        status = self.job.status
        if status in (ImportJob.Status.IMPORTING, ImportJob.Status.IMPORTED, ImportJob.Status.UNDONE):
            return "import"
        return "check"

    def get_page_title(self):
        job = self.job
        titles = {
            ImportJob.Status.CHECKING: _("Checking %(file)s"),
            ImportJob.Status.CHECKED: _("%(file)s is ready to import"),
            ImportJob.Status.NOTHING: _("%(file)s matches what is stored"),
            ImportJob.Status.PROBLEMS: _("%(file)s needs changes"),
            ImportJob.Status.IMPORTING: _("Importing %(file)s"),
            ImportJob.Status.IMPORTED: _("%(file)s was imported"),
            ImportJob.Status.UNDONE: _("%(file)s was imported, then undone"),
            ImportJob.Status.FAILED: _("%(file)s could not be read"),
            ImportJob.Status.DISCARDED: _("%(file)s was not imported"),
            ImportJob.Status.MATCHING: _("%(file)s: columns to match"),
        }
        return titles.get(job.status, "%(file)s") % {"file": job.filename}

    def get_page_lead(self):
        job = self.job
        return _("%(n)s rows of %(type)s for %(dataset)s") % {
            "n": job.row_count,
            "type": job.type_name,
            "dataset": self.dataset,
        }

    def get(self, request, *args, **kwargs):
        job = self.job
        if job.status == ImportJob.Status.MATCHING:
            return redirect(reverse(self.dataset, "imports-columns", job=job.pk))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        job = self.job
        action = request.POST.get("action")
        if action == "import" and job.status == ImportJob.Status.CHECKED and job.writes:
            job.status = ImportJob.Status.IMPORTING
            job.save()
            tasks.start(tasks.import_job, job.pk, request.user.pk)
        elif action == "discard" and job.status in (ImportJob.Status.CHECKED, ImportJob.Status.PROBLEMS, ImportJob.Status.MATCHING):
            job.status = ImportJob.Status.DISCARDED
            job.save()
            messages.info(request, _("Nothing from %(file)s was imported.") % {"file": job.filename})
            return redirect(reverse(self.dataset, "import", type=job.definition_name))
        elif action == "recheck" and job.status in (ImportJob.Status.CHECKED, ImportJob.Status.PROBLEMS, ImportJob.Status.NOTHING):
            job.status = ImportJob.Status.CHECKING
            job.save()
            tasks.start(tasks.check_job, job.pk)
        elif action == "undo" and job.status == ImportJob.Status.IMPORTED:
            conflicts = engine.undo_conflicts(job)
            if conflicts:
                messages.error(request, _("This import can no longer be undone. Some of its records have changed since."))
            else:
                engine.undo(job, request.user)
                messages.success(request, _("The import of %(file)s was undone.") % {"file": job.filename})
        return redirect(job.get_absolute_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.job
        show = self.request.GET.get("show", "")
        order = ["problem", "new", "update", "unchanged", "skipped"]
        rows = job.rows
        if show in order:
            rows = [r for r in rows if r["outcome"] == show]
        elif job.summary.get("problem"):
            show = "problem"
            rows = [r for r in rows if r["outcome"] == "problem"]
        try:
            page = max(1, int(self.request.GET.get("page", 1)))
        except ValueError:
            page = 1
        start = (page - 1) * self.per_page
        context["show"] = show
        context["page_rows"] = rows[start : start + self.per_page]
        context["row_page"] = page
        context["has_next"] = start + self.per_page < len(rows)
        context["shown_total"] = len(rows)
        labels = {
            "problem": _("Need changes"),
            "new": _("New"),
            "update": _("Updated"),
            "unchanged": _("Unchanged"),
            "skipped": _("Skipped"),
        }
        if job.status in (ImportJob.Status.IMPORTED, ImportJob.Status.UNDONE):
            labels["new"] = _("Added")
        context["tiles"] = [
            {"key": key, "label": labels[key], "count": job.summary.get(key, 0)}
            for key in order
            if job.summary.get(key, 0) or key in ("new", "update")
        ]
        context["column_labels"] = {c.name: str(c.label) for c in context["schema"].columns}
        context["column_labels"][""] = ""
        context["column_map"] = job.column_map
        context["mapped_headings"] = [h for h in job.headers if job.column_map.get(h)]
        context["key_headings"] = [
            h for h in job.headers if job.column_map.get(h) in ("name", "local_id", "sample")
        ] or context["mapped_headings"][:2]
        context["progress"] = engine.progress(job)
        context["percent"] = int(100 * context["progress"] / job.row_count) if job.row_count else 0
        context["status_url"] = reverse(self.dataset, "imports-status", job=job.pk)
        context["problems_url"] = reverse(self.dataset, "imports-problems", job=job.pk)
        if job.status == ImportJob.Status.IMPORTED:
            context["conflicts"] = engine.undo_conflicts(job)
        context["mode_label"] = ImportJob.Mode(job.mode).label
        context["empty_label"] = ImportJob.Empty(job.empty_cells).label
        context["nothing_to_write"] = job.status == ImportJob.Status.NOTHING
        return context


class JobStatus(JobPage):
    """The progress bar, asked for every second while the job runs."""

    url_path = "<int:job>/status"
    name = "status"
    template_name = "tabular/partials/progress.html"

    def get(self, request, *args, **kwargs):
        job = self.job
        job.refresh_from_db()
        if not job.is_running:
            response = HttpResponse("")
            response["HX-Refresh"] = "true"
            return response
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["progress"] = engine.progress(self.job)
        context["percent"] = int(100 * context["progress"] / self.job.row_count) if self.job.row_count else 0
        context["status_url"] = reverse(self.dataset, "imports-status", job=self.job.pk)
        return context


class JobProblems(JobPage):
    url_path = "<int:job>/problems.xlsx"
    name = "problems"

    def get(self, request, *args, **kwargs):
        return exports.problems_response(self.job)


DatasetImports.extra_views = [JobColumns, JobStatus, JobProblems, JobDetail]
