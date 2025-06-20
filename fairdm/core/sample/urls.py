from django.urls import include, path

from fairdm import plugins

urlpatterns = [
    path("samples/<str:uuid>/", include((plugins.sample.get_urls(), "sample"))),
]
