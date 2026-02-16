from django.urls import URLPattern

# from django.urls import path

# from .views import DatasetPackageDownloadView, MetadataDownloadView

# urlpatterns = [
#     path("dataset/<str:uuid>/package/", DatasetPackageDownloadView.as_view(), name="dataset-download"),
#     path("dataset/<str:uuid>/metadata/", MetadataDownloadView.as_view(), name="dataset-metadata-download"),
# ]
urlpatterns: list[URLPattern] = []
