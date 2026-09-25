# Decisions: 018-overview-pages

Questions settled while writing the specification without asking the maintainer, with the reasoning
behind each. The maintainer's own rulings are recorded under *Clarifications* in `spec.md`.

## Where the extra cards go in the facts column

The agreed order is citation, identifiers and licence, people, parent record, dates. Two kinds of
card fall outside it. The readiness checklist goes first. It is shown only to the team, and it is
the one card that asks them to act, so it belongs where they look first. Cards particular to one
kind of record (funding on a project, related publications and versions on a dataset) go between
the people credited and the parent record. They describe the record itself, and the parent record
and dates describe where it sits.

## Projects and datasets do not choose a template by type

Samples and measurements are polymorphic, and portals subclass them, so a type needs somewhere to
put its own fields. Projects and datasets have fixed schemas that portals do not extend. A portal
that wants a different project page overrides the template the usual way, and the shared
`overview.` blocks give it the same points to change as a sample type has.

## D1. The page skeleton owns every block

One template, `overview/page.html`, defines every `overview.*` block in page order. Each page's
template extends it and only fills blocks. This puts the anatomy (FR-001–FR-003) and the block
names (FR-005) in one file, so two pages can't drift apart, and a portal developer reads one list.

**ADR:** pending, decided at convergence.

## D2. Record-specific facts sit in one wrapper block

Funding, related publications and versions sit inside `overview.record_facts`, between the people
credited and the parent record, so the fixed order in FR-003 holds without the skeleton knowing
every page's cards. Each card inside it has its own block too (`overview.funding`,
`overview.publications`, `overview.versions`).

**ADR:** none. It is local to these templates, and the block list in the docs is the record.

## D3. Placeholder actions are a partial, not a component

A disabled button with its explanation is one element. It gets a shared include so the four pages
render it the same way, without a new Cotton component or a new namespace.

**ADR:** none. It is local to this feature.

## D4. Project charts count what a visitor may see

A visitor's figures and charts on a project count the project's public datasets, published or
not. This is the same scope as the counts FR-016 allows on a public, unpublished dataset. A chart
of records by type is a breakdown of those counts and shows no record's data. The growth chart
shows when records were added, not what they hold.

**ADR:** none. It follows directly from FR-015 and FR-016.

## D5. The seed command refuses outside development

The command creates three accounts with a written-down password, one of them a superuser. It
reuses the environment guard `create_dev_accounts` uses (ADR 0022's reasoning: a refusal guards
the act), so it can't run against a production database by mistake.

**ADR:** none. It applies an existing ADR.

## D6. Waiver: `test_detail_page_renders` changes premise

`tests/test_core/test_measurement/test_models.py::test_detail_page_renders` asserts that a
signed-out visitor gets 200 on a measurement in a factory (private) dataset. FR-014 makes that a
404 by design. The test gets a public, published dataset instead, and a new test asserts the 404
for the private case. The change is to the test's setup, not its assertion.

**ADR:** none. It is a test update.

## D7. Design review dispositions

One reviewer read the plan through three lenses and returned eight findings. All of them were
checked against the code before being acted on.

- **The measurement address (high).** The plugin base mounts an overview without `url_path` at
  `overview/`. Remedied in plan D5 and T026/T028: `url_path = None`, and the tests pin the
  literal path.
- **Per-row visibility for lists (high).** The branches switched the filter off for anyone on the
  *page's* dataset team, which let a team member see records from a third dataset. Remedied in
  plan D3 and T019a/T020/T022/T026/T029: `visible_to(user)` on the Sample and Measurement
  QuerySets, applied per row.
- **Related samples unfiltered (high).** Parents and subsamples can sit in another dataset.
  Remedied in the same rule, with a T020 case.
- **A private parent project named on a public dataset (medium).** Remedied: the parent project is
  shown only when `project_is_visible` passes (plan D3, T013/T014/T020/T026).
- **Seed accounts outside E501 (medium).** Remedied: `EXAMPLE_ACCOUNT_EMAILS` is defined in the
  package, and E501 checks it (plan D6, T011).
- **Article XI cohesion (medium).** Remedied: shared behaviour moves to `RecordOverviewPlugin`,
  page logic to each `Overview` plugin, and visibility to QuerySets and a Dataset property. Module
  functions are kept for pure formatting only (plan D3).
- **ECharts replaceable (low).** Remedied: it loads from its own `overview.chart_library` block
  (plan D7).
- **The growth chart for visitors (low, likely).** Declined. D4 stands. A running total of record
  counts is a count, and the maintainer ruled that counts on a public, unpublished dataset are
  shown.

**ADR:** none. These are the dispositions of one review.

## D8. Shared overview behaviour lives on plugin classes

`RecordOverviewPlugin` holds the behaviour all four pages share, and each page's `Overview`
plugin holds its own. A portal changes a page's behaviour by subclassing its plugin, the same way
it changes a page's look through the `overview.*` blocks.

**ADR:** pending, decided at convergence together with D1.
