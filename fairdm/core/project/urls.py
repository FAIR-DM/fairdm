from django.urls import include, path

from fairdm.plugins import registry

from .models import Project
from .views import ProjectCreateView, ProjectListView

urlpatterns = [
    path("projects/", ProjectListView.as_view(), name="project-list"),
    # Declared ahead of the record include below: Django matches in declaration order, and a
    # route declared after it would have `create` swallowed as a `uuid` (T093, 013 plan P5).
    path("projects/create/", ProjectCreateView.as_view(), name="project-create"),
    path(
        "projects/<str:uuid>/",
        include((registry.get_urls_for_model(Project), "project")),
    ),
]
