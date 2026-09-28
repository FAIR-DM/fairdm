"""URL configuration for locations."""

from django.urls import include, path

from fairdm.plugins import registry

from .models import Point
from .views import PointDetailView

# A location has no uuid, so its coordinate pair is declared as its address for the plugin routes.
registry.declare_addressing(
    Point,
    route="<str:lon>/<str:lat>",
    lookup={"lon": "x", "lat": "y"},
)

urlpatterns = [
    path(
        "location/<str:lon>/<str:lat>/",
        PointDetailView.as_view(),
        name="point-detail",
    ),
    path(
        f"location/{registry.route_for(Point)}/",
        include((registry.get_urls_for_model(Point), "point")),
    ),
]
