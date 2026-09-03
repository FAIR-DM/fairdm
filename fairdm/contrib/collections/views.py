from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch, path, reverse
from django.utils.translation import gettext_lazy as _
from django_filters.filterset import FilterSet

from fairdm.registry import registry
from fairdm.registry.factories import PublishedChoicesMixin
from fairdm.views import FairDMTableView


class DataTableView(FairDMTableView):
    """
    A view for displaying tabular data for Sample and Measurement sub-types.

    This view combines SingleTableMixin from django-tables2 with FairDMListView
    to provide a rich tabular interface with filtering and pagination.
    """

    template_name_suffix = "_table"
    template_name = "collections/listing.html"
    model_config = None  # To be set dynamically based on the model

    def setup(self, request, *args, **kwargs):
        """Assign `search_fields` before `SearchMixin` runs (T039, FR-024).

        Assigning the attribute is the requirement, not overriding
        `get_search_fields()`: the shell publishes
        `context["is_searchable"] = bool(self.search_fields)` by reading the
        attribute directly, so an override alone would hide the search box
        while search kept working.
        """
        super().setup(request, *args, **kwargs)
        self.search_fields = self.model_config.get_search_fields()

    def get_filterset_class(self) -> type[FilterSet] | None:
        """The type's own filter set, with publication scoping applied last.

        The scoping is applied here rather than in the factory because a
        registration may supply its own `filterset_class` or override
        `get_filterset_class()`, in which case the factory never runs - and
        because the two core filter mixins assign their `dataset` and `sample`
        choice lists at instantiation, after any class-level scoping. This is
        the one place every listing's filter set passes through, whichever tier
        of the configuration API produced it (FR-030, SC-002).
        """
        return PublishedChoicesMixin.applied_to(
            registry.get_for_model(self.model).get_filterset_class()
        )

    def get_queryset(self):
        """Narrow the shell's own chain through publication, never build a fresh one.

        Chaining from `super()` keeps `SearchMixin` and `BaseFilterView`'s work intact
        (research.md R1, R6). The deep `select_related` for a measurement type lands
        here rather than in `with_related()` or `published()` - see decisions.md D13.
        """
        queryset = super().get_queryset().published().with_related()
        if self.model in registry.measurements:
            queryset = queryset.select_related("sample__dataset", "sample__location")
        return queryset

    def get_context_data(self, **kwargs):

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
        """The switcher's entries for one kind, samples or measurements - each
        `{name, url, is_current}`, reversed from the `<slug>-list` URL names (FR-042
        to FR-045). Built from the registry at render time, so a new registration
        needs no per-type wiring (plan.md Summary)."""
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
        """
        Return the class to use for the table.
        """
        return self.model_config.get_table_class()

    def get_table_kwargs(self):
        """
        Return the keyword arguments for instantiating the table.

        Allows passing customized arguments to the table constructor, for example,
        to remove the buttons column, you could define this method in your View::

            def get_table_kwargs(self):
                return {"exclude": ("buttons",)}
        """
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
        """This listing's own empty-state heading (FR-018), not the shell's.

        Built per-instance from `model_config`, so it names the type on screen -
        `empty_state_heading` cannot be a plain class attribute for that reason.
        """
        return _("No published %(type)s yet") % {
            "type": self.model_config.get_verbose_name_plural()
        }

    def get_empty_state_message(self):
        """This listing's own empty-state message (FR-018), not the shell's.

        Overrides the hook outright rather than the `empty_state_message` attribute:
        the shell's own implementation only returns it when `show_action("create")` is
        true, which gates a create button this read-only listing never offers.
        """
        return _("There are no published %(type)s to show in this listing yet.") % {
            "type": self.model_config.get_verbose_name_plural()
        }

    @classmethod
    def get_urls(cls, **kwargs):
        """
        Return the URLs for the table view.
        """
        if not registry.samples and not registry.measurements:
            # In case there are no samples or measurements registered, return an empty list.
            return [], None
        urls = []
        seen_addresses: dict[str, type] = {}

        def add_listing_url(prefix: str, model_class: type) -> None:
            """Register one listing route, refusing a duplicate address (FR-050)."""
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

        # Process sample models
        for model_class in registry.samples:
            add_listing_url("samples", model_class)

        # Process measurement models
        for model_class in registry.measurements:
            add_listing_url("measurements", model_class)

        return urls, "collections"


# TODO: Create a statistics view for collections. This view will provide summary statistics
# and visualizations for the data in the collections. It should respond to filtering and support
# exporting of statistics. It should also support htmx for opening as a modal from the table view.
