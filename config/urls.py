"""URL configuration for the demo portal."""

from django.urls import include, path

urlpatterns = [
    path("", include("fairdm.conf.urls")),
]
