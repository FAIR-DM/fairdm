from django.urls import include, path

from fairdm import plugins

from .views import ContributorContactView
from .views.account import UpdateAffiliations, UpdateIdentifiers, UpdateProfile
from .views.organization import OrganizationCreateView, OrganizationListView
from .views.person import ActiveMemberListView, ContributorListView, PersonCreateView, PortalTeamView

account = [
    path("profile/", UpdateProfile.as_view(), name="contributor-profile"),
    path("identifiers/", UpdateIdentifiers.as_view(), name="contributor-identifiers"),
    path("affiliations/", UpdateAffiliations.as_view(), name="contributor-affiliations"),
]


urlpatterns = [
    path("account/", include(account)),
    path(
        "community/",
        include(
            [
                path("portal-team/", PortalTeamView.as_view(), name="portal-team"),
                path("active-members/", ActiveMemberListView.as_view(), name="active-member-list"),
                path("contributors/", ContributorListView.as_view(), name="contributor-list"),
                path("organizations/", OrganizationListView.as_view(), name="organization-list"),
                path("add-person/", PersonCreateView.as_view(), name="person-create"),
            ]
        ),
    ),
    path("contributor/<str:uuid>/", include((plugins.contributor.get_urls(), "contributor"))),
    path("contributor/<str:uuid>/contact/", ContributorContactView.as_view(), name="contributor-contact"),
    path("organization/new/", OrganizationCreateView.as_view(), name="organization-add"),
]
