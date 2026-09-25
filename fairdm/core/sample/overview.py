"""What the sample overview page draws, from the base ``Sample`` model alone.

Everything here reads fields every sample has, whatever its type. What a particular sample type
adds (a rock's hardness, a water sample's pH) is drawn by that type's own template, which extends
``sample/sample_overview.html`` and fills its blocks. See ``Overview.get_template_names``.

A physical sample is best understood through its history: collected, prepared, stored,
perhaps destroyed. The sample vocabularies already describe that history three ways — a date type,
a contributor role and a description type for each step — so the page puts them back together
as one timeline instead of three unrelated lists.
"""

from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.utils.translation import ngettext

from fairdm.core import overview as shared
from fairdm.core.measurement.models import Measurement

from .models import Sample, SampleDescription, SampleRelation

#: Each step in a sample's history: its date type, the contributor role that performs it, the
#: description type that explains it, and what the page calls it. The order is the order a
#: specimen usually moves through; dated steps are then sorted by their dates.
LIFECYCLE = [
    ("Created", None, None, gettext_lazy("Created")),
    ("Collected", "Collection", "SampleCollection", gettext_lazy("Collected")),
    ("Prepared", "Preparation", "SamplePreparation", gettext_lazy("Prepared")),
    ("Archival", "Storage", "SampleStorage", gettext_lazy("Archived")),
    ("Returned", None, None, gettext_lazy("Returned")),
    ("Restored", "Restoration", None, gettext_lazy("Restored")),
    ("Destroyed", "Destruction", "SampleDestruction", gettext_lazy("Destroyed")),
]

#: The theme colour each custody status carries. Only "destroyed" is a warning to a reuser;
#: the rest report where the specimen is.
STATUS_VARIANTS = {
    "available": "success",
    "in_use": "info",
    "stored": "neutral",
    "destroyed": "error",
}

#: What each status means to someone hoping to re-examine the specimen.
STATUS_MEANING = {
    "available": gettext_lazy("The specimen can be requested for further study."),
    "in_use": gettext_lazy("The specimen is being worked on and may not be available."),
    "stored": gettext_lazy("The specimen is archived and can be retrieved."),
    "destroyed": gettext_lazy("The specimen no longer exists. Its data remains."),
    "unknown": gettext_lazy("Where the specimen is now has not been recorded."),
}


def build(request, sample, can_manage):
    from fairdm.core.project.plugins import project_is_visible

    user = request.user
    entries = shared.credits(sample)
    descriptions = {d.type: d.value for d in sample.descriptions.all()}
    dates = {d.type: d.value for d in sample.dates.all()}
    measurements = measurement_summary(user, sample)
    relations = related_samples(user, sample)
    # The status field hands back a vocabulary concept, not its stored string.
    status = getattr(sample.status, "name", sample.status) or "unknown"
    status_labels = dict(type(sample)._meta.get_field("status").choices)
    status_ = {
        "value": status,
        "label": status_labels.get(status, status),
        "variant": STATUS_VARIANTS.get(status),
        "meaning": STATUS_MEANING.get(status, ""),
    }
    history = shared.timeline(LIFECYCLE, dates, descriptions, entries)
    project = sample.dataset.project
    if project is not None and not project_is_visible(request, project):
        project = None
    identifiers = shared.identifiers(sample)
    igsn = next((i for i in identifiers if i["type"] == "IGSN"), None)
    collected = dates.get("Collected")
    sample_type = str(type(sample)._meta.verbose_name)

    parents = [{"label": _("Dataset"), "record": sample.dataset}]
    if project is not None:
        parents.append({"label": _("Project"), "record": project})

    citation_text = shared.citation(
        request,
        authors=shared.with_role(entries, "Collection"),
        year=getattr(getattr(collected, "date", None), "year", None) or sample.added.year,
        title=f"{sample.name} [{sample_type}]",
        link=igsn["link"] if igsn else request.build_absolute_uri(sample.get_absolute_url()),
    )
    citation = {"title": _("Cite this sample"), "text": citation_text}
    if not igsn:
        citation["note"] = _(
            "This sample has no IGSN, so the citation points at this page. An IGSN gives the "
            "physical specimen an identifier that outlives the portal."
        )

    return {
        "record": sample,
        "overview_icon": "sample",
        "can_manage": can_manage,
        "sample_type": sample_type,
        "status": status_,
        "lifecycle": history,
        "notes": descriptions.get("Other"),
        "measurements": measurements,
        "relations": relations,
        "location": sample.location,
        "project": project,
        "counts": {
            "measurements": measurements["total"],
            "measurements_desc": ngettext("%(n)s type", "%(n)s types", len(measurements["types"]))
            % {"n": len(measurements["types"])}
            if measurements["types"]
            else _("None yet"),
            "related": len(relations["parents"]) + len(relations["children"]),
            "related_desc": relations_summary(relations),
            "people": len(entries),
        },
        "citation": citation,
        "identifiers": identifiers,
        "license": sample.dataset.license,
        "license_note": _("from its dataset"),
        "access_text": _("Open to everyone.")
        if sample.dataset.data_is_public
        else _("Its dataset's team only, until the dataset is published."),
        "api_url": shared.safe_reverse("api:sample-detail", uuid=sample.uuid),
        "people": shared.people(entries),
        "parents": parents,
        "details": [
            {"label": _("Custody"), "text": status_["label"], "note": status_["meaning"]},
            {"label": _("Type"), "text": sample_type[:1].upper() + sample_type[1:]},
            {"label": _("Added"), "date": sample.added},
            {"label": _("Last updated"), "date": sample.modified},
        ],
    }


def measurement_summary(user, sample):
    """Measurements made on this sample, grouped by type.

    A measurement can belong to a different dataset than its sample, which is how one team
    measures another team's specimens. Each is shown only if the viewer may see its own dataset,
    and being on the sample's dataset team opens nothing else.
    """
    queryset = (
        Measurement.objects.filter(sample=sample).visible_to(user).select_related("dataset")
    )
    groups = {}
    for measurement in queryset.order_by("-added"):
        model = type(measurement)
        group = groups.setdefault(
            model,
            {"label": str(model._meta.verbose_name_plural), "items": [], "count": 0},
        )
        group["count"] += 1
        if len(group["items"]) < 5:
            group["items"].append(
                {"measurement": measurement, "elsewhere": measurement.dataset_id != sample.dataset_id}
            )
    types = sorted(groups.values(), key=lambda g: -g["count"])
    return {"types": types, "total": sum(g["count"] for g in types)}


def related_samples(user, sample):
    """Parents and subsamples. Either may sit in another dataset, so each is checked against its
    own dataset. One the viewer may not see is described, never named or linked, and isn't
    counted."""
    parents = [
        r.target_id for r in SampleRelation.objects.filter(source=sample, type="child_of")
    ]
    children = [
        r.source_id for r in SampleRelation.objects.filter(target=sample, type="child_of")
    ]
    visible = Sample.objects.filter(pk__in=parents + children).visible_to(user).in_bulk()

    def entries(pks):
        shown = [visible[pk] for pk in pks if pk in visible]
        return [
            {"sample": s, "type": str(type(s)._meta.verbose_name)} for s in shown
        ], len(pks) - len(shown)

    parent_entries, hidden_parents = entries(parents)
    child_entries, hidden_children = entries(children)
    return {
        "parents": parent_entries,
        "children": child_entries,
        "hidden": hidden_parents + hidden_children,
    }


def relations_summary(relations):
    parts = []
    if relations["parents"]:
        parts.append(
            ngettext("%(n)s parent", "%(n)s parents", len(relations["parents"]))
            % {"n": len(relations["parents"])}
        )
    if relations["children"]:
        parts.append(
            ngettext("%(n)s subsample", "%(n)s subsamples", len(relations["children"]))
            % {"n": len(relations["children"])}
        )
    return " · ".join(parts) or _("None recorded")
