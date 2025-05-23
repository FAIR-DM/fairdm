from django.urls import path

# from fairdm.plugins import plugins
from .views import PointDetailView

urlpatterns = [
    # path("loc/<str:uuid>/", include(plugins["location"].get_urls())),
    path("location/<str:lon>/<str:lat>/", PointDetailView.as_view(), name="point-detail"),
]
