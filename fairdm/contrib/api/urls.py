from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers

from . import viewsets
from .views import IdentitityAPIView, MeasurementMetadataView, TOSView

# ============= BASE ROUTERS =============
router = routers.SimpleRouter()
router.register("project", viewsets.ProjectViewset)
router.register("dataset", viewsets.DatasetViewset)

for viewset in viewsets.sample_viewsets:
    router.register(
        f"samples/{viewset.queryset.model._meta.model_name}",
        viewset,
    )
for viewset in viewsets.measurement_viewsets:
    router.register(
        f"measurements/{viewset.queryset.model._meta.model_name}",
        viewset,
    )

app_name = "api"
urlpatterns = [
    path(
        "",
        SpectacularSwaggerView.as_view(template_name="fairdm/pages/spectacular.html", url_name="api:schema"),
        name="swagger-ui",
    ),
    path("", include(router.urls)),
    path("identity/", IdentitityAPIView.as_view(), name="identity"),
    path("measurements/", MeasurementMetadataView.as_view(), name="measurement-metadata"),
    path("", include("fairdm.contrib.contributors.api.urls")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("tos/", TOSView.as_view(), name="tos"),
    # path("auth/", include("rest_framework.urls", namespace="rest_framework")),
    # path("auth/", include("dj_rest_auth.urls")),
    # path("auth/register/", include("dj_rest_auth.registration.urls")),
]
