from django.urls import include, path

from fairdm.plugins import registry

from .models import Dataset
from .views import (
    DatasetCreateView,
    DatasetListView,
)

urlpatterns = [
    path("datasets/create/", DatasetCreateView.as_view(), name="dataset-create"),
    path("datasets/", DatasetListView.as_view(), name="dataset-list"),
    path("dataset/<str:uuid>/", include((registry.get_urls_for_model(Dataset), "dataset"))),
]
