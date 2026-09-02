import contextlib

from django.core.exceptions import ImproperlyConfigured
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import RedirectView
from django_filters.filterset import FilterSet

from fairdm.contrib.import_export.utils import export_choices
from fairdm.registry import registry
from fairdm.views import FairDMTableView, FairDMTemplateView


class DataTableView(FairDMTableView):
    """
    A view for displaying tabular data for Sample and Measurement sub-types.

    This view combines SingleTableMixin from django-tables2 with FairDMListView
    to provide a rich tabular interface with filtering, export, and pagination.
    """

    export_formats = ["csv", "xls", "xlsx", "json", "latex", "ods", "tsv", "yaml"]
    template_name_suffix = "_table"
    model_config = None  # To be set dynamically based on the model
    paginate_by = 20

    def get_filterset_class(self) -> type[FilterSet] | None:
        return registry.get_for_model(self.model).get_filterset_class()

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
        from django.urls import NoReverseMatch

        context = super().get_context_data(**kwargs)
        context["registry"] = registry
        # context["collection_menu"] = AppMenu.get("Data Collections")
        context["export_choices"] = export_choices

        # Determine collection type (sample or measurement)
        is_sample = self.model in registry.samples

        context["collection_type"] = "sample" if is_sample else "measurement"
        context["collection_type_verbose"] = "Sample" if is_sample else "Measurement"

        # Get all available collections of this type
        collection_models = registry.samples if is_sample else registry.measurements
        collection_list = []

        for model_class in collection_models:
            config = registry.get_for_model(model_class)
            slug = config.get_slug()
            try:
                url = reverse(f"{slug}-list")
            except NoReverseMatch:
                url = None

            collection_list.append(
                {
                    "name": config.get_verbose_name_plural(),
                    "verbose_name": config.get_verbose_name(),
                    "url": url,
                    "slug": slug,
                    "is_current": model_class == self.model,
                }
            )

        context["available_collections"] = collection_list
        context["current_model_verbose_name"] = self.model_config.get_verbose_name()
        context["current_model_verbose_name_plural"] = (
            self.model_config.get_verbose_name_plural()
        )

        # Page information for modal
        context["page"] = {
            "title": self.model_config.get_verbose_name_plural(),
            "description": (
                f"Browse and filter all {self.model_config.get_verbose_name_plural().lower()} "
                f"in this portal. Use the search bar to find specific records, apply filters "
                f"to narrow down results, and export data in various formats."
            ),
        }

        return context

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
        return _(
            "There are no published %(type)s to show in this listing yet."
        ) % {"type": self.model_config.get_verbose_name_plural()}

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

        # if registry.samples:
        #     first_config = registry.get_for_model(registry.samples[0])
        #     return urls, f"{first_config.get_slug()}-collection"

        return urls, "collections"


class CollectionRedirectView(RedirectView):
    """
    Redirects to the first registered collection.
    This is useful for the default view when no specific collection is requested.
    """

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Redirect to the first registered collection.
        """
        if not registry.samples and not registry.measurements:
            return "/"

        if registry.samples:
            first_model = registry.samples[0]
            config = registry.get_for_model(first_model)
            return f"/samples/{config.get_slug()}/"

        if registry.measurements:
            first_model = registry.measurements[0]
            config = registry.get_for_model(first_model)
            return f"/measurements/{config.get_slug()}/"

        return "/"


class CollectionsOverview(FairDMTemplateView):
    """
    Overview page for all data collections in the portal.

    Displays statistics and navigation for all registered Sample and Measurement types.
    """

    template_name = "collections/overview.html"
    title = "Data Collections"
    heading_config = {
        "icon": "table",
        "title": "Data Collections",
        "description": (
            "Explore tabular data collections by sample or measurement type. "
            "Each collection provides filtering, sorting, and export capabilities "
            "to help you discover and analyze research data."
        ),
    }

    def get_context_data(self, **kwargs):
        """Add collection statistics and type information to the context."""
        from django.urls import NoReverseMatch

        context = super().get_context_data(**kwargs)

        # Calculate overall statistics
        total_samples = 0
        total_measurements = 0

        for sample_model in registry.samples:
            with contextlib.suppress(Exception):
                total_samples += sample_model.objects.count()

        for measurement_model in registry.measurements:
            with contextlib.suppress(Exception):
                total_measurements += measurement_model.objects.count()

        context.update(
            {
                "total_samples": total_samples,
                "total_measurements": total_measurements,
                "total_sample_types": len(registry.samples),
                "total_measurement_types": len(registry.measurements),
            }
        )

        # Prepare sample type information with statistics
        sample_types = []
        for sample_model in registry.samples:
            try:
                config = registry.get_for_model(sample_model)
                slug = config.get_slug()

                # Try to get the collection URL
                try:
                    url = reverse(f"{slug}-collection")
                except NoReverseMatch:
                    url = None

                count = sample_model.objects.count()

                sample_types.append(
                    {
                        "name": config.get_verbose_name_plural(),
                        "verbose_name": config.get_verbose_name(),
                        "url": url,
                        "count": count,
                        "slug": slug,
                        "icon": "sample",
                    }
                )
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Failed to add sample type {sample_model.__name__}: {e}"
                )

        # Prepare measurement type information with statistics
        measurement_types = []
        for measurement_model in registry.measurements:
            try:
                config = registry.get_for_model(measurement_model)
                slug = config.get_slug()

                # Try to get the collection URL
                try:
                    url = reverse(f"{slug}-collection")
                except NoReverseMatch:
                    url = None

                count = measurement_model.objects.count()

                measurement_types.append(
                    {
                        "name": config.get_verbose_name_plural(),
                        "verbose_name": config.get_verbose_name(),
                        "url": url,
                        "count": count,
                        "slug": slug,
                        "icon": "measurement",
                    }
                )
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Failed to add measurement type {measurement_model.__name__}: {e}"
                )

        context.update(
            {
                "sample_types": sample_types,
                "measurement_types": measurement_types,
            }
        )

        return context


class SamplesOverview(FairDMTemplateView):
    """
    Detailed overview page for all sample collections.

    Displays comprehensive statistics, charts, and information about all registered Sample types.
    """

    template_name = "collections/samples_overview.html"
    title = "Sample Collections"
    heading_config = {
        "icon": "sample",
        "title": "Sample Collections",
        "description": (
            "Browse and explore all sample collections in this portal. "
            "Samples represent physical specimens, collection units, or observational locations in your research."
        ),
    }

    def get_context_data(self, **kwargs):
        """Add sample collection statistics and type information to the context."""
        from django.urls import NoReverseMatch

        context = super().get_context_data(**kwargs)

        # Calculate sample statistics
        total_samples = 0
        sample_types = []

        for sample_model in registry.samples:
            try:
                config = registry.get_for_model(sample_model)
                slug = config.get_slug()

                try:
                    url = reverse(f"{slug}-collection")
                except NoReverseMatch:
                    url = None

                count = sample_model.objects.count()
                total_samples += count

                sample_types.append(
                    {
                        "name": config.get_verbose_name_plural(),
                        "verbose_name": config.get_verbose_name(),
                        "url": url,
                        "count": count,
                        "slug": slug,
                        "icon": "sample",
                        "model": sample_model,
                    }
                )
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Failed to add sample type {sample_model.__name__}: {e}"
                )

        # Sort by count descending
        sample_types.sort(key=lambda x: x["count"], reverse=True)

        context.update(
            {
                "total_samples": total_samples,
                "total_sample_types": len(registry.samples),
                "sample_types": sample_types,
            }
        )

        return context


class MeasurementsOverview(FairDMTemplateView):
    """
    Detailed overview page for all measurement collections.

    Displays comprehensive statistics, charts, and information about all registered Measurement types.
    """

    template_name = "collections/measurements_overview.html"
    title = "Measurement Collections"
    heading_config = {
        "icon": "measurement",
        "title": "Measurement Collections",
        "description": (
            "Browse and explore all measurement collections in this portal. "
            "Measurements capture observations, analyses, and experimental results associated with samples."
        ),
    }

    def get_context_data(self, **kwargs):
        """Add measurement collection statistics and type information to the context."""
        from django.urls import NoReverseMatch

        context = super().get_context_data(**kwargs)

        # Calculate measurement statistics
        total_measurements = 0
        measurement_types = []

        for measurement_model in registry.measurements:
            try:
                config = registry.get_for_model(measurement_model)
                slug = config.get_slug()

                try:
                    url = reverse(f"{slug}-collection")
                except NoReverseMatch:
                    url = None

                count = measurement_model.objects.count()
                total_measurements += count

                measurement_types.append(
                    {
                        "name": config.get_verbose_name_plural(),
                        "verbose_name": config.get_verbose_name(),
                        "url": url,
                        "count": count,
                        "slug": slug,
                        "icon": "measurement",
                        "model": measurement_model,
                    }
                )
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Failed to add measurement type {measurement_model.__name__}: {e}"
                )

        # Sort by count descending
        measurement_types.sort(key=lambda x: x["count"], reverse=True)

        context.update(
            {
                "total_measurements": total_measurements,
                "total_measurement_types": len(registry.measurements),
                "measurement_types": measurement_types,
            }
        )

        return context


# TODO: Create a statistics view for collections. This view will provide summary statistics
# and visualizations for the data in the collections. It should respond to filtering and support
# exporting of statistics. It should also support htmx for opening as a modal from the table view.
