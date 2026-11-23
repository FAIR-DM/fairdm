"""Export and Import on every records table.

Added to the portal's listings and to the Samples and Measurements tabs. ``?export=<format>``
downloads the rows the filters leave, or every row the viewer may see with ``&scope=all``.
"""

from __future__ import annotations

from urllib.parse import urlencode

from django.http import Http404
from django.utils import timezone
from django.utils.translation import gettext as _

from fairdm.contrib.plugins import reverse

from . import exports
from .definitions import definition_for_model

FORMAT_LABELS = [
    ("csv", "CSV", _("Opens anywhere")),
    ("xlsx", "Excel", _("With the column guide inside")),
    ("ods", "OpenDocument", _("LibreOffice, Numbers")),
    ("tsv", "TSV", _("Tab-separated text")),
    ("json", "JSON", _("For scripts")),
]


class RecordTransferMixin:
    """Answer ``?export=`` with a file, and give the template the Import and Export menus."""

    def transfer_definition(self):
        """The import definition of the type this table lists, or None when it lists none."""
        if getattr(self, "chosen", "unset") is None:
            return None
        model = getattr(self, "model", None)
        return definition_for_model(model) if model is not None else None

    def get(self, request, *args, **kwargs):
        fmt = request.GET.get("export")
        if not fmt:
            return super().get(request, *args, **kwargs)
        definition = self.transfer_definition()
        if definition is None or fmt not in definition.formats:
            raise Http404(_("Nothing to export here."))
        schema = definition.columns()
        if request.GET.get("scope") == "all":
            queryset = self.get_queryset()
        else:
            filterset = self.get_filterset()
            queryset = filterset.qs if filterset is not None else self.get_queryset()
        queryset = definition.export_rows(queryset)
        holder = getattr(self, "base_object", None)
        stem = f"{holder} {schema.name}" if holder is not None else schema.name
        stem = f"{stem} {timezone.localdate().isoformat()}"
        return exports.export_response(schema, queryset, fmt, stem)

    def transfer_urls(self, scope, definition):
        params = self.request.GET.copy()
        for key in ("export", "scope", "page"):
            params.pop(key, None)
        out = []
        for fmt, label, hint in FORMAT_LABELS:
            if fmt not in definition.formats:
                continue
            if scope == "filtered":
                query = params.copy()
                query["export"] = fmt
                encoded = query.urlencode()
            else:
                encoded = urlencode({"export": fmt, "scope": "all"})
            out.append({"fmt": fmt, "label": label, "hint": hint, "url": f"?{encoded}"})
        return out

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        definition = self.transfer_definition()
        if definition is None:
            context["transfer"] = None
            return context
        refinements = context.get("refinements") or []
        shown = context.get("result_count")
        context["transfer"] = {
            "filtered": bool(refinements),
            "shown": shown,
            "shown_urls": self.transfer_urls("filtered", definition),
            "all_urls": self.transfer_urls("all", definition),
            "import_url": None,
            "import_chooser": None,
            "imports_url": None,
            "type_name": str(definition.model._meta.verbose_name_plural),
        }
        holder = getattr(self, "base_object", None)
        if holder is not None and getattr(self, "holder", None) == "dataset":
            from .plugins import can_import, import_chooser

            if can_import(self.request, holder):
                # A table of one type imports that type. A tab that hasn't been given a type
                # offers every type of its kind.
                if self.kwargs.get("type"):
                    context["transfer"]["import_url"] = reverse(holder, "import", type=definition.name)
                else:
                    context["transfer"]["import_chooser"] = import_chooser(holder, definition.kind)
                context["transfer"]["imports_url"] = reverse(holder, "imports")
        return context
