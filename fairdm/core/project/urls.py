from django.urls import include, path

from fairdm.plugins import registry

from .models import Project
from .views import ProjectCreateView, ProjectDetailView, ProjectListView, ProjectUpdateView

urlpatterns = [
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("projects/create/", ProjectCreateView.as_view(), name="project-create"),
    path("projects/<str:uuid>/", ProjectDetailView.as_view(), name="project-detail"),
    path("projects/<str:uuid>/edit/", ProjectUpdateView.as_view(), name="project-update"),
    path("project/<str:uuid>/", include((registry.get_view_for_model(Project).get_urls(), "project"))),
]
