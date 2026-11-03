"""The Samples and Measurements tabs of a dataset.

Each tab lists the samples or the measurements of one registered type at a time, the most
numerous type unless the address names another.
"""

from dataclasses import dataclass
from typing import Any

import django_tables2 as tables
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Model, QuerySet
from django.http import Http404
from django.urls import path
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.collections.views import DataTableView
from fairdm.contrib.plugins import Plugin, reverse
from fairdm.contrib.plugins.mixins import PrivateRecordNotFoundMixin
from fairdm.core.dataset.models import Dataset
from fairdm.core.dataset.plugins import dataset_records_visible
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.registry import registry
from fairdm.registry.config import ModelConfiguration
from fairdm.registry.factories import PublishedChoicesMixin


@dataclass(frozen=True)
class RecordType:
    """One registered type that a tab can list, with the number of records it holds.

    Attributes:
        model: The sample or measurement class.
        config: The registry configuration of the class.
        count: How many records of the type the viewer may see.
    """

    model: type[Model]
    config: ModelConfiguration
    count: int

    @property
    def name(self) -> str:
        """The type's plural name."""
        return capfirst(str(self.config.get_verbose_name_plural()))

    @property
    def slug(self) -> str:
        """The type's slug, which names it in the address."""
        return self.config.get_slug()


@dataclass(frozen=True)
class KindName:
    """Stands for the sample or measurement kind where no type is listed."""

    label: str

    def get_verbose_name_plural(self) -> str:
        """Return the kind's plural name."""
        return self.label


def type_counts(queryset: QuerySet) -> list[RecordType]:
    """Count a polymorphic queryset's records per registered type, most numerous first.

    A tie is broken by the types' names, so the order is stable.

    Args:
        queryset: Samples or measurements.

    Returns:
        One entry per registered type the queryset holds.
    """
    rows = (
        queryset.order_by()
        .values("polymorphic_ctype")
        .annotate(count=Count("pk"))
        .order_by()
    )
    entries = []
    for row in rows:
        model = ContentType.objects.get_for_id(row["polymorphic_ctype"]).model_class()
        if model is None or not registry.is_registered(model):
            continue
        entries.append(RecordType(model, registry.get_for_model(model), row["count"]))
    return sorted(entries, key=lambda entry: (-entry.count, entry.name))


class NoRecords(tables.Table):
    """The table of a tab with nothing to list. It has no columns and takes no rows."""


class SampleColumn(tables.Column):
    """A measurement's sample, named and linked only where the viewer may open it."""

    def __init__(self, openable: set[int], **kwargs: Any) -> None:
        self.openable = openable
        kwargs.setdefault("verbose_name", _("Sample"))
        kwargs.setdefault("order_by", ("sample__name",))
        super().__init__(accessor="sample", **kwargs)

    def render(self, value: Sample) -> str:
        """Name the sample and link it, or give a dash where the viewer may not open it."""
        if value.dataset_id in self.openable:
            return format_html('<a href="{}">{}</a>', value.get_absolute_url(), value)
        return "—"


class RecordsTab(PrivateRecordNotFoundMixin, Plugin, DataTableView):
    """The samples or the measurements of a dataset, one registered type at a time.

    Attributes:
        base_model: ``Sample`` or ``Measurement``.
        kind_label: The plural name of the kind, used as the page heading.
        record_state: ``"listed"`` when the viewer may see records, ``"empty"`` when there
            are none to show.
        type_entries: The types offered in the switcher, as dicts for the template.
        chosen: The type this request lists, or ``None`` when the state is ``"empty"``.
    """

    base_model: type[Model]
    kind_label = ""
    template_name = "record_lists/records.html"
    paginate_by = 50
    check = staticmethod(dataset_records_visible)

    record_state = "listed"
    type_entries: list[dict[str, Any]] = []
    chosen: RecordType | None = None

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

    def handle_no_permission(self):
        """Answer 404 to anyone not offered the tab, whether or not the dataset is public.

        A public dataset that is not yet published opens for a visitor, its records do not, and
        the tab says no more about them than the dataset's address would for a private one.

        Raises:
            Http404: Always.
        """
        raise Http404("No records match the given query.")

    # Which records each page lists ---------------------------------------------------------

    def scope(self) -> QuerySet:
        """Return every record of this kind in the page's dataset, whoever looks."""
        return self.base_model.objects.filter(dataset=self.base_object)  # type: ignore[attr-defined]

    def visible_records(self) -> QuerySet:
        """Return the dataset's records that the viewer may see."""
        return self.scope().visible_to(self.request.user)

    # The request ---------------------------------------------------------------------------

    def get(self, request, *args, **kwargs):
        """Choose the type to show, then list its records."""
        self.resolve_type()
        return super().get(request, *args, **kwargs)

    def resolve_type(self) -> None:
        """Work out which types are listed and which one this request shows.

        Sets ``record_state``, ``type_entries``, ``chosen``, ``model`` and ``model_config``.
        A tab that lists nothing keeps no type: it builds no table and no filter set.

        Raises:
            Http404: The address names a type that is not listed.
        """
        counts = type_counts(self.visible_records())
        wanted = self.kwargs.get("type")
        self.chosen = None
        self.type_entries = []
        self.record_state = "empty"
        if counts:
            self.record_state = "listed"
            self.chosen = counts[0]
            if wanted:
                self.chosen = next((e for e in counts if e.slug == wanted), None)
        if wanted and self.chosen is None:
            raise Http404("Nothing of that type is listed here.")
        if self.chosen is None:
            self.model = self.base_model
            self.model_config = KindName(str(self.kind_label))
            return
        self.model = self.chosen.model
        self.model_config = self.chosen.config
        name = f"{self.get_name()}-type"
        self.type_entries = [
            {
                "name": entry.name,
                "url": reverse(self.base_object, name, type=entry.slug),
                "count": entry.count,
                "is_current": entry is self.chosen,
            }
            for entry in counts
        ]

    def get_queryset(self):
        """Limit to the chosen type's records in this dataset that the viewer may see."""
        if self.chosen is None:
            return self.base_model.objects.none()  # type: ignore[attr-defined]
        queryset = self.model.objects.filter(pk__in=self.visible_records().values("pk"))
        if hasattr(queryset, "with_related"):
            queryset = queryset.with_related()
        queryset = queryset.select_related("dataset__project")
        if self.base_model is Measurement:
            queryset = queryset.select_related(
                "sample__dataset__project"
            ).with_effective_location(self.request.user)
        return queryset

    def get_table_class(self):
        """Return the chosen type's table, or a table with no columns where nothing is listed."""
        if self.chosen is None:
            return NoRecords
        return self.chosen.config.get_table_class()

    def get_table_kwargs(self):
        """Lead with the record's name, and with the sample on a measurement."""
        kwargs = super().get_table_kwargs()
        if self.chosen is None:
            return kwargs
        lead = ["name"]
        if self.base_model is Measurement:
            # Sketch: decided per dataset, which misses a sample opened by a credit on itself.
            seen = set(
                Sample.objects.visible_to(self.request.user)
                .values_list("dataset_id", flat=True)
                .distinct()
            )
            kwargs["extra_columns"] = [("sample_name", SampleColumn(seen))]
            kwargs["exclude"] = [*kwargs["exclude"], "sample"]
            lead.append("sample_name")
        # The registration's own order puts a measurement's name last, so the lead is pinned.
        kwargs["sequence"] = (*lead, "...")
        kwargs["exclude"] = [*kwargs["exclude"], "dataset"]
        return kwargs

    @property
    def toolbar_filters(self) -> list[str]:
        """Draw the search and the status in the toolbar, where the filter set has them."""
        filterset = self.get_filterset_class()
        if filterset is None:
            return []
        return [name for name in ("q", "status") if name in filterset.base_filters]

    def get_filterset_class(self):
        """Return the chosen type's filter set without the dataset filter, or none."""
        if self.chosen is None:
            return None
        filterset = PublishedChoicesMixin.applied_to(
            self.chosen.config.get_filterset_class()
        )
        if "dataset" not in filterset.base_filters:
            return filterset
        narrowed = type(filterset.__name__, (filterset,), {})
        # Set after the class exists: the filter set's metaclass rebuilds ``base_filters``.
        narrowed.base_filters = {
            name: f for name, f in filterset.base_filters.items() if name != "dataset"
        }
        return narrowed

    def get_listing_entries(self, models):
        """Offer no switcher between the portal's listings: this page has its own."""
        return []

    def get_empty_state_heading(self):
        """Say that nothing matches, since an empty table here always follows a search or filter."""
        return _("No %(type)s match") % {
            "type": self.model_config.get_verbose_name_plural()
        }

    def get_context_data(self, **kwargs):
        """Add the type switcher, the state of the list and the page heading."""
        context = super().get_context_data(**kwargs)
        context["type_entries"] = self.type_entries
        context["current_type"] = next(
            (e for e in self.type_entries if e["is_current"]), None
        )
        context["record_state"] = self.record_state
        context["kind"] = self.base_model.__name__.lower()
        context["holder"] = "dataset"
        # The table view replaces ``page`` with its own title, which drops the record's trail.
        context["page"] = {
            **(context.get("page") or {}),
            "title": self.kind_label,
            "breadcrumbs": self.get_breadcrumbs(),
        }
        return context


@plugins.register(Dataset, label=_("Samples"), icon="sample", order=300)
class Samples(RecordsTab):
    """List the samples of a dataset, in the table of each sample type."""

    url_path = "samples"
    base_model = Sample
    kind_label = _("Samples")
    page_title = _("Samples")


@plugins.register(Dataset, label=_("Measurements"), icon="measurement", order=400)
class Measurements(RecordsTab):
    """List the measurements of a dataset, in the table of each measurement type."""

    url_path = "measurements"
    base_model = Measurement
    kind_label = _("Measurements")
    page_title = _("Measurements")
