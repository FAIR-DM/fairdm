"""Context the redesigned overview pages need on top of what the plugins already gather.

Prototype code: written to make the screens work, not to the repository's standards. The rebuild
moves each piece onto the plugin that owns it.
"""

import json
import re
from collections import defaultdict

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.urls import reverse
from django.utils.translation import gettext, ngettext

from fairdm.core.overview import sentence_case

CREATOR = "https://w3id.org/fairdm/vocabularies/contributor-roles/creator"


def _bibtex_escape(text):
    return str(text).replace("{", "\\{").replace("}", "\\}").replace("&", "\\&")


def citation_formats(record, kind, citation_text, credits, request):
    """Write the record's citation as APA-style text, BibTeX and RIS.

    The plain citation is the one the plugin already wrote. BibTeX and RIS are built from the same
    parts: creators (the people credited as creators, else everyone credited), year, title,
    publisher and the DOI or the page's address.
    """
    creators = [
        c["contributor"]
        for c in credits
        if any(uri.endswith("/creator") for uri in c["roles"])
    ] or [c["contributor"] for c in credits]
    year_match = re.search(r"\((\d{4})\)", citation_text or "")
    year = year_match.group(1) if year_match else str(getattr(record, "added", None).year)
    doi = None
    for identifier in record.identifiers.select_related("type").all():
        if str(identifier.value).startswith("10."):
            doi = identifier.value
            break
    url = f"https://doi.org/{doi}" if doi else request.build_absolute_uri(record.get_absolute_url())
    publisher = getattr(getattr(request, "site", None), "name", "") or "FairDM"
    title = record.name if getattr(record, "name", None) else str(record)

    def name_parts(c):
        last = getattr(c, "last_name", "") or ""
        first = getattr(c, "first_name", "") or ""
        if last:
            return last, first
        return str(c), ""

    bib_type = "@misc" if kind in ("project", "sample", "measurement") else "@dataset"
    key = re.sub(r"[^A-Za-z]", "", name_parts(creators[0])[0] if creators else "fairdm") + year
    authors = " and ".join(
        f"{_bibtex_escape(last)}, {_bibtex_escape(first)}" if first else f"{{{_bibtex_escape(last)}}}"
        for last, first in (name_parts(c) for c in creators)
    )
    bib_lines = [f"{bib_type}{{{key},"]
    if authors:
        bib_lines.append(f"  author    = {{{authors}}},")
    bib_lines += [
        f"  title     = {{{{{_bibtex_escape(title)}}}}},",
        f"  year      = {{{year}}},",
        f"  publisher = {{{_bibtex_escape(publisher)}}},",
    ]
    if doi:
        bib_lines.append(f"  doi       = {{{doi}}},")
    bib_lines.append(f"  url       = {{{url}}}")
    bib_lines.append("}")

    ris_type = {"dataset": "DATA", "project": "GEN", "sample": "GEN", "measurement": "DATA"}[kind]
    ris_lines = [f"TY  - {ris_type}"]
    for last, first in (name_parts(c) for c in creators):
        ris_lines.append(f"AU  - {last}, {first}" if first else f"AU  - {last}")
    ris_lines += [f"TI  - {title}", f"PY  - {year}", f"PB  - {publisher}"]
    if doi:
        ris_lines.append(f"DO  - {doi}")
    ris_lines += [f"UR  - {url}", "ER  - "]

    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60] or kind
    return {
        "formats": [
            {"key": "text", "label": gettext("Text"), "value": citation_text, "file": ""},
            {"key": "bibtex", "label": "BibTeX", "value": "\n".join(bib_lines), "file": f"{slug}.bib"},
            {"key": "ris", "label": "RIS", "value": "\n".join(ris_lines), "file": f"{slug}.ris"},
        ],
        "doi": doi,
        "url": url,
    }


def credits_for_panel(credits, shown=6):
    """Split the credits into the named rows and the faces after them."""
    rows = []
    for entry in credits:
        roles = list(entry["roles"].values())
        rows.append(
            {
                "contributor": entry["contributor"],
                "roles": ", ".join(sentence_case(r) for r in roles[:2])
                + (f" +{len(roles) - 2}" if len(roles) > 2 else ""),
                "affiliation": entry["affiliation"],
            }
        )
    return {
        "named": rows[:shown],
        "faces": [r["contributor"] for r in rows[shown : shown + 10]],
        "more": max(len(rows) - shown - 10, 0),
        "total": len(rows),
    }


def map_points(samples, limit=1500):
    """The samples with a location, as features for the coverage map, and how many have none."""
    with_location = samples.filter(location__isnull=False)
    features = []
    for sample in with_location.select_related("dataset")[:limit]:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [round(sample.location.x, 5), round(sample.location.y, 5)]},
                "properties": {
                    "name": str(sample),
                    "url": sample.get_absolute_url(),
                    "type": sentence_case(type(sample)._meta.verbose_name),
                    "dataset": str(sample.dataset),
                },
            }
        )
    total = samples.count()
    located = with_location.count()
    if not features:
        return {"geojson": None, "located": 0, "total": total, "missing": total}
    xs = [f["geometry"]["coordinates"][0] for f in features]
    ys = [f["geometry"]["coordinates"][1] for f in features]
    return {
        "geojson": json.dumps({"type": "FeatureCollection", "features": features}).replace("<", "\\u003c"),
        "bounds": [min(xs), min(ys), max(xs), max(ys)],
        "located": located,
        "total": total,
        "missing": total - located,
        "datasets": len({f["properties"]["dataset"] for f in features}),
    }


def activity(samples, measurements, datasets=None, limit=8):
    """Recent changes, worked out from when records were added.

    Samples and measurements added on the same day to the same dataset are one entry. A dataset
    being added is its own entry.
    """
    events = []
    for kind, queryset, icon in (("sample", samples, "sample"), ("measurement", measurements, "measurement")):
        rows = (
            queryset.annotate(day=TruncDate("added"))
            .values("day", "dataset", "dataset__name", "dataset__uuid")
            .annotate(n=Count("pk"))
            .order_by("-day")[:limit]
        )
        for row in rows:
            if kind == "sample":
                text = ngettext("%(n)s sample added", "%(n)s samples added", row["n"]) % {"n": row["n"]}
            else:
                text = ngettext("%(n)s measurement added", "%(n)s measurements added", row["n"]) % {
                    "n": row["n"]
                }
            events.append(
                {
                    "day": row["day"],
                    "kind": kind,
                    "icon": icon,
                    "text": text,
                    "target": row["dataset__name"],
                    "dataset_id": row["dataset"],
                }
            )
    from fairdm.core.models import Dataset

    by_id = Dataset.all_objects.in_bulk([e["dataset_id"] for e in events])
    for event in events:
        dataset = by_id.get(event.pop("dataset_id"))
        event["url"] = dataset.get_absolute_url() if dataset else ""
    if datasets is not None:
        for dataset in datasets.order_by("-added")[:limit]:
            events.append(
                {
                    "day": dataset.added.date() if hasattr(dataset.added, "date") else dataset.added,
                    "kind": "dataset",
                    "icon": "dataset",
                    "text": gettext("Dataset created"),
                    "target": dataset.name,
                    "url": dataset.get_absolute_url(),
                }
            )
    events.sort(key=lambda e: (e["day"], e["kind"] == "dataset"), reverse=True)
    grouped = defaultdict(list)
    for event in events[:limit]:
        grouped[event["day"]].append(event)
    return [{"day": day, "events": items} for day, items in grouped.items()]


def measurement_types(sample, user):
    """How many of the sample's visible measurements there are of each type."""
    from django.contrib.contenttypes.models import ContentType

    from fairdm.core.models import Measurement

    rows = (
        Measurement.objects.filter(sample=sample)
        .visible_to(user)
        .values("polymorphic_ctype")
        .annotate(n=Count("pk"))
        .order_by("-n")
    )
    result = []
    for row in rows:
        model = ContentType.objects.get_for_id(row["polymorphic_ctype"]).model_class()
        if model is None:
            continue
        result.append({"key": sentence_case(model._meta.verbose_name), "label": sentence_case(model._meta.verbose_name_plural), "n": row["n"]})
    return result


def primary_identifier(identifiers):
    """The identifier a reader looks for first: a DOI or IGSN that resolves."""
    for identifier in identifiers or []:
        if identifier.get("link"):
            return identifier
    return None


def mix(samples, measurements):
    """Records by type, samples and measurements apart, for the type bars."""
    from fairdm.core.plugins import RecordOverviewPlugin

    sample_rows = RecordOverviewPlugin._type_counts(samples)
    measurement_rows = RecordOverviewPlugin._type_counts(measurements)
    counts = [n for _, n in sample_rows + measurement_rows]
    if not counts:
        return None
    return {"samples": sample_rows, "measurements": measurement_rows, "max": max(counts)}


def edit_links(request, record):
    """The editing pages the viewer may open, keyed by what each edits, for the panel that shows it."""
    from fairdm.contrib.plugins import reverse as plugin_reverse
    from fairdm.contrib.plugins.access import can_open
    from fairdm.core import editing

    keys = {
        editing.EditDetails: "details",
        editing.EditDescriptions: "descriptions",
        editing.EditKeywords: "keywords",
        editing.EditKeyDates: "dates",
        editing.EditIdentifiers: "identifiers",
        editing.DeleteRecord: "delete",
    }
    may_see = can_open(editing.RecordEditingPage.overview_for(record), request, record)
    return {
        keys[page]: plugin_reverse(record, page.get_name())
        for page in editing.MENU_PAGES
        if page in keys and page.may_be_used_by(request, record, may_see)
    }
