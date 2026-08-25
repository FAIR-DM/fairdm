from django.urls import include, path

from fairdm.plugins import registry

from .models import Dataset
from .views import DatasetCreateView, DatasetDeleteView, DatasetListView

urlpatterns = [
    path("datasets/", DatasetListView.as_view(), name="dataset-list"),
    # Declared ahead of the record include below: Django matches in declaration order, and a
    # route declared after it would have `create` swallowed as a `uuid` (014 plan P2, T057).
    path("datasets/create/", DatasetCreateView.as_view(), name="dataset-create"),
    # The standalone delete page stays at its own address for now (014 T056): `Overview`'s
    # `Update` extra view answers `update` (US-3); `Delete` is appended when US-6 builds it.
    path(
        "datasets/<str:uuid>/delete/",
        DatasetDeleteView.as_view(),
        name="dataset-delete",
    ),
    # The dataset's own page and its registered pages (overview, its update page, descriptions,
    # keywords and key dates) sit under the plural address every other page in this feature uses,
    # replacing the singular `dataset/<uuid>/` mount this include used to have (014 plan P2,
    # research.md R3).
    path(
        "datasets/<str:uuid>/",
        include((registry.get_urls_for_model(Dataset), "dataset")),
    ),
]
