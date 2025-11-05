from django.urls import include, path

from .views import SampleDetailView

urlpatterns = [
    path("samples/<str:uuid>/", include((SampleDetailView.get_urls(), "sample"))),
]
