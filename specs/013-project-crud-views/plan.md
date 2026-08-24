# Plan — 013 Managing a project through the portal

Dated 2026-08-23, from `spec.md` and `research.md`. Decisions are recorded here for veto rather than
raised as questions.

## Shape of the work

The specification asks for six things. Research changed the size of four of them, in both
directions.

| Story | What the plan does | Size against expectation |
|---|---|---|
| US-1 Find a project | Add the entry link, test what is untested | smaller |
| US-2 Register a project | Test what is untested; no behaviour change | smaller |
| US-3 Correct attributes | Add identifiers and dates as inline sets; retire the duplicate page | **larger** |
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
produced this audit.

Its permission string is the one thing worth carrying across. `project-update` checks the bare
codename `change_project`, which only the object-level layer can grant; `ProjectConfigure` checks
`project.change_project`, which either layer can. The app-labelled form is kept, so a portal
administrator holding the model-level permission is not locked out of a page they can see.

**Consequence to accept:** a tab a user sees today disappears, replaced by an Edit button on the same
page. No data and no address a user could have bookmarked is lost, since the tab's fields are a
subset.

### P2 — Descriptions are a registered page with one field per type, not a formset

The unregistered `Descriptions`, `Keywords` and `KeyDates` classes in `project/plugins.py` are
deleted rather than registered.

The generic description plugin is a formset that adds and removes rows. The specification asks for a
fixed set of labelled areas, one per description type, because the vocabulary is closed at seven and
the model allows one row per type. Those are different interfaces, and the generic one is also
broken where it is registered — it resolves to the record's detail template and never draws its
formset.

So the descriptions page is a purpose-built form: one text area per type in
`FairDMDescriptions.from_collection("Project")`, labelled with the type's name and helped by its
definition. Saving writes, updates or deletes one row per non-empty area.

It is registered as a page against the project, which supplies the address, the menu entry, the
permission gate and the breadcrumbs, and means the tab is hidden from users who may not open it —
satisfying FR-042 without a second mechanism.

**Not fixing the generic plugin here.** Dataset and sample carry the same defect and it is their
work, routed out below.

### P3 — Identifiers and dates use the shell's inline formsets

The attributes page becomes an inline-formset view over `ProjectIdentifier` and `ProjectDate`, using
the shell's `InlineFormSet` and `InlinesMixin` rather than django-extra-views.

The constitution names the shell as the default interface layer, the shell's system ships the
templates, the row-adding JavaScript and an atomic parent-then-children save, and the alternative is
the module that is already broken. Against it: this repository would be its first caller, which is
the main risk on this run.

Three settings are not optional:

- `extra = 0` on both sets. The shell omits anything unset, so Django's default of three blank rows
  applies otherwise.
- `formset = DateInlineFormSet` on the dates set, reusing the class already written for the admin
  (`project/admin.py:24-66`). Without it the sibling comparison in `ProjectDate.clean()` is skipped
  on creation and compares against stale values on update. This is the single most likely thing to
  ship broken and unnoticed.
- `value` and `type` present in both field lists. A model `clean()` that keys an error to a field
  absent from the form raises rather than reporting.

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

- Detail: `directory = ["list", "update", "delete"]`, update and delete gated on the user's
  permission for that project.
- List: `directory = ["create"]`, create shown to signed-in users.
- Update: `show_delete_action` gated on delete permission, which lights the Delete button the shell
  already draws in the form body.
- Delete: `show_list_action = True`, which is what makes the Back button a link.
- Descriptions page: reached as a tab, returns to the project.

`show_*_action` accepts a callable taking the user, so the permission-dependent cases need no custom
template logic.

## Order

Two independent tracks. The second is larger and touches one file the first also touches, so the
navigation work lands first to keep the conflict at one file rather than three.

1. **US-5, US-6, US-1, US-2** — navigation, the deletion refusal, the listing link, and the tests
   for behaviour that is already correct but unproven. All in `views.py`, `urls.py` and tests.
2. **US-3** — the attributes page gains its inline sets and `ProjectConfigure` is retired.
3. **US-4** — the descriptions page.

## Verification beyond the suite

Three things cannot be settled by a unit test and get checked on a running page before the work is
called done:

1. A date row added with the Add-row button renders a working date widget. The clone is a string
   substitution and breaks widgets needing their own initialisation.
2. A blocked deletion page shows the alert and the dataset names, with no confirmation field and no
   delete button.
3. The Edit, Delete and Descriptions entries appear for a permitted user and are absent for one who
   is not.

## Test obligations

Every task carries its test, and ten requirements the code already satisfies have no test at all.
Those are the quiet half of this run: the search, the filters, both name-ordering directions, the
empty state, the base classes, the whitespace-trimmed confirmation, and the absence of related
fields from the attributes form.

Two patterns are being established rather than followed, and both should be settled once and reused:

- Asserting a link is on a page. Django's `assertContains` is used nowhere in the suite; the
  existing idiom is a raw substring check. A single helper is worth writing.
- Asserting the deprecation is gone. Warnings are silenced file-wide, so the test needs an explicit
  `filterwarnings` marker or it passes vacuously.

## Routed out

Real, found on the way, and belonging elsewhere.

- **Contributor plugin pages have no permission gate.** Anonymous GET of
  `project/<uuid>/contributors/` returns 200; `contributors/add/` returns 500 rather than 403, from
  an unrelated form defect. Child views are not scoped to their parent, so any contribution id
  resolves under any project's address. Authorisation, not this feature.
- **Dataset and sample description and key-date pages render the record's detail template**, so
  their formsets never appear, and the test covering them asserts only a 200.
- **`ProjectDateFactory` is missing from the factories package exports.** Small enough to fold in,
  since this feature needs it.

## Risks

1. **First caller of the shell's inline system in this repository.** Nothing here exercises it, so
   there is no regression net beneath it and the shell's own tests are not shipped in the wheel.
2. **The date widget inside a cloned row is unverified**, and it is the piece most likely to look
   fine in a test and fail in a browser.
3. **Retiring a tab a user can see today.** Deliberate, and the replacement is on the same page.
4. **Identifier validation queries once per concrete subclass per row.** Fine at the sizes involved,
   worth knowing before the row count grows.
