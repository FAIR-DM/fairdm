"""URL routes for the project list, create and record pages."""

from django.urls import include, path

from fairdm.plugins import registry

from .models import Project
from .views import ProjectCreateView, ProjectListView

urlpatterns = [
    path("projects/", ProjectListView.as_view(), name="project-list"),
    # Declared before the record include, or `create` would be matched as a `uuid`.
    path("projects/create/", ProjectCreateView.as_view(), name="project-create"),
    path(
        "projects/<str:uuid>/",
        include((registry.get_urls_for_model(Project), "project")),
    ),
]
