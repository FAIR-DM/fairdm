from django.urls import include, path

from fairdm.plugins import registry

from .models import Sample

urlpatterns = [
    path("samples/<str:uuid>/", include((registry.get_urls_for_model(Sample), "sample"))),
]
