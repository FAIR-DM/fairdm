"""The portal's site search: what the dock's Search item and the header's search field find.

Prototype code. Each kind matches the query against a record's name and identifiers with a plain
``icontains`` and limits the records to the ones the request may see, the same way the record's
own list page does.
"""

from urllib.parse import urlencode

from django.db.models import Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from mvp.search import Kind, Result, register


class ProjectKind(Kind):
    name = "projects"
    label = _("Projects")
    icon = "project"
    description = _("Research projects and the datasets they hold")

    def find(self, query, request):
        from fairdm.core.project.models import Project

        return (
            Project.objects.get_visible()
            .filter(Q(name__icontains=query) | Q(uuid__iexact=query))
            .order_by("name")
        )

    def result(self, item):
        return Result(title=item.name, url=item.get_absolute_url(), where=str(_("Project")))

    def more_url(self, query):
        return reverse("project-list") + "?" + urlencode({"q": query})


class DatasetKind(Kind):
    name = "datasets"
    label = _("Datasets")
    icon = "dataset"
    description = _("Published collections of samples and measurements")

    def find(self, query, request):
        from fairdm.core.dataset.models import Dataset

        return (
            Dataset.all_objects.visible_to(request.user)
            .filter(Q(name__icontains=query) | Q(uuid__iexact=query))
            .select_related("project")
            .order_by("name")
        )

    def result(self, item):
        where = item.project.name if item.project_id else str(_("Dataset"))
        return Result(title=item.name, url=item.get_absolute_url(), where=where)

    def more_url(self, query):
        return reverse("dataset-list") + "?" + urlencode({"q": query})


class SampleKind(Kind):
    name = "samples"
    label = _("Samples")
    icon = "sample"
    description = _("Physical samples, found by name or by their own identifier")

    def find(self, query, request):
        from fairdm.core.sample.models import Sample

        return (
            Sample.objects.visible_to(request.user)
            .filter(Q(name__icontains=query) | Q(local_id__icontains=query) | Q(uuid__iexact=query))
            .select_related("dataset")
            .order_by("name")
        )

    def result(self, item):
        passage = " · ".join(part for part in [item.local_id, item.dataset.name if item.dataset_id else ""] if part)
        return Result(
            title=item.name,
            url=item.get_absolute_url(),
            where=str(item._meta.verbose_name).capitalize(),
            passage=passage,
        )


class MeasurementKind(Kind):
    name = "measurements"
    label = _("Measurements")
    icon = "measurement"
    description = _("Measurements made on samples")

    def find(self, query, request):
        from fairdm.core.measurement.models import Measurement

        return (
            Measurement.objects.visible_to(request.user)
            .filter(Q(name__icontains=query) | Q(uuid__iexact=query))
            .select_related("sample")
            .order_by("name")
        )

    def result(self, item):
        return Result(
            title=item.name,
            url=item.get_absolute_url(),
            where=str(item._meta.verbose_name).capitalize(),
            passage=item.sample.name if item.sample_id else "",
        )


class PeopleKind(Kind):
    name = "people"
    label = _("People")
    icon = "people"
    description = _("Researchers who contribute to the portal")

    def find(self, query, request):
        from fairdm.contrib.contributors.models import Person

        return Person.objects.real().filter(name__icontains=query).order_by("name")

    def result(self, item):
        return Result(title=item.name, url=item.get_absolute_url(), where=str(_("Person")))

    def more_url(self, query):
        return reverse("people-list") + "?" + urlencode({"q": query})


class OrganizationKind(Kind):
    name = "organizations"
    label = _("Organizations")
    icon = "organization"
    description = _("Institutions, funders and groups")

    def find(self, query, request):
        from fairdm.contrib.contributors.models import Organization

        return Organization.objects.filter(name__icontains=query).order_by("name")

    def result(self, item):
        return Result(title=item.name, url=item.get_absolute_url(), where=str(_("Organization")))

    def more_url(self, query):
        return reverse("organization-list") + "?" + urlencode({"q": query})


class LiteratureKind(Kind):
    name = "literature"
    label = _("Literature")
    icon = "literature"
    description = _("Publications the datasets cite")

    def find(self, query, request):
        from literature.models import Item

        return Item.objects.filter(title__icontains=query).order_by("title")

    def result(self, item):
        return Result(title=item.title, url=item.get_absolute_url(), where=str(_("Literature")))


def register_kinds():
    """Register every kind, in the order the results page shows their groups."""
    for kind in (
        ProjectKind(),
        DatasetKind(),
        SampleKind(),
        MeasurementKind(),
        PeopleKind(),
        OrganizationKind(),
        LiteratureKind(),
    ):
        register(kind)
