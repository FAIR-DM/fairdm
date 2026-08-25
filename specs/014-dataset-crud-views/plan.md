# Plan — 014 Managing a dataset through the portal

Dated 2026-08-25, from `spec.md` and `research.md`. Decisions are recorded here rather than raised
as questions.

## Shape of the work

The specification asks for six things. This feature is the dataset counterpart of 013, and the
machinery 013 built is already in the tree — the row-set declarations for a dataset's dates and
identifiers, the vocabulary-driven descriptions form, the precision-aware date comparison. Most of
what remains is configuration and the tests that pin it.

| Story | What the plan does | Size against expectation |
|---|---|---|
| US-1 Find a dataset | Add the entry link; repair three filters | **larger** |
| US-2 Register a dataset | Use the declared form again, add visibility, filter the project field | as expected |
| US-3 Correct attributes | Row sets for identifiers and dates; the page moves into the collection; the DOI box goes | **larger** |
| US-4 Describe a dataset | Configuration — the form already exists | **much smaller** |
| US-5 Move between pages | The overview registration, then the tab strip | as expected |
| US-6 Remove a dataset | A warning the shared page has no slot for | **larger** |

Two things found in research change the plan rather than the specification, and both are recorded
below: the shared deletion page offers no warning slot (P5), and its confirmation field is drawn
twice on the version this project runs, so a browser cannot complete a deletion at all (P6).

## Decisions taken

### P1 — The dataset's pages are one registered collection

The dataset's detail page becomes an `Overview` registration against `Dataset`, and the update,
descriptions and deletion pages become extra views belonging to it. The standalone `dataset-detail`,
`dataset-update` and `dataset-delete` routes are retired, and the separate `Descriptions` and
`KeyDates` registrations go with them — dates move onto the update page, descriptions become an
extra view.

This is `fairdm/core/project/plugins.py:263-293` applied to datasets, and the reasoning is 013's P1
unchanged: a menu entry's address is built as `f"{model_name}:{name}"`, so a page outside the
registration namespace can never appear in the record's own navigation. What is different for a
dataset is that there is no accident to undo — the dataset never had an overview registration, and
`fairdm/core/dataset/templates/dataset/plugins/overview.html` is a template written for one that was
never wired up (#190).

`Overview` mixes in `CRUDDirectoryMixin` and states `directory` and `crud_views` for all three
actions, because the mixin's defaults resolve to the standalone routes this feature retires.

**Every page states its own permission and its own visibility rule** — `dataset.change_dataset` for
the update and descriptions pages, `dataset.delete_dataset` for the deletion page — because
inheriting either does not work (research R2, #279 and #284). The visibility rule follows the
project's two-function shape: a plain one for the overview and the descriptions page, and one that
additionally admits a record-level holder of the page's own permission for update and delete, since
creating a dataset grants all five rights at once and an editor of a private dataset must not be
refused.

### P2 — The addresses move to the plural form, in one step

`fairdm/core/dataset/urls.py` becomes the project's shape: the listing, then the creation route,
then the record include under `datasets/<str:uuid>/`. The creation route is declared **ahead** of the
include, or `create` is read as a uuid.

`Dataset.get_absolute_url()` is overridden to reverse `dataset:overview`, mirroring
`Project.get_absolute_url()` (`fairdm/core/project/models.py:144-152`) — whose docstring names the
dataset as the record still doing it the old way. The `BaseModel` default is left alone; samples and
measurements are #283's business, not this feature's.

This is the change with the widest blast radius, and research R3 lists every call site. It is done
as one task with the whole sweep in it, not spread across stories, because a half-moved route set
leaves the application unreachable in ways no single story's tests would catch.

### P3 — Identifiers and dates are row sets on the update page

`Update` is `Plugin, InlinesMixin, FairDMUpdateView` with
`inlines = [DatasetIdentifierInline, DatasetDatesInline]`, mirroring the project exactly. The
declarations already exist in `fairdm/core/related_records.py`; `DatasetDatesInline` is a subclass
in `plugins.py` attaching `date_ordering_formset(DatasetDate.START_TYPE, DatasetDate.END_TYPE, …)`,
parameterised rather than literal, which is what that helper was built for.

The message wording differs from the project's — a dataset's pair is a collection start and end, not
a project start and end — and the model already phrases it that way in
`DatasetDate.clean()`.

**The DOI field is removed from `DatasetForm`**, along with the `save()` override that created and
deleted a `DatasetIdentifier` behind it. The identifier row set replaces both. The dataset's
identifier vocabulary holds DOI alone today, so nothing is lost, and the pre-population that read an
existing DOI into the box goes with it.

### P4 — The form gains visibility and stops nesting a form element

Two changes to `DatasetForm`, both from research R6 and R7.

`Meta.helper_attrs = {"form_tag": False}`. Every FairDM form is given a crispy helper automatically,
and the shared render tag takes the `{% crispy form %}` branch whenever one is present, which emits
its own `<form>` inside the one the page already opened. Project, sample and measurement all set this
and the dataset is the only core form that does not. Setting it through `helper_attrs` rather than
replacing the helper in `__init__` keeps the derived layout, the form id and the interaction
attributes, all three of which the project's approach discards.

`visibility` is declared explicitly with `RadioSelect` and `initial = Visibility.PUBLIC`, and the
layout is stated through `Meta.fieldsets` so the field can be presented as inline radios without
hand-writing a helper. The model default stays private; the two defaults answer different questions
and 013 recorded that as an architecture decision.

`DatasetCreateForm` narrows `Meta.fields` to `name`, `visibility`, `license`, `project`. The create
view stops declaring its own `fields` list and uses the form class, and passes `request` so the
project field is narrowed — all three of those lines exist in the file today, commented out.

### P5 — The deletion warning is a per-model template, and the shared page gets an issue

The shared deletion page has no warning slot: its only prominent channels are a refusal that
suppresses the submit button, and a fixed-shape list of cascading object names. FR-046 needs neither
— it needs counts, prominent, with the deletion still available.

`fairdm/core/dataset/templates/dataset/dataset_confirm_delete.html` extends the shared page and
overrides `{% block before_form %}` with `{{ block.super }}` plus the dataset's own warning. This is
a supported extension point, not a workaround: `BaseTemplateNameMixin` deliberately puts Django's
own `<app>/<model>_confirm_delete.html` ahead of the shared template, and nothing of the shared
markup is restated.

The counts come from a `get_context_data` override on `Delete`, two aggregates on the relations
`has_data` already uses.

**Raised upstream, not built here**: the shared page should take a `warnings` list and a block around
it, so this is configuration rather than a template per record type. Filed against django-mvp.

### P6 — The confirmation field is an upstream defect and stays one

On the version this project runs, `require_confirmation = True` draws the confirmation field twice —
once outside the `<form>` element and once inside it — and the enabling script watches the outer one
while the browser posts the inner, empty one. A deletion cannot be completed in a browser. The
project's deletion page has this today, merged.

The fix already exists in the django-mvp working tree, unreleased, and deletes the duplicate with a
comment describing exactly this fault.

**This feature does not fork the shared markup to route around it.** Overriding `before_form` to
drop one of the two fields would fix one page and leave the defect live on every other, invisibly.
The plan instead:

- writes the behavioural test for FR-045 against the posted form, as the existing deletion tests are;
- adds a rendering test asserting the deletion page carries exactly one control named
  `confirmation`, which **fails today** and is the check that reports when the upstream fix lands;
- marks that test as expected-to-fail against the pinned version, with the issue in the reason, so
  the suite stays green and the failure is not silently absorbed;
- raises the defect against django-mvp with the reproduction.

If Sam would rather this feature carried a temporary local override, that is a scope change and goes
back through a delta brief.

### P7 — Descriptions is an extra view, and the generic plugin is left alone

`Descriptions` becomes `Plugin, MetadataMixin, MVPFormView` with
`form_class = VocabularyDescriptionsForm`, `related_model = DatasetDescription`, and
`template_name = "form_view.html"` stated explicitly — a plain form view derives no template from a
model, so leaving it unset makes Django raise before the fallback is reached. This is the project's
`Descriptions` with two names changed.

The generic `DescriptionsPlugin` and `KeyDatesPlugin` are not repaired and not removed: the sample
pages still use them, and they are #280's business. PR #287 repaired them for both record types and
is superseded here for the dataset half only.

### P8 — The listing's three filter faults

`date_type` is repointed from `dates__date_type` to `dates__type`, matching the sibling filter that
works. The visibility filter is removed — it cannot change the result set on a listing that shows
public datasets only. The project filter's queryset is narrowed to projects the viewer may see, and
the branch in `__init__` that tests authentication and then sets the same value in both arms goes.

The stale INTERNAL visibility level in the module and class docstrings is corrected in the same
pass.

### P9 — Keywords: the registration goes, the base classes stay

`Keywords` is deleted from `fairdm/core/dataset/plugins.py`. `KeywordsPlugin` and `KeywordForm` are
left where they are, registered by nothing, and #298 decides whether the rebuild reuses them or they
are retired. Removing unused framework surface is a different change with a different risk and does
not belong in a feature about a dataset's pages.

## Order

1. **Foundations** — the dates row set, the form changes, the filter repairs. No page moves yet, so
   the suite stays meaningful throughout.
2. **US-3** — the update page as an extra view, with its row sets. The largest story and the one the
   others' navigation depends on.
3. **US-4** — descriptions as an extra view.
4. **US-6** — deletion as an extra view, with the warning template.
5. **US-5** — the overview registration, the address move, and the links. Last, because it is the
   step that retires the standalone routes, and it wants the pages it links to already built.
6. **US-2** and **US-1** — creation and the listing, which are the smallest and depend on nothing
   above except the form changes.

US-1 and US-2 could run earlier; they are placed last because their remaining work is small and the
address move touches their tests.

## Verification beyond the suite

- Every page rendered as a real request, signed in and signed out, with and without each permission.
  The visibility-rule defect in R2 was found this way in 013 and is invisible to a unit test.
- The deletion page rendered in a browser, to confirm the duplicate-field defect and to confirm the
  warning reads as a warning.
- `makemigrations --check` across all apps: no model field changes are planned, so this must stay
  clean.

## Test obligations

- Every FR that changes behaviour gets a test that fails before the change.
- The address move gets a test asserting the singular form no longer answers, not merely that the
  plural one does.
- The filter repairs get behavioural tests that run a query — the existing `date_type` test asserts
  only that the field appears on a form, which is why the defect survived.
- The warning gets a test asserting rendered content, not context keys. 013 recorded that a refusal
  test asserting context passed against a page that showed the user nothing.

## Raised separately

- django-mvp: no warning slot on the shared deletion page (P5).
- django-mvp: the confirmation field is drawn twice (P6).
- #298: the keyword rebuild, and what becomes of the now-unregistered base classes (P9).
- #297: the project's deletion refusal, keyed on visibility rather than publication.
- #296: takedown requests for published data.

## Risks

- **The address move is wide.** Its blast radius is enumerated in research R3 and it is done as one
  task with the whole sweep, but a missed reversal shows up as a 500 on a page no test opens. The
  render-every-page check above is the backstop.
- **The upstream deletion defect may turn out to matter more than the plan assumes.** If Sam wants a
  working deletion page in this release rather than when django-mvp next ships, the answer is a
  django-mvp release, not a local override, and that is a sequencing decision rather than a
  technical one.
