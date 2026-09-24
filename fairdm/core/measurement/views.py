"""Views for the Measurement app."""

from django.http import Http404
from django.utils.translation import gettext as _

from fairdm.views import FairDMDetailView

from . import overview
from .models import Measurement


class MeasurementDetailView(FairDMDetailView):
    """A measurement's own page, at its permanent address.

    Drawn from ``measurement/measurement_overview.html``, which reads only the base
    ``Measurement`` model and the registry's description of its type. A measurement type adds its
    own content by providing ``<app_label>/<model_name>_overview.html``, extending that template
    and filling its blocks — see :meth:`get_template_names`.

    A measurement follows its own dataset: anyone may open it once that dataset is public and
    published, and otherwise only the dataset's team. Anyone else gets a 404, so the address never
    confirms that the measurement exists.
    """

    model = Measurement
    context_object_name = "measurement"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    def get_object(self, queryset=None):
        measurement = super().get_object(queryset)
        if not overview.measurement_is_visible(self.request, measurement):
            raise Http404(_("No measurement matches the given query."))
        return measurement

    def get_template_names(self):
        """The most specific overview template the measurement's own type chain provides.

        Walks the class hierarchy from the measurement's type up to ``Measurement``, so a type
        provides ``<app_label>/<model_name>_overview.html`` and a subtype of it inherits that
        page until it provides its own.
        """
        names = []
        for cls in type(self.object).__mro__:
            if cls is Measurement:
                break
            if isinstance(cls, type) and issubclass(cls, Measurement) and not cls._meta.abstract:
                names.append(f"{cls._meta.app_label}/{cls._meta.model_name}_overview.html")
        return [*names, "measurement/measurement_overview.html"]

    def get_page_title(self):
        return self.object.name

    def get_breadcrumbs(self):
        """Project › dataset › sample › this measurement: the path a reader came down."""
        measurement = self.object
        dataset = measurement.dataset
        crumbs = []
        if dataset.project_id:
            crumbs.append({"text": str(dataset.project), "href": dataset.project.get_absolute_url()})
        crumbs.append({"text": str(dataset), "href": dataset.get_absolute_url()})
        crumbs.append({"text": str(measurement.sample), "href": measurement.sample.get_absolute_url()})
        crumbs.append({"text": self.get_page_title()})
        return crumbs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(overview.build(self.request, self.object))
        return context
