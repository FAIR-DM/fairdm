"""URL configuration for autocomplete app."""

from django.urls import path

from .views import (
    SCOPES,
    TAG_SCOPES,
    ConceptAutocomplete,
    DatasetAutocompleteView,
    MeasurementAutocompleteView,
    OrganizationAutocompleteView,
    PersonAutocompleteView,
    ProjectAutocompleteView,
    PublicationAutocompleteView,
    RorAutocompleteView,
    SampleAutocompleteView,
    TagAutocompleteView,
)

app_name = "autocomplete"

urlpatterns = [
    path("concept/", ConceptAutocomplete.as_view(), name="concept"),
]

#: The record views, by the kind of record they offer.
RECORD_VIEWS = {
    "project": ProjectAutocompleteView,
    "dataset": DatasetAutocompleteView,
    "sample": SampleAutocompleteView,
    "measurement": MeasurementAutocompleteView,
}

for _kind, _view in RECORD_VIEWS.items():
    for _scope in SCOPES:
        urlpatterns.append(
            path(
                f"records/{_kind}/{_scope}/",
                _view.for_scope(_scope).as_view(),
                name=f"{_kind}-{_scope}",
            )
        )

#: The views behind the person and organization fields. Nothing about them varies by scope.
CONTRIBUTOR_VIEWS = {
    "person": PersonAutocompleteView,
    "organization": OrganizationAutocompleteView,
}

for _kind, _view in CONTRIBUTOR_VIEWS.items():
    urlpatterns.append(
        path(f"records/{_kind}/", _view.as_view(), name=f"{_kind}-public")
    )

urlpatterns.append(
    path("publication/", PublicationAutocompleteView.as_view(), name="publication")
)

for _scope in TAG_SCOPES:
    urlpatterns.append(
        path(
            f"tags/{_scope}/",
            TagAutocompleteView.for_scope(_scope).as_view(),
            name=f"tag-{_scope}",
        )
    )

urlpatterns.append(path("ror/", RorAutocompleteView.as_view(), name="ror"))
