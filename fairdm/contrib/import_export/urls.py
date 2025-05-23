from django.urls import path

from .views import DataExportView, DataImportView, DatasetPackageDownloadView, MetadataDownloadView

urlpatterns = [
    path("dataset/<str:uuid>/import/", DataImportView.as_view(), name="dataset-import-view"),
    path("dataset/<str:uuid>/export/", DataExportView.as_view(), name="dataset-export-view"),
    path("dataset/<str:uuid>/package/", DatasetPackageDownloadView.as_view(), name="dataset-download"),
    path("dataset/<str:uuid>/metadata/", MetadataDownloadView.as_view(), name="dataset-metadata-download"),
    # path("dataset/<str:uuid>/upload/", DatasetUpload.as_view(), name="dataset-upload"),
]
