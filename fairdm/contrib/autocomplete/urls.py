"""URL configuration for autocomplete app."""

from django.urls import path

from .views import ConceptAutocomplete, ContributorAutocomplete, OrganizationAutocomplete

app_name = "autocomplete"

urlpatterns = [
    path("concept/", ConceptAutocomplete.as_view(), name="concept"),
    path("contributor/", ContributorAutocomplete.as_view(), name="contributor"),
    path("organization/", OrganizationAutocomplete.as_view(), name="organization"),
]
