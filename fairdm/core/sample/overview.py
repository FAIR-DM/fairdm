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

from fairdm.contrib.contributors.models import Contributor
from fairdm.contrib.plugins.access import has_perm
from fairdm.core.measurement.models import Measurement
from fairdm.utils.choices import Visibility

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


def sample_is_visible(request, obj):
    """A sample follows its dataset: open to everyone once the dataset is public and published,
    and otherwise only to the dataset's team."""
    if obj is None:
        return True
    dataset = obj.dataset
    if dataset.visibility == Visibility.PUBLIC and dataset.published:
        return True
    return has_perm(request, "dataset.view_dataset", dataset) or has_perm(
        request, "dataset.change_dataset", dataset
    )


def build(request, sample, can_manage):
    contributions = list(sample.contributors.prefetch_related("roles"))
    people = Contributor.objects.in_bulk([c.contributor_id for c in contributions])
    credits = [
        {"contributor": people[c.contributor_id], "roles": {r.name: r.label for r in c.roles.all()}}
        for c in contributions
    ]
    descriptions = {d.type: d.value for d in sample.descriptions.all()}
    dates = {d.type: d.value for d in sample.dates.all()}
    measurements = measurement_summary(request, sample, can_manage)
    relations = related_samples(sample)
    # The status field hands back a vocabulary concept, not its stored string.
    status = getattr(sample.status, "name", sample.status) or "unknown"
    status_labels = dict(type(sample)._meta.get_field("status").choices)
    return {
        "can_manage": can_manage,
        "sample_type": str(type(sample)._meta.verbose_name),
        "status": {
            "value": status,
            "label": status_labels.get(status, status),
            "variant": STATUS_VARIANTS.get(status),
            "meaning": STATUS_MEANING.get(status, ""),
        },
        "lifecycle": lifecycle(sample, dates, descriptions, credits),
        "notes": descriptions.get("Other"),
        "credits": credits,
        "identifiers": identifiers(sample),
        "measurements": measurements,
        "relations": relations,
        "location": sample.location,
        "counts": {
            "measurements": measurements["total"],
            "measurements_desc": ngettext("%(n)s type", "%(n)s types", len(measurements["types"]))
            % {"n": len(measurements["types"])}
            if measurements["types"]
            else _("None yet"),
            "related": len(relations["parents"]) + len(relations["children"]),
            "related_desc": relations_summary(relations),
            "people": len(credits),
        },
        "citation": citation(request, sample, credits, dates),
    }


def lifecycle(sample, dates, descriptions, credits):
    steps = []
    for date_type, role, description_type, label in LIFECYCLE:
        who = [c["contributor"] for c in credits if role and role in c["roles"]]
        date = dates.get(date_type)
        note = descriptions.get(description_type) if description_type else None
        if date or who or note:
            steps.append(
                {
                    "label": label,
                    "date": date,
                    # A full date is formatted by the template; a year or month alone is shown as
                    # recorded, rather than padded out to a day nobody wrote down.
                    "day": date.date if date is not None and date.precision == 2 else None,
                    "people": who,
                    "note": note,
                }
            )
    dated = sorted((s for s in steps if s["date"]), key=lambda s: str(s["date"]))
    undated = [s for s in steps if not s["date"]]
    return dated + undated


def identifiers(sample):
    result = []
    for identifier in sample.identifiers.all():
        value = identifier.value
        # An IGSN is a DataCite DOI since 2023, so both resolve through doi.org.
        link = f"https://doi.org/{value}" if value.startswith("10.") else None
        result.append({"type": identifier.type, "value": value, "link": link})
    return result


def measurement_summary(request, sample, can_manage):
    """Measurements made on this sample, grouped by type.

    A measurement can belong to a different dataset than its sample — that is how one team
    measures another team's specimens — so each carries its dataset, and a visitor sees only
    measurements whose own dataset is released to them.
    """
    queryset = Measurement.objects.filter(sample=sample).select_related("dataset")
    if not can_manage:
        queryset = queryset.filter(dataset__visibility=Visibility.PUBLIC, dataset__published=True)
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


def related_samples(sample):
    parents = [
        r.target
        for r in SampleRelation.objects.filter(source=sample, type="child_of").select_related("target")
    ]
    children = [
        r.source
        for r in SampleRelation.objects.filter(target=sample, type="child_of").select_related("source")
    ]
    # The relation rows hold the polymorphic base; fetch each sample as its own type.
    real = Sample.objects.in_bulk([s.pk for s in parents + children])
    def entry(stub):
        sample = real[stub.pk]
        return {"sample": sample, "type": str(type(sample)._meta.verbose_name)}

    return {
        "parents": [entry(s) for s in parents],
        "children": [entry(s) for s in children],
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


def format_authors(contributors):
    """"Keller, A., Brandt, L. & Demir, Y." — the DataCite creator list as a reader writes it."""
    names = []
    for contributor in contributors:
        last, first = getattr(contributor, "last_name", ""), getattr(contributor, "first_name", "")
        names.append(f"{last}, {first[0]}." if last and first else str(contributor))
    if len(names) > 1:
        return ", ".join(names[:-1]) + " & " + names[-1]
    return names[0] if names else ""


def citation(request, sample, credits, dates):
    """DataCite's citation for a physical object: Collectors (Year). Name [type]. Publisher.
    Identifier — the IGSN when there is one, since that is what resolves to the specimen."""
    collectors = [c["contributor"] for c in credits if "Collection" in c["roles"]]
    collected = dates.get("Collected")
    year = getattr(getattr(collected, "date", None), "year", None) or sample.added.year
    igsn = next((i.value for i in sample.identifiers.all() if i.type == "IGSN"), None)
    link = f"https://doi.org/{igsn}" if igsn else request.build_absolute_uri(sample.get_absolute_url())
    authors = format_authors(collectors)
    publisher = getattr(getattr(request, "site", None), "name", "") or ""
    parts = [
        f"{authors} ({year})." if authors else f"({year}).",
        f"{sample.name} [{type(sample)._meta.verbose_name}].",
        f"{publisher}.",
        link,
    ]
    return {"text": " ".join(p for p in parts if p.strip(". ")), "has_igsn": bool(igsn)}
