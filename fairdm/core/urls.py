from django.urls import include, path

urlpatterns = [
    path("", include("fairdm.core.project.urls")),
    path("", include("fairdm.core.dataset.urls")),
    path("", include("fairdm.core.sample.urls")),
    # path("", include("fairdm.core.measurement.urls")),
]
