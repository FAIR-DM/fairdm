"""Pairing the headings of a file with the columns of a record type."""

import re

from django.utils.translation import gettext as _

from .models import ImportJob
from .schema import UNIT_IN_LABEL


class HeadingMatcher:
    """Finds the column each heading of a file means.

    A heading matches a column by its name, its label, its label without a unit in
    brackets or one of its aliases, ignoring case, spaces and punctuation. Where two
    columns claim the same words the first column of the schema keeps them, so
    ``Sample ID`` is the Local ID, never a measurement's sample.

    Args:
        schema: The ``TableSchema`` of the record type the file is imported as.

    Attributes:
        schema: The table schema.
        keys: The column each normalised heading means.
    """

    def __init__(self, schema):
        """Index the importable columns by every heading they answer to."""
        self.schema = schema
        self.keys = {}
        for column in schema.importable:
            label = str(column.label)
            words = [column.name, label, UNIT_IN_LABEL.sub("", label), *column.aliases]
            for word in words:
                self.keys.setdefault(self.normalise(word), column)

    @classmethod
    def normalise(cls, heading):
        """Reduce a heading to its letters and digits, in lower case.

        Args:
            heading: A heading, or None.

        Returns:
            ``Rock type``, ``rock_type`` and ``ROCK-TYPE`` all give ``rocktype``.
        """
        return re.sub(r"[^a-z0-9]", "", str(heading or "").lower())

    def match(self, heading):
        """Find the column a heading means.

        Args:
            heading: A heading of the file.

        Returns:
            The column, or None when the heading means none.
        """
        key = self.normalise(heading)
        return self.keys.get(key) if key else None

    def match_columns(self, headings):
        """Match every heading of a file.

        Args:
            headings: The headings, in file order.

        Returns:
            The name of the column of each heading. The first heading to take a column
            keeps it, and a heading that means no column, or one already taken, is
            an empty string.
        """
        matched, taken = {}, set()
        for heading in headings:
            column = self.match(heading)
            if column and column.name not in taken:
                matched[heading] = column.name
                taken.add(column.name)
            else:
                matched[heading] = ""
        return matched

    def problems(self, job):
        """Say what stops the matched columns from being checked.

        Args:
            job: The import job, with its ``column_map`` and ``mode``.

        Returns:
            A sentence for each problem, empty when the file can be checked.
        """
        chosen = [name for name in job.column_map.values() if name]
        mapped = set(chosen)
        problems = []
        if not mapped:
            problems.append(_("No column in the file is matched to a field."))
        for name in sorted({n for n in chosen if chosen.count(n) > 1}):
            column = self.schema.get(name)
            problems.append(
                _("Two columns are matched to %(column)s. Match only one of them.")
                % {"column": column.label if column else name}
            )
        if job.mode != ImportJob.Mode.UPDATE:
            missing = [c for c in self.schema.required if c.name not in mapped]
            if missing:
                problems.append(
                    _("New records need %(columns)s, and no column is matched to it.")
                    % {"columns": ", ".join(str(c.label) for c in missing)}
                    if len(missing) == 1
                    else _("New records need %(columns)s, and none are matched.")
                    % {"columns": ", ".join(str(c.label) for c in missing)}
                )
        if job.mode == ImportJob.Mode.UPDATE and not {"portal_id", "local_id"} & mapped:
            problems.append(
                _("Updating needs a Portal ID or Local ID column to find each record.")
            )
        return problems

    def warnings(self, job):
        """Say what is worth knowing, though the file can still be checked.

        Args:
            job: The import job, with its ``column_map`` and ``mode``.

        Returns:
            A sentence for each warning.
        """
        mapped = {name for name in job.column_map.values() if name}
        warnings = []
        if job.mode == ImportJob.Mode.BOTH and not {"portal_id", "local_id"} & mapped:
            warnings.append(
                _(
                    "The file has no Portal ID or Local ID column, so every row will "
                    "be added as a new record. Importing it a second time would add "
                    "every row again."
                )
            )
        if ("latitude" in mapped) != ("longitude" in mapped):
            warnings.append(
                _(
                    "Only one of latitude and longitude is matched. "
                    "A location needs both."
                )
            )
        return warnings

    def needs_matching(self, job):
        """Say whether the person must look at the matching before the check.

        Args:
            job: The import job, with its ``headers``, ``column_map`` and ``mode``.

        Returns:
            True when a heading is matched to no column or a problem stops the check.
            Warnings alone leave the matching to be skipped. The job's page shows them.
        """
        unmatched = any(not job.column_map.get(h) for h in job.headers)
        return unmatched or bool(self.problems(job))
