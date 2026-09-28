"""URL routes for the measurement pages."""

from django.urls import path

from .views import MeasurementDetailView

app_name = "measurement"

urlpatterns = [
    path(
        "<str:uuid>/",
        MeasurementDetailView.as_view(),
        name="overview",
    ),
]
