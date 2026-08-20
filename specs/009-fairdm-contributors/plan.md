# Implementation Plan — 009 contributors and contributions

**Branch**: `009-fairdm-contributors` · **Date**: 2026-08-20 · **Spec**: [spec.md](spec.md)

Decisions: [decisions.md](decisions.md) · Research: [research.md](research.md)

## Shape of the work

Most of this feature is built. The specification was rewritten against the code rather than the
other way round, so the majority of its requirements describe behaviour that already exists and
needs only a test that genuinely covers it. What remains divides into four kinds:

1. **One field that does not exist.** An organisation has no type. It is added as a nine-value
   selection taken from ROR, with a migration and validation.
2. **Three things that are built and wrong.** Deleting a parent organisation deletes its children.
   Three separate places decide whether a person has claimed their account, and only one reads the
   field that stores it. The administrative action offering to transfer ownership performs no
   transfer.
3. **Two things that are built and unused.** A privacy mechanism nothing calls, and a ranking score
   nothing computes. The first becomes a general configuration store, the second is removed.
4. **A derivation that developers currently have to do themselves.** A person's account state is
   determinable from three fields, and every caller has to know which three.

Everything else is a test. That is not a small part of the work: the audit found `ghost()`,
`invited()`, `real()` and `active()` with no tests at all, no test linking a credit to a sample or a
measurement, no test of the identifier uniqueness constraint, and five tests that pass for reasons
unrelated to what their names claim.

## The decisions that shape it

- **The specification describes the record layer and the administrative interface only.** Views,
  plugins, forms and the portal's own editing pages are deferred (D1). Several defects found in
  those layers are raised as issues and are not touched here.
- **Ownership is derived, not stored** (D13). No permission rows are written or read. Work on
  ownership is work on the affiliation record and the backend that reads it.
- **The account state is derived too** (D8), so it is written twice — once as a property and once as
  a queryset condition — and the two are tested against each other rather than separately.
- **Nothing is built for the synchronisation or export specifications.** The fields those
  specifications own are left in place untouched (D2, D3, D11).
- **A test that asserts a defect is a defect.** Five such tests are rewritten as part of the task
  that touches their subject, and the decision record names each (D19).

## Data model

Changes to the schema, all in `fairdm/contrib/contributors/`:

| Change | Model | Migration operation |
|---|---|---|
| Add `type`, nine ROR values, nullable | `Organization` | `AddField` |
| `parent` delete rule becomes `SET_NULL` | `Organization` | `AlterField` |
| `privacy_settings` becomes `config` | `Contributor` | `RenameField` + `AlterField` + data migration clearing it |
| Remove `weight` | `Contributor` | `RemoveField` |

Nothing else changes shape. `Affiliation`, `Contribution` and `ContributorIdentifier` are correct as
built, and the work against them is tests and one administrative action.

Migrations are squashed to one per model at convergence, per the repository's own standard.

## Ordering and parallelism

The work divides into ten stories, and they are unusually independent because most of them touch
different files. Three constraints order them:

- **The account state (US-3) precedes the claim-status corrections.** The administrative filter and
  the default-seeding branch both need somewhere correct to read from.
- **The configuration field (US-1) precedes anything else touching `Contributor.save`**, because
  removing the privacy-seeding branch changes that method.
- **The migrations are written by one hand.** Four schema changes across two models, landing in
  parallel, is how a repository acquires two migration leaves. They are done first, in one task, and
  everything else builds on them.

After that the stories run in parallel. US-4 and US-6 both touch organisations but not the same
concern — one is the record, the other is the permission backend.

## What this plan does not do

- Touch any view, plugin, form, widget or template.
- Fix the Datasets tab, the claim-link action, or the second claiming path. Each is raised as its
  own issue (#248, #249, #250).
- Add a keyword or expertise vocabulary to contributors (D17).
- Add a person's position at an institution (D7).
- Remove the dead forms and widgets. They are view-layer and belong to the specification that
  inherits them (D1).
- Change anything about how ownership is checked for staff. That waits on #247 (D10).
