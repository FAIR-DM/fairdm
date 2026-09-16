from django.urls import include, path

from fairdm.plugins import registry

from .models import Contributor

# from .views.claiming import ClaimProfileConfirmView, ClaimProfileView
from .views.organization import OrganizationListView
from .views.person import PersonListView
from .views.team import TeamView

urlpatterns = [
    # path("claim/<str:token>/", ClaimProfileView.as_view(), name="claim-profile"),
    # path("claim/<str:token>/confirm/", ClaimProfileConfirmView.as_view(), name="claim-profile-confirm"),
    path(
        "community/",
        include(
            [
                path("people/", PersonListView.as_view(), name="people-list"),
                path(
                    "organizations/",
                    OrganizationListView.as_view(),
                    name="organization-list",
                ),
                path("team/", TeamView.as_view(), name="team"),
            ]
        ),
    ),
    path(
        "contributor/<str:uuid>/",
        include((registry.get_urls_for_model(Contributor), "contributor")),
    ),
]
