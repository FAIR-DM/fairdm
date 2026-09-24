"""Helpers shared by the record overview pages (project and dataset).

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
