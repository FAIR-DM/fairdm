from django.urls import include, path

from .plugins import plugins
from .views import PointDetailView

urlpatterns = [
    path("loc/<str:pk>/", include(plugins.get_urls("location"))),
    path("location/<str:lon>/<str:lat>/", PointDetailView.as_view(), name="point-detail"),
]
