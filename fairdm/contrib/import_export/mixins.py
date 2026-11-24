"""The export a records table answers with."""

from urllib.parse import urlencode

from django.db.models import Exists, OuterRef
from django.http import Http404
from django.utils import timezone

from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample

from .definitions import get_definition
from .exports import EXPORT_FORMATS, TableExport, format_for


class RecordExportMixin:
    """Answers ``?export=<format>`` on a records table with the table's rows as a file.

    Add it first among a table view's bases. A request without ``export`` is left to the
    view. The rows are those the table shows for the request's search and filters, or
    with ``scope=all`` every row the table could list, whatever page the address names.
    """

    def export_definition(self):
        """Find the definition that decides the columns of the file.

        Returns:
            The import definition of the listed type, or None when the view lists no
            type or the type has no definition of its own.
        """
        if getattr(self, "chosen", True) is None:
            return None
        definition = get_definition(self.model._meta.model_name)
        if definition is None or definition.model is not self.model:
            return None
        return definition

    def get(self, request, *args, **kwargs):
        """Write the file when the request asks for one, else list the records.

        Args:
            request: The request.
            *args: Passed to the view.
            **kwargs: Passed to the view.

        Returns:
            The file, or the page.

        Raises:
            Http404: When the request asks for a file the view cannot write: it lists
                no type, or the format is not one of ``EXPORT_FORMATS``.
        """
        if "export" not in request.GET:
            return super().get(request, *args, **kwargs)
        key = request.GET["export"]
        definition = self.export_definition()
        if definition is None or format_for(key) is None:
            raise Http404("No such export.")
        return TableExport(definition.table_schema()).response(
            self.export_queryset(definition), key, self.export_stem()
        )

    def export_queryset(self, definition=None):
        """Return the records a file holds, in primary-key order.

        Args:
            definition: The listed type's definition, found when not given.

        Returns:
            Every record the table could list for ``scope=all``, else those the
            request's search and filters leave. A measurement is annotated with
            whether its sample is open to the viewer, and the cells' relations are
            loaded with the rows.
        """
        definition = definition or self.export_definition()
        queryset = self.get_queryset()
        if self.request.GET.get("scope") != "all":
            filterset = self.get_filterset()
            if filterset is not None:
                queryset = filterset.qs
        queryset = queryset.prefetch_related(None)
        relations = [
            column.attribute
            for column in definition.table_schema().columns
            if column.kind == "concept"
            and column.attribute
            and column.model_field is not None
            and column.model_field.is_relation
        ]
        if issubclass(definition.model, Measurement):
            relations.append("sample")
            if "sample_open" not in queryset.query.annotations:
                queryset = queryset.annotate(
                    sample_open=Exists(
                        Sample.objects.visible_to(self.request.user).filter(
                            pk=OuterRef("sample_id")
                        )
                    )
                )
        return queryset.select_related(*relations)

    def export_stem(self):
        """Name the file: the record whose tab it is, the type and the day.

        Returns:
            The words the file's name is made from, which the response slugifies.
        """
        words = []
        record = getattr(self, "base_object", None)
        if record is not None:
            words.append(str(record))
        words.append(str(self.model_config.get_verbose_name_plural()))
        words.append(timezone.localdate().isoformat())
        return " ".join(words)

    def export_menu(self, context):
        """Describe the menu the page offers.

        Args:
            context: The page's context, which holds the refinements and the count.

        Returns:
            None when the table lists no type or no rows, else a dict of ``filtered``,
            ``shown``, ``type_name`` and ``formats``, each format with its label, hint
            and the addresses of the rows shown and of every row.
        """
        if self.export_definition() is None or not context.get("result_count"):
            return None
        query = self.request.GET.copy()
        for name in ("export", "scope", "page"):
            query.pop(name, None)
        formats = []
        for export_format in EXPORT_FORMATS:
            shown = query.copy()
            shown["export"] = export_format.key
            formats.append(
                {
                    "label": export_format.label,
                    "hint": export_format.hint,
                    "shown_url": f"?{shown.urlencode()}",
                    "all_url": "?"
                    + urlencode({"export": export_format.key, "scope": "all"}),
                }
            )
        return {
            "filtered": bool(context.get("refinements")),
            "shown": context["result_count"],
            "type_name": self.model_config.get_verbose_name_plural(),
            "formats": formats,
        }

    def get_context_data(self, **kwargs):
        """Add ``export_menu``, what the export menu draws.

        Args:
            **kwargs: Passed to the view.

        Returns:
            The context.
        """
        context = super().get_context_data(**kwargs)
        context["export_menu"] = self.export_menu(context)
        return context
