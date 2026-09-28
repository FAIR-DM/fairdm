"""Shared formsets for the rows of related records a record carries."""

from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from partial_date import PartialDate

from .dates import precedes


def date_ordering_formset(start_type, end_type, message):
    """Return a formset class that refuses a backwards start/end date pair.

    A formset validates every form before any of them saves, so a per-row
    ``clean()`` that looks its sibling up in the database (as
    ``ProjectDate.clean()`` and ``DatasetDate.clean()`` do) sees no unsaved
    sibling when both dates are new rows in the same submission. The
    returned formset reads the start and end values off the forms'
    ``cleaned_data`` instead, so the pair is checked whichever of the two
    (or both) is unsaved.

    The message is passed whole rather than assembled from a noun so that
    each record type states its own date vocabulary and the sentence stays
    translatable as one unit.

    Args:
        start_type: The date type value marking the start of the pair.
        end_type: The date type value marking the end of the pair.
        message: The error message, using ``%(start)s`` and ``%(end)s``
            placeholders.

    Returns:
        A ``BaseInlineFormSet`` subclass whose ``clean()`` raises a
        ``ValidationError`` when the end precedes the start.
    """

    class DateOrderingFormSet(BaseInlineFormSet):
        def clean(self):
            """Reject a formset whose end date precedes its start date."""
            super().clean()

            start_value = None
            end_value = None
            for form in self.forms:
                if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                    continue
                value = form.cleaned_data.get("value")
                if not value:
                    continue
                # The form field holds the raw string. The model field only converts it
                # in `full_clean()`, which runs after the formset's own `clean()`.
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
