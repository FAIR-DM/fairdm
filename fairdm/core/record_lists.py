"""The list tabs that show a dataset's samples and measurements, and a sample's measurements.

Prototype for specification 023. Everything here is untested and is the plan's to rebuild.
"""

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.http import Http404
from django.urls import path
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from django_tables2 import RequestConfig

from fairdm.contrib.collections.views import DataTableView
from fairdm.contrib.plugins import Plugin, reverse
from fairdm.contrib.plugins.mixins import PrivateRecordNotFoundMixin
from fairdm.registry import registry
from fairdm.views import FairDMTemplateView

HIDDEN_COLUMNS = [
    "polymorphic_ctype",
    "measurement_ptr",
    "sample_ptr",
    "options",
    "image",
    "created",
    "modified",
]


def type_counts(queryset):
    """Count a polymorphic queryset's records per registered type, most numerous first.

    Args:
        queryset: Samples or measurements.

    Returns:
        ``(model class, registry configuration, count)`` tuples.
    """
    rows = (
        queryset.order_by()
        .values("polymorphic_ctype")
        .annotate(count=Count("pk"))
        .order_by("-count")
    )
    entries = []
    for row in rows:
        model = ContentType.objects.get_for_id(row["polymorphic_ctype"]).model_class()
        if model is None or not registry.is_registered(model):
            continue
        entries.append((model, registry.get_for_model(model), row["count"]))
    return entries


class DatasetRecords(PrivateRecordNotFoundMixin, Plugin, DataTableView):
    """List the records of one kind that belong to a dataset, one registered type at a time.

    Attributes:
        base_model: ``Sample`` or ``Measurement``.
        kind_label: The plural name of the kind, used as the page heading.
    """

    base_model = None
    kind_label = ""
    template_name = "record_lists/dataset_records.html"
    paginate_by = 50

    @classmethod
    def get_urls(cls, menu_class=None, model=None):
        """Add the address that names a type beneath the tab's own address."""
        patterns = super().get_urls(menu_class=menu_class, model=model)
        patterns.append(
            path(
                f"{cls.get_url_path()}/<slug:type>/",
                cls.as_view(menu=menu_class, registered_model=model),
                name=f"{cls.get_name()}-type",
            )
        )
        return patterns

    def setup(self, request, *args, **kwargs):
        """Choose the type to show before the table view reads its configuration."""
        self.request, self.args, self.kwargs = request, args, kwargs
        self.type_entries = []
        self.record_state = "listed"
        if self.has_permission():
            self.resolve_type()
        if self.model is None or self.model is self.registered_model:
            # Nothing to list: the table view still needs a configuration to set itself up with.
            models = (
                registry.samples
                if self.base_model.__name__ == "Sample"
                else registry.measurements
            )
            self.model = models[0]
            self.model_config = registry.get_for_model(self.model)
        super().setup(request, *args, **kwargs)

    def visible_records(self):
        """Return the dataset's records of this kind that the viewer may see."""
        return self.base_model.objects.filter(dataset=self.base_object).visible_to(
            self.request.user
        )

    def resolve_type(self):
        """Work out which types the dataset holds and which one this request shows."""
        counts = type_counts(self.visible_records())
        if not counts:
            held = self.base_model.objects.filter(dataset=self.base_object).exists()
            self.record_state = "unpublished" if held else "empty"
            self.model = None
            return
        wanted = self.kwargs.get("type")
        chosen = counts[0]
        if wanted:
            matches = [entry for entry in counts if entry[1].get_slug() == wanted]
            if not matches:
                raise Http404("This dataset holds no records of that type.")
            chosen = matches[0]
        self.model, self.model_config, __ = chosen
        name = f"{self.get_name()}-type"
        self.type_entries = [
            {
                "name": capfirst(config.get_verbose_name_plural()),
                "url": reverse(self.base_object, name, type=config.get_slug()),
                "count": count,
                "is_current": model is self.model,
            }
            for model, config, count in counts
        ]

    def get_queryset(self):
        """Limit to the dataset's own records of the chosen type that the viewer may see."""
        if self.record_state != "listed":
            return self.model.objects.none()
        queryset = self.model.objects.filter(pk__in=self.visible_records().values("pk"))
        if hasattr(queryset, "with_related"):
            queryset = queryset.with_related()
        if self.model in registry.measurements:
            queryset = queryset.select_related("sample__dataset", "sample__location")
        return queryset

    def get_empty_state_heading(self):
        """Say that nothing matches, since an empty table here always follows a search or filter."""
        return _("No %(type)s match") % {
            "type": self.model_config.get_verbose_name_plural()
        }

    def get_context_data(self, **kwargs):
        """Add the type switcher, the state of the list and the page heading."""
        context = super().get_context_data(**kwargs)
        current = next((e for e in self.type_entries if e["is_current"]), None)
        context["type_entries"] = self.type_entries
        context["current_type"] = current
        context["record_state"] = self.record_state
        context["kind"] = self.base_model.__name__.lower()
        context["page"] = {"title": self.kind_label}
        return context


class SampleMeasurements(Plugin, FairDMTemplateView):
    """List every measurement made on a sample, grouped by measurement type on one page."""

    template_name = "record_lists/sample_measurements.html"
    page_title = _("Measurements")

    def handle_no_permission(self):
        """Answer exactly as for a sample that does not exist."""
        raise Http404("No sample matches the given query.")

    def get_context_data(self, **kwargs):
        """Build one table per measurement type the viewer may see."""
        from fairdm.core.measurement.models import Measurement

        context = super().get_context_data(**kwargs)
        sample = self.base_object
        visible = Measurement.objects.filter(sample=sample).visible_to(
            self.request.user
        )
        groups = []
        total = 0
        elsewhere = 0
        for index, (model, config, count) in enumerate(type_counts(visible)):
            queryset = model.objects.filter(pk__in=visible.values("pk")).select_related(
                "dataset", "sample__dataset", "sample__location"
            )
            table = config.get_table_class()(
                queryset, exclude=HIDDEN_COLUMNS, prefix=f"t{index}-"
            )
            RequestConfig(self.request, paginate=False).configure(table)
            other = queryset.exclude(dataset_id=sample.dataset_id).count()
            groups.append(
                {
                    "name": capfirst(config.get_verbose_name_plural()),
                    "anchor": config.get_slug(),
                    "count": count,
                    "elsewhere": other,
                    "table": table,
                }
            )
            total += count
            elsewhere += other
        context["groups"] = groups
        context["total"] = total
        context["elsewhere"] = elsewhere
        context["sample"] = sample
        context["page"] = {"title": _("Measurements")}
        return context
