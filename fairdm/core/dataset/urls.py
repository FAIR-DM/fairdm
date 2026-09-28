"""URL routes for the dataset list, create and record pages."""

from django.urls import include, path

from fairdm.plugins import registry

from .models import Dataset
from .views import DatasetCreateView, DatasetListView

urlpatterns = [
    path("datasets/", DatasetListView.as_view(), name="dataset-list"),
    # Declared before the record include, or `create` would be matched as a `uuid`.
    path("datasets/create/", DatasetCreateView.as_view(), name="dataset-create"),
    path(
        "datasets/<str:uuid>/",
        include((registry.get_urls_for_model(Dataset), "dataset")),
    ),
]
