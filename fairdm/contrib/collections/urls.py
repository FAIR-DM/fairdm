from django.urls import include, path

from .views import (
    CollectionsOverview,
    DataTableView,
    MeasurementsOverview,
    SamplesOverview,
)

urlpatterns = [
    path("collections/", CollectionsOverview.as_view(), name="data-collections"),
    path("collections/samples/", SamplesOverview.as_view(), name="samples-overview"),
    path(
        "collections/measurements/",
        MeasurementsOverview.as_view(),
        name="measurements-overview",
    ),
    path("collections/", include(DataTableView.get_urls()[0])),
]
