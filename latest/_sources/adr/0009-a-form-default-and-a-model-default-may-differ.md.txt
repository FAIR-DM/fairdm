# ADR 0009 — A form's default and a model's default may legitimately differ

**Status:** accepted

## Decision

A field's default on a model and its pre-selected value on a form are separate decisions, and they
are allowed to disagree when the two creation paths differ in who is watching.

The first case is project visibility. The model defaults a new project to private. The creation form
pre-selects public. Both are deliberate and neither is a bug to be reconciled.

Where they disagree, the disagreement is recorded on the field or the form, so that the next reader
finds the reasoning rather than an apparent inconsistency.

## Why

**A visible choice is not a hidden default.** A researcher filling in the creation form is looking at
a pair of radio buttons and answering a question. Pre-selecting the value the portal would rather
have is a nudge toward an open catalogue, made in the open. Nothing about a brand new project needs
protecting, and a project nobody can find is a project nobody can contribute to.

**A record created without a form has nobody to nudge.** An import, a fixture, a management command
or an API call creates records with no one reading a screen. There the safe value has to hold,
because the alternative is publishing something whose author never chose to publish it. The model's
default is the last line for exactly those paths, and it is the only default they consult.

**Collapsing the two loses one of them.** Making the model default public to match the form would
change what an unattended import does, silently, in the direction of exposure. Making the form
default private to match the model would remove the nudge and make the common case slower for no
gain in safety, because the person is right there and answering.

## Consequences

A reader comparing a model field to the form that edits it may find two different defaults and no
error. The obligation this creates is documentary: any such pair carries a note saying which path
each governs and why they differ. An undocumented disagreement is still a defect — it is the
explanation, not the difference, that makes this acceptable.

This does not license divergence in validation. A value the model refuses must be refused by the
form too; only the starting point may differ.
