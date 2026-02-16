from django.urls import include, path

from .views import MeasurementDetailView

urlpatterns = [
    path(
        "measurements/<str:uuid>/",
        include((MeasurementDetailView.get_urls(), "measurement")),
    ),
]
