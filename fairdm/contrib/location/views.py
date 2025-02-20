from fairdm.views import FairDMDetailView

from .models import Point
from .plugins import LocationDetailMenu


class PointDetailView(FairDMDetailView):
    model = Point
    template_name = "locations/location_detail.html"
    menu = LocationDetailMenu

    def get_object(self, queryset=None):
        return Point.objects.get(x=self.kwargs["lon"], y=self.kwargs["lat"])

    def user_can_edit(self):
        return False
