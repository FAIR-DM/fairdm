"""Views for the Measurement app."""

from django.views.generic import DetailView

from .models import Measurement


class MeasurementDetailView(DetailView):
    """Placeholder detail view for Measurement model.

    Displays basic measurement information including name, UUID, and links to
    related dataset and sample. Full detail view implementation is deferred to
    a future feature.

    Template: measurement/detail.html
    Context:
        measurement: The Measurement instance (via DetailView's 'object')
    """

    model = Measurement
    template_name = "measurement/detail.html"
    context_object_name = "measurement"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
