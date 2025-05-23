from django.urls import include, path

from fairdm.views import FairDMListView

from . import plugins
from .models import Sample

urlpatterns = [
    # path("projects/create/", ProjectCreateView.as_view(), name="project-create"),
    path("projects/", FairDMListView.as_view(model=Sample), name="project-list"),
    path("project/<str:uuid>/", include(plugins.registry.get_urls())),
]
