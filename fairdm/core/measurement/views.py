"""Views for measurements."""

from django.views.generic import DetailView

from .models import Measurement


class MeasurementDetailView(DetailView):
    """Placeholder detail page showing a measurement's name, UUID and links to its dataset and sample."""

    model = Measurement
    template_name = "measurement/detail.html"
    context_object_name = "measurement"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
