"""Pure helpers shared by the four record overview pages: project, dataset, sample and measurement.

What the pages work out from a record lives on ``fairdm.core.plugins.RecordOverviewPlugin``. What
stays here has no shared subject: how a name is written in a citation, how a partial date becomes a
date, how data is serialised into a script element, and how a credit is read.
"""

import json
from datetime import date

from django.urls import NoReverseMatch, reverse

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
    contributions = list(
        obj.contributors.select_related("affiliation").prefetch_related("roles")
    )
    real = Contributor.objects.in_bulk([c.contributor_id for c in contributions])
    for contribution in contributions:
        contribution.contributor = real[contribution.contributor_id]
    return contributions


def is_person(contributor):
    return isinstance(contributor, Person)


def roles_of(contribution):
    return {role.name for role in contribution.roles.all()}


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
    """ "Keller, A., Oliveira, T. & Brandt, L." — the DataCite creator list as a reader writes it."""
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


def with_role(entries, role):
    return [entry["contributor"] for entry in entries if role in entry["roles"]]
