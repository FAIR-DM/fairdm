from django.urls import include, path

from fairdm.plugins import registry

from .models import Dataset
from .views import (
    DatasetCreateView,
    DatasetDeleteView,
    DatasetListView,
    DatasetUpdateView,
)

urlpatterns = [
    path("datasets/", DatasetListView.as_view(), name="dataset-list"),
    # Declared ahead of the record include below: Django matches in declaration order, and a
    # route declared after it would have `create` swallowed as a `uuid` (014 plan P2, T057).
    path("datasets/create/", DatasetCreateView.as_view(), name="dataset-create"),
    # The standalone update and delete pages stay at their own addresses for now (014 T056):
    # `Overview.extra_views` is empty until the runs that build their replacements as additional
    # views append them (US-3, US-6), and there is no route without a page behind it.
    path(
        "datasets/<str:uuid>/update/",
        DatasetUpdateView.as_view(),
        name="dataset-update",
    ),
    path(
        "datasets/<str:uuid>/delete/",
        DatasetDeleteView.as_view(),
        name="dataset-delete",
    ),
    # The dataset's own page and its registered pages (currently descriptions, keywords and key
    # dates) now sit under the plural address every other page in this feature uses, replacing
    # the singular `dataset/<uuid>/` mount this include used to have (014 plan P2, research.md R3).
    path(
        "datasets/<str:uuid>/",
        include((registry.get_urls_for_model(Dataset), "dataset")),
    ),
]
