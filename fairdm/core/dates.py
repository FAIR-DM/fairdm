"""Precision-aware comparison of the partial dates a record carries.

A `PartialDate` mixes precision into its own ordering (`self.date >=
other.date and self.precision >= other.precision`), so comparing two values
of different precision directly is unsafe. `precedes()` is the one
implementation of the precision-aware comparison every date rule needs.
"""

from partial_date import PartialDate


def precedes(a: PartialDate, b: PartialDate) -> bool:
    """Return whether one partial date is earlier than another.

    Compares at the coarser of the two precisions: years only if either is
    year-precision, year and month if either is month-precision, and the
    full date only when both carry day precision.

    Args:
        a: The date expected to come first.
        b: The date expected to come second.

    Returns:
        True when ``a`` is earlier than ``b`` at their shared precision.
    """
    precision = min(a.precision, b.precision)
    if precision == PartialDate.YEAR:
        return bool(a.date.year < b.date.year)
    if precision == PartialDate.MONTH:
        return bool((a.date.year, a.date.month) < (b.date.year, b.date.month))
    return bool(a.date < b.date)
