"""URL configuration for import and export."""

from django.urls import URLPattern, path

from .views import TableSchemaView

urlpatterns: list[URLPattern] = [
    path(
        "table-schemas/<slug:name>/",
        TableSchemaView.as_view(),
        name="table_schema",
    ),
]
