"""Registered pages for a sample: its overview and keywords."""

from typing import Any

from django.utils.translation import gettext, ngettext
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.generic.plugins import KeywordsPlugin
from fairdm.contrib.plugins.access import has_perm
from fairdm.core.measurement.models import Measurement
from fairdm.core.overview import safe_reverse, sentence_case
from fairdm.core.plugins import TypedOverviewPlugin

from ..utils import documentation_link
from .models import Sample, SampleRelation


@plugins.register(Sample, label=_("Overview"), icon="view", order=0)
class Overview(TypedOverviewPlugin):
    """The sample's own page, drawn from ``sample/sample_overview.html``, which reads only the
    base ``Sample`` model. A sample type adds its own content with
    ``<app_label>/<model_name>_overview.html``; see :class:`TypedOverviewPlugin`.

    A physical sample is best understood through its history: collected, prepared, stored,
    perhaps destroyed. The sample vocabularies already describe that history three ways (a date
    type, a contributor role and a description type for each step), so the page puts them back
    together as one timeline instead of three unrelated lists.

    Attributes:
        lifecycle: Each step in a sample's history as its date type, the contributor role that
            performs it, the description type that explains it and what the page calls it. The
            order is the order a specimen usually moves through; dated steps are then sorted by
            their dates.
        status_variants: The theme colour each custody status carries. Only "destroyed" is a
            warning to a reuser; the rest report where the specimen is.
        status_meanings: What each status means to someone hoping to re-examine the specimen.
        measurements_shown: How many measurements are listed before the rest are counted.
    """

    # The overview edits no fields, so it declares no fieldsets.
    fieldsets: list[tuple[str | None, dict[str, Any]]] = []
    base_model = Sample
    fallback_template = "sample/sample_overview.html"

    lifecycle = [
        ("Created", None, None, _("Created")),
        ("Collected", "Collection", "SampleCollection", _("Collected")),
        ("Prepared", "Preparation", "SamplePreparation", _("Prepared")),
        ("Archival", "Storage", "SampleStorage", _("Archived")),
        ("Returned", None, None, _("Returned")),
        ("Restored", "Restoration", None, _("Restored")),
        ("Destroyed", "Destruction", "SampleDestruction", _("Destroyed")),
    ]
    status_variants = {
        "available": "success",
        "in_use": "info",
        "stored": "neutral",
        "destroyed": "error",
    }
    status_meanings = {
        "available": _("The specimen can be requested for further study."),
        "in_use": _("The specimen is being worked on and may not be available."),
        "stored": _("The specimen is archived and can be retrieved."),
        "destroyed": _("The specimen no longer exists. Its data remains."),
        "unknown": _("Where the specimen is now has not been recorded."),
    }
    measurements_shown = 10

    def get_context_data(self, **kwargs):
        """Add the sample and everything the overview page draws."""
        from fairdm.core.project.plugins import project_is_visible

        context = super().get_context_data(**kwargs)
        sample = self.base_object
        entries = self.get_credits()
        descriptions = {d.type: d.value for d in sample.descriptions.all()}
        dates = {d.type: d.value for d in sample.dates.all()}
        measurements = self.get_measurements()
        relations = self.get_related_samples()
        status = self.get_status()
        project = sample.dataset.project
        if project is not None and not project_is_visible(self.request, project):
            project = None
        identifiers = self.get_identifiers()

        context["sample"] = sample
        context.update(
            {
                "record": sample,
                "overview_icon": "sample",
                "can_manage": has_perm(
                    self.request, "dataset.change_dataset", sample.dataset
                ),
                "can_edit": has_perm(self.request, "sample.change_sample", sample),
                "urls": {"keywords": safe_reverse("sample:keywords", uuid=sample.uuid)},
                "sample_type": str(type(sample)._meta.verbose_name),
                "status": status,
                "lifecycle": self.get_timeline(
                    self.lifecycle, dates, descriptions, entries
                ),
                "notes": descriptions.get("Other"),
                "measurements": measurements,
                "relations": relations,
                "location": sample.location,
                "project": project,
                "counts": {
                    "measurements": measurements["total"],
                    "related": len(relations["parents"]) + len(relations["children"]),
                    "related_desc": self.get_relations_summary(relations),
                    "people": len(entries),
                },
                "citation": self.get_citation_details(entries, dates, identifiers),
                "identifiers": identifiers,
                "api_url": safe_reverse("api:sample-detail", uuid=sample.uuid),
                "type_info": self.get_type_info(),
                "people": self.get_people(entries),
                "details": self.get_details(project, status),
            }
        )
        return context

    def get_status(self):
        """Read the sample's custody status as the page shows it.

        Returns:
            The stored value, its label, the badge colour, and what it means for re-examining the
            specimen.
        """
        sample = self.base_object
        # The status field hands back a vocabulary concept, not its stored string.
        value = getattr(sample.status, "name", sample.status) or "unknown"
        labels = dict(type(sample)._meta.get_field("status").choices)
        return {
            "value": value,
            "label": labels.get(value, value),
            "variant": self.status_variants.get(value),
            "meaning": self.status_meanings.get(value, ""),
        }

    def get_details(self, project, status):
        """Write the Details card's entries: where the sample sits, its licence, status and dates.

        Args:
            project: The parent project, or ``None`` when there is none or the viewer may not see it.
            status: The sample's status, from :meth:`get_status`.

        Returns:
            The entries for :class:`c-card.details`.
        """
        sample = self.base_object
        parents = []
        if project is not None:
            parents.append(
                {"label": gettext("Project"), "icon": "project", "record": project}
            )
        parents.append(
            {"label": gettext("Dataset"), "icon": "dataset", "record": sample.dataset}
        )
        parents.append(self.get_license_entry(sample.dataset.license))
        return [
            *parents,
            {
                "label": gettext("Status"),
                "icon": "box",
                "text": status["label"],
                "note": status["meaning"],
            },
            {"label": gettext("Added"), "icon": "calendar", "date": sample.added},
            {"label": gettext("Last updated"), "icon": "time", "date": sample.modified},
        ]

    def get_citation_details(self, entries, dates, identifiers):
        """Write the citation, in DataCite's form for a physical object.

        Args:
            entries: The record's credits, from :meth:`get_credits`.
            dates: The sample's dates, by type.
            identifiers: The sample's identifiers, from :meth:`get_identifiers`.

        Returns:
            The card's title and text, with a note when the sample has no IGSN.
        """
        sample = self.base_object
        igsn = next((i for i in identifiers if i["type"] == "IGSN"), None)
        collected = dates.get("Collected")
        text = self.get_citation(
            authors=self.get_contributors_with_role(entries, "Collection"),
            year=getattr(getattr(collected, "date", None), "year", None)
            or sample.added.year,
            title=f"{sample.name} [{type(sample)._meta.verbose_name}]",
            link=igsn["link"]
            if igsn
            else self.request.build_absolute_uri(sample.get_absolute_url()),
        )
        citation = {"title": gettext("Citation"), "text": text}
        if not igsn:
            citation["note"] = gettext(
                "This sample has no IGSN, so the citation points at this page. An IGSN gives the "
                "physical specimen an identifier that outlives the portal."
            )
        return citation

    def get_measurements(self):
        """Read the measurements made on this sample, most recent first.

        A measurement can belong to a different dataset than its sample, which is how one team
        measures another team's specimens. Each is shown only if the viewer may see its own
        dataset, and being on the sample's dataset team opens nothing else.

        Returns:
            The measurements shown, how many the viewer may see and how many are left over.
        """
        sample = self.base_object
        queryset = (
            Measurement.objects.filter(sample=sample)
            .visible_to(self.request.user)
            .select_related("dataset")
            .order_by("-added")
        )
        total = queryset.count()
        items = [
            {
                "measurement": m,
                "type": sentence_case(type(m)._meta.verbose_name),
                "elsewhere": m.dataset_id != sample.dataset_id,
            }
            for m in queryset[: self.measurements_shown]
        ]
        return {
            "items": items,
            "total": total,
            "more": max(total - self.measurements_shown, 0),
        }

    def get_related_samples(self):
        """Read the sample's parents and subsamples.

        Either may sit in another dataset, so each is checked against its own dataset. One the
        viewer may not see is described, never named or linked, and is counted in ``hidden``.

        Returns:
            The visible relations, all together and split into parents and subsamples, and how
            many the viewer may not see.
        """
        sample = self.base_object
        parents = [
            r.target_id
            for r in SampleRelation.objects.filter(source=sample, type="child_of")
        ]
        children = [
            r.source_id
            for r in SampleRelation.objects.filter(target=sample, type="child_of")
        ]
        visible = (
            Sample.objects.filter(pk__in=parents + children)
            .visible_to(self.request.user)
            .in_bulk()
        )

        def entries(pks, relation):
            shown = [visible[pk] for pk in pks if pk in visible]
            return [
                {
                    "sample": s,
                    "type": sentence_case(type(s)._meta.verbose_name),
                    "relation": relation,
                    "elsewhere": s.dataset_id != sample.dataset_id,
                }
                for s in shown
            ], len(pks) - len(shown)

        parent_entries, hidden_parents = entries(parents, gettext("Parent sample"))
        child_entries, hidden_children = entries(children, gettext("Subsample"))
        return {
            "items": parent_entries + child_entries,
            "parents": parent_entries,
            "children": child_entries,
            "hidden": hidden_parents + hidden_children,
        }

    def get_relations_summary(self, relations):
        """Say how many parents and subsamples are shown, for the figure's caption.

        Args:
            relations: The relations, from :meth:`get_related_samples`.

        Returns:
            For example "1 parent · 2 subsamples", or "None recorded".
        """
        parts = []
        if relations["parents"]:
            parts.append(
                ngettext("%(n)s parent", "%(n)s parents", len(relations["parents"]))
                % {"n": len(relations["parents"])}
            )
        if relations["children"]:
            parts.append(
                ngettext(
                    "%(n)s subsample", "%(n)s subsamples", len(relations["children"])
                )
                % {"n": len(relations["children"])}
            )
        return " · ".join(parts) or gettext("None recorded")


# A plugin with no declared `permission` admits every request, anonymous included, so the page
# below names the right it needs. It is not a tab: the overview's Manage menu links to it.
@plugins.register(Sample, label=_("Keywords"), icon="keywords", menu=False)
class Keywords(KeywordsPlugin):
    """Edit the sample's keywords."""

    permission = "sample.change_sample"
    heading_config = {
        "description": _(
            "Providing key dates for your sample is essential for understanding its timeline and context. Key dates help users identify important milestones, such as when the sample was collected, processed, or analyzed. This information is crucial for interpreting the sample's relevance and applicability to specific research questions or applications."
        ),
        "links": [documentation_link("sample/keywords")],
    }
