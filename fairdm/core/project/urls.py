from django.urls import include, path

from fairdm.plugins import registry

from .models import Project
from .views import ProjectCreateView, ProjectListView

urlpatterns = [
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("projects/create/", ProjectCreateView.as_view(), name="project-create"),
    path("project/<str:uuid>/", include((registry.get_view_for_model(Project).get_urls(), "project"))),
]
