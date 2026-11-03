"""The Samples and Measurements tabs of a dataset, a project, a person and an organization.

Sketch for specification 023. Everything here is untested and is the plan's to rebuild.
"""

import django_tables2 as tables
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.http import Http404
from django.urls import path
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.collections.views import DataTableView
from fairdm.contrib.contributors.models import Contributor, Organization
from fairdm.contrib.plugins import Plugin, reverse
from fairdm.contrib.plugins.mixins import PrivateRecordNotFoundMixin
from fairdm.core.dataset.models import Dataset
from fairdm.core.dataset.plugins import dataset_is_visible
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.project.plugins import project_is_visible
from fairdm.core.sample.models import Sample
from fairdm.registry import registry
from fairdm.utils.choices import Visibility


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


def tab_is_visible(request, obj):
    """Open the tab for exactly the viewers the record's overview opens for."""
    if isinstance(obj, Dataset):
        return dataset_is_visible(request, obj)
    if isinstance(obj, Project):
        return project_is_visible(request, obj)
    return True


class DatasetColumn(tables.Column):
    """The dataset a row belongs to, by name, linked where the viewer may open it."""

    def __init__(self, openable, **kwargs):
        self.openable = openable
        kwargs.setdefault("verbose_name", _("Dataset"))
        kwargs.setdefault("order_by", ("dataset__name",))
        super().__init__(accessor="dataset", **kwargs)

    def render(self, value):
        if value.pk in self.openable:
            return format_html('<a href="{}">{}</a>', value.get_absolute_url(), value)
        return str(value)


class RecordsTab(PrivateRecordNotFoundMixin, Plugin, DataTableView):
    """The samples or the measurements associated with one record, one registered type at a time.

    Attributes:
        base_model: ``Sample`` or ``Measurement``.
        kind_label: The plural name of the kind, used as the page heading.
    """

    base_model = None
    kind_label = ""
    template_name = "record_lists/records.html"
    paginate_by = 50
    check = staticmethod(tab_is_visible)

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

    # Which records each page lists ---------------------------------------------------------

    def scope(self):
        """Return every record of this kind associated with the page's record, whoever looks."""
        obj = self.base_object
        records = self.base_model.objects.all()
        if isinstance(obj, Dataset):
            return records.filter(dataset=obj)
        if isinstance(obj, Project):
            return records.filter(dataset__project=obj)
        # ``all_objects``: the default managers leave out private records, which the
        # contributor's own page lists.
        datasets = Dataset.all_objects.filter(contributors__contributor=obj)
        projects = Project.objects.filter(contributors__contributor=obj)
        credited = (
            Q(pk__in=obj.credited_object_ids(self.base_model))
            | Q(dataset__in=datasets.values("pk"))
            | Q(dataset__project__in=projects.values("pk"))
        )
        if isinstance(obj, Organization):
            credited |= Q(dataset__project__owner=obj)
        return records.filter(credited)

    def viewer(self):
        """Return whom the list is shown as: on a contributor's page, only that person sees more."""
        obj = self.base_object
        if isinstance(obj, Contributor) and self.request.user.pk != obj.pk:
            return None
        return self.request.user

    def visible_records(self):
        """Return the associated records the viewer may see."""
        return self.scope().visible_to(self.viewer())

    @property
    def spans_datasets(self):
        """Whether rows can come from more than one dataset."""
        return not isinstance(self.base_object, Dataset)

    # The request ---------------------------------------------------------------------------

    def setup(self, request, *args, **kwargs):
        """Choose the type to show before the table view reads its configuration."""
        self.request, self.args, self.kwargs = request, args, kwargs
        self.type_entries = []
        self.record_state = "listed"
        self.model = None
        if self.has_permission():
            self.resolve_type()
        if self.model is None:
            # Nothing to list: the table view still needs a configuration to set itself up with.
            models = (
                registry.samples
                if self.base_model is Sample
                else registry.measurements
            )
            self.model = models[0]
            self.model_config = registry.get_for_model(self.model)
        super().setup(request, *args, **kwargs)

    def resolve_type(self):
        """Work out which types are listed and which one this request shows."""
        counts = type_counts(self.visible_records())
        if not counts:
            waiting = self.scope().filter(
                dataset__visibility=Visibility.PUBLIC, dataset__published=False
            )
            self.record_state = (
                "unpublished"
                if not isinstance(self.base_object, Contributor) and waiting.exists()
                else "empty"
            )
            if self.kwargs.get("type"):
                raise Http404("Nothing of that type is listed here.")
            return
        wanted = self.kwargs.get("type")
        chosen = counts[0]
        if wanted:
            matches = [entry for entry in counts if entry[1].get_slug() == wanted]
            if not matches:
                raise Http404("Nothing of that type is listed here.")
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
        """Limit to the chosen type's associated records that the viewer may see."""
        if self.record_state != "listed":
            return self.model.objects.none()
        queryset = self.model.objects.filter(pk__in=self.visible_records().values("pk"))
        if hasattr(queryset, "with_related"):
            queryset = queryset.with_related()
        queryset = queryset.select_related("dataset__project")
        if self.model in registry.measurements:
            queryset = queryset.select_related(
                "sample__dataset__project"
            ).with_effective_location(self.request.user)
        return queryset

    def get_table_kwargs(self):
        """Name each row's dataset where rows come from several, and drop the icon where not."""
        kwargs = super().get_table_kwargs()
        if self.spans_datasets:
            openable = set(
                Dataset.all_objects.visible_to(self.request.user).values_list(
                    "pk", flat=True
                )
            )
            # A name of its own: the base table's ``render_dataset`` draws the icon column.
            kwargs["extra_columns"] = [("dataset_name", DatasetColumn(openable))]
            kwargs["sequence"] = ("name", "dataset_name", "...")
        kwargs["exclude"] = [*kwargs["exclude"], "dataset"]
        return kwargs

    def get_empty_state_heading(self):
        """Say that nothing matches, since an empty table here always follows a search or filter."""
        return _("No %(type)s match") % {
            "type": self.model_config.get_verbose_name_plural()
        }

    def get_context_data(self, **kwargs):
        """Add the type switcher, the state of the list and the page heading."""
        context = super().get_context_data(**kwargs)
        current = next((e for e in self.type_entries if e["is_current"]), None)
        obj = self.base_object
        context["type_entries"] = self.type_entries
        context["current_type"] = current
        context["record_state"] = self.record_state
        context["kind"] = self.base_model.__name__.lower()
        context["holder"] = (
            "dataset"
            if isinstance(obj, Dataset)
            else "project"
            if isinstance(obj, Project)
            else "contributor"
        )
        context["own_page"] = (
            isinstance(obj, Contributor) and self.request.user.pk == obj.pk
        )
        context["page"] = {"title": self.kind_label}
        return context


@plugins.register(
    Dataset, Project, Contributor, label=_("Samples"), icon="sample", order=300
)
class Samples(RecordsTab):
    """List the samples associated with the record, in the table of each sample type."""

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
    """List the measurements associated with the record, in the table of each measurement type."""

    url_path = "measurements"
    base_model = Measurement
    kind_label = _("Measurements")
    page_title = _("Measurements")
