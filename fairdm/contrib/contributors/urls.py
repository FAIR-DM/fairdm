"""URL configuration for contributors."""

from django.urls import include, path

from fairdm.plugins import registry

from .models import Contributor
from .views.claiming import ClaimProfileConfirmView, ClaimProfileView
from .views.organization import OrganizationListView
from .views.person import PersonListView
from .views.team import TeamView

# The portal includes this module without a namespace. The claim pages keep the
# ``contributors`` one that the administration's claim link and the confirmation form reverse.
_claim_patterns = [
    path("<str:token>/", ClaimProfileView.as_view(), name="claim-profile"),
    path(
        "<str:token>/confirm/",
        ClaimProfileConfirmView.as_view(),
        name="claim-profile-confirm",
    ),
]

urlpatterns = [
    path("claim/", include((_claim_patterns, "contributors"))),
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
