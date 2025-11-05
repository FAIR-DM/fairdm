from django.urls import include, path

from .views import ProjectCreateView, ProjectDetailPage, ProjectListView

urlpatterns = [
    path("projects/", ProjectListView.as_view(), name="project-list"),
    path("projects/create/", ProjectCreateView.as_view(), name="project-create"),
    path("project/<str:uuid>/", include((ProjectDetailPage.get_urls(), "project"))),
]
