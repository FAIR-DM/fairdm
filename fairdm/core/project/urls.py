from django.urls import include, path

from fairdm import plugins

from .views import ProjectCreateView, ProjectListView

urlpatterns = [
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("projects/create/", ProjectCreateView.as_view(), name="project-create"),
    path("project/<str:uuid>/", include(plugins.project.get_urls())),
]
