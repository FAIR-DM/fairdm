"""Pure helpers shared by the four record overview pages: project, dataset, sample and measurement.

What the pages work out from a record, including who is credited on it, lives on
``fairdm.core.plugins.RecordOverviewPlugin``. What stays here has no shared subject: how a name is
written in a citation, how a partial date becomes a date, and how data is serialised into a script
element.
"""

import json
from datetime import date

from django.urls import NoReverseMatch, reverse


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
