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
| US-3 Correct attributes | Add identifiers as a row set, dates as fields, and retire the duplicate page | **larger** |
| US-4 Describe a project | Build a slot form and register it as a page | as expected |
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

### P2 — Descriptions are a registered page with one field per type, not a formset

The unregistered `Descriptions`, `Keywords` and `KeyDates` classes in `project/plugins.py` are
deleted rather than registered.

The generic description plugin is a formset that adds and removes rows. The specification asks for a
fixed set of labelled areas, one per description type, because the vocabulary is closed at seven and
the model allows one row per type. Those are different interfaces, and the generic one is also
broken where it is registered, because it resolves to the record's detail template and never draws
its formset.

So the descriptions page is a purpose-built form: one text area per type in
`FairDMDescriptions.from_collection("Project")`, labelled with the type's name and helped by its
definition. Saving writes, updates or deletes one row per non-empty area.

It is registered as a page against the project, which supplies the address, the menu entry, the
breadcrumbs and the permission gate, and means the tab is hidden from users who may not open it.
That satisfies FR-042 without a second mechanism.

It declares `permission = "project.change_project"`, the same string as the attributes page. The
check is only supplied where one is declared: a registered page with no permission is open to
everyone, anonymous included, and the record is fetched through an unfiltered manager on the
assumption that the page gates itself. That omission is exactly what leaves the contributor pages
open today, and it is not repeated here.

Not fixing the generic plugin here. Dataset and sample carry the same defect and it is their work,
raised separately below.

### P3 — Identifiers are an inline set; dates are two fields

The two related records on the attributes page do not get the same treatment, and the dividing line
is the one P2 already drew. A closed vocabulary with one row per type is a fixed set of fields. An
open, repeating record is a formset.

- Identifiers repeat. Any number, types drawn from a vocabulary, no ceiling. That is a formset,
  using the shell's `InlineFormSet` and `InlinesMixin` rather than django-extra-views.
- Dates do not. The project date vocabulary holds exactly two members, Start and End, and the
  model allows one row per type. That is two form fields, written onto their rows on save, in the
  same way descriptions are seven fields rather than a list.

Treating dates as fields removes three things from this work: the sibling-validation formset class,
the row-adding control on the dates set, and the manual browser check that the cloned date widget
survives. The end-before-start rule becomes an ordinary `clean()` on the attributes form, with both
values in hand, which is where it can actually be enforced.

The constitution names the shell as the default interface layer, the shell's system ships the
templates, the row-adding JavaScript and an atomic parent-then-children save, and the alternative is
the module that is already broken. Against it: this repository would be its first caller, which is
the main risk here.

Two settings on the identifier set are not optional:

- `extra = 0`. The shell omits anything left unset, so Django's default of three blank rows applies
  otherwise.
- `value` and `type` both present in the field list. A model `clean()` that keys an error to a field
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

## Order

Two independent tracks. The second is larger and touches one file the first also touches, so the
navigation work lands first to keep the conflict at one file rather than three.

1. **US-5, US-6, US-1, US-2** — navigation, the deletion refusal, the listing link, and the tests
   for behaviour that is already correct but unproven. All in `views.py`, `urls.py` and tests.
2. **US-3** — the attributes page gains its identifier rows and date fields, and `ProjectConfigure` is retired.
3. **US-4** — the descriptions page.

## Verification beyond the suite

Three things cannot be settled by a unit test and get checked on a running page before the work is
called done:

1. An identifier row added with the Add-row control renders a working row. The clone is a string
   substitution and breaks any widget needing its own initialisation. This no longer applies to
   dates, which are ordinary fields under P3.
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
