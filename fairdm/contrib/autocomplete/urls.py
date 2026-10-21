"""URL configuration for autocomplete app."""

from django.urls import path

from .views import (
    ConceptAutocomplete,
    ContributorAutocomplete,
    DatasetAutocompleteView,
    OrganizationAutocomplete,
)

app_name = "autocomplete"

urlpatterns = [
    path("concept/", ConceptAutocomplete.as_view(), name="concept"),
    path("contributor/", ContributorAutocomplete.as_view(), name="contributor"),
    path("organization/", OrganizationAutocomplete.as_view(), name="organization"),
]

#: The record views, by the kind of record they offer.
RECORD_VIEWS = {"dataset": DatasetAutocompleteView}

#: Scope is part of the address, so a request can never widen what an address offers.
SCOPES = ("public", "view", "edit")

for _kind, _view in RECORD_VIEWS.items():
    for _scope in SCOPES:
        urlpatterns.append(
            path(
                f"records/{_kind}/{_scope}/",
                _view.for_scope(_scope).as_view(),
                name=f"{_kind}-{_scope}",
            )
        )
