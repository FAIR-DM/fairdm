from django.urls import include, path

from fairdm.plugins import registry

from .models import Dataset
from .views import DatasetCreateView, DatasetListView

urlpatterns = [
    path("datasets/", DatasetListView.as_view(), name="dataset-list"),
    # Declared ahead of the record include below: Django matches in declaration order, and a
    # route declared after it would have `create` swallowed as a `uuid` (014 plan P2, T057).
    path("datasets/create/", DatasetCreateView.as_view(), name="dataset-create"),
    # The dataset's own page and its registered pages (overview, its update page, descriptions,
    # its deletion page, keywords and key dates) sit under the plural address every other page in
    # this feature uses, replacing the singular `dataset/<uuid>/` mount this include used to have
    # (014 plan P2, research.md R3). `Overview`'s `Update` extra view answers `update` (US-3) and
    # `Delete` answers `delete` (US-6), retiring the standalone `dataset-update`/`dataset-delete`
    # routes this include used to carry.
    path(
        "datasets/<str:uuid>/",
        include((registry.get_urls_for_model(Dataset), "dataset")),
    ),
]
