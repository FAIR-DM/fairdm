"""A URL layout that mounts the project pages under another prefix."""

from django.urls import include, path, re_path

from fairdm.views.permalink import PORTAL_ID_PATTERN, PermalinkView

urlpatterns = [
    path("records/", include("fairdm.core.project.urls")),
    re_path(
        rf"^(?P<portal_id>{PORTAL_ID_PATTERN})/$",
        PermalinkView.as_view(),
        name="permalink",
    ),
]
