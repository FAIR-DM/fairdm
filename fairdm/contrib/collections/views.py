from django.urls import path, reverse
from django.views.generic import RedirectView
from django_tables2.views import SingleTableMixin

from fairdm.contrib.import_export.utils import export_choices
from fairdm.registry import registry
from fairdm.views import FairDMListView, FairDMTemplateView

# from fairdm.menus import AppMenu


class DataTableView(SingleTableMixin, FairDMListView):
    """
    A view for displaying tabular data for Sample and Measurement sub-types.

    This view combines SingleTableMixin from django-tables2 with FairDMListView
    to provide a rich tabular interface with filtering, export, and pagination.
    """

    export_formats = ["csv", "xls", "xlsx", "json", "latex", "ods", "tsv", "yaml"]
    template_name_suffix = "_table"
    template_name = "collections/table_view.html"
    model_config = None  # To be set dynamically based on the model
    paginate_by = 20

    def get_context_data(self, **kwargs):
        from django.urls import NoReverseMatch

        context = super().get_context_data(**kwargs)
        context["registry"] = registry
        # context["collection_menu"] = AppMenu.get("Data Collections")
        context["export_choices"] = export_choices

        # Determine collection type (sample or measurement)
        is_sample = self.model in registry.samples
        is_measurement = self.model in registry.measurements

        context["collection_type"] = "sample" if is_sample else "measurement"
        context["collection_type_verbose"] = "Sample" if is_sample else "Measurement"

        # Get all available collections of this type
        collection_models = registry.samples if is_sample else registry.measurements
        collection_list = []

        for model_class in collection_models:
            config = registry.get_for_model(model_class)
            slug = config.get_slug()
            try:
                url = reverse(f"{slug}-collection")
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
        context["current_model_verbose_name_plural"] = self.model_config.get_verbose_name_plural()

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
        return {
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

    @classmethod
    def get_urls(cls, **kwargs):
        """
        Return the URLs for the table view.
        """
        if not registry.samples and not registry.measurements:
            # In case there are no samples or measurements registered, return an empty list.
            return [], None
        urls = []

        # Process sample models
        for model_class in registry.samples:
            config = registry.get_for_model(model_class)
            slug = config.get_slug()
            urls.append(
                path(
                    f"samples/{slug}/",
                    cls.as_view(model=model_class, model_config=config, **kwargs),
                    name=f"{slug}-collection",
                )
            )

        # Process measurement models
        for model_class in registry.measurements:
            config = registry.get_for_model(model_class)
            slug = config.get_slug()
            urls.append(
                path(
                    f"measurements/{slug}/",
                    cls.as_view(model=model_class, model_config=config, **kwargs),
                    name=f"{slug}-collection",
                )
            )

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
            try:
                total_samples += sample_model.objects.count()
            except Exception:
                pass

        for measurement_model in registry.measurements:
            try:
                total_measurements += measurement_model.objects.count()
            except Exception:
                pass

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
                logger.warning(f"Failed to add sample type {sample_model.__name__}: {e}")

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
                logger.warning(f"Failed to add measurement type {measurement_model.__name__}: {e}")

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
                logger.warning(f"Failed to add sample type {sample_model.__name__}: {e}")

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
                logger.warning(f"Failed to add measurement type {measurement_model.__name__}: {e}")

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
