from django.urls import include, path

from .views import (
    DatasetCreateView,
    DatasetDetailView,
    DatasetListView,
)

urlpatterns = [
    path("datasets/create/", DatasetCreateView.as_view(), name="dataset-create"),
    path("datasets/", DatasetListView.as_view(), name="dataset-list"),
    path("dataset/<str:uuid>/", include((DatasetDetailView.get_urls(), "dataset"))),
]
