"""URL configuration for autocomplete app."""

from django.urls import path

from . import records, sketch_pages
from .views import (
    ConceptAutocomplete,
    ContributorAutocomplete,
    OrganizationAutocomplete,
)

app_name = "autocomplete"

urlpatterns = [
    path("concept/", ConceptAutocomplete.as_view(), name="concept"),
    path("contributor/", ContributorAutocomplete.as_view(), name="contributor"),
    path("organization/", OrganizationAutocomplete.as_view(), name="organization"),
]

# SKETCH ONLY: one address per record kind and scope, so a request can never widen its scope.
_record_views = {
    "project": records.ProjectAutocomplete,
    "dataset": records.DatasetAutocomplete,
    "sample": records.SampleAutocomplete,
    "measurement": records.MeasurementAutocomplete,
}
for _kind, _view in _record_views.items():
    for _scope in ("public", "view", "edit"):
        urlpatterns.append(
            path(
                f"records/{_kind}/{_scope}/",
                _view.as_view(scope=_scope),
                name=f"{_kind}-{_scope}",
            )
        )
for _kind, _view in {
    "person": records.PersonAutocomplete,
    "organization": records.OrganizationAutocomplete,
    "publication": records.PublicationAutocomplete,
}.items():
    for _scope in ("public", "view", "edit"):
        urlpatterns.append(
            path(
                f"records/{_kind}/{_scope}/", _view.as_view(), name=f"{_kind}-{_scope}"
            )
        )

urlpatterns += [
    path("records/tags/", records.TagAutocomplete.as_view(), name="tags"),
    path(
        "sketch/new-sample/",
        sketch_pages.SketchNewSample.as_view(),
        name="sketch-new-sample",
    ),
    path(
        "sketch/new-measurement/",
        sketch_pages.SketchNewMeasurement.as_view(),
        name="sketch-new-measurement",
    ),
]
