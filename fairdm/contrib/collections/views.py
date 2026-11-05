"""Tabular listing view for the registered sample and measurement types."""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Count
from django.urls import NoReverseMatch, path, reverse
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from django_filters.filterset import FilterSet

from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.registry import registry
from fairdm.registry.factories import PublishedChoicesMixin
from fairdm.views import FairDMTableView

# The columns a generated table holds that say nothing to a reader of the records.
BOOKKEEPING_COLUMNS = (
    "polymorphic_ctype",
    "measurement_ptr",
    "sample_ptr",
    "options",
    "image",
    "created",
    "modified",
)


class DataTableView(FairDMTableView):
    """Display the published records of one Sample or Measurement sub-type as a filterable table.

    Attributes:
        template_name_suffix: Suffix appended to the model name when resolving a template.
        template_name: The listing template.
        model_config: The registry configuration for the listed model, set per route
            by ``get_urls``.
    """

    template_name_suffix = "_table"
    template_name = "collections/listing.html"
    model_config = None

    @property
    def toolbar_filters(self) -> list[str]:
        """Draw the search and the status in the toolbar, wherever the filter set has them."""
        available = self.get_filterset_class().base_filters
        return [name for name in ("q", "status") if name in available]

    def get_filterset_class(self) -> type[FilterSet] | None:
        """Return the type's filter set with publication scoping applied last."""
        return PublishedChoicesMixin.applied_to(
            registry.get_for_model(self.model).get_filterset_class()
        )

    def get_queryset(self):
        """Limit to published records outside private projects, with related objects loaded.

        Measurements carry ``effective_location`` for the viewer, which the table's latitude and
        longitude read.
        """
        queryset = (
            super().get_queryset().published().outside_private_projects().with_related()
        )
        if self.model in registry.measurements:
            queryset = queryset.select_related(
                "sample__dataset__project"
            ).with_effective_location(self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        """Add the registry, the listed kind and the switcher's entries."""
        context = super().get_context_data(**kwargs)
        context["registry"] = registry
        context["kind"] = (
            "measurement" if self.model in registry.measurements else "sample"
        )
        context["type_entries"] = self.get_listing_entries()
        return context

    def get_page_title(self):
        """Return the listed type's plural name."""
        return self.model_config.get_verbose_name_plural()

    def get_listing_entries(self):
        """Build the switcher entries: every listing of the same kind, most records first.

        A tie is broken by the types' names, so the order is stable. A type with no published
        records is still offered, with a count of nought.

        Returns:
            One ``{name, url, count, is_current}`` dict per sample type, or per measurement
            type, with a ``<slug>-list`` route.
        """
        if self.model in registry.measurements:
            models, base = registry.measurements, Measurement
        else:
            models, base = registry.samples, Sample
        counts = dict(
            base.objects.published()
            .outside_private_projects()
            .order_by()
            .values_list("polymorphic_ctype")
            .annotate(count=Count("pk"))
        )
        entries = []
        for model_class in models:
            config = registry.get_for_model(model_class)
            try:
                url = reverse(f"{config.get_slug()}-list")
            except NoReverseMatch:
                continue
            ctype = ContentType.objects.get_for_model(model_class)
            entries.append(
                {
                    "name": capfirst(str(config.get_verbose_name_plural())),
                    "url": url,
                    "count": counts.get(ctype.pk, 0),
                    "is_current": model_class == self.model,
                }
            )
        entries.sort(key=lambda entry: (-entry["count"], str(entry["name"])))
        return entries

    def get_table_class(self):
        """Return the table class from the model configuration."""
        return self.model_config.get_table_class()

    def get_table_kwargs(self):
        """Exclude bookkeeping columns and set the empty-state text."""
        kwargs = {"exclude": list(BOOKKEEPING_COLUMNS)}
        kwargs["empty_text"] = self.get_empty_state_heading()
        return kwargs

    def get_empty_state_heading(self):
        """Return an empty-state heading naming the listed type."""
        return _("No published %(type)s yet") % {
            "type": self.model_config.get_verbose_name_plural()
        }

    def get_empty_state_message(self):
        """Return an empty-state message naming the listed type."""
        # The shell only returns `empty_state_message` when a create action is shown, which this read-only listing never has.
        return _("There are no published %(type)s to show in this listing yet.") % {
            "type": self.model_config.get_verbose_name_plural()
        }

    @classmethod
    def get_urls(cls, **kwargs):
        """Build one listing route per registered sample and measurement type.

        Args:
            **kwargs: Extra keyword arguments passed to ``as_view``.

        Returns:
            A ``(urlpatterns, app_name)`` pair, with an empty list and no namespace
            when nothing is registered. Two models that resolve to the same listing
            address raise ``ImproperlyConfigured``.
        """
        if not registry.samples and not registry.measurements:
            return [], None
        urls = []
        seen_addresses: dict[str, type] = {}

        def add_listing_url(prefix: str, model_class: type) -> None:
            """Register one listing route, refusing a duplicate address."""
            config = registry.get_for_model(model_class)
            slug = config.get_slug()
            address = f"{prefix}/{slug}/"
            if address in seen_addresses:
                raise ImproperlyConfigured(
                    f"{seen_addresses[address].__name__} and {model_class.__name__} "
                    f"both resolve to the listing address '{address}'."
                )
            seen_addresses[address] = model_class
            urls.append(
                path(
                    address,
                    cls.as_view(model=model_class, model_config=config, **kwargs),
                    name=f"{slug}-list",
                )
            )

        for model_class in registry.samples:
            add_listing_url("samples", model_class)

        for model_class in registry.measurements:
            add_listing_url("measurements", model_class)

        return urls, "collections"
