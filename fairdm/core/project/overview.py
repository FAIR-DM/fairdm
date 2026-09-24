"""What the project overview page draws, gathered in one place.

The overview is a project's landing page, read by three kinds of visitor: someone deciding
whether the data is usable to them, someone who has to cite it, and the team keeping the record
complete. Everything here is derived from the project's own records; nothing is stored.

Private records never reach a figure a visitor can see. A visitor's counts are taken over the
project's public datasets only, and the samples and measurements beneath them; a member of the
team sees everything, with the private share called out.
"""

import json
from collections import Counter, OrderedDict
from datetime import date

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from pyecharts import options as opts
from pyecharts.charts import Bar, Line

from fairdm.contrib.contributors.models import Contributor, Person
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.utils.choices import Visibility

from .models import ProjectDescription
from .transforms import to_json_ld

#: How many datasets the overview lists before handing over to the Datasets page.
DATASET_PREVIEW = 5

#: Roles that name the people a visitor should see first, in this order.
LEAD_ROLES = ["ProjectLeader", "ProjectManager"]


def build(request, project, can_manage):
    datasets = Dataset.all_objects.filter(project=project)
    if not can_manage:
        datasets = datasets.filter(visibility=Visibility.PUBLIC)
    dataset_ids = list(datasets.values_list("pk", flat=True))
    samples = Sample.objects.filter(dataset_id__in=dataset_ids)
    measurements = Measurement.objects.filter(dataset_id__in=dataset_ids)

    context = {
        "can_manage": can_manage,
        "descriptions": descriptions(project),
        "timeline": timeline(project),
        "team": team(project),
        "funding": project.funding or [],
        "identifiers": list(project.identifiers.all()),
        "counts": counts(datasets, samples, measurements, can_manage),
        "datasets_preview": datasets_preview(datasets),
        "licenses": licenses(datasets),
        "composition_chart": composition_chart(samples, measurements),
        "growth_chart": growth_chart(samples, measurements),
        "citation": citation(request, project),
        "json_ld": json.dumps(to_json_ld(project), default=str)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026"),
        "api_url": safe_reverse(f"api:{project._meta.model_name}-detail", uuid=project.uuid),
        "urls": {
            "datasets": safe_reverse("project:dataset-list", uuid=project.uuid),
            "contributors": safe_reverse("project:contribution-list", uuid=project.uuid),
            "update": safe_reverse("project:overview-update", uuid=project.uuid),
            "descriptions": safe_reverse("project:overview-descriptions", uuid=project.uuid),
            "delete": safe_reverse("project:overview-delete", uuid=project.uuid),
            "add_dataset": safe_reverse("dataset-create"),
        },
    }
    if can_manage:
        context["readiness"] = readiness(project, context)
    return context


def safe_reverse(name, **kwargs):
    try:
        return reverse(name, kwargs=kwargs or None)
    except NoReverseMatch:
        return None


def descriptions(project):
    """The project's descriptions in the vocabulary's own order, abstract first."""
    by_type = {d.type: d.value for d in project.descriptions.all()}
    labels = dict(ProjectDescription.VOCABULARY.choices)
    return [
        {"type": t, "label": labels.get(t, t), "value": by_type[t]}
        for t in ProjectDescription.VOCABULARY.values
        if by_type.get(t)
    ]


def as_date(partial):
    if partial is None:
        return None
    value = getattr(partial, "date", partial)
    return value if isinstance(value, date) else None


def timeline(project):
    """Start, end and how far through the project today is, in whole years."""
    dates = {d.type: d.value for d in project.dates.all()}
    start, end = dates.get("Start"), dates.get("End")
    start_d, end_d = as_date(start), as_date(end)
    result = {
        "start": start,
        "end": end,
        "start_date": start_d,
        "end_date": end_d,
        "percent": None,
        "year": None,
        "years": None,
    }
    if start_d and end_d and end_d > start_d:
        today = timezone.localdate()
        total = (end_d - start_d).days
        elapsed = min(max((today - start_d).days, 0), total)
        result["percent"] = round(100 * elapsed / total)
        result["years"] = max(round(total / 365.25), 1)
        result["year"] = min(elapsed // 365 + 1, result["years"])
        result["finished"] = today > end_d
        result["not_started"] = today < start_d
    return result


def contributions_of(project):
    """The project's credits with each contributor as its own subtype, Person or Organization.

    ``select_related`` stops at the polymorphic base, which has neither a person's name parts nor
    a way to tell the two apart, so the real instances are fetched in one extra query.
    """
    contributions = list(project.contributors.prefetch_related("roles"))
    real = Contributor.objects.in_bulk([c.contributor_id for c in contributions])
    for contribution in contributions:
        contribution.contributor = real[contribution.contributor_id]
    return contributions


def is_person(contributor):
    return isinstance(contributor, Person)


def roles_of(contribution):
    return {role.name for role in contribution.roles.all()}


def team(project):
    """Leads and the contact person by name; everyone else as a count and a few faces."""
    contributions = contributions_of(project)
    leads, contact, others = [], None, []
    for contribution in contributions:
        roles = roles_of(contribution)
        entry = {
            "contributor": contribution.contributor,
            "roles": [r.label for r in contribution.roles.all() if r.name != "Creator"],
        }
        if "ContactPerson" in roles and contact is None:
            contact = entry
        if roles & set(LEAD_ROLES):
            leads.append(entry)
        elif "ContactPerson" not in roles:
            others.append(entry)
    leads.sort(key=lambda e: 0 if "Project Leader" in e["roles"] else 1)
    return {
        "leads": leads,
        "contact": contact if contact and contact not in leads else None,
        "contact_is_lead": bool(contact and contact in leads),
        "others": others,
        "total": len(contributions),
        "people": sum(1 for c in contributions if is_person(c.contributor)),
        "organizations": sum(1 for c in contributions if not is_person(c.contributor)),
        "has_contact": contact is not None,
    }


def counts(datasets, samples, measurements, can_manage):
    total = datasets.count()
    public = datasets.filter(visibility=Visibility.PUBLIC).count()
    published = datasets.filter(published=True).count()
    sample_types = samples.values("polymorphic_ctype").distinct().count()
    measurement_types = measurements.values("polymorphic_ctype").distinct().count()

    if can_manage and total != public:
        dataset_desc = _("%(public)s public · %(private)s private") % {
            "public": public,
            "private": total - public,
        }
    elif total:
        dataset_desc = ngettext("%(n)s published", "%(n)s published", published) % {"n": published}
    else:
        dataset_desc = _("None yet")
    return {
        "datasets": total,
        "datasets_desc": dataset_desc,
        "samples": samples.count(),
        "samples_desc": ngettext("%(n)s type", "%(n)s types", sample_types) % {"n": sample_types}
        if sample_types
        else _("None yet"),
        "measurements": measurements.count(),
        "measurements_desc": ngettext("%(n)s type", "%(n)s types", measurement_types)
        % {"n": measurement_types}
        if measurement_types
        else _("None yet"),
    }


def datasets_preview(datasets):
    rows = (
        datasets.select_related("license")
        .annotate(
            n_samples=Count("samples", distinct=True),
            n_measurements=Count("measurements", distinct=True),
        )
        .order_by("-modified")
    )
    return {"rows": list(rows[:DATASET_PREVIEW]), "more": max(rows.count() - DATASET_PREVIEW, 0)}


def licenses(datasets):
    counter = Counter(
        datasets.filter(visibility=Visibility.PUBLIC).values_list("license__name", flat=True)
    )
    unlicensed = counter.pop(None, 0)
    return {"items": counter.most_common(), "unlicensed": unlicensed}


def type_counts(queryset):
    rows = queryset.values("polymorphic_ctype").annotate(n=Count("pk")).order_by("-n")
    result = []
    for row in rows:
        model = ContentType.objects.get_for_id(row["polymorphic_ctype"]).model_class()
        result.append((str(model._meta.verbose_name_plural).capitalize(), row["n"]))
    return result


def composition_chart(samples, measurements):
    """Records by type, largest first — one hue, since the bars compare magnitude."""
    items = type_counts(samples) + type_counts(measurements)
    if not items:
        return None
    items.sort(key=lambda item: item[1])  # ECharts draws the first category at the bottom
    chart = (
        Bar()
        .add_xaxis([label for label, _ in items])
        .add_yaxis(
            _("Records"),
            [n for _, n in items],
            bar_max_width=18,
            label_opts=opts.LabelOpts(is_show=True, position="right"),
            itemstyle_opts=opts.ItemStyleOpts(border_radius=[0, 4, 4, 0]),
        )
        .reversal_axis()
        .set_global_opts(
            legend_opts=opts.LegendOpts(is_show=False),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(splitline_opts=opts.SplitLineOpts(is_show=True)),
        )
    )
    chart.options["grid"] = {"left": 8, "right": 40, "top": 8, "bottom": 8, "containLabel": True}
    return {
        "chart": chart,
        "height": f"{max(len(items) * 44 + 32, 160)}px",
        "description": "; ".join(f"{label}: {n}" for label, n in reversed(items)),
    }


def monthly(queryset):
    return OrderedDict(
        (row["month"].date() if hasattr(row["month"], "date") else row["month"], row["n"])
        for row in queryset.annotate(month=TruncMonth("added"))
        .values("month")
        .annotate(n=Count("pk"))
        .order_by("month")
    )


def growth_chart(samples, measurements):
    """Cumulative samples and measurements by month — two series on one count axis."""
    by_sample, by_measurement = monthly(samples), monthly(measurements)
    months = sorted(set(by_sample) | set(by_measurement))
    if len(months) < 2:
        return None
    # Fill the gaps so a quiet month reads as flat, not as a missing point.
    first, last = months[0], months[-1]
    months, cursor = [], first
    while cursor <= last:
        months.append(cursor)
        cursor = date(cursor.year + cursor.month // 12, cursor.month % 12 + 1, 1)

    def cumulative(series):
        total, values = 0, []
        for month in months:
            total += series.get(month, 0)
            values.append(total)
        return values

    samples_line, measurements_line = cumulative(by_sample), cumulative(by_measurement)
    line_style = opts.LineStyleOpts(width=2)
    chart = (
        Line()
        .add_xaxis([m.strftime("%b %Y") for m in months])
        .add_yaxis(
            _("Samples"), samples_line, is_symbol_show=False, linestyle_opts=line_style,
            label_opts=opts.LabelOpts(is_show=False),
        )
        .add_yaxis(
            _("Measurements"), measurements_line, is_symbol_show=False, linestyle_opts=line_style,
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            legend_opts=opts.LegendOpts(pos_left="left", pos_top="top"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(boundary_gap=False),
        )
    )
    chart.options["grid"] = {"left": 8, "right": 16, "top": 40, "bottom": 8, "containLabel": True}
    return {
        "chart": chart,
        "description": _(
            "From %(first)s to %(last)s the project grew to %(samples)s samples and "
            "%(measurements)s measurements."
        )
        % {
            "first": months[0].strftime("%B %Y"),
            "last": months[-1].strftime("%B %Y"),
            "samples": samples_line[-1],
            "measurements": measurements_line[-1],
        },
    }


def author_name(contributor):
    last = getattr(contributor, "last_name", "")
    first = getattr(contributor, "first_name", "")
    if last and first:
        return f"{last}, {first[0]}."
    return str(contributor)


def citation(request, project):
    """A DataCite-shaped citation: Creators (Year). Title. Publisher. Identifier."""
    creators = [c.contributor for c in contributions_of(project) if "Creator" in roles_of(c)]
    start = {d.type: d.value for d in project.dates.all()}.get("Start")
    year = as_date(start).year if as_date(start) else project.added.year
    doi = next((i.value for i in project.identifiers.all() if i.type == "DOI"), None)
    link = f"https://doi.org/{doi}" if doi else request.build_absolute_uri(project.get_absolute_url())
    names = [author_name(c) for c in creators]
    if len(names) > 1:
        authors = ", ".join(names[:-1]) + " & " + names[-1]
    else:
        authors = names[0] if names else ""
    publisher = getattr(getattr(request, "site", None), "name", "") or ""
    parts = [f"{authors} ({year})." if authors else f"({year}).", f"{project.name}.", f"{publisher}.", link]
    return {"text": " ".join(p for p in parts if p.strip(". ")), "link": link, "has_doi": bool(doi), "creators": len(creators)}


def readiness(project, context):
    """The metadata a harvester or a reuser looks for, and whether this project has it yet.

    Each item comes from DataCite's required and recommended properties or from what the FAIR
    principles ask of a record. Items with nowhere to fix them yet carry no link.
    """
    urls = context["urls"]
    descriptions_ = {d["type"] for d in context["descriptions"]}
    team_ = context["team"]
    counts_ = context["counts"]
    items = [
        (_("An abstract describes the project"), "Abstract" in descriptions_, urls["descriptions"]),
        (_("At least one creator is credited"), context["citation"]["creators"] > 0, urls["contributors"]),
        (_("Someone is named as the contact"), team_["has_contact"], urls["contributors"]),
        (_("A start date is recorded"), context["timeline"]["start"] is not None, urls["update"]),
        (_("Keywords make it findable"), project.keywords.exists(), None),
        (_("Funding is acknowledged"), bool(project.funding), None),
        (_("It has a persistent identifier (DOI)"), context["citation"]["has_doi"], urls["update"]),
        (_("At least one dataset is public"), Dataset.all_objects.filter(project=project, visibility=Visibility.PUBLIC).exists(), urls["datasets"]),
        (_("Every public dataset has a licence"), counts_["datasets"] > 0 and context["licenses"]["unlicensed"] == 0 and bool(context["licenses"]["items"]), urls["datasets"]),
        (_("The project is public"), project.visibility == Visibility.PUBLIC, urls["update"]),
    ]
    done = sum(1 for _, ok, _ in items if ok)
    return {
        "items": [{"label": label, "done": ok, "url": url} for label, ok, url in items],
        "done": done,
        "total": len(items),
        "percent": round(100 * done / len(items)),
    }
