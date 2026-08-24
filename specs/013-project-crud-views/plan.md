# Plan — 013 Managing a project through the portal

Dated 2026-08-23, from `spec.md` and `research.md`. Decisions are recorded here rather than raised
as questions.

## Shape of the work

The specification asks for six things. Research changed the size of four of them, in both
directions.

| Story | What the plan does | Size against expectation |
|---|---|---|
| US-1 Find a project | Add the entry link, test what is untested | smaller |
| US-2 Register a project | Test what is untested; no behaviour change | smaller |
| US-3 Correct attributes | Add identifier and date row sets through a shared mixin, retire the duplicate page | **larger** |
| US-4 Describe a project | Build a vocabulary-driven form, reusable across record types | as expected |
| US-5 Move between pages | Switch on the shell's existing buttons | **much smaller** |
| US-6 Remove a project | Populate the shell's refusal contract | smaller |

## Decisions taken

### P1 — One project editing page, and it is `project-update`

`ProjectConfigure` is retired and its registration removed. `project-update` becomes the attributes
page the specification describes and gains the link that `ProjectConfigure` currently has.

`project-update` has the complete field set, an explicit redirect and the only tests that exist.
`ProjectConfigure` is narrower, untested and redirects by accident. Keeping both means two pages
editing overlapping fields through two different permission strings, which is the condition that
prompted this review.

Its permission behaviour is the one thing worth carrying across, and the mechanism matters more than
the string. `project-update` calls `user.has_perm("change_project", project)`, which only the
object-level layer can satisfy. Changing the string alone does not help: measured on this branch, a
user holding the model-level permission gets `True` from `has_perm("project.change_project")` and
**`False`** from `has_perm("project.change_project", project)`, because Django's own backend returns
nothing once a record is passed.

What makes the plugin admit both is that it asks twice. So the attributes page adopts the same
helper the plugin layer already uses, `fairdm.contrib.plugins.access.has_perm(request, permission,
obj)`, which tries the model level, then the record, and memoises the answer on the request. The
string becomes `project.change_project` to match.

Consequence to accept: a tab a user sees today disappears, replaced by an Edit button on the same
page. No data and no address a user could have bookmarked is lost, since the tab's fields are a
subset.

### P2 — Descriptions are a registered page, one area per vocabulary type

The unregistered `Descriptions`, `Keywords` and `KeyDates` classes in `project/plugins.py` are
deleted rather than registered.

The generic description plugin adds and removes rows. The specification asks for a fixed set of
labelled areas, one per description type, because the model allows one row per type. Those are
different interfaces, and the generic one is also broken where it is registered, because it resolves
to the record's detail template and never draws its formset.

So the descriptions page is a form whose fields are generated from the related model's `VOCABULARY`:
one text area per concept, labelled with its name and helped by its definition. Saving writes,
updates or deletes one row per area.

**Driving the fields off the vocabulary is what makes this expand without code.** A new description
type is a vocabulary entry and the page grows a field, which is the same property the row sets have
for dates and identifiers under P3. The two shapes differ in what the user sees, not in what it
costs to extend them.

It is registered as a page against the project, which supplies the address, the menu entry, the
breadcrumbs and the permission check, and means the tab is hidden from users who may not open it.
That satisfies FR-042 without a second mechanism.

It declares `permission = "project.change_project"`, the same string as the attributes page. The
check is only supplied where one is declared: a registered page with no permission is open to
everyone, anonymous included, and the record is fetched through an unfiltered manager on the
assumption that the page checks for itself. That omission is exactly what leaves the contributor
pages open today, and it is not repeated here.

Not fixing the generic plugin here. Datasets and samples carry the same defect and it is their work,
raised separately below.

### P3 — Identifiers and dates are both inline sets

Both related records on the attributes page are edited as row sets, using the interface layer's own
`InlineFormSet` and `InlinesMixin` rather than django-extra-views.

Dates get the same treatment as identifiers even though a project has only two date types today.
Two reasons, and neither is about the project.

- **The vocabulary will grow.** Community feedback adds date types, and adding one should be a
  vocabulary entry rather than a new form field, a new save branch and a new test. A row set absorbs
  a new type with no code at all.
- **The other record types have several.** Datasets, samples and measurements all carry more dates
  than a project does. If the project's page treats dates as fields and theirs treat dates as rows,
  a user who learns one page has to learn the next. Consistency across the record types is worth
  more than the validation class it costs here.

Three settings are not optional:

- `extra = 0` on both sets. The interface layer omits anything left unset, so Django's default of
  three blank rows applies otherwise.
- `formset = DateInlineFormSet` on the dates set, reusing the class already written for the admin
  (`project/admin.py:24-66`). Without it the sibling comparison in `ProjectDate.clean()` is skipped
  when the parent is new and compares against stale values otherwise, because the sibling row is
  unsaved and the check queries the database. This is the single most likely thing to ship broken
  and unnoticed.
- `value` and `type` present in both field lists. A model `clean()` that keys an error to a field
  absent from the form raises rather than reporting it.

The three form classes this replaces (`ProjectDateForm` and `ProjectIdentifierForm` here,
`ProjectDescriptionForm` under P2) are used by nothing in the running code today. They are deleted
with their tests rather than left beside the machinery that supersedes them. `ProjectDateForm` in
particular describes a field the model does not have and carries a commented-out `clean()`, so
leaving it is leaving a trap.

### P4 — The deletion refusal populates the shell's contract

`is_protected` and `protected_objects` are set instead of the invented `protected_datasets`, in a
`get_context_data` override that runs after the shell's own assignment rather than through keyword
arguments, which the shell overwrites.

The refusal is also evaluated when the page is opened, not only when it is submitted. Today a user
whose project cannot be deleted gets a fully armed confirmation form and finds out only after typing
the name. The signal stays as the enforcement point, so the guarantee still holds however the
deletion is attempted.

The existing test asserts the invented key and is rewritten to assert what the page says.

### P5 — Navigation is configuration on five views

No new templates. Each view declares `directory` and the matching `show_<action>_action`, the
deprecated names go, and the shell's existing buttons appear.

- Detail: `directory = ["update", "delete"]`, the shell's own default, which deliberately omits the
  listing because the breadcrumb already links it. Update and delete gated on the user's permission
  for that project.
- List: `directory = ["create"]`, create shown to signed-in users.
- Update: `show_delete_action` gated on delete permission, which lights the Delete button the shell
  already draws in the form body, plus `show_detail_action` and `show_list_action`.
- Delete: `show_list_action` and `show_detail_action`.
- Descriptions page: reached as a tab, returns to the project.

The two flags on each of the update and delete pages are load-bearing, not tidiness. The shell
builds both pages' breadcrumbs through the same resolution, so dropping the deprecated names without
replacing them costs the attributes page its link back to the project, a link that works today, and
leaves the deletion page with no route to the project at all, since its back control falls back to
the listing. On the update page a missing `show_list_action` also puts the literal string `None`
into the Delete button's address.

A permission-dependent flag is written as a method, not a lambda. The shell reads the flag with
`getattr`, so a lambda in the class body binds as a method and is called with an argument too many.
That is a 500 on the project page, confirmed on this branch. The method form is also what gives the
object-level check access to the record.

### P6 — Everything here is built for the four record types, not for projects

Datasets, samples and measurements follow this feature, in that order. Anything written
project-shaped now is written three more times later, so the default is a piece parameterised by the
record type, with the project supplying only what is genuinely its own.

The structure supports this already. Every core record has a `<Model>Description`, `<Model>Date` and
`<Model>Identifier` subclassing the same three abstract models, each carrying a `VOCABULARY` and
reachable from its parent under the same names: `descriptions`, `dates`, `identifiers`. A component
can therefore find a record's related models from the record itself, without a per-model register.

So:

- **The attributes page's related sets come from a mixin**, which builds the date and identifier row
  sets from the parent model's own relations. A record type's page declares which sets it wants, not
  how to build them.
- **The descriptions page is one view and one form**, generated from the related model's vocabulary
  and registered once per record type.
- **Templates and components are shared.** The interface layer already ships the row-set component;
  the descriptions page needs one template, and it is written against "a record and its vocabulary"
  rather than against a project.
- **The permission string is derived from the record type**, not written out per page.

The proof is a test, not an intention: **the mixin and the descriptions form are exercised against
`Dataset` as well as `Project`, without adding dataset pages in this work.** That is what
distinguishes a reusable piece from a project-shaped one that happens to be called generic, and it
costs one test module. Where something genuinely cannot generalise, it stays in the project's own
module and the reason is written down.

## Order

Two independent tracks. The second is larger and touches one file the first also touches, so the
navigation work lands first to keep the conflict at one file rather than three.

1. **US-5, US-6, US-1, US-2** — navigation, the deletion refusal, the listing link, and the tests
   for behaviour that is already correct but unproven. All in `views.py`, `urls.py` and tests.
2. **US-3** — the attributes page gains its identifier and date row sets, and `ProjectConfigure` is retired.
3. **US-4** — the descriptions page.

## Verification beyond the suite

Three things cannot be settled by a unit test and get checked on a running page before the work is
called done:

1. A row added to either set with the Add-row control renders working fields. The clone is a string
   substitution and breaks any widget needing its own initialisation, which puts the partial-date
   widget on the dates set squarely in scope.
2. A blocked deletion page shows the alert and the dataset names, with no confirmation field and no
   delete button.
3. The Edit, Delete and Descriptions entries appear for a permitted user and are absent for one who
   is not.

## Test obligations

Every task carries its test, and ten requirements the code already satisfies have no test at all.
Those are the quiet half of this work: the search, the filters, both name-ordering directions, the
empty state, the base classes, the whitespace-trimmed confirmation, and the absence of related
fields from the attributes form.

Two assertion patterns need settling once and reusing:

- Asserting a link is on a page uses `pytest_django.asserts.assertContains` against
  `f'href="{reverse(...)}"'`, and `assertNotContains` for the negative. It is installed and usable
  from a plain test function. The suite has not used it before, which is not the same as it being
  unavailable, and it is preferable to writing a helper of our own.
- Asserting the deprecation is gone needs an explicit `filterwarnings` marker on the test.
  Warnings are silenced for the whole suite, so without it the assertion passes vacuously.

## Raised separately

Real, found on the way, and belonging elsewhere.

- Contributor plugin pages have no permission gate. Anonymous GET of
  `project/<uuid>/contributors/` returns 200. `contributors/add/` returns 500 rather than 403, from
  an unrelated form defect. Child views are not scoped to their parent, so any contribution id
  resolves under any project's address. Authorisation, not this feature.
- Dataset and sample description and key-date pages render the record's detail template, so
  their formsets never appear, and the test covering them asserts only a 200.
- `ProjectDateFactory` is missing from the factories package exports. Small enough to fold in,
  since this feature needs it.

## Risks

1. First caller of the shell's inline system in this repository. Nothing here exercises it, so
   there is no regression net beneath it and the shell's own tests are not shipped in the wheel.
   Narrower than it was: under P3 only identifiers use it.
2. A cloned identifier row is unverified, and it is the piece most likely to look fine in a test
   and fail in a browser.
3. Retiring a tab a user can see today. Deliberate, and the replacement is on the same page.
4. Identifier validation queries once per concrete subclass per row. Fine at the sizes involved,
   worth knowing before the row count grows.
5. The attributes page's existing tests break when the identifier set lands. Their submissions
   carry no formset bookkeeping, so the page will reject them. Expected follow-on work inside that
   task, not a regression to diagnose.
