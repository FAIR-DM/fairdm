from django.urls import include, path

from .views import (
    CollectionRedirectView,
    DataTableView,
)

urlpatterns = [
    path("data/collections.html", CollectionRedirectView.as_view(), name="data-collections"),
    path("", include(DataTableView.get_urls())),
    path("", include("fairdm.core.project.urls")),
    path("", include("fairdm.core.dataset.urls")),
    path("", include("fairdm.core.sample.urls")),
    # path("", include("fairdm.core.measurement.urls")),
]
