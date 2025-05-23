from django.urls import include, path

from .views import (
    DataTableView,
)

urlpatterns = [
    path("", include("fairdm.core.project.urls")),
    path("", include("fairdm.core.dataset.urls")),
    path("", include("fairdm.core.sample.urls")),
    # path("", include("fairdm.core.measurement.urls")),
    path("data/collections/", DataTableView.as_view(), name="data-table"),
]
