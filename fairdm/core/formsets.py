"""Shared formsets for the rows of related records a record carries.

This module is not a page, view or URL. It is consumed by the Django admin
inlines in ``fairdm/core/project/admin.py`` and
``fairdm/core/dataset/admin.py``, and by the record's own pages in
``fairdm/core/project/plugins.py``.
"""

from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from partial_date import PartialDate

from .dates import precedes


def date_ordering_formset(start_type, end_type, message):
    """Return a ``BaseInlineFormSet`` that refuses a backwards
    ``start_type``/``end_type`` pair across the whole formset.

    Parameterised on its start type, its end type and its whole message, so
    the same rule serves every record type that has an ordered pair of dates
    without generalising onto the ones that do not (plan P6) - a record type
    with no such pair simply never calls this.

    The message is passed whole rather than assembled from a noun so that
    each record type states its own date vocabulary in its own words - a
    dataset's pair is its collection start and collection end, and its
    model-level validation says so too. It also keeps the sentence
    translatable as one unit.

    A formset validates every form before any of them saves, so a per-row
    ``clean()`` that looks its sibling up in the database (as
    ``ProjectDate.clean()``/``DatasetDate.clean()`` do) sees no unsaved
    sibling when both the start and the end are new rows in the same
    submission, and each form's individual validation short-circuits. This
    reads the start and end values directly off the forms' own
    ``cleaned_data`` instead, so the pair is checked whichever of the two
    (or both) is unsaved.
    """

    class DateOrderingFormSet(BaseInlineFormSet):
        def clean(self):
            super().clean()

            start_value = None
            end_value = None
            for form in self.forms:
                if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                    continue
                value = form.cleaned_data.get("value")
                if not value:
                    continue
                # The form field stores the raw string; the model field's
                # `PartialDate` conversion only happens on `full_clean()`,
                # which a formset's own `clean()` runs before, so it is
                # done here too.
                if not isinstance(value, PartialDate):
                    value = PartialDate(value)
                if form.cleaned_data.get("type") == start_type:
                    start_value = value
                elif form.cleaned_data.get("type") == end_type:
                    end_value = value

            if start_value is None or end_value is None:
                return

            if precedes(end_value, start_value):
                raise ValidationError(
                    message % {"start": start_value, "end": end_value}
                )

    return DateOrderingFormSet
