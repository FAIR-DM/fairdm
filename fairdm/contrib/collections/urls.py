from django.urls import include, path

from .views import DataTableView

urlpatterns = [
    path("collections/", include(DataTableView.get_urls()[0])),
]
