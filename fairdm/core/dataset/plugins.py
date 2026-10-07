"""Registered pages for a dataset: overview and delete."""

from collections import Counter, OrderedDict

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.utils.translation import gettext, ngettext
from django.utils.translation import gettext_lazy as _
from mvp.views.detail import CRUDDirectoryMixin
from partial_date import PartialDate

from fairdm import plugins
from fairdm.contrib.contributors.models import Person
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins.access import has_perm
from fairdm.contrib.plugins.mixins import (
    PrivateRecordNotFoundMixin,
    RecordOwnPageBackFallbackMixin,
)
from fairdm.core.measurement.models import Measurement
from fairdm.core.overview import (
    as_date,
    format_partial_date,
    json_ld,
    safe_reverse,
    sentence_case,
)
from fairdm.core.plugins import RecordOverviewPlugin
from fairdm.core.sample.models import Sample
from fairdm.registry import registry
from fairdm.utils.choices import Visibility
from fairdm.views import FairDMDeleteView

from .models import (
    Dataset,
    DatasetDescription,
    DatasetLiteratureRelation,
)

DATASET_SETTINGS = getattr(settings, "FAIRDM_DATASET", {})


def dataset_is_visible(request, obj):
    """Return whether the request's user may view a dataset.

    A public dataset is always visible, a private one only with ``dataset.view_dataset``.
    The plugin lookup reads through ``Dataset.all_objects`` so a private dataset's owner can
    still open it, which is why this check is needed. It is set as ``Overview.check``.

    Args:
        request: The current request.
        obj: The dataset, or ``None`` when no record has been resolved.

    Returns:
        True when the page may be shown.
    """
    if obj is None:
        return True
    if obj.visibility == Visibility.PUBLIC:
        return True
    return has_perm(request, "dataset.view_dataset", obj)


def visible_to_holder_of(permission):
    """Build a page check that also admits a holder of one record-level permission.

    Like :func:`dataset_is_visible`, except a private dataset also stays visible to a user
    holding ``permission`` on it. A level includes the ones below it, so anyone who holds the
    page's own permission on the dataset can also view it, and this check says so directly.

    Args:
        permission: The permission to accept at record level.

    Returns:
        A ``check(request, obj)`` callable.
    """

    def check(request, obj):
        if dataset_is_visible(request, obj):
            return True
        if obj is None:
            return False
        return request.user.has_perm(permission, obj)

    return check


class Delete(
    PrivateRecordNotFoundMixin, RecordOwnPageBackFallbackMixin, Plugin, FairDMDeleteView
):
    """Delete the dataset, confirmed by typing its name, with a preview of what goes with it.

    An additional view of :class:`Overview`. Unlike the project deletion page it has no
    protected-object guard, because a dataset's visibility never blocks its own deletion.
    """

    url_path = "delete"
    permission = "dataset.delete_dataset"
    check = staticmethod(visible_to_holder_of("dataset.delete_dataset"))
    page_title = _("Delete dataset")
    model = Dataset
    require_confirmation = True
    show_related_objects = True
    success_url = reverse_lazy("dataset-list")

    def get_confirmation_value(self):
        """Ask the user to type the dataset's name."""
        return self.base_object.name

    def _collect_deletion_data(self):
        """Cache the collector's walk for the life of the request."""
        # The walk loads every sample and measurement, and both `is_protected` and
        # `related_objects_summary` need it.
        if not hasattr(self, "deletion_data"):
            self.deletion_data = super()._collect_deletion_data()
        return self.deletion_data

    def get_context_data(self, **kwargs):
        """Replace the cascade preview with a count of samples and measurements.

        Everything else the collector reports is deleted with the dataset but never listed,
        as it would run to thousands of lines. A protected object keeps the shell's own preview,
        because ``protected_objects`` names what blocks deletion, not what it would remove.
        """
        context = super().get_context_data(**kwargs)
        if self.show_related_objects and not context["is_protected"]:
            context["related_objects"] = self.related_objects_summary()
        return context

    def related_objects_summary(self):
        """Count the samples and measurements a deletion removes, by concrete class.

        Returns:
            A list of ``(label, lines, 0)`` groups, one each for samples and measurements
            that have instances.
        """
        # Sample and Measurement are multi-table inherited, so `Collector` reports one row as two
        # entries. Skipping the bare base class avoids counting it twice.
        related_map, _protected = self._collect_deletion_data()
        sample_counts = Counter()
        measurement_counts = Counter()
        for instances in related_map.values():
            for instance in instances:
                concrete = type(instance)
                if concrete is Sample or concrete is Measurement:
                    continue
                if isinstance(instance, Sample):
                    sample_counts[concrete] += 1
                elif isinstance(instance, Measurement):
                    measurement_counts[concrete] += 1

        groups = []
        for label, counts in (
            (_("Samples"), sample_counts),
            (_("Measurements"), measurement_counts),
        ):
            if not counts:
                continue
            lines = [
                f"{concrete._meta.verbose_name_plural.title()} ({count})"
                for concrete, count in sorted(
                    counts.items(), key=lambda item: item[0]._meta.verbose_name_plural
                )
            ]
            groups.append((label, lines, 0))
        return groups


@plugins.register(Dataset, label=_("Overview"), icon="view", order=0)
class Overview(PrivateRecordNotFoundMixin, CRUDDirectoryMixin, RecordOverviewPlugin):
    """The dataset's own page and the root of its collection.

    Its ``extra_views`` are :class:`Delete`, and ``directory`` names the action link it needs.
    The editing pages are the shared ones in :mod:`fairdm.core.editing`, reached from the Manage
    menu.

    A dataset is the unit a portal cites and distributes. Its page answers a reuser's questions:
    what it is, whether its data is published, what it holds and how it grew, when each step of its
    life happened, how to cite it and who made it. Two gates decide what a visitor sees.
    Visibility governs the page and ``published`` governs the records, so a public, unpublished
    dataset shows its description, its counts and its charts to everyone. The page lists no
    record. Nothing here is written for a particular portal's types.

    Attributes:
        bookkeeping_fields: Fields every record carries that say nothing about its data.
    """

    url_path = None
    model = Dataset
    check = staticmethod(dataset_is_visible)
    template_name = "dataset/dataset_detail.html"
    extra_views = [Delete]

    directory = ["delete"]
    crud_views = {"delete": "dataset:overview-delete"}

    bookkeeping_fields = {
        "id",
        "uuid",
        "name",
        "dataset",
        "sample",
        "added",
        "modified",
        "options",
    }

    def show_delete_action(self, user):
        """Show the delete action to a user who may open the delete page."""
        return has_perm(self.request, Delete.permission, self.base_object)

    def get_context_data(self, **kwargs):
        """Add the dataset and everything the overview page draws."""
        context = super().get_context_data(**kwargs)
        dataset = self.base_object
        can_manage = has_perm(self.request, "dataset.change_dataset", dataset)
        samples = Sample.objects.filter(dataset=dataset)
        measurements = Measurement.objects.filter(dataset=dataset)
        data_types = self.get_record_types(samples, measurements)

        page = {
            "can_manage": can_manage,
            "access": self.get_access(),
            "descriptions": self.get_descriptions(),
            "dates": self.get_dates(),
            "team": self.get_team(),
            "literature": self.get_literature(),
            "data_types": data_types,
            "counts": self.get_counts(samples, measurements, data_types),
            "composition_chart": self.get_composition_chart(samples, measurements),
            "growth_chart": self.get_growth_chart(samples, measurements),
            "project_info": self.get_project_info(),
            "api_url": safe_reverse("api:dataset-detail", uuid=dataset.uuid),
            "urls": {
                "update": safe_reverse("dataset:edit", uuid=dataset.uuid),
                "descriptions": safe_reverse("dataset:descriptions", uuid=dataset.uuid),
                "delete": safe_reverse("dataset:overview-delete", uuid=dataset.uuid),
            },
        }
        page["counts"]["publications"] = len(page["literature"]["items"])
        page["citation"] = self.get_citation_details(page)
        page["json_ld"] = json_ld(self.get_schema_org(page))
        if can_manage and not dataset.data_is_public:
            page["readiness"] = self.get_readiness(page)
        page.update(self.get_shared_context(page))

        context["dataset"] = dataset
        context.update(page)
        return context

    def get_shared_context(self, page):
        """Provide the keys every overview page has, which the shared skeleton and cards read.

        Args:
            page: The page context gathered so far.

        Returns:
            The record, its icon, the header's people, the citation, People, Identifiers and
            Details cards, the timeline and, for the team, the readiness checklist.
        """
        dataset = self.base_object
        citation = page["citation"]
        creators = [entry["contributor"] for entry in page["team"]["creators"]]
        result = {
            "record": dataset,
            "overview_icon": "dataset",
            "has_charts": bool(page["composition_chart"] or page["growth_chart"]),
            "citation": {"title": gettext("Citation"), "text": citation["text"]},
            "identifiers": self.get_identifiers(),
            "people": self.get_people(),
            "header_people": creators,
            "header_people_label": gettext("Creators"),
            "lifecycle": self.get_lifecycle(page["dates"]),
            "details": self.get_details(page["project_info"]),
        }
        if citation["from_reference"]:
            result["citation"]["note"] = gettext(
                "Cite the data publication above rather than this page."
            )
        elif not citation["has_doi"]:
            result["citation"]["note"] = gettext(
                "This dataset has no DOI yet, so the citation points at this page. It gets one "
                "when it is published."
            )
        if "readiness" in page:
            readiness = page["readiness"]
            readiness["title"] = gettext("Ready to publish?")
            if readiness["ready"]:
                readiness["summary"] = gettext("Everything required is in place.")
            else:
                readiness["summary"] = ngettext(
                    "%(n)s required item missing",
                    "%(n)s required items missing",
                    readiness["missing_required"],
                ) % {"n": readiness["missing_required"]}
            readiness["about"] = gettext(
                "What a data repository needs before it can publish this dataset and give it a "
                "DOI."
            )
            result["readiness"] = readiness
        return result

    def get_details(self, project_info):
        """List the Details rows: the project, the licence and when the dataset last changed.

        Args:
            project_info: The project the viewer may see with its other datasets, or ``None``.

        Returns:
            The rows as ``c-card.details`` draws them.
        """
        dataset = self.base_object
        rows = []
        if project_info:
            row = {
                "label": gettext("Project"),
                "icon": "project",
                "record": project_info["project"],
            }
            if project_info["siblings"]:
                row["note"] = ngettext(
                    "%(n)s other dataset in this project",
                    "%(n)s other datasets in this project",
                    project_info["siblings"],
                ) % {"n": project_info["siblings"]}
            rows.append(row)
        rows.append(self.get_license_entry(dataset.license))
        rows.append(
            {"label": gettext("Last updated"), "icon": "time", "date": dataset.modified}
        )
        return rows

    def get_lifecycle(self, dates):
        """List the dataset's key dates in the order they happened.

        Args:
            dates: The dataset's dates as returned by :meth:`get_dates`.

        Returns:
            The steps as ``c-card.timeline`` draws them.
        """
        dataset = self.base_object
        steps = []
        if dates["collection_start"]:
            end = dates["collection_end"]
            steps.append(
                {
                    "label": gettext("Collected"),
                    "sort": as_date(dates["collection_start"]),
                    "date": f"{format_partial_date(dates['collection_start'])} \u2013 "
                    + (format_partial_date(end) if end else gettext("ongoing")),
                }
            )
        steps.append(
            {
                "label": gettext("Added to the portal"),
                "sort": dataset.added.date(),
                "day": dataset.added,
                "date": dataset.added,
            }
        )
        for key, label in (
            ("submitted", gettext("Submitted")),
            ("published", gettext("Published")),
            ("available", gettext("Available from")),
            ("withdrawn", gettext("Withdrawn")),
        ):
            if dates[key]:
                steps.append(
                    {
                        "label": label,
                        "sort": as_date(dates[key]),
                        "day": dates[key].date
                        if dates[key].precision == PartialDate.DAY
                        else None,
                        "date": dates[key],
                    }
                )
        return sorted(steps, key=lambda step: step["sort"])

    def get_access(self):
        """Name the dataset's access state, in the words the page uses for it everywhere.

        Returns:
            The state (``private``, ``public`` or ``published``) and its label.
        """
        dataset = self.base_object
        if dataset.visibility != Visibility.PUBLIC:
            return {"state": "private", "label": gettext("Private")}
        if dataset.data_is_public:
            return {"state": "published", "label": gettext("Published")}
        return {"state": "public", "label": gettext("Unpublished")}

    def get_descriptions(self):
        """List the dataset's descriptions in the vocabulary's own order.

        Returns:
            One entry per description type the dataset has text for.
        """
        by_type = {d.type: d.value for d in self.base_object.descriptions.all()}
        labels = dict(DatasetDescription.VOCABULARY.choices)
        return [
            {"type": t, "label": labels.get(t, t), "value": by_type[t]}
            for t in DatasetDescription.VOCABULARY.values
            if by_type.get(t)
        ]

    def get_dates(self):
        """Read the dataset's recorded dates, each with the precision it was recorded at.

        Returns:
            The collection start and end and the available, submitted, published and withdrawn
            dates, each ``None`` when not recorded, and the withdrawal written out as recorded.
        """
        values = {d.type: d.value for d in self.base_object.dates.all()}
        return {
            "collection_start": values.get("CollectionStart"),
            "collection_end": values.get("CollectionEnd"),
            "available": values.get("Available"),
            "submitted": values.get("Submitted"),
            "published": values.get("Published"),
            "withdrawn": values.get("Withdrawn"),
            "withdrawn_text": format_partial_date(values.get("Withdrawn")),
        }

    def get_team(self):
        """Gather the dataset's creators, and whether anyone is credited as its contact person.

        Returns:
            The creators, whether a contact person is credited, and how many contributions the
            dataset has.
        """
        contributions = self.get_contributions()
        creators, has_contact = [], False
        for contribution in contributions:
            roles = self.get_role_names(contribution)
            if "Creator" in roles:
                creators.append(
                    {
                        "contributor": contribution.contributor,
                        "roles": [r.label for r in contribution.roles.all()],
                    }
                )
            has_contact = has_contact or "ContactPerson" in roles
        return {
            "creators": creators,
            "has_contact": has_contact,
            "total": len(contributions),
        }

    def get_literature(self):
        """List the related publications, worded from the publication's side.

        DataCite relation types read from the dataset's side ("dataset IsDescribedBy paper"),
        which is backwards for a visitor looking at the paper. Each is restated from the paper's
        side, and the relations a reuser cares most about come first.

        Returns:
            The publications as ``items``, each with its relation, its DOI and its year.
        """
        wording = OrderedDict(
            [
                ("IsDescribedBy", gettext("Describes this dataset")),
                ("IsDocumentedBy", gettext("Documents this dataset")),
                ("IsSupplementTo", gettext("This dataset supplements it")),
                ("IsCitedBy", gettext("Cites this dataset")),
                ("IsReferencedBy", gettext("Refers to this dataset")),
                ("Cites", gettext("Cited by this dataset")),
                ("References", gettext("Referred to by this dataset")),
            ]
        )
        order = list(wording)
        relations = sorted(
            DatasetLiteratureRelation.objects.filter(
                dataset=self.base_object
            ).select_related("literature_item"),
            key=lambda r: (
                order.index(r.relationship_type)
                if r.relationship_type in order
                else len(order)
            ),
        )
        items = [
            {
                "relation": wording.get(
                    relation.relationship_type,
                    relation.get_relationship_type_display(),
                ),
                "item": relation.literature_item,
                "doi": relation.literature_item.get_doi(),
                "year": (
                    relation.literature_item.item.get("issued", {}).get("date-parts")
                    or [[None]]
                )[0][0],
            }
            for relation in relations
        ]
        return {"items": items}

    def get_record_types(self, samples, measurements):
        """List the registered sample and measurement types the dataset holds, largest first.

        A type the registry no longer holds is left out. The figures, the readiness checklist and
        the ``variableMeasured`` list of the page's schema.org description read this.

        Args:
            samples: The dataset's samples.
            measurements: The dataset's measurements.

        Returns:
            One entry per type with its ``kind``, its ``label`` and the labels of its ``fields``.
        """
        result = []
        for kind, queryset in (("sample", samples), ("measurement", measurements)):
            rows = (
                queryset.values("polymorphic_ctype")
                .annotate(n=Count("pk"))
                .order_by("-n")
            )
            for row in rows:
                model = ContentType.objects.get_for_id(
                    row["polymorphic_ctype"]
                ).model_class()
                if model is None or not registry.is_registered(model):
                    continue
                config = registry.get_for_model(model)
                names = [
                    n
                    for n in config.resolve_fields("table")
                    if n not in self.bookkeeping_fields and "__" not in n
                ]
                model_fields = {f.name: f for f in model._meta.get_fields()}
                result.append(
                    {
                        "kind": kind,
                        "label": sentence_case(model._meta.verbose_name_plural),
                        "fields": [
                            str(model_fields[n].verbose_name).capitalize()
                            for n in names
                            if n in model_fields
                        ],
                    }
                )
        return result

    def get_counts(self, samples, measurements, data_types):
        """Count the dataset's samples and measurements and the types each spans.

        Args:
            samples: The dataset's samples.
            measurements: The dataset's measurements.
            data_types: The types the dataset holds, from :meth:`get_record_types`.

        Returns:
            The counts, each with a short description of how many types it spans.
        """

        def types(kind):
            n = sum(1 for t in data_types if t["kind"] == kind)
            return (
                ngettext("%(n)s type", "%(n)s types", n) % {"n": n}
                if n
                else gettext("None yet")
            )

        return {
            "samples": samples.count(),
            "samples_desc": types("sample"),
            "measurements": measurements.count(),
            "measurements_desc": types("measurement"),
        }

    def get_project_info(self):
        """Find the parent project when the viewer may see it.

        Nothing ties a dataset's visibility to its project's, so a public dataset can sit in a
        private project that must not be named.

        Returns:
            The project and how many other datasets in it the viewer may see, or ``None``.
        """
        from fairdm.contrib.contributors.choices import ContributionLevel
        from fairdm.core.project.plugins import project_is_visible

        dataset = self.base_object
        project = dataset.project
        if project is None or not project_is_visible(self.request, project):
            return None
        siblings = Dataset.all_objects.filter(project=project).exclude(pk=dataset.pk)
        if not has_perm(self.request, "project.change_project", project):
            visible = Q(visibility=Visibility.PUBLIC)
            user = self.request.user
            if user.is_authenticated:
                held = Dataset.all_objects.accessible_to(user, ContributionLevel.VIEW)
                visible |= Q(pk__in=held.values("pk"))
            siblings = siblings.filter(visible)
        return {"project": project, "siblings": siblings.count()}

    def get_citation_details(self, page):
        """Cite the dataset's own data publication when it has one, else DataCite's form.

        The year of the built citation is the Published date, else the Available date, else the
        year the dataset was added.

        Args:
            page: The page context gathered so far.

        Returns:
            The citation ``text`` and ``link`` and whether it ``has_doi``, ``from_reference`` and
            how many ``creators`` it names.
        """
        dataset = self.base_object
        if dataset.reference_id:
            reference = dataset.reference
            doi = reference.get_doi()
            return {
                "text": str(reference),
                "link": f"https://doi.org/{doi}" if doi else None,
                "has_doi": bool(doi),
                "creators": len(page["team"]["creators"]),
                "from_reference": True,
            }
        creators = [entry["contributor"] for entry in page["team"]["creators"]]
        when = as_date(page["dates"]["published"] or page["dates"]["available"])
        year = when.year if when else dataset.added.year
        doi = next(
            (i.value for i in dataset.identifiers.all() if i.type == "DOI"), None
        )
        link = (
            f"https://doi.org/{doi}"
            if doi
            else self.request.build_absolute_uri(dataset.get_absolute_url())
        )
        return {
            "text": self.get_citation(
                authors=creators, year=year, title=dataset.name, link=link
            ),
            "link": link,
            "has_doi": bool(doi),
            "creators": len(creators),
            "from_reference": False,
        }

    def get_schema_org(self, page):
        """Describe the dataset as schema.org ``Dataset``, the shape harvesters read.

        It names the variables measured and never their values, so it carries nothing a visitor
        could not read on the page.

        Args:
            page: The page context gathered so far.

        Returns:
            The description, ready to be serialised into the page head.
        """
        dataset = self.base_object
        url = self.request.build_absolute_uri(dataset.get_absolute_url())
        abstract = next(
            (d["value"] for d in page["descriptions"] if d["type"] == "Abstract"), ""
        )
        data = OrderedDict(
            [
                ("@context", "https://schema.org/"),
                ("@type", "Dataset"),
                ("name", dataset.name),
                ("url", url),
                ("identifier", page["citation"]["link"] or url),
                ("isAccessibleForFree", True),
                ("dateModified", dataset.modified.date().isoformat()),
            ]
        )
        if abstract:
            data["description"] = abstract
        if dataset.license_id:
            data["license"] = dataset.license.canonical_url or dataset.license.name
        keywords = [k.label for k in dataset.keywords.all()]
        if keywords:
            data["keywords"] = keywords
        creators = []
        for entry in page["team"]["creators"]:
            person = entry["contributor"]
            if isinstance(person, Person):
                creators.append(
                    {
                        "@type": "Person",
                        "name": str(person),
                        "givenName": person.first_name,
                        "familyName": person.last_name,
                    }
                )
            else:
                creators.append({"@type": "Organization", "name": str(person)})
        if creators:
            data["creator"] = creators
        start, end = (
            as_date(page["dates"]["collection_start"]),
            as_date(page["dates"]["collection_end"]),
        )
        if start:
            data["temporalCoverage"] = (
                f"{start.isoformat()}/{end.isoformat() if end else '..'}"
            )
        variables = [label for t in page["data_types"] for label in t["fields"]]
        if variables:
            data["variableMeasured"] = variables
        if page["project_info"]:
            data["isPartOf"] = {
                "@type": "ResearchProject",
                "name": dataset.project.name,
                "url": self.request.build_absolute_uri(
                    dataset.project.get_absolute_url()
                ),
            }
        site = getattr(self.request, "site", None)
        if site is not None:
            data["includedInDataCatalog"] = {"@type": "DataCatalog", "name": site.name}
        return data

    def get_readiness(self, page):
        """List what has to be in place before the dataset is published, and whether it is yet.

        Items come from DataCite's mandatory and recommended properties and from what a formal
        publication would need to submit the record unaided. Items with nowhere to fix them yet
        carry no link.

        Args:
            page: The page context gathered so far.

        Returns:
            The items, how many are done, the percentage, whether every required one is, and how
            many required ones are missing.
        """
        dataset = self.base_object
        urls = page["urls"]
        described = {d["type"] for d in page["descriptions"]}
        items = [
            (
                gettext("An abstract describes the data"),
                "Abstract" in described,
                urls["descriptions"],
                True,
            ),
            (
                gettext("The methods are described"),
                "Methods" in described,
                urls["descriptions"],
                True,
            ),
            (
                gettext("At least one creator is credited"),
                bool(page["team"]["creators"]),
                None,
                True,
            ),
            (
                gettext("Someone is named as the contact"),
                page["team"]["has_contact"],
                None,
                True,
            ),
            (
                gettext("A licence is chosen"),
                dataset.license_id is not None,
                urls["update"],
                True,
            ),
            (
                gettext("It holds samples or measurements"),
                bool(page["data_types"]),
                None,
                True,
            ),
            (
                gettext("The collection period is recorded"),
                page["dates"]["collection_start"] is not None,
                urls["update"],
                True,
            ),
            (
                gettext("Keywords make it findable"),
                dataset.keywords.exists(),
                None,
                False,
            ),
            (
                gettext("A related publication is linked"),
                bool(page["literature"]["items"]),
                None,
                False,
            ),
            (
                gettext("The dataset is public"),
                dataset.visibility == Visibility.PUBLIC,
                urls["update"],
                False,
            ),
        ]
        required = [i for i in items if i[3]]
        done_required = sum(1 for i in required if i[1])
        done = sum(1 for i in items if i[1])
        return {
            "items": [
                {"label": label, "done": ok, "url": url, "required": req}
                for label, ok, url, req in items
            ],
            "done": done,
            "total": len(items),
            "percent": round(100 * done / len(items)),
            "ready": done_required == len(required),
            "missing_required": len(required) - done_required,
        }
