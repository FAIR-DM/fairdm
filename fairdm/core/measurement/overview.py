"""What the measurement overview page draws, from the base ``Measurement`` model alone.

Everything here reads fields every measurement has, plus what the registry says about the
measurement's type. What a particular type adds (an element and its concentration, an isotope
ratio) is drawn by that type's own template, which extends
``measurement/measurement_overview.html`` and fills its blocks — see
``MeasurementDetailView.get_template_names``.

A reuser asks four things of a single measurement: what the result was, what it was measured
on, how it was measured, and whether they can cite and reuse it. The page answers them in that
order.
"""

from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from fairdm.contrib.contributors.models import Contributor
from fairdm.contrib.plugins.access import has_perm
from fairdm.registry import registry
from fairdm.utils.choices import Visibility

from .models import Measurement

#: Each step in how a measurement was made: its date type, the contributor role that performs
#: it, the description type that explains it, and what the page calls it. The measurement
#: vocabularies describe the same procedure three ways, so the page puts them back together.
PROCEDURE = [
    ("Setup", "MeasurementPreparation", "MeasurementSetup", gettext_lazy("Set up")),
    (None, "MeasurementCollection", "MeasurementConditions", gettext_lazy("Measured")),
    ("TearDown", None, "MeasurementTearDown", gettext_lazy("Taken down")),
]

#: Rows shown in the list of other measurements made on the same sample.
SIBLINGS = 8


def dataset_is_open(dataset):
    return dataset.visibility == Visibility.PUBLIC and dataset.published


def is_team(request, dataset):
    return has_perm(request, "dataset.view_dataset", dataset) or has_perm(
        request, "dataset.change_dataset", dataset
    )


def measurement_is_visible(request, measurement):
    """A measurement follows its own dataset, not its sample's: open to everyone once that
    dataset is public and published, and otherwise only to the dataset's team."""
    return dataset_is_open(measurement.dataset) or is_team(request, measurement.dataset)


def build(request, measurement):
    can_manage = has_perm(request, "dataset.change_dataset", measurement.dataset)
    contributions = list(measurement.contributors.prefetch_related("roles"))
    people = Contributor.objects.in_bulk([c.contributor_id for c in contributions])
    credits = [
        {"contributor": people[c.contributor_id], "roles": {r.name: r.label for r in c.roles.all()}}
        for c in contributions
    ]
    descriptions = {d.type: d.value for d in measurement.descriptions.all()}
    dates = {d.type: d.value for d in measurement.dates.all()}
    sample = measurement.sample
    return {
        "can_manage": can_manage,
        "measurement_type": str(type(measurement)._meta.verbose_name),
        "result": result(measurement),
        "method": method(measurement),
        "procedure": procedure(dates, descriptions, credits),
        "notes": descriptions.get("Other"),
        "credits": credits,
        "sample": sample,
        "sample_type": str(type(sample)._meta.verbose_name),
        "sample_visible": dataset_is_open(sample.dataset) or is_team(request, sample.dataset),
        "other_dataset": sample.dataset_id != measurement.dataset_id,
        "siblings": siblings(request, measurement, can_manage),
        "identifiers": identifiers(measurement),
        "citation": citation(request, measurement, credits, dates),
    }


def result(measurement):
    """The value, when the measurement's type declares one.

    ``Measurement.get_value`` is part of the base model's contract: a type that defines ``value``
    (and optionally ``uncertainty``) gets its result shown here with no template of its own. A
    type that records its result some other way leaves this empty and fills the
    ``measurement.result`` block itself.
    """
    if getattr(measurement, "value", None) is None:
        return None
    return {"text": measurement.print_value()}


def method(measurement):
    """What the registry says about how this type of measurement is made, and by whose rules."""
    model = type(measurement)
    if not registry.is_registered(model):
        return None
    config = registry.get_for_model(model)
    metadata = config.metadata
    if not metadata:
        return {"description": config.description or ""}
    return {
        "description": metadata.description,
        "authority": metadata.authority,
        "citation": metadata.citation,
        "keywords": metadata.keywords,
    }


def procedure(dates, descriptions, credits):
    steps = []
    for date_type, role, description_type, label in PROCEDURE:
        date = dates.get(date_type) if date_type else None
        who = [c["contributor"] for c in credits if role and role in c["roles"]]
        note = descriptions.get(description_type)
        if date or who or note:
            steps.append(
                {
                    "label": label,
                    "date": date,
                    "day": date.date if date is not None and date.precision == 2 else None,
                    "people": who,
                    "note": note,
                }
            )
    return steps


def siblings(request, measurement, can_manage):
    """Other measurements made on the same sample, most recent first — the context a single
    value is read against. A visitor sees only those whose own dataset is released."""
    queryset = (
        Measurement.objects.filter(sample_id=measurement.sample_id)
        .exclude(pk=measurement.pk)
        .select_related("dataset")
        .order_by("-added")
    )
    if not can_manage:
        queryset = queryset.filter(dataset__visibility=Visibility.PUBLIC, dataset__published=True)
    total = queryset.count()
    rows = [
        {
            "measurement": m,
            "type": str(type(m)._meta.verbose_name),
            "same_type": type(m) is type(measurement),
        }
        for m in queryset[:SIBLINGS]
    ]
    return {"rows": rows, "more": max(total - SIBLINGS, 0), "total": total}


def identifiers(measurement):
    return [
        {
            "type": i.type,
            "value": i.value,
            "link": f"https://doi.org/{i.value}" if i.value.startswith("10.") else None,
        }
        for i in measurement.identifiers.all()
    ]


def format_authors(contributors):
    """"Keller, A., Brandt, L. & Demir, Y." — the DataCite creator list as a reader writes it."""
    names = []
    for contributor in contributors:
        last, first = getattr(contributor, "last_name", ""), getattr(contributor, "first_name", "")
        names.append(f"{last}, {first[0]}." if last and first else str(contributor))
    if len(names) > 1:
        return ", ".join(names[:-1]) + " & " + names[-1]
    return names[0] if names else ""


def citation(request, measurement, credits, dates):
    """Who measured it (Year). Name [type] of <sample>. Publisher. Identifier."""
    measurers = [c["contributor"] for c in credits if "MeasurementCollection" in c["roles"]]
    setup = dates.get("Setup")
    year = getattr(getattr(setup, "date", None), "year", None) or measurement.added.year
    doi = next((i.value for i in measurement.identifiers.all() if i.type == "DOI"), None)
    link = f"https://doi.org/{doi}" if doi else request.build_absolute_uri(measurement.get_absolute_url())
    authors = format_authors(measurers)
    publisher = getattr(getattr(request, "site", None), "name", "") or ""
    title = _("%(name)s [%(type)s] of %(sample)s") % {
        "name": measurement.name,
        "type": type(measurement)._meta.verbose_name,
        "sample": measurement.sample,
    }
    parts = [f"{authors} ({year})." if authors else f"({year}).", f"{title}.", f"{publisher}.", link]
    return {"text": " ".join(p for p in parts if p.strip(". ")), "has_doi": bool(doi)}
