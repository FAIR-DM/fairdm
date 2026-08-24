"""Comparison of the partial dates a record carries.

A `PartialDate` mixes precision into its own ordering (`self.date >=
other.date and self.precision >= other.precision`), so comparing two values
of different precision directly is unsafe. `precedes()` is the one
implementation of the precision-aware comparison every date rule in the
platform needs.

Only the comparison itself lives here. Each record type still states its own
date rule in its own words - the shape of that rule is deliberately repeated
per record type rather than lifted to `AbstractDate` (spec 004, Article III),
and this module does not change that.
"""

from partial_date import PartialDate


def precedes(a: PartialDate, b: PartialDate) -> bool:
    """Whether PartialDate `a` is earlier than PartialDate `b`.

    Compares at the coarser of the two precisions: years only if either is
    year-precision, year and month if either is month-precision, and the
    full date only when both carry day precision.
    """
    precision = min(a.precision, b.precision)
    if precision == PartialDate.YEAR:
        return bool(a.date.year < b.date.year)
    if precision == PartialDate.MONTH:
        return bool((a.date.year, a.date.month) < (b.date.year, b.date.month))
    return bool(a.date < b.date)
