"""The portal's site search: the record types a person can find from any page.

django-mvp draws the search page, the dialog and the header field. Each kind here
finds records of one type by running the type's own list ``q`` filter over the records
the person may open, so the header and the list page agree on what matches.
"""

from django.db.models import Exists, OuterRef
from django.utils.translation import gettext_lazy as _
from django_filters import FilterSet
from literature.importers.normalizers import IdentifierNormalizer
from literature.ui.filters import ItemFilterSet
from mvp.search import Kind, Result, register
from mvp.search.registry import default_registry

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.filters import OrganizationFilter, PersonFilter
from fairdm.core.dataset.filters import DatasetFilter
from fairdm.core.measurement.filters import MeasurementFilter
from fairdm.core.project.filters import ProjectFilter
from fairdm.core.sample.filters import SampleFilter


class RecordKind(Kind):
    """A kind that finds the records of one type with the type's own list search.

    Subclasses set the four attributes django-mvp's ``Kind`` asks for, plus
    ``filterset_class`` and ``ordering``, and define :meth:`records` and
    :meth:`describe`.

    Attributes:
        filterset_class: The list's filter set. Only its ``q`` filter is used, and it
            is never instantiated.
        ordering: Field names the results are ordered by. Ends with ``"pk"``, because
            the results page pages through them and one column is not a total order.
    """

    filterset_class: type[FilterSet] | None = None
    ordering: tuple[str, ...] = ("pk",)

    def records(self, user):
        """Return the records the person may open.

        Args:
            user: The signed-in user, or an anonymous one.

        Returns:
            A queryset of the records the person may open.

        Raises:
            NotImplementedError: Always, until a subclass defines it.
        """
        raise NotImplementedError(f"{type(self).__name__} must define records().")

    def describe(self, item):
        """Return the line under a result's title.

        Args:
            item: One record.

        Returns:
            A ``(where, passage)`` pair of strings.

        Raises:
            NotImplementedError: Always, until a subclass defines it.
        """
        raise NotImplementedError(f"{type(self).__name__} must define describe().")

    def find(self, query, request):
        """Find the records that match the query and that the person may open.

        Args:
            query: The cleaned query.
            request: The request the search is for.

        Returns:
            A queryset in the kind's order.
        """
        matching = self.filterset_class.base_filters["q"].filter(
            self.records(request.user), query
        )
        return matching.order_by(*self.ordering)

    def result(self, item):
        """Turn one record into a result that links to its page.

        Args:
            item: One record from :meth:`find`.

        Returns:
            The result, its line from :meth:`describe`.
        """
        where, passage = self.describe(item)
        return Result(
            title=str(item),
            url=item.get_absolute_url(),
            where=where,
            passage=passage,
        )


class ProjectKind(RecordKind):
    """Projects the person may open."""

    name = "projects"
    label = _("Projects")
    icon = "project"
    description = _("Research projects and the datasets they hold")
    filterset_class = ProjectFilter
    ordering = ("name", "pk")

    def records(self, user):
        """Return the public projects and those the person holds a level on."""
        from fairdm.core.project.models import Project

        return Project.objects.get_visible() | Project.objects.accessible_to(
            user, ContributionLevel.VIEW
        )

    def describe(self, item):
        """Name the record type, as the project has no parent."""
        return str(_("Project")), ""


class DatasetKind(RecordKind):
    """Datasets the person may open."""

    name = "datasets"
    label = _("Datasets")
    icon = "dataset"
    description = _("Collections of samples and measurements")
    filterset_class = DatasetFilter
    ordering = ("name", "pk")

    def records(self, user):
        """Return the datasets the person may open, marking those whose project they may.

        A person with a level on a dataset alone may open it inside a private project,
        and that project's name is not theirs to read.
        """
        from fairdm.core.dataset.models import Dataset

        projects = ProjectKind().records(user).filter(pk=OuterRef("project_id"))
        return (
            Dataset.all_objects.visible_to(user)
            .select_related("project")
            .annotate(project_is_open=Exists(projects))
        )

    def describe(self, item):
        """Name the dataset's project when the person may open it."""
        named = item.project_id and item.project_is_open
        return (item.project.name if named else str(_("Dataset"))), ""


class SampleKind(RecordKind):
    """Samples the person may open, of every registered type."""

    name = "samples"
    label = _("Samples")
    icon = "sample"
    description = _("Physical samples, found by name or by their own identifier")
    filterset_class = SampleFilter
    ordering = ("name", "pk")

    def records(self, user):
        """Return the samples the person may open, with their dataset."""
        from fairdm.core.sample.models import Sample

        return Sample.objects.visible_to(user).select_related("dataset")

    def describe(self, item):
        """Name the sample's type, then its local ID and dataset."""
        parts = [item.local_id, item.dataset.name if item.dataset_id else ""]
        return str(item._meta.verbose_name).capitalize(), " · ".join(
            part for part in parts if part
        )


class MeasurementKind(RecordKind):
    """Measurements the person may open, of every registered type."""

    name = "measurements"
    label = _("Measurements")
    icon = "measurement"
    description = _("Measurements made on samples")
    filterset_class = MeasurementFilter
    ordering = ("name", "pk")

    def records(self, user):
        """Return the measurements the person may open, marking those whose sample they may.

        A measurement follows its own dataset, so it can hang from a sample in a dataset
        the person may not open.
        """
        from fairdm.core.measurement.models import Measurement
        from fairdm.core.sample.models import Sample

        samples = Sample.objects.visible_to(user).filter(pk=OuterRef("sample_id"))
        return (
            Measurement.objects.visible_to(user)
            .select_related("sample")
            .annotate(sample_is_open=Exists(samples))
        )

    def describe(self, item):
        """Name the measurement's type, then its sample when the person may open it."""
        named = item.sample_id and item.sample_is_open
        return str(item._meta.verbose_name).capitalize(), (
            item.sample.name if named else ""
        )


class PeopleKind(RecordKind):
    """The people who contribute to the portal."""

    name = "people"
    label = _("People")
    icon = "people"
    description = _("Researchers who contribute to the portal")
    filterset_class = PersonFilter
    ordering = ("name", "pk")

    def records(self, user):
        """Return every person except superusers and the anonymous user."""
        from fairdm.contrib.contributors.models import Person

        return Person.objects.real()

    def describe(self, item):
        """Name the record type."""
        return str(_("Person")), ""


class OrganizationKind(RecordKind):
    """The organizations that appear on the portal."""

    name = "organizations"
    label = _("Organizations")
    icon = "organization"
    description = _("Institutions, funders and groups")
    filterset_class = OrganizationFilter
    ordering = ("name", "pk")

    def records(self, user):
        """Return every organization."""
        from fairdm.contrib.contributors.models import Organization

        return Organization.objects.all()

    def describe(self, item):
        """Name the record type."""
        return str(_("Organization")), ""


class LiteratureKind(RecordKind):
    """The publications the portal's datasets cite."""

    name = "literature"
    label = _("Literature")
    icon = "literature"
    description = _("Publications the datasets cite")
    filterset_class = ItemFilterSet
    ordering = ("title", "pk")

    def records(self, user):
        """Return every reference."""
        from literature.models import Item

        return Item.objects.all()

    def find(self, query, request):
        """Find references, and none when the query is only a DOI prefix.

        The list's filter reads a prefix such as ``doi:`` as no words and would return
        every reference, so the words are read here the way it reads them first.

        Args:
            query: The cleaned query.
            request: The request the search is for.

        Returns:
            A queryset of references in the kind's order.
        """
        words = (IdentifierNormalizer.normalize_doi(word) for word in query.split())
        if not any(words):
            return self.records(request.user).none()
        return super().find(query, request)

    def describe(self, item):
        """Name the record type."""
        return str(_("Literature")), ""


def register_kinds():
    """Register every kind, in the order the results page shows their groups.

    Safe to call again: a kind that is already registered is left as it is, because
    ``FairDMConfig.ready()`` can run more than once in one process.
    """
    for kind in (
        ProjectKind(),
        DatasetKind(),
        SampleKind(),
        MeasurementKind(),
        PeopleKind(),
        OrganizationKind(),
        LiteratureKind(),
    ):
        if kind.name not in default_registry.kinds:
            register(kind)
