"""Views for the Sample app."""

from django.views.generic import DetailView

from fairdm.views import FairDMBaseMixin

from .models import Sample


class SampleDetailView(FairDMBaseMixin, DetailView):
    """Detail view for Sample model with plugin support.

    This view displays a sample and makes plugin URLs available.
    """

    model = Sample
    template_name = "sample/sample_detail.html"
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    context_object_name = "sample"
