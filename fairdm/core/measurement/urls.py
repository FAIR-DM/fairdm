"""URL routes for the measurement pages."""

from django.urls import include, path, re_path

from fairdm.plugins import registry

from .models import Measurement
from .views import FormerAddressRedirect

app_name = "measurement"

urlpatterns = [
    path("measurements/<str:uuid>/", include(registry.get_urls_for_model(Measurement))),
    re_path(
        r"^measurement/(?P<uuid>[^/]+)/(?P<rest>.*)$",
        FormerAddressRedirect.as_view(),
        name="former-address",
    ),
]
