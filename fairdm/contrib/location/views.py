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

    def user_can_edit(self):
        """Never offer editing."""
        return False
