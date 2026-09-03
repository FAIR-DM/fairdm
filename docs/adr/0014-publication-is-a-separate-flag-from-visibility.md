# ADR 0014 — Publication is a separate flag from visibility

**Status:** accepted

## Decision

A dataset carries a `published` boolean, separate from its `visibility`. Publication decides
whether the data held beneath the dataset may be shown; visibility decides whether the dataset's
own metadata may be read. Neither implies the other, and a dataset that is published while private
is an ordinary state rather than a contradiction.

The flag is set in the Django admin and nowhere else. No page a researcher can reach exposes it,
and no form includes it.

## Why

**They answer different questions.** Visibility answers "may anyone read that this dataset exists
and what it is about", which a researcher decides about their own work. Publication answers "may
anyone read the data beneath it", which is a release. Reusing one field for both would make the act
of describing your work publicly the same act as releasing it.

**The admin is the point, not a shortcut.** A control on the researcher's own dataset page is where
they would look for it, and that is the argument against putting it there: it makes publishing a
click. A reviewed publication workflow is worth designing properly, and an administrator-only flag
is a deliberately awkward placeholder whose awkwardness is what stops it hardening into the
workflow before the workflow exists.

**The migration leaves every dataset unpublished.** Defaulting existing rows to published would
release data on upgrade that nobody chose to release.

## Consequences

Any code deciding whether a record may be shown reads `published`, never `visibility`. A query
written against visibility to answer a data question is a defect even when it currently returns
the right rows.

A real publication workflow, when it is built, replaces the admin control. It does not replace the
field, and it inherits the separation above rather than collapsing the two.
