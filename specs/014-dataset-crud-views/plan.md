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
| US-1 Find a dataset | Add the entry link; repair four filters; collapse two searches into one | **larger** |
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

**The refusal code for a private dataset is preserved, and this is not automatic.** The pages being
retired answer 404 to a request for a private dataset the user may not touch, deliberately, so the
response does not confirm that the record exists — `fairdm/core/dataset/views.py:46-55` says so, and
`fairdm.api.permissions` raises `NotFound` for the same reason. The registered path does not behave
that way: `Plugin.has_permission` hands a refusal to `PermissionRequiredMixin.handle_no_permission`,
which sends an anonymous visitor to log in and gives a signed-in stranger 403. Both disclose that the
dataset exists. Moving the pages without acting would therefore turn four addresses into an existence
oracle for embargoed metadata, and the only visible symptom would be two existing assertions going
red — the kind of thing an address sweep absorbs.

So the dataset's pages override `handle_no_permission` to raise `Http404` when the record is not
public, and to fall through to the inherited behaviour when it is. That reproduces exactly what the
standalone views do today: no rights and not public answers 404, no rights and public answers 403.
The assertions at `tests/test_core/test_dataset/test_views.py:205` and `:287` are re-aimed at the new
addresses and keep their expected status. The same disclosure exists on the project's registered
pages, which are out of this feature's scope; it is raised separately.

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
- marks that test `@pytest.mark.xfail(strict=True, reason=…)` against the pinned version, with the
  issue in the reason, so the suite stays green and the failure is not silently absorbed. **Strict is
  the whole mechanism**: `xfail_strict` defaults to False and this project does not set it, so
  without it the day the upstream fix lands the test passes unexpectedly, is reported as `xpassed`
  and fails nothing — and the one signal that FR-045 has become satisfiable in a browser never fires;
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

### P8 — The listing's filter faults, and its two searches

`date_type` is repointed from `dates__date_type` to `dates__type`, matching the sibling filter that
works.

`image` is repointed from `images` to `image`. It is inherited from `BaseListFilter`
(`fairdm/core/filters.py:13-18`), which declares a relation neither record type has — both carry a
scalar `image` — so applying it raises `FieldError` and the page 500s. This is the same shape as the
`date_type` fault, one level up: the fix is one line in the shared base and it repairs the project
listing in the same pass.

The visibility filter is removed — it cannot change the result set on a listing that shows public
datasets only.

**The project filter's rule is stated rather than inherited.** It offers public projects, plus any
the requester holds `view_project` on at record level, and public projects alone for a visitor who is
not signed in. This is not the rule the creation form uses — that one is contribution-based
(`request.user.projects.all()`), which is the right rule for "projects this researcher may file
under" and the wrong one for a listing open to anonymous visitors, where it raises. Two different
questions, two different rules. The branch in `__init__` that tests authentication and then sets the
same value in both arms goes.

**The listing keeps one search, not two.** `DatasetListView.search_fields` binds to `?q=` while
`DatasetFilter.search` is offered on the same page under `?search=`, over a different field set, and
neither reaches the dataset's external identifiers — which is what a researcher pastes into a search
box. `DatasetFilter.search` is withdrawn as the duplicate and `search_fields` becomes
`["name", "uuid", "identifiers__value", "descriptions__value", "keywords__name"]`: the project's set
(`fairdm/core/project/views.py:27`) plus the two the dataset's own requirements name, and keywords
carried over from the withdrawn filter so nothing is lost.

The stale INTERNAL visibility level in the module and class docstrings is corrected in the same
pass.

### P9 — Keywords: the registration goes, the base classes stay

`Keywords` is deleted from `fairdm/core/dataset/plugins.py`. `KeywordsPlugin` and `KeywordForm` are
left where they are, registered by nothing, and #298 decides whether the rebuild reuses them or they
are retired. Removing unused framework surface is a different change with a different risk and does
not belong in a feature about a dataset's pages.

## Order

1. **Foundations** — the dates row set, the form changes, the filter repairs, **and the registration
   and address move (T056, T057, T059)**.
2. **US-3** — the update page as an extra view, with its row sets. The largest story and the one the
   others' navigation depends on.
3. **US-4** — descriptions as an extra view.
4. **US-6** — deletion as an extra view, with the warning template.
5. **US-5** — the singular form ceasing to answer, the links, and the navigation-entry count
   (T058, T060–T068).
6. **US-2** and **US-1** — creation and the listing, which are the smallest and depend on nothing
   above except the form changes.

**Why the registration comes first, against the instinct to move addresses last.** An extra view has
no route of its own: `Plugin.get_urls` (`fairdm/contrib/plugins/base.py:123-137`) mounts each entry
of `extra_views` inside the *owning registered* plugin's patterns, which is why the project's
`Update`, `Delete` and `Descriptions` carry no registration decorator and exist only because
`Overview.extra_views` lists them. Until `Overview` is registered, `dataset:overview-update`,
`-descriptions` and `-delete` do not resolve at all, so every behavioural task in steps 2–4 is a view
test with no view to request — failing with `NoReverseMatch`, which is failing for the wrong reason
and does not satisfy Article I.

The reason the move was placed last — that it wants the pages it links to already built — is met by
registering `Overview` with an empty `extra_views` and appending each page as it lands. The links
themselves stay in US-5, where they belong.

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
- The project's registered pages answer 403 or a login redirect for a private project, disclosing
  that it exists, where the API answers 404 (P1). Out of scope here; raised for the project's own
  pages.

## Risks

- **The address move is wide.** Its blast radius is enumerated in research R3 and it is done as one
  task with the whole sweep, but a missed reversal shows up as a 500 on a page no test opens. The
  render-every-page check above is the backstop.
- **The upstream deletion defect may turn out to matter more than the plan assumes.** If Sam wants a
  working deletion page in this release rather than when django-mvp next ships, the answer is a
  django-mvp release, not a local override, and that is a sequencing decision rather than a
  technical one.
