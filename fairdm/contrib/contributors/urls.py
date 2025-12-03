from django.urls import include, path

from fairdm.plugins import registry

from .models import Contributor
from .views import CommunityDashboardView
from .views.organization import OrganizationListView
from .views.person import (
    ActiveMemberListView,
    ContributorListView,
    PersonCreateView,
    PortalTeamView,
)

urlpatterns = [
    path(
        "community/",
        include(
            [
                path("", CommunityDashboardView.as_view(), name="community-dashboard"),
                path("portal-team/", PortalTeamView.as_view(), name="portal-team"),
                path("active-members/", ActiveMemberListView.as_view(), name="active-member-list"),
                path("contributors/", ContributorListView.as_view(), name="person-list"),
                path("organizations/", OrganizationListView.as_view(), name="organization-list"),
                path("add-person/", PersonCreateView.as_view(), name="person-create"),
            ]
        ),
    ),
    path("contributor/<str:uuid>/", include((registry.get_view_for_model(Contributor).get_urls(), "contributor"))),
]
