"""Plugin pages for measurements.

A measurement has its own page at its permanent address, ``/measurement/<uuid>/``, in the same
tabbed detail view as projects, datasets and samples. The overview is its first tab, and a portal
adds further tabs by registering plugins against ``Measurement`` here or in its own app.
"""

from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.plugins.access import has_perm
from fairdm.core.plugins import TypedOverviewPlugin

from . import overview
from .models import Measurement


@plugins.register(Measurement, label=_("Overview"), icon="view", order=0)
class Overview(TypedOverviewPlugin):
    """The measurement's own page, drawn from ``measurement/measurement_overview.html``, which
    reads only the base ``Measurement`` model and the registry's description of its type. A
    measurement type adds its own content with ``<app_label>/<model_name>_overview.html``; see
    :class:`TypedOverviewPlugin`."""

    base_model = Measurement
    fallback_template = "measurement/measurement_overview.html"
    # The root of the measurement's address, as the project and dataset overviews are. Left unset
    # the plugin base would mount it at `overview/` and move the permanent address.
    url_path = None

    def get_page_title(self):
        return self.base_object.name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["measurement"] = self.base_object
        context.update(
            overview.build(
                self.request,
                self.base_object,
                can_manage=has_perm(
                    self.request, "dataset.change_dataset", self.base_object.dataset
                ),
            )
        )
        return context
