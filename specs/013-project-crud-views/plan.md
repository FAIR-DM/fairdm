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
| US-3 Correct attributes | Row sets for identifiers and dates; the page moves into the collection | **larger** |
| US-4 Describe a project | Build a vocabulary-driven form, reusable across record types | as expected |
| US-5 Move between pages | The tab strip, once the pages are one collection | **much smaller** |
| US-6 Remove a project | Populate the shell's refusal contract | smaller |

## Decisions taken

### P1 — The project's pages are one registered collection

The project's detail page becomes an Overview registration against `Project`, and the attributes and
deletion pages become extra views belonging to it. `ProjectConfigure` and the standalone
`project-update` and `project-delete` routes are retired.

**This restores what was dismantled by accident.** Before May, `project/plugins.py` registered nine
plugins, among them `Overview`, `Edit` and `Delete`, and `Project.get_absolute_url()` returned
`project:overview`. The May work added standalone views alongside them. The registry rework of
2026-08-11 then cut the registrations from nine to three while migrating to decorator arguments, and
`Overview`, `Edit`, `Delete`, `Descriptions`, `Keywords` and `KeyDates` all lost their decorator in
the move. Nothing in any commit message, spec or plan records a reason to leave the architecture.
The dead classes in that file and the missing overview are the residue of that migration.

**Why the detail page has to be a registration rather than a route of its own.** A menu entry's
address is built as `f"{model_name}:{name}"` and there is no way to give an entry an arbitrary URL
name, so a page outside the registration namespace can never appear in the record's own navigation.
Verified by rendering: on any project sub-page the tab strip offers Datasets, Export, Configure and
Contributors and no way back to the project, and on the project page itself no tab is selected. The
project page also draws that strip through a hardcoded call in its own template while every other
page draws it from context — two paths for one strip. Making the overview a registration collapses
both, and the selected-tab match starts working for free.

**Why the attributes and deletion pages are extra views rather than registrations of their own.** A
registration is a collection of related functionality carrying **one** menu entry, and its own
template links whatever else it owns. If every page an addon needs took a menu entry, the strip
fills with noise. So Overview registers once, and the attributes and deletion pages hang off it. The
overview's template links them, which is outside this feature's scope.

**The permission trap that comes with that, and must not be repeated.** An extra view inherits its
owner's `check` but **not** its `permission`: the resolution reads `check` from the owner and
`permission` from the view itself. An extra view that declares no permission is therefore open to
everyone, including anonymous visitors, no matter how restricted its owner is. That is not
theoretical — it is why the contributor pages answer an anonymous request today, raised as #279. So
**every extra view here declares its own permission explicitly**, and the attributes and deletion
pages each carry `project.change_project` and `project.delete_project`.

**And the record's own privacy check has to move with it.** The current detail view enforces
visibility on private projects by refusing in `get_object`. A registered page resolves its record
through machinery that deliberately reads past filtered managers, on the assumption that the page
gates itself. Moved without reimplementing that check as the page's own `check`, private projects
become readable by anyone holding a link. This is the single thing on this decision that must not be
got wrong, and it gets a test naming it.

The permission behaviour of the retired pages carries across. The standalone attributes page asks
`user.has_perm("change_project", project)`, which only the record-level layer can satisfy: measured
on this branch, a user holding the permission at model level gets `True` from
`has_perm("project.change_project")` and **`False`** from `has_perm("project.change_project",
project)`. The registered pages ask twice, model level then record, through the shared helper. That
is the behaviour to keep, and the string becomes `project.change_project`.

Consequence to accept: `project-detail`, `project-update` and `project-delete` stop existing as
names. Four reversals in the running code and nine in tests, none of them in a template, because
templates go through the record's own address method.

### P2 — Descriptions is one of the project's page's own belongings, one area per vocabulary type

**Revised 2026-08-24 (D13).** This section first made the descriptions page a registration of its
own, matching Dataset and Sample. That was matching the wrong thing: those two are registrations
because nothing has restructured them yet. A page per navigation entry does not scale — every
add-on registering a page against a record competes for the same strip — so the descriptions page
belongs to the project's page exactly as the update and deletion pages do, and the project's own
page draws the link. The rest of this section stands as written, with "registered as a page against
the project" reading as "belonging to the project's page".


The unregistered `Descriptions`, `Keywords` and `KeyDates` classes in `project/plugins.py` are
deleted rather than registered.

The generic description plugin adds and removes rows. The specification asks for a fixed set of
labelled areas, one per description type, because the model allows one row per type. Those are
different interfaces, and the generic one is also broken where it is registered, because it resolves
to the record's detail template and never draws its formset.

So the descriptions page is a form whose fields are generated from the related model's `VOCABULARY`:
one text area per concept, labelled with its name and helped by its definition. Saving writes,
updates or deletes one row per area.

Driving the fields off the vocabulary is what lets the page expand without code: a new description
type is a vocabulary entry, and the page grows a field.

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
- **The other record types carry more of them.** A page that treats dates as fields here and as rows
  everywhere else makes a user learn each record type separately. P6 covers what that costs.

Three settings are not optional:

- `extra = 0` on both sets. The interface layer omits anything left unset, so Django's default of
  three blank rows applies otherwise.
- The date-ordering rule on the dates set, as the shared parameterised formset described in P6.
  Without it the check in `ProjectDate.clean()` runs and finds nothing: it looks the sibling up in
  the database, so where both rows are submitted together it sees neither, and where one is stored
  it compares against the stored value rather than the submitted one. This is the single most likely
  thing to ship broken and unnoticed.
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

### P5 — Navigation is the tab strip, plus configuration on the listing

Most of what an earlier draft of this plan put here dissolves under P1. Once the project's pages are
one registered collection, the tab strip *is* the navigation between them: the overview carries the
menu entry, and its template links the attributes and deletion pages. Entries are hidden from users
who may not open them without extra work, because the menu's visibility test and the page's own
access test are the same function — which is FR-041 and FR-042 together.

What remains is genuinely configuration, on the two pages that stay outside the collection:

- **The listing** keeps `directory = ["create"]` and shows the create action to signed-in users. It
  is a page about the record type rather than about a record, so it is not part of any record's
  collection.
- **The listing entry** links to the record through the record's own address method, which follows
  wherever P1 puts it.

Two rules that still apply wherever these attributes are set:

- The superseded `has_<action>_permission` names go. They are honoured, they warn, and they are
  removed in the next release of the interface layer. One of the four in the project views is dead
  already: the listing's `has_list_permission` is never consulted, because a listing's directory does
  not contain its own action.
- A permission-dependent flag is a method, not a lambda in the class body. The flag is read with
  `getattr`, so a plain function binds as a method and is then called with an argument too many —
  a 500 on the page, confirmed on this branch.

**The prefix collision, settled: plural everywhere.** Registered pages for a project mount under
`project/<uuid>/` while the project's own page is at `projects/<uuid>/`. One of them had to move, and
the singular form is the one that goes: a project stays at `projects/<uuid>/`, which is the
address a reader may have cited, and its pages become `projects/<uuid>/<page>/`. Contributors,
datasets and export change address as a result, and that is accepted.

Two things this has to get right in the URL configuration:

- **Order.** The `projects/create/` route must stay declared ahead of the `projects/<uuid>/` include,
  or `create` is read as an identifier and the creation page resolves to a record lookup that fails.
  Django matches in declaration order, so this is a matter of not reordering the file.
- **The record's own page is the include's root**, reached because the overview declares no path
  segment of its own. The contributor pages already work this way. `projects/<uuid>/` therefore keeps
  answering with no route of its own, which is what retires `project-detail`.

**The same split exists on datasets and measurements**, and is not this feature's to fix: a dataset's
pages mount at `dataset/<uuid>/` and measurements are included under `measurement/`, while samples
are already plural. Raised separately so the singular form leaves the repository in one pass rather
than one record type at a time. Raised as issue #283.

### P6 — Built for the four record types, by declaration rather than by machinery

Datasets, samples and measurements follow this feature, in that order. Anything written
project-shaped now is written three more times later. The first draft of this decision answered that
with a mixin that resolved each record's related models at runtime and built its row sets
dynamically. That was the wrong instrument, for a reason worth recording.

**The declaration it would have replaced is five lines.** A row set needs a model, the two fields
every one of these records has, and no blank rows. The invariant part factors into a single shared
base; what remains is one line per related model. A resolver that computes those four lines is a
mechanism with one caller, and it buys nothing that a base class does not.

**Worse, the resolver would have hidden a real difference.** Only two of the four record types have
an ordered pair of dates, and they do not agree on the names: a project's are `Start` and `End`, a
dataset's are `CollectionStart` and `CollectionEnd`, and samples and measurements have no such pair
at all — their vocabularies are `Created`/`Destroyed`/`Collected`/… and `Setup`/`TearDown`. Handing
every record type the same date rule means three of them get a rule that silently checks nothing,
because its type names are not in their vocabulary. That is the defect this plan calls the most
likely thing to ship unnoticed, reintroduced by the attempt to generalise.

So the shape is:

- **One shared row-set base** carrying the fields and `extra = 0`, with one subclass per related
  model naming only its model. Each record type's page lists the sets it wants.
- **One date-ordering rule, parameterised** on its start type, its end type and the noun in its
  message, in a shared module. A record type that has no ordered pair does not use it, and that is
  an explicit decision rather than a rule that runs and finds nothing.
- **The descriptions page is one view and one form**, its fields generated from the related model's
  vocabulary, registered once per record type. This one genuinely is generic: the vocabulary is the
  only thing that varies and every one of these models carries it.
- **The permission string stays written out per page.** Deriving it from the record type breaks on
  the polymorphic types, where a concrete subclass reports its own app: a sample subclass derives
  `fairdm_demo.change_rocksample`, which nothing grants, because grants are normalised to the
  polymorphic base. The existing pages already write the string out, and this follows them.

**This removes duplication that already exists**, which is the strongest evidence the shape is
right. The date-ordering rule has been copy-pasted once already — `fairdm/core/project/admin.py:24`
and `fairdm/core/dataset/admin.py:74`, the second one's docstring saying it mirrors the first, and
only the second carrying a test. Lifting one parameterised version and pointing both admins at it is
net work removed from datasets, samples and measurements rather than added here.

The guard is that the shared pieces are tested against two record types, not one: the row-set base
and the descriptions form are exercised over `Project` and `Dataset` in the same test, asserting
behaviour rather than construction. Asserting that a component built from a model's own relations
yields that model's relations proves nothing — it can only fail if a literal name was left behind.

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
