"""Views for locations."""

from fairdm.views import FairDMDetailView

from .models import Point


class PointDetailView(FairDMDetailView):
    """Show a location, found by its longitude and latitude."""

    model = Point
    template_name = "locations/location_detail.html"

    def get_object(self, queryset=None):
        """Look the point up by the ``lon`` and ``lat`` URL parts."""
        return Point.objects.get(x=self.kwargs["lon"], y=self.kwargs["lat"])

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
