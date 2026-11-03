"""The Samples and Measurements tabs of a dataset, a project and a contributor.

Each tab lists the samples or the measurements of one registered type at a time, the most
numerous type unless the address names another.
"""

from dataclasses import dataclass
from functools import partial
from typing import Any

import django_tables2 as tables
from django.contrib.contenttypes.models import ContentType
from django.db.models import Case, Count, Exists, F, Model, OuterRef, QuerySet, When
from django.http import Http404, HttpRequest
from django.urls import path
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet
from django_tables2.data import TableQuerysetData

from fairdm import plugins
from fairdm.contrib.collections.tables import MeasurementTable, SampleTable
from fairdm.contrib.collections.views import DataTableView
from fairdm.contrib.contributors.models import Contributor
from fairdm.contrib.plugins import Plugin, reverse
from fairdm.contrib.plugins.mixins import PrivateRecordNotFoundMixin
from fairdm.core.dataset.models import Dataset
from fairdm.core.dataset.plugins import dataset_records_visible
from fairdm.core.measurement.filters import MeasurementFilter
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.project.plugins import project_is_visible
from fairdm.core.sample.filters import SampleFilter
from fairdm.core.sample.models import Sample
from fairdm.registry import registry
from fairdm.registry.config import ModelConfiguration
from fairdm.registry.factories import ScopedChoicesMixin

FALLBACK_SLUG = "other"


@dataclass(frozen=True)
class FallbackType:
    """Stands for the records of every type that is no longer registered.

    It answers the questions a tab asks of a registered type's configuration, with the
    base table and filter set of the kind.

    Attributes:
        base_model: ``Sample`` or ``Measurement``.
    """

    base_model: type[Model]

    def get_slug(self) -> str:
        """Return the slug that names the fallback in the address."""
        return FALLBACK_SLUG

    def get_verbose_name_plural(self) -> str:
        """Return the base model's plural name."""
        return str(self.base_model._meta.verbose_name_plural)

    def get_table_class(self) -> type[tables.Table]:
        """Return the base table of the kind."""
        return SampleTable if self.base_model is Sample else MeasurementTable

    def get_filterset_class(self) -> type[FilterSet]:
        """Return the base filter set of the kind."""
        return SampleFilter if self.base_model is Sample else MeasurementFilter


@dataclass(frozen=True)
class RecordType:
    """One type that a tab can list, with the number of records it holds.

    Attributes:
        model: The sample or measurement class. The base class for the fallback entry.
        config: The registry configuration of the class, or the fallback's.
        count: How many records of the type the viewer may see.
        unregistered: For the fallback entry, the content types whose records it lists.
    """

    model: type[Model]
    config: ModelConfiguration | FallbackType
    count: int
    unregistered: tuple[int, ...] = ()

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
        One entry per registered type the queryset holds, then one for the records of
        types no longer registered, when there are any.
    """
    rows = (
        queryset.order_by()
        .values("polymorphic_ctype")
        .annotate(count=Count("pk"))
        .order_by()
    )
    entries = []
    gone: dict[int, int] = {}
    for row in rows:
        model = ContentType.objects.get_for_id(row["polymorphic_ctype"]).model_class()
        if model is None or not registry.is_registered(model):
            gone[row["polymorphic_ctype"]] = row["count"]
            continue
        entries.append(RecordType(model, registry.get_for_model(model), row["count"]))
    entries.sort(key=lambda entry: (-entry.count, entry.name))
    if gone:
        entries.append(
            RecordType(
                queryset.model,
                FallbackType(queryset.model),
                sum(gone.values()),
                tuple(gone),
            )
        )
    return entries


class NoRecords(tables.Table):
    """The table of a tab with nothing to list. It has no columns and takes no rows."""


class StableOrderData(TableQuerysetData):
    """Table rows whose order always ends in the primary key, so paging never repeats a row.

    The order a table applies, by its ``Meta.order_by`` or by a column the reader chose,
    replaces the queryset's own, and a column that holds equal values leaves ties in no
    fixed order. Appending ``pk`` after every ordering makes each page the same on every
    request.
    """

    def __init__(self, data: QuerySet) -> None:
        super().__init__(self.tie_break(data))

    def order_by(self, aliases) -> None:
        """Order the rows as the table asks, then by primary key."""
        super().order_by(aliases)
        self.data = self.tie_break(self.data)

    @staticmethod
    def tie_break(queryset: QuerySet) -> QuerySet:
        """Return the queryset with ``pk`` last in its order, unless a unique key already is.

        Args:
            queryset: The rows to order.

        Returns:
            The queryset, ordered.
        """
        ordering = list(queryset.query.order_by or queryset.model._meta.ordering)
        last = ordering[-1] if ordering else None
        if isinstance(last, str) and last.lstrip("-") in ("pk", "id"):
            return queryset.order_by(*ordering)
        return queryset.order_by(*ordering, "pk")


class DatasetColumn(tables.Column):
    """A record's dataset, linked only where the viewer may open it, otherwise only named.

    It reads the ``dataset_open`` annotation the tab puts on every row, never the database.
    """

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("verbose_name", _("Dataset"))
        kwargs.setdefault("order_by", ("dataset__name",))
        super().__init__(accessor="dataset", **kwargs)

    def render(self, record: Model, value: Dataset) -> str:
        """Link the dataset where the viewer may open it, else give its name."""
        if record.dataset_open:  # type: ignore[attr-defined]
            return format_html('<a href="{}">{}</a>', value.get_absolute_url(), value)
        return str(value)


class SampleColumn(tables.Column):
    """A measurement's sample, named and linked only where the viewer may open it.

    It reads the ``sample_open`` annotation the tab puts on every row, never the database.
    The sample's name is never drawn for a viewer who may not open it.
    """

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("verbose_name", _("Sample"))
        super().__init__(accessor="sample", **kwargs)

    def render(self, record: Model, value: Sample) -> str:
        """Link the sample where the viewer may open it, else give a dash."""
        if record.sample_open:  # type: ignore[attr-defined]
            return format_html('<a href="{}">{}</a>', value.get_absolute_url(), value)
        return "—"

    def order(self, queryset: QuerySet, is_descending: bool) -> tuple[QuerySet, bool]:
        """Order by the sample's name, with the samples the viewer may not open last.

        Only the rows with an openable sample are ordered by name. The rest sort as one block
        after them, left to the table's primary-key tie-break in either direction, so the order
        reveals neither which measurements share a hidden sample nor where its name would fall.

        Args:
            queryset: The rows to order.
            is_descending: Whether the reader asked for the descending order.

        Returns:
            The ordered rows, and ``True`` to say the column ordered them itself.
        """
        name = Case(When(sample_open=True, then=F("sample__name")))
        return (
            queryset.order_by(
                "-sample_open", name.desc() if is_descending else name.asc()
            ),
            True,
        )


def records_are_offered(request: HttpRequest, obj: Model | None) -> bool:
    """Return whether the request's user is offered the tabs of a dataset, project or contributor.

    A dataset's tabs follow its records (:func:`dataset_records_visible`). A project's follow
    the project's own page: what its datasets hold is decided row by row, so a project whose
    records the viewer may not see answers ``empty`` rather than 404. A contributor's follow
    the contributor's overview, which opens for everyone.

    Args:
        request: The current request.
        obj: The dataset, project or contributor, or ``None`` when no record has been resolved.

    Returns:
        True when the tabs may be shown.
    """
    if isinstance(obj, Contributor):
        return True
    if isinstance(obj, Project):
        return project_is_visible(request, obj)
    return dataset_records_visible(request, obj)


class RecordsTab(PrivateRecordNotFoundMixin, Plugin, DataTableView):
    """The samples or the measurements of a dataset, project or contributor, one type at a time.

    A dataset's tab lists the records in the dataset. A project's lists the records in any of
    its datasets, each row naming its dataset. A contributor's lists the records credited to
    them or beneath something credited to them (``Contributor.get_associated_records``), each
    row naming its dataset.

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
    check = staticmethod(records_are_offered)

    record_state = "listed"
    filterset_classes: dict[Any, type[FilterSet]] = {}
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

    @property
    def holder(self) -> str:
        """The kind of record the page belongs to: ``"dataset"``, ``"project"`` or ``"contributor"``."""
        return self.registered_model._meta.model_name  # type: ignore[union-attr,return-value]

    def scope(self) -> QuerySet:
        """Return every record of this kind the page's record is associated with, whoever looks."""
        if self.holder == "contributor":
            return self.base_object.get_associated_records(self.base_model)  # type: ignore[union-attr]
        lookup = "dataset__project" if self.holder == "project" else "dataset"
        return self.base_model.objects.filter(**{lookup: self.base_object})  # type: ignore[attr-defined]

    def is_own_page(self) -> bool:
        """Return whether the page is a person's own and that person is the one looking."""
        user = self.request.user
        return (
            self.holder == "contributor"
            and user.is_authenticated
            and user.pk == self.base_object.pk  # type: ignore[union-attr]
            and not self.base_object.is_organization  # type: ignore[union-attr]
        )

    def viewer(self):
        """Return the user whose view of the records decides the list, or ``None`` for released only.

        A contributor's page lists only what is released to everyone, unless a person looks at
        their own, which also lists what they hold a level on.
        """
        if self.holder == "contributor" and not self.is_own_page():
            return None
        return self.request.user

    def visible_records(self) -> QuerySet:
        """Return the page's records that the viewer may see."""
        return self.scope().visible_to(self.viewer())

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
        """Limit to the chosen type's records on this page that the viewer may see.

        Every row carries ``dataset_open`` and, on measurements, ``sample_open``: whether
        the request's user may open the row's dataset and sample.
        """
        if self.chosen is None:
            return self.base_model.objects.none()  # type: ignore[attr-defined]
        user = self.request.user
        queryset = self.model.objects.filter(pk__in=self.visible_records().values("pk"))
        if self.chosen.unregistered:
            queryset = queryset.filter(polymorphic_ctype__in=self.chosen.unregistered)
        if hasattr(queryset, "with_related"):
            queryset = queryset.with_related()
        queryset = queryset.select_related("dataset__project").annotate(
            dataset_open=Exists(
                Dataset.all_objects.visible_to(user).filter(pk=OuterRef("dataset_id"))
            )
        )
        if self.base_model is Measurement:
            queryset = (
                queryset.select_related("sample__dataset__project")
                .annotate(
                    sample_open=Exists(
                        Sample.objects.visible_to(user).filter(pk=OuterRef("sample_id"))
                    )
                )
                .with_effective_location(user)
            )
        return queryset

    def get_table_data(self):
        """Return the rows with their order ending in the primary key."""
        return StableOrderData(super().get_table_data())

    def get_table_class(self):
        """Return the chosen type's table, or a table with no columns where nothing is listed."""
        if self.chosen is None:
            return NoRecords
        return self.chosen.config.get_table_class()

    def get_table_kwargs(self):
        """Lead with the record's name, then its dataset on a project, then its sample.

        The dataset icon column is dropped: a dataset's rows are all in the page's dataset, and
        a project's name theirs in a column of its own.
        """
        kwargs = super().get_table_kwargs()
        if self.chosen is None:
            return kwargs
        lead = ["name"]
        extra = []
        # The registration's own order puts a measurement's name last, so the lead is pinned.
        kwargs["exclude"] = [*kwargs["exclude"], "dataset"]
        if self.holder != "dataset":
            extra.append(("dataset_name", DatasetColumn()))
            lead.append("dataset_name")
        if self.base_model is Measurement:
            # The base table renders ``sample`` with its own method, which a column cannot override.
            extra.append(("sample_name", SampleColumn()))
            kwargs["exclude"] = [*kwargs["exclude"], "sample"]
            lead.append("sample_name")
        kwargs["extra_columns"] = extra
        kwargs["sequence"] = (*lead, "...")
        return kwargs

    @property
    def toolbar_filters(self) -> list[str]:
        """Draw the search and the status in the toolbar, where the filter set has them."""
        filterset = self.get_filterset_class()
        if filterset is None:
            return []
        return [name for name in ("q", "status") if name in filterset.base_filters]

    def get_filterset_class(self):
        """Return the chosen type's filter set with this tab's scoping, or none.

        The registry builds a type's filter set anew on each call, so the scoped class is
        kept per configuration: a request would otherwise leave a new class behind.
        """
        if self.chosen is None:
            return None
        config = self.chosen.config
        if config not in self.filterset_classes:
            self.filterset_classes[config] = ScopedChoicesMixin.applied_to(
                config.get_filterset_class()
            )
        return self.filterset_classes[config]

    def get_filterset_kwargs(self) -> dict[str, Any]:
        """Return what scopes the filter set to this tab's rows, for its constructor.

        Its choices are the records the listed rows point to that the viewer may see, and
        it has no dataset filter on a dataset's page, since every row is in that dataset. The
        record filters offer a person's own records on that person's page, and public records
        on any other contributor's.
        """
        kwargs: dict[str, Any] = {}
        if self.holder == "dataset":
            kwargs["drop"] = ("dataset",)
        if self.holder == "contributor":
            if self.is_own_page():
                kwargs["owner"] = self.base_object
            else:
                kwargs["scope"] = "public"
        return kwargs

    def get_filterset(self, filterset_class=None):
        """Build the filter set with the scoping of :meth:`get_filterset_kwargs`."""
        filterset_class = filterset_class or self.get_filterset_class()
        if filterset_class is not None:
            filterset_class = partial(filterset_class, **self.get_filterset_kwargs())
        return super().get_filterset(filterset_class)

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
        context["holder"] = self.holder
        context["own_page"] = self.is_own_page()
        return context

    def get_page_title(self):
        """Return the kind's plural name, which ends the breadcrumb trail."""
        return self.kind_label


@plugins.register(
    Dataset, Project, Contributor, label=_("Samples"), icon="sample", order=300
)
class Samples(RecordsTab):
    """List the samples of a dataset, project or contributor, in the table of each sample type."""

    url_path = "samples"
    base_model = Sample
    kind_label = _("Samples")
    page_title = _("Samples")


@plugins.register(
    Dataset,
    Project,
    Contributor,
    label=_("Measurements"),
    icon="measurement",
    order=400,
)
class Measurements(RecordsTab):
    """List the measurements of a dataset, project or contributor, in the table of each type."""

    url_path = "measurements"
    base_model = Measurement
    kind_label = _("Measurements")
    page_title = _("Measurements")
