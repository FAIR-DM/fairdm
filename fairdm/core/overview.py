"""Helpers shared by the four record overview pages: project, dataset, sample and measurement.

Each overview gathers its own context; what lives here is the handful of rules both pages apply
the same way — who a contributor really is, how an author is written in a citation, and how a
set of records is broken down by type — so the two pages never disagree about them.
"""

import json
from datetime import date

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext as _
from pyecharts import options as opts
from pyecharts.charts import Bar

from fairdm.contrib.contributors.models import Contributor, Person


def safe_reverse(name, **kwargs):
    try:
        return reverse(name, kwargs=kwargs or None)
    except NoReverseMatch:
        return None


def as_date(partial):
    if partial is None:
        return None
    value = getattr(partial, "date", partial)
    return value if isinstance(value, date) else None


def contributions_of(obj):
    """The record's credits with each contributor as its own subtype, Person or Organization.

    ``select_related`` stops at the polymorphic base, which has neither a person's name parts nor
    a way to tell the two apart, so the real instances are fetched in one extra query.
    """
    contributions = list(obj.contributors.prefetch_related("roles"))
    real = Contributor.objects.in_bulk([c.contributor_id for c in contributions])
    for contribution in contributions:
        contribution.contributor = real[contribution.contributor_id]
    return contributions


def is_person(contributor):
    return isinstance(contributor, Person)


def roles_of(contribution):
    return {role.name for role in contribution.roles.all()}


def type_counts(queryset):
    rows = queryset.values("polymorphic_ctype").annotate(n=Count("pk")).order_by("-n")
    result = []
    for row in rows:
        model = ContentType.objects.get_for_id(row["polymorphic_ctype"]).model_class()
        result.append((sentence_case(model._meta.verbose_name_plural), row["n"]))
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


def author_name(contributor):
    last = getattr(contributor, "last_name", "")
    first = getattr(contributor, "first_name", "")
    if last and first:
        return f"{last}, {first[0]}."
    return str(contributor)


def sentence_case(text):
    """Capitalise the first letter only, so "XRF measurements" keeps its acronym."""
    text = str(text)
    return text[:1].upper() + text[1:]


def format_authors(contributors):
    """"Keller, A., Oliveira, T. & Brandt, L." — the DataCite creator list as a reader writes it."""
    names = [author_name(c) for c in contributors]
    if len(names) > 1:
        return ", ".join(names[:-1]) + " & " + names[-1]
    return names[0] if names else ""


def json_ld(data):
    """Serialise ``data`` for an inline ``<script>``, with the characters that could end the
    element escaped, so user-written names and descriptions can never break out of it."""
    return (
        json.dumps(data, default=str)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def credits(obj):
    """Everyone credited on ``obj``: each contributor as its own type, with its role labels.

    Returns ``[{"contributor", "roles": {name: label}}]`` in the record's own order.
    """
    return [
        {"contributor": c.contributor, "roles": {r.name: r.label for r in c.roles.all()}}
        for c in contributions_of(obj)
    ]


def people(entries, named_roles=(), condensed=False):
    """Split credits into the people named in full and everyone else, as ``c-card.people`` draws
    them. With no ``named_roles`` everyone is named. Named people are ordered by the first of
    ``named_roles`` they hold."""
    order = list(named_roles)
    named, others = [], []
    for entry in entries:
        item = {"contributor": entry["contributor"], "roles": list(entry["roles"].values())}
        held = [order.index(name) for name in entry["roles"] if name in order]
        if not order or held:
            named.append((min(held, default=0), item))
        else:
            others.append(item)
    named.sort(key=lambda pair: pair[0])
    return {
        "named": [item for _, item in named],
        "others": others,
        "total": len(entries),
        "condensed": condensed,
    }


def with_role(entries, role):
    return [entry["contributor"] for entry in entries if role in entry["roles"]]


def identifiers(obj):
    """``obj``'s identifiers, each with a doi.org link when it is a DOI or an IGSN (an IGSN is a
    DataCite DOI since 2023)."""
    return [
        {
            "type": i.type,
            "value": i.value,
            "link": f"https://doi.org/{i.value}" if str(i.value).startswith("10.") else None,
        }
        for i in obj.identifiers.all()
    ]


def citation(request, *, authors, year, title, link):
    """DataCite's citation form: Creators (Year). Title. Publisher. Identifier."""
    names = format_authors(authors)
    publisher = getattr(getattr(request, "site", None), "name", "") or ""
    parts = [f"{names} ({year})." if names else f"({year}).", f"{title}.", f"{publisher}.", link]
    return " ".join(p for p in parts if p.strip(". "))


def timeline(steps, dates, descriptions, entries):
    """One entry per step in a record's life, joining the three ways the vocabularies describe
    it: a date type, a contributor role and a description type.

    ``steps`` is ``[(date_type, role, description_type, label)]``. Dated steps come first in date
    order, undated ones after them in the table's order. A date recorded only to the year or the
    month is shown as recorded, never padded out to a day.
    """
    result = []
    for date_type, role, description_type, label in steps:
        when = dates.get(date_type) if date_type else None
        who = with_role(entries, role) if role else []
        note = descriptions.get(description_type) if description_type else None
        if when or who or note:
            result.append(
                {
                    "label": label,
                    "date": when,
                    "day": when.date if when is not None and when.precision == 2 else None,
                    "people": who,
                    "note": note,
                }
            )
    dated = sorted((s for s in result if s["date"]), key=lambda s: str(s["date"]))
    return dated + [s for s in result if not s["date"]]
