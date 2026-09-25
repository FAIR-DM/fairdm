from django.urls import include, path

from fairdm.plugins import registry

from .models import Measurement

app_name = "measurement"

urlpatterns = [
    path("<str:uuid>/", include(registry.get_urls_for_model(Measurement))),
]
