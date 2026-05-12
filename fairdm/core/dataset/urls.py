from django.urls import include, path

from fairdm.plugins import registry

from .models import Dataset
from .views import (
    DatasetCreateView,
    DatasetDeleteView,
    DatasetDetailView,
    DatasetListView,
    DatasetUpdateView,
)

urlpatterns = [
    path("datasets/", DatasetListView.as_view(), name="dataset-list"),
    path("datasets/create/", DatasetCreateView.as_view(), name="dataset-create"),
    path("datasets/<str:uuid>/", DatasetDetailView.as_view(), name="dataset-detail"),
    path("datasets/<str:uuid>/update/", DatasetUpdateView.as_view(), name="dataset-update"),
    path("datasets/<str:uuid>/delete/", DatasetDeleteView.as_view(), name="dataset-delete"),
    path("dataset/<str:uuid>/", include((registry.get_urls_for_model(Dataset), "dataset"))),
]
