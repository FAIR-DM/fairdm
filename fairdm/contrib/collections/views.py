"""Tabular listing view for the registered sample and measurement types."""

from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch, path, reverse
from django.utils.translation import gettext_lazy as _
from django_filters.filterset import FilterSet

from fairdm.registry import registry
from fairdm.registry.factories import PublishedChoicesMixin
from fairdm.views import FairDMTableView


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
        return [name for name in ("search", "status") if name in available]

    def get_filterset_class(self) -> type[FilterSet] | None:
        """Return the type's filter set with publication scoping applied last."""
        return PublishedChoicesMixin.applied_to(
            registry.get_for_model(self.model).get_filterset_class()
        )

    def get_queryset(self):
        """Limit to published records with related objects loaded, chaining from the parent queryset.

        Measurements carry ``effective_location`` for the viewer, which the table's latitude and
        longitude read.
        """
        queryset = super().get_queryset().published().with_related()
        if self.model in registry.measurements:
            queryset = queryset.select_related(
                "sample__dataset"
            ).with_effective_location(self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        """Add the registry, the sample and measurement switcher entries and the page title."""
        context = super().get_context_data(**kwargs)
        context["registry"] = registry
        context["sample_listings"] = self.get_listing_entries(registry.samples)
        context["measurement_listings"] = self.get_listing_entries(
            registry.measurements
        )

        context["page"] = {
            "title": self.model_config.get_verbose_name_plural(),
        }

        return context

    def get_listing_entries(self, models):
        """Build the switcher entries for samples or measurements.

        Args:
            models: The registered model classes of one kind.

        Returns:
            One ``{name, url, is_current}`` dict per model with a ``<slug>-list`` route.
        """
        entries = []
        for model_class in models:
            config = registry.get_for_model(model_class)
            try:
                url = reverse(f"{config.get_slug()}-list")
            except NoReverseMatch:
                continue
            entries.append(
                {
                    "name": config.get_verbose_name_plural(),
                    "url": url,
                    "is_current": model_class == self.model,
                }
            )
        return entries

    def get_table_class(self):
        """Return the table class from the model configuration."""
        return self.model_config.get_table_class()

    def get_table_kwargs(self):
        """Exclude bookkeeping columns and set the empty-state text."""
        kwargs = {
            "exclude": [
                "polymorphic_ctype",
                "measurement_ptr",
                "sample_ptr",
                "options",
                "image",
                "created",
                "modified",
            ],
        }
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
