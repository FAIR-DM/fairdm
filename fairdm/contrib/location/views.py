"""Views for locations."""

from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404

from fairdm.views import FairDMDetailView

from .models import Point


class PointDetailView(FairDMDetailView):
    """Show a location, found by its longitude and latitude."""

    model = Point
    template_name = "locations/location_detail.html"

    def get_object(self, queryset=None):
        """Look the point up by the ``lon`` and ``lat`` URL parts, or answer 404."""
        try:
            return get_object_or_404(Point, x=self.kwargs["lon"], y=self.kwargs["lat"])
        except ValidationError as error:
            # Not a pair of numbers, so it is no location's address.
            raise Http404 from error

    def get_context_data(self, **kwargs):
        """Add the samples taken at the location that the viewer may see."""
        context = super().get_context_data(**kwargs)
        context["samples"] = self.object.samples.visible_to(
            self.request.user
        ).select_related("dataset")
        return context

    def user_can_edit(self):
        """Never offer editing."""
        return False
