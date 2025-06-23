from django.urls import include, path

from fairdm import plugins

from .views import ContributorContactView
from .views.edit import UpdateAffiliations, UpdateIdentifiers, UpdateProfile
from .views.generic import (
    ContributorRolesAutocomplete,
    OrganizationAutocomplete,
    PersonAutocomplete,
)
from .views.organization import OrganizationCreateView, OrganizationListView, OrgRORCreateView
from .views.person import ActiveMemberListView, ContributorListView, PortalTeamView

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
            ]
        ),
    ),
    path("contributor/<str:uuid>/", include((plugins.contributor.get_urls(), "contributor"))),
    path("contributor/<str:uuid>/contact/", ContributorContactView.as_view(), name="contributor-contact"),
    path("organization/add/", OrganizationCreateView.as_view(), name="create"),
    path("organization/add/ror/", OrgRORCreateView.as_view(), name="ror-create"),
    path("contributors/person-autocomplete/", PersonAutocomplete.as_view(), name="person-autocomplete"),
    path(
        "contributors/organization-autocomplete/", OrganizationAutocomplete.as_view(), name="organization-autocomplete"
    ),
    path("contributors/roles-autocomplete/", ContributorRolesAutocomplete.as_view(), name="roles-autocomplete"),
]
