"""The map of sample locations shown beside a record's overview."""

from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.contributors.models import Contributor
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins.mixins import PrivateRecordNotFoundMixin
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.views import FairDMTemplateView


def record_is_visible(request, obj):
    """Return whether the request's user may open the record the map belongs to.

    Args:
        request: The current request.
        obj: The project, dataset, sample or contributor, or ``None`` when none was resolved.

    Returns:
        True when the map may be shown.
    """
    from fairdm.core.dataset.plugins import dataset_is_visible
    from fairdm.core.project.plugins import project_is_visible

    if isinstance(obj, Project):
        return project_is_visible(request, obj)
    if isinstance(obj, Sample):
        obj = obj.dataset
    if isinstance(obj, Dataset):
        if obj.project is not None and not project_is_visible(request, obj.project):
            return False
        return dataset_is_visible(request, obj)
    return True


@plugins.register(
    Project, Dataset, Sample, Contributor, label=_("Map"), icon="map", order=300
)
class SampleMap(PrivateRecordNotFoundMixin, Plugin, FairDMTemplateView):
    """Plot a set of samples as points, one point per location.

    The set depends on the page: a dataset's samples, the samples of a project's datasets, the
    one sample, or the samples of the public datasets a person or organization is credited on.
    The map has no settings and no extension points. An addon that wants a richer one removes
    this plugin and registers its own.
    """

    name = "map"
    page_title = _("Map")
    template_name = "locations/sample_map.html"
    check = staticmethod(record_is_visible)

    def get_samples(self):
        """Return the samples this page's map is drawn from, already limited to the viewer.

        Returns:
            A queryset of samples with their locations loaded.
        """
        from fairdm.core.dataset.plugins import dataset_is_visible

        record = self.base_object
        samples = Sample.objects.select_related("location")
        if isinstance(record, Sample):
            return samples.filter(pk=record.pk)
        if isinstance(record, Dataset):
            return samples.filter(dataset=record)
        if isinstance(record, Project):
            datasets = [
                dataset.pk
                for dataset in Dataset.all_objects.filter(project=record)
                if dataset_is_visible(self.request, dataset)
            ]
            return samples.filter(dataset__in=datasets)
        return samples.filter(dataset__in=record.datasets.get_visible())

    def get_context_data(self, **kwargs):
        """Add the points and the counts the page states beside them."""
        context = super().get_context_data(**kwargs)
        record = self.base_object
        points, unplotted = {}, 0
        for sample in self.get_samples():
            location = sample.location
            if location is None or not (
                -90 <= location.y <= 90 and -180 <= location.x <= 180
            ):
                unplotted += 1
                continue
            point = points.setdefault(
                location.pk,
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(location.x), float(location.y)],
                    },
                    "properties": {"count": 0, "samples": []},
                },
            )
            point["properties"]["count"] += 1
            point["properties"]["samples"].append(
                {
                    "name": sample.name,
                    "type": str(type(sample)._meta.verbose_name),
                    "url": sample.get_absolute_url(),
                }
            )
        plotted = sum(p["properties"]["count"] for p in points.values())
        context.update(
            {
                "record": record,
                "kind": "sample"
                if isinstance(record, Sample)
                else "contributor"
                if isinstance(record, Contributor)
                else record._meta.model_name,
                "sample_location": record.location
                if isinstance(record, Sample)
                else None,
                "plotted": plotted,
                "unplotted": unplotted,
                "total": plotted + unplotted,
                "locations": len(points),
                "geojson": {
                    "type": "FeatureCollection",
                    "features": list(points.values()),
                },
            }
        )
        return context
