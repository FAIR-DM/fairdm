"""What the dataset overview page draws, gathered in one place.

A dataset is the unit a portal cites and distributes, and it has no samples or measurements page of
its own, so its overview carries the data as well as the record: a preview of every record type it
holds, built from the registry's own table for that type, and a summary of each type's fields.
Nothing here is written for a particular portal's types — every sample and measurement type a
portal registers renders the same way.

Two gates decide what a visitor sees. Visibility governs the metadata; ``published`` governs the
data. A public, unpublished dataset therefore shows its description, its field summaries and its
counts to everyone, and its rows and value ranges only to its team.
"""

from collections import OrderedDict

from django.contrib.contenttypes.models import ContentType
from django.db import models as dj_models
from django.db.models import Max, Min
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from fairdm.core import overview as shared
from fairdm.core.measurement.models import Measurement
from fairdm.core.overview import (
    as_date,
    composition_chart,
    sentence_case,
    contributions_of,
    format_authors,
    is_person,
    json_ld,
    roles_of,
    safe_reverse,
)
from fairdm.core.sample.models import Sample
from fairdm.registry import registry
from fairdm.utils.choices import Visibility

from .models import Dataset, DatasetDescription, DatasetLiteratureRelation

#: Rows shown in each record type's preview.
PREVIEW_ROWS = 10

#: Fields every record carries that say nothing about the data itself.
BOOKKEEPING_FIELDS = {"id", "uuid", "name", "dataset", "sample", "added", "modified", "options"}

#: The order a reuser wants people in: who made it, who to write to, then everyone else.
ROLE_ORDER = ["Creator", "ContactPerson"]


def build(request, dataset, can_manage):
    can_see_data = dataset.data_is_public or can_manage
    samples = Sample.objects.filter(dataset=dataset)
    measurements = Measurement.objects.filter(dataset=dataset)
    data_types = record_types(dataset, samples, measurements, can_see_data)

    context = {
        "can_manage": can_manage,
        "can_see_data": can_see_data,
        "access": access(dataset),
        "descriptions": descriptions(dataset),
        "dates": dates(dataset),
        "team": team(dataset),
        "identifiers": list(dataset.identifiers.all()),
        "literature": literature(dataset),
        "data_types": data_types,
        "counts": counts(samples, measurements, data_types),
        "composition_chart": composition_chart(samples, measurements)
        if len(data_types) > 1
        else None,
        "project_info": project_info(request, dataset, can_manage),
        "api_url": safe_reverse("api:dataset-detail", uuid=dataset.uuid),
        "urls": {
            "update": safe_reverse("dataset:overview-update", uuid=dataset.uuid),
            "descriptions": safe_reverse("dataset:overview-descriptions", uuid=dataset.uuid),
            "delete": safe_reverse("dataset:overview-delete", uuid=dataset.uuid),
        },
    }
    context["counts"]["publications"] = len(context["literature"]["items"])
    context["citation"] = citation(request, dataset, context)
    context["json_ld"] = json_ld(schema_org(request, dataset, context))
    if can_manage and not dataset.data_is_public:
        context["readiness"] = readiness(dataset, context)
    context.update(shared_context(request, dataset, context))
    return context


ACCESS_TEXT = {
    "published": _("Open. Every record is shown on this page and through the API."),
    "public": _("Description only, until the dataset is published."),
    "private": _("The team only."),
}


def shared_context(request, dataset, context):
    """The keys every overview page provides, which the shared skeleton and cards read."""
    citation_ = context["citation"]
    result = {
        "record": dataset,
        "overview_icon": "dataset",
        "has_charts": bool(context["composition_chart"]),
        "citation": {"title": _("Cite this dataset"), "text": citation_["text"]},
        "identifiers": shared.identifiers(dataset),
        "license": dataset.license,
        "access_text": ACCESS_TEXT[context["access"]["state"]],
        "people": shared.people(shared.credits(dataset), named_roles=ROLE_ORDER),
        "parents": [],
        "details": dataset_details(dataset, context["dates"]),
    }
    if citation_["from_reference"]:
        result["citation"]["note"] = _("Cite the data publication above rather than this page.")
    elif not citation_["has_doi"]:
        result["citation"]["note"] = _(
            "This dataset has no DOI yet, so the citation points at this page. It gets one when "
            "it is published."
        )
    info = context["project_info"]
    if info:
        project = info["project"]
        parent = {
            "label": _("Project"),
            "record": project,
            "badge": project.get_status_display(),
            "badge_variant": project.status_badge_variant,
        }
        if info["siblings"]:
            parent["detail"] = ngettext(
                "%(n)s other dataset in this project",
                "%(n)s other datasets in this project",
                info["siblings"],
            ) % {"n": info["siblings"]}
            parent["detail_url"] = project.get_absolute_url()
        result["parents"].append(parent)
    if "readiness" in context:
        readiness_ = context["readiness"]
        readiness_["title"] = _("Ready to publish?")
        if readiness_["ready"]:
            readiness_["summary"] = _("Everything required is in place.")
        else:
            readiness_["summary"] = ngettext(
                "%(n)s required item missing",
                "%(n)s required items missing",
                readiness_["missing_required"],
            ) % {"n": readiness_["missing_required"]}
        readiness_["about"] = _(
            "What a data repository needs before it can publish this dataset and give it a DOI."
        )
        result["readiness"] = readiness_
    return result


def dataset_details(dataset, dates_):
    rows = []
    if dates_["collection_start"]:
        rows.append({"label": _("Collected"), "date": dates_["collection_start"], "until": dates_["collection_end"]})
    for key, label in (
        ("submitted", _("Submitted")),
        ("published", _("Published")),
        ("available", _("Available from")),
    ):
        if dates_[key]:
            rows.append({"label": label, "date": dates_[key]})
    rows.append({"label": _("Added"), "date": dataset.added})
    rows.append({"label": _("Last updated"), "date": dataset.modified})
    return rows


def access(dataset):
    """The dataset's access state, in the words the page uses for it everywhere."""
    if dataset.visibility != Visibility.PUBLIC:
        return {"state": "private", "label": _("Private")}
    if dataset.data_is_public:
        return {"state": "published", "label": _("Published")}
    return {"state": "public", "label": _("Public, data not yet published")}


def descriptions(dataset):
    by_type = {d.type: d.value for d in dataset.descriptions.all()}
    labels = dict(DatasetDescription.VOCABULARY.choices)
    return [
        {"type": t, "label": labels.get(t, t), "value": by_type[t]}
        for t in DatasetDescription.VOCABULARY.values
        if by_type.get(t)
    ]


def dates(dataset):
    values = {d.type: d.value for d in dataset.dates.all()}
    return {
        "collection_start": as_date(values.get("CollectionStart")),
        "collection_end": as_date(values.get("CollectionEnd")),
        "available": as_date(values.get("Available")),
        "submitted": as_date(values.get("Submitted")),
        "published": as_date(values.get("Published")),
        "withdrawn": as_date(values.get("Withdrawn")),
    }


def team(dataset):
    """Creators first, then the contact person, then everyone else by their first role."""
    contributions = contributions_of(dataset)
    creators, contact, others = [], None, []
    for contribution in contributions:
        roles = roles_of(contribution)
        entry = {
            "contributor": contribution.contributor,
            "roles": [r.label for r in contribution.roles.all()],
        }
        if "Creator" in roles:
            creators.append(entry)
        if "ContactPerson" in roles and contact is None:
            contact = entry
        if not roles & set(ROLE_ORDER):
            others.append(entry)
    return {
        "creators": creators,
        "contact": contact if contact and contact not in creators else None,
        "has_contact": contact is not None,
        "others": others,
        "total": len(contributions),
        "people": sum(1 for c in contributions if is_person(c.contributor)),
        "organizations": sum(1 for c in contributions if not is_person(c.contributor)),
    }


#: DataCite relation types read from the dataset's side ("dataset IsDescribedBy paper"), which is
#: backwards for a visitor looking at the paper. Each is restated from the paper's side, and the
#: relations a reuser cares most about come first.
RELATION_WORDING = OrderedDict(
    [
        ("IsDescribedBy", _("Describes this dataset")),
        ("IsDocumentedBy", _("Documents this dataset")),
        ("IsSupplementTo", _("This dataset supplements it")),
        ("IsCitedBy", _("Cites this dataset")),
        ("IsReferencedBy", _("Refers to this dataset")),
        ("Cites", _("Cited by this dataset")),
        ("References", _("Referred to by this dataset")),
    ]
)


def literature(dataset):
    order = list(RELATION_WORDING)
    relations = sorted(
        DatasetLiteratureRelation.objects.filter(dataset=dataset).select_related("literature_item"),
        key=lambda r: order.index(r.relationship_type) if r.relationship_type in order else len(order),
    )
    items = [
        {
            "relation": RELATION_WORDING.get(
                relation.relationship_type, relation.get_relationship_type_display()
            ),
            "item": relation.literature_item,
            "doi": relation.literature_item.get_doi(),
            "year": (relation.literature_item.item.get("issued", {}).get("date-parts") or [[None]])[0][0],
        }
        for relation in relations
    ]
    return {"items": items}


def field_kind(field):
    if getattr(field, "base_units", None):
        return _("Quantity")
    if field.choices:
        return _("Choice")
    if isinstance(field, dj_models.BooleanField):
        return _("Yes / no")
    if isinstance(field, (dj_models.IntegerField, dj_models.FloatField, dj_models.DecimalField)):
        return _("Number")
    if isinstance(field, dj_models.DateTimeField):
        return _("Date and time")
    if isinstance(field, dj_models.DateField):
        return _("Date")
    if isinstance(field, dj_models.ForeignKey):
        return _("Link")
    return _("Text")


def field_summary(model, config, queryset, can_see_data):
    """One row per field a reuser has to understand: what it means, what kind of value, the unit
    and, for numbers, the range this dataset actually spans."""
    names = [n for n in config.resolve_fields("table") if n not in BOOKKEEPING_FIELDS and "__" not in n]
    rows, numeric = [], []
    for name in names:
        try:
            field = model._meta.get_field(name)
        except Exception:  # a table column that isn't a model field — nothing to describe
            continue
        kind = field_kind(field)
        row = {
            "name": name,
            "label": str(field.verbose_name).capitalize(),
            "help": str(field.help_text or ""),
            "kind": kind,
            "unit": str(getattr(field, "base_units", "") or ""),
            "range": None,
        }
        if kind == _("Number"):
            numeric.append(name)
        rows.append(row)
    if can_see_data and numeric and queryset.exists():
        aggregates = queryset.aggregate(
            **{f"{n}__min": Min(n) for n in numeric}, **{f"{n}__max": Max(n) for n in numeric}
        )
        for row in rows:
            low, high = aggregates.get(f"{row['name']}__min"), aggregates.get(f"{row['name']}__max")
            if low is not None and high is not None:
                row["range"] = (low, high)
    return rows


def preview_table(config, queryset):
    table_class = config.get_table_class()
    table = table_class(queryset[:PREVIEW_ROWS], orderable=False)
    # The dataset column names the page the reader is already on.
    for column in ("dataset",):
        if column in table.columns.names():
            table.columns.hide(column)
    return table


def record_types(dataset, samples, measurements, can_see_data):
    """Every sample and measurement type this dataset holds, largest first, each described by
    its registry configuration so any portal's types render without a template of their own."""
    result = []
    for kind, queryset in (("sample", samples), ("measurement", measurements)):
        rows = (
            queryset.values("polymorphic_ctype")
            .annotate(n=dj_models.Count("pk"))
            .order_by("-n")
        )
        for row in rows:
            model = ContentType.objects.get_for_id(row["polymorphic_ctype"]).model_class()
            if model is None or not registry.is_registered(model):
                continue
            config = registry.get_for_model(model)
            typed = model.objects.filter(dataset=dataset).order_by("pk")
            metadata = config.metadata
            result.append(
                {
                    "kind": kind,
                    "slug": config.get_slug(),
                    "label": sentence_case(model._meta.verbose_name_plural),
                    "count": row["n"],
                    "description": config.get_description() if (metadata and metadata.description) or config.description else "",
                    "authority": metadata.authority if metadata else None,
                    "schema_citation": metadata.citation if metadata else None,
                    "fields": field_summary(model, config, typed, can_see_data),
                    "table": preview_table(config, typed) if can_see_data else None,
                }
            )
    return result


def counts(samples, measurements, data_types):
    sample_types = sum(1 for t in data_types if t["kind"] == "sample")
    measurement_types = sum(1 for t in data_types if t["kind"] == "measurement")

    def types(n):
        return ngettext("%(n)s type", "%(n)s types", n) % {"n": n} if n else _("None yet")

    return {
        "samples": samples.count(),
        "samples_desc": types(sample_types),
        "measurements": measurements.count(),
        "measurements_desc": types(measurement_types),
    }


def project_info(request, dataset, can_manage):
    """The parent project, when the viewer may see it. Nothing ties a dataset's visibility to
    its project's, so a public dataset can sit in a private project that must not be named."""
    from fairdm.core.project.plugins import project_is_visible

    project = dataset.project
    if project is None or not project_is_visible(request, project):
        return None
    siblings = Dataset.all_objects.filter(project=project).exclude(pk=dataset.pk)
    if not can_manage:
        siblings = siblings.filter(visibility=Visibility.PUBLIC)
    return {"project": project, "siblings": siblings.count()}


def citation(request, dataset, context):
    """The dataset's own data publication when it has one; otherwise a DataCite citation:
    Creators (Year). Title. Publisher. Identifier."""
    if dataset.reference_id:
        reference = dataset.reference
        doi = reference.get_doi()
        return {
            "text": str(reference),
            "link": f"https://doi.org/{doi}" if doi else None,
            "has_doi": bool(doi),
            "creators": len(context["team"]["creators"]),
            "from_reference": True,
        }
    creators = [entry["contributor"] for entry in context["team"]["creators"]]
    dates_ = context["dates"]
    when = dates_["published"] or dates_["available"]
    year = when.year if when else dataset.added.year
    doi = next((i.value for i in context["identifiers"] if i.type == "DOI"), None)
    link = f"https://doi.org/{doi}" if doi else request.build_absolute_uri(dataset.get_absolute_url())
    authors = format_authors(creators)
    publisher = getattr(getattr(request, "site", None), "name", "") or ""
    parts = [f"{authors} ({year})." if authors else f"({year}).", f"{dataset.name}.", f"{publisher}.", link]
    return {
        "text": " ".join(p for p in parts if p.strip(". ")),
        "link": link,
        "has_doi": bool(doi),
        "creators": len(creators),
        "from_reference": False,
    }


def schema_org(request, dataset, context):
    """schema.org ``Dataset`` — the shape Google Dataset Search and most harvesters read."""
    url = request.build_absolute_uri(dataset.get_absolute_url())
    abstract = next((d["value"] for d in context["descriptions"] if d["type"] == "Abstract"), "")
    data = OrderedDict(
        [
            ("@context", "https://schema.org/"),
            ("@type", "Dataset"),
            ("name", dataset.name),
            ("url", url),
            ("identifier", context["citation"]["link"] or url),
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
    for entry in context["team"]["creators"]:
        person = entry["contributor"]
        if is_person(person):
            creators.append(
                {"@type": "Person", "name": str(person), "givenName": person.first_name, "familyName": person.last_name}
            )
        else:
            creators.append({"@type": "Organization", "name": str(person)})
    if creators:
        data["creator"] = creators
    start, end = context["dates"]["collection_start"], context["dates"]["collection_end"]
    if start:
        data["temporalCoverage"] = f"{start.isoformat()}/{end.isoformat() if end else '..'}"
    # Field names only: a visitor on an unpublished dataset may read what each field means, never
    # the range of values it holds.
    variables = [f["label"] for t in context["data_types"] for f in t["fields"]]
    if variables:
        data["variableMeasured"] = variables
    if context["project_info"]:
        data["isPartOf"] = {
            "@type": "ResearchProject",
            "name": dataset.project.name,
            "url": request.build_absolute_uri(dataset.project.get_absolute_url()),
        }
    site = getattr(request, "site", None)
    if site is not None:
        data["includedInDataCatalog"] = {"@type": "DataCatalog", "name": site.name}
    return data


def readiness(dataset, context):
    """What has to be in place before the dataset is published, and whether it is yet.

    Items come from DataCite's mandatory and recommended properties and from what a formal
    publication would need to submit the record unaided. Items with nowhere to fix them yet carry
    no link.
    """
    urls = context["urls"]
    described = {d["type"] for d in context["descriptions"]}
    dates_ = context["dates"]
    items = [
        (_("An abstract describes the data"), "Abstract" in described, urls["descriptions"], True),
        (_("The methods are described"), "Methods" in described, urls["descriptions"], True),
        (_("At least one creator is credited"), bool(context["team"]["creators"]), None, True),
        (_("Someone is named as the contact"), context["team"]["has_contact"], None, True),
        (_("A licence is chosen"), dataset.license_id is not None, urls["update"], True),
        (_("It holds samples or measurements"), bool(context["data_types"]), None, True),
        (_("The collection period is recorded"), dates_["collection_start"] is not None, urls["update"], True),
        (_("Keywords make it findable"), dataset.keywords.exists(), None, False),
        (_("A related publication is linked"), bool(context["literature"]["items"]), None, False),
        (_("The dataset is public"), dataset.visibility == Visibility.PUBLIC, urls["update"], True),
    ]
    required = [i for i in items if i[3]]
    done_required = sum(1 for i in required if i[1])
    done = sum(1 for i in items if i[1])
    return {
        "items": [
            {"label": label, "done": ok, "url": url, "required": req} for label, ok, url, req in items
        ],
        "done": done,
        "total": len(items),
        "percent": round(100 * done / len(items)),
        "ready": done_required == len(required),
        "missing_required": len(required) - done_required,
    }
