from django.urls import include, path

from fairdm import plugins

from .views import (
    DatasetCreateView,
    DatasetListView,
)

urlpatterns = [
    path("datasets/create/", DatasetCreateView.as_view(), name="dataset-create"),
    path("datasets/", DatasetListView.as_view(), name="dataset-list"),
    path("dataset/<str:uuid>/", include(plugins.dataset.get_urls())),
]
