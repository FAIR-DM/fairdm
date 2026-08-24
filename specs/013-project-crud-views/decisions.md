# Decisions — 013 Managing a project through the portal

This records the audit behind the rewritten `spec.md`, dated 2026-08-23. Each entry states what the
previous specification said, what the code does, which way it was settled and why. It exists so a
later reader can tell a deliberate narrowing from an oversight.

The previous specification was written on 2026-05-11 and described four views: a listing, a
creation form, an attributes form and a deletion page. All four were built and most of what it
asked for is present and correct. Three things changed underneath it. Later work added an image
field and a record of who created a project, neither of which it mentions. One requirement was
quietly abandoned in the code with a note explaining why. And one requirement was implemented
halfway, in a way that passes its test while doing nothing a user can see.

The larger change is to scope rather than to accuracy. The previous specification managed a
project's own fields and left its descriptions, dates and identifiers to the Django admin, which is
the thing the roadmap item exists to stop needing. Those records are now part of the feature.

---

## D1 — Funding leaves the feature

**Previous specification**: FR-018 and FR-028 required funding among the editable attributes, as a
JSON text area.

**Code**: `forms.py:61-74` declares the field. `forms.py:80` omits it from the form's declared field
list, and the shell's form layer then removes any field absent from that list before rendering
(`fairdm/forms/base.py:110-114`). The field has therefore never been reachable. A note above the
declaration, at `forms.py:78-79`, records the reason: the field is complex enough to deserve an
interface of its own rather than a raw JSON box.

**Settled**: funding leaves this feature. The unreachable declaration is deleted rather than left
in place.

**Why**: issue #175 argues the field should stop being JSON altogether and become a related model
shared by projects and datasets, since a funder is an organisation the portal already models.
Building a JSON text area now means building a thing we have already decided to delete. Leaving the
declaration in place means leaving code that looks like a feature and is not one.

**Left open**: nothing here. Funding editing is issue #175's to design.

---

## D2 — Descriptions, dates and identifiers join the feature

**Previous specification**: FR-018 excluded them, and the assumptions said related data was
"managed through separate, dedicated interfaces outside the scope of this feature". No such
interface was ever built, so in practice they were managed through the Django admin.

**Code**: `ProjectDescription`, `ProjectDate` and `ProjectIdentifier` exist as related models with
controlled type vocabularies (`models.py:155, 185, 257`) and are editable in the Django admin
(`admin.py:16, 70, 79`). There is no portal page for any of them. Issue #171 records the gap.

**Settled**: all three join the feature. Descriptions get a page of their own. Dates and
identifiers are edited alongside the project's own attributes. Issue #171 is closed by this feature
except for keywords.

**Why**: the roadmap item this feature serves is about managing records without the Django admin,
and a project whose descriptions can only be written by an administrator has not met it. The
application shell already provides view classes for editing related records alongside a parent, so
this is configuration rather than new machinery, which is what Article XIV asks for. Descriptions
are separated from the rest because they are long-form prose and the others are short values.

**Left open**: which of the shell's facilities fits each case, and how the descriptions page is
laid out. Both are settled during planning.

---

## D3 — Keywords stay out

**Previous specification**: silent on keywords beyond excluding them from the attributes form.

**Code**: keywords are configured per portal through a setting, which the project filter reads to
build its filters (`filters.py:51-106`). There is no editing interface.

**Settled**: keywords remain uneditable through the portal and issue #171 stays open for them
alone.

**Why**: keywords are chosen from controlled vocabularies, and the package that will hold those
vocabularies is not yet integrated. Building a picker now means building it against a vocabulary
layer that is about to be replaced. This is a deferral with a named trigger, not an omission.

---

## D4 — Both visibility defaults are correct

**Previous specification**: silent on defaults.

**Code**: the creation form pre-selects Public (`forms.py:50`). The model's own default is Private
(`models.py:86`).

**Settled**: both stay, and the specification now says so and why.

**Why**: they answer different questions. A person filling in the creation form is looking at the
choice and making it deliberately, and the portal's purpose is served by encouraging openness
there. A record created outside the portal — by an import, a fixture, the API — has nobody looking
at a form, and the safe assumption for it is that nothing has been reviewed for release yet. A
single value cannot serve both.

---

## D5 — The deletion refusal never says what it is refusing

**Previous specification**: FR-023 required the page to be redrawn listing the blocking datasets by
name, and SC-003 measured it.

**Code**: the refusal itself is correct and well placed. A signal on the project raises when a
public dataset exists (`models.py:280-298`), the page catches it inside the ordinary form flow and
puts the datasets into the page's context (`views.py:211-219`), and there is no custom request
handling, exactly as the previous specification asked.

Nothing then reads that context. The name it is stored under appears twice in the repository: once
where it is written, and once in a test asserting it was written. The page that renders is the
shell's standard deletion page, which reads a different name populated by a different mechanism:
the database's own protection, which this signal never triggers. What a user sees is the ordinary
confirmation page, unchanged, still inviting them to delete, with no explanation and no dataset
named.

**Settled**: the specification keeps its requirement. This is a defect and closing it is work in
this feature.

**Why**: the requirement was right, and the direction of this drift is that the code is wrong. It
is worth recording how it survived: the test asserts the datasets reached the context rather than
that they reached the reader, so it passes on an implementation that shows the user nothing. The
replacement test asserts on what the page says.

---

## D6 — The pages use a mechanism the shell has deprecated, and their links are broken

**Previous specification**: silent on navigation entirely. It specified four pages and never said
how anyone reaches them.

**Code**: the listing and attributes pages set attributes named for permissions
(`views.py:44-45, 150-151`) that the shell renamed at 0.16 and removes at 0.18. They still work,
they emit a deprecation warning, and despite their names they decide only whether a link is drawn.
Two consequences are visible now. The deletion page sets none of them, so its back link resolves to
nothing and renders empty. The attributes page draws no link to deletion. Beyond that, no page in
the feature links to any other: neither the project's own page nor its listing entry mentions the
attributes, descriptions or deletion pages, so all three are reachable only by typing an address.

**Settled**: navigation joins the feature. The attributes are renamed to the shell's current ones,
the missing links are added, and each page's links are tested for resolving.

**Why**: these are this feature's own pages, and a page nobody can reach has not been delivered.
The rename is on a removal clock that would otherwise be hit blind, and the two names differ in a
way worth writing down: the old one reads as though it controls access and it never did. Access is
checked separately on every page, as it was before.

---

## D7 — The listing entry was never a placeholder, and is not this feature's to design

**Previous specification**: FR-007 required "a minimal placeholder list-item template" whose visual
design was "deferred to a future spec".

**Code**: a full card with an image, a date, an abstract and a contributor list
(`templates/project/project_card.html`).

**Settled**: the specification stops calling it a placeholder. The card and the project's own page
keep their current design, and this feature changes them only to add links.

**Why**: the deferral happened and the design landed. The specification simply never caught up.
Redesigning either page is separate work, and the project page already has an issue of its own
(#167).

---

## D8 — Requirements state behaviour, not the code that produces it

**Previous specification**: several requirements named the mechanism as well as the outcome — which
field list to override, which widget to redeclare on which subclass, which base class each view
inherits.

**Code**: two of those mechanisms differ from what was written while producing exactly the
specified result. The creation form's field set is narrowed by the shell rather than by Django's
own mechanism, and the creation form inherits its visibility choice rather than redeclaring it.

**Settled**: requirements describe what a person can do and what the portal guarantees.
Architectural constraints stay where they carry a real obligation — use the shell's facilities
rather than hand-written equivalents, use its current mechanism for declaring links — and the rest
is settled during planning.

**Why**: both of these read as drift and neither is. A specification written at that altitude
generates false findings on every later audit and forbids improvements that change nothing a user
sees. It also made the previous document hard to read: the single longest requirement in it was
about form class inheritance.

---

## D9 — Undocumented behaviour, now written down

Found during the audit, correct, and previously unrecorded. Each is now in the specification.

- A project records who created it (`views.py:94`, `models.py:113-125`). Added by later work.
- A project's image is validated for size and rendered through a thumbnailing widget
  (`forms.py:24-32`). Added by the image field specification, 015.
- Creation, change and deletion each report success to the user. The shell does this.
- A page's configured destination is overridden by a validated destination in the request when one
  is present. The shell does this, so the destinations in this specification are what happens
  absent that, not guarantees.

---

## D10 — A record's pages are one registered collection, not one registration each

**Previous specification**: silent on how a page is addressed. The pages were given routes of their
own, outside the portal's per-record navigation, which is why none of them links to any other.

**Code**: a navigation entry's address is built from the record's name and the registration's own
name, so a page addressed independently can never appear in that navigation. Rendered as an
anonymous visitor, a project's navigation offers datasets, export, configure and contributors, with
no entry for the project itself and no entry marked as current.

**Settled**: the project's own page is its overview registration, and the attributes and deletion
pages belong to that registration rather than standing beside it. `ProjectConfigure` and the
independent editing and deletion routes are retired.

**Why**: a registration carries one navigation entry. One registration per page fills the record's
navigation with noise as soon as add-ons contribute their own, so a registration is a collection of
related functionality with a single entry, and the collection's own template links whatever else it
owns. The portal was built this way until three months ago: nine registrations existed against a
project, among them the overview, the editing page and the deletion page, and the record's address
method returned the overview. The registry rework of 2026-08-11 cut them to three while migrating to
decorator arguments, and six lost their registration in the move with no reason recorded in any
commit message, specification or plan. This restores an architecture that was dismantled in passing.

**Left open**: the layout of the overview template, which links the collection's other pages. Out of
scope here per FR-047.

---

## D11 — One address prefix, and it is the plural one

**Previous specification**: silent. The convention was never written down, and both forms are in use.

**Code**: a project is at `projects/<uuid>/` while the pages registered against it mount under
`project/<uuid>/`. Datasets carry the same split. Samples are plural already, and measurements are
singular throughout.

**Settled**: the singular form goes. A project keeps `projects/<uuid>/` and its pages become segments
below it.

**Why**: the plural address is the one a reader may have cited, and the inconsistency is worth
removing rather than entrenching. The cost is that the pages already registered against a project —
contributors, datasets, export — change address, which is accepted.

**Left open**: nothing for this feature. Datasets and measurements are raised separately so the
singular form leaves the repository in one pass rather than one record type at a time.

---

## Implementer decisions — US3 Foundations (T001-T005)

Mini-ADRs from the Foundations phase build, per `implement-story.md` §2.6. Lighter-weight than the
design-review entries above: these are choices made while building T001-T005, not settled during
planning.

### T002 — `fields` on `RelatedRecordInline` is a tuple, not a list

**Decision**: `RelatedRecordInline.fields = ("type", "value")`.

**Why**: it was first written as a list. `BaseInlineFormSet.__init__` appends the parent foreign
key's name to `form._meta.fields` in place when it is a list
(`django/forms/models.py:1115-1118`), and `get_factory_kwargs()` passes the class attribute through
by reference, so building one subclass's formset (`ProjectDateInline`) permanently mutated the
shared base class attribute for every other subclass, including `DatasetDateInline`'s. Reproduced
with a failing test (`test_each_subclass_names_only_its_model`) before fixing; kept as a permanent
regression test (`test_building_one_declarations_formset_does_not_mutate_the_shared_fields_tuple`).
A tuple is immutable, which routes Django through its own copy-on-write branch instead.

**Revisit if**: a future subclass needs to override `fields` with something other than a 2-tuple —
still fine as a tuple, but worth re-reading this note before changing it back to a list for any
reason.

### T002/T004 — the row sets and the descriptions form are separate modules

**Decision**: `fairdm/core/related_records.py` (row sets, T002) and `fairdm/core/descriptions.py`
(the vocabulary form, T004) are two files, not one.

**Why**: built together first, in one module, since both are "shared related-record pieces" per
the brief. Split before committing so each task keeps its own clean commit, and because they serve
different consumers later: US-3's attributes page lists row sets, US-4's descriptions page uses the
form. Keeping them apart now means neither future story imports something the other doesn't need.

**Revisit if**: nothing currently anticipated - this is a module-boundary call, not a load-bearing
constraint.

### T003 — the shared rule's message drops "collection" from the dataset wording

**Decision**: `date_ordering_formset`'s message reads "The %(noun)s's end date (...) cannot be
before its start date (...)" for both project and dataset, rather than keeping the dataset-specific
"collection end date"/"collection start date" phrasing the duplicate carried.

**Why**: the rule is parameterised on the noun alone (as the brief specifies), not on a
per-record-type phrase fragment. No test in this repository asserts the literal error string - the
existing admin tests for both `ProjectAdmin` and `DatasetAdmin` assert refusal (`response.status_code
== 200`, no object created), not wording - so this was free to standardise. Recorded here because
it is still user-facing text that changed on purpose.

**Revisit if**: a future test starts asserting the literal message text, or a portal's translators
report the wording is now ambiguous for dataset collection dates specifically.

### T005 — permission fixtures each carry their own project as `.project`

**Decision**: `user_with_change_permission`, `user_with_delete_permission` and
`user_with_no_permission` each build a fresh `Project` internally and set it as an in-memory
`.project` attribute on the returned `User`, rather than depending on the module's `private_project`
fixture or returning a tuple.

**Why**: the brief names five fixtures, one per bullet, each yielding one thing. A tuple return
breaks the plain `def test_x(self, user_with_change_permission):` shape every other fixture in this
package uses, and coupling the permission fixtures to `private_project` would make a test that asks
for `user_with_change_permission` alone unable to assert the grant without also requesting a second,
unrelated-looking fixture.

**Revisit if**: a later story's test needs the permission-holding user and one of the public/private
project fixtures to refer to the *same* project - at that point pass the project in explicitly at
the call site rather than fixture-parametrizing.

---

## Implementer decisions — US3 (T026-T049, T088)

### T034/T040 — `Attributes(Plugin, InlinesMixin, FairDMUpdateView)`, `InlinesMixin` in the middle

**Decision**: `InlinesMixin` sits between `Plugin` and `FairDMUpdateView` in the base list, not
first and not last.

**Why**: `InlinesMixin.form_valid`/`form_invalid`/`get_context_data` are the terminal handlers for
the update flow and must reach `FairDMUpdateView`'s (→ `MVPUpdateView`'s) `get_form`,
`get_success_message` etc. through `super()`, the same relative order the shell's own
`MVPInlineUpdateView(InlinesMixin, MVPUpdateView)` uses. `Plugin` goes first because its
`get_context_data` (adding `base_object`, breadcrumbs, `plugin_menu`) and its `dispatch`
(`PermissionRequiredMixin`) must run outermost, matching every other page in this file.

**Revisit if**: a future additional view needs the row-set mixin and this ordering does not
linearise (C3 conflict) — unlikely, since `Plugin` and `FairDMUpdateView` do not share a
non-`View`/`object` ancestor.

### T040 — `ProjectDatesInline` (identifier row set + ordering rule combined) lives in `plugins.py`, not `related_records.py`

**Decision**: the subclass that pairs `ProjectDateInline` (from `related_records.py`) with
`date_ordering_formset(ProjectDate.START_TYPE, ProjectDate.END_TYPE, ...)` is declared in
`fairdm/core/project/plugins.py`, next to `Attributes`, rather than added to
`related_records.py` alongside the base declarations.

**Why**: the brief's prohibitions scope this story to `forms.py`, `plugins.py`, templates and
tests — `related_records.py` is a shared module built and tested in an earlier phase and is not
to be rebuilt or extended here. More fundamentally, *which* shared rule pairs with *which* shared
declaration is a choice this page makes for itself (plan P6: a dataset's dates page will pair the
same `DatasetDateInline` base with its own `CollectionStart`/`CollectionEnd` parameterisation) —
it is page-specific configuration, not a third shared declaration.

**Revisit if**: three or more record types end up writing the identical
`<Type>DatesInline(<Type>DateInline)` combining pattern — at that point a small factory in
`related_records.py` (`with_ordering(base, start, end, message)`) might be worth it, but plan P6
already rejected a resolver-based version of this same idea for hiding the real difference
between record types that have an ordered pair and those that do not.

### T026 — one composed test rather than treating scattered pre-existing coverage as sufficient

**Decision**: added `TestAttributesPageOverHTTP` with a dedicated test asserting the address
shape and the anonymous redirect together, rather than leaving T026 satisfied by the combination
of `test_the_attributes_page_resolves_as_an_extra_view_of_the_overview`
(`test_plugins.py`, Track 1) and `test_project_update_anonymous_redirects_to_login`
(`test_views.py`, pre-existing, stale `T022` numbering) — both of which already proved every
piece of T026's acceptance criterion before this task ran.

**Why**: the brief names T026 as its own task with its own acceptance criterion; leaving it
"satisfied by inference" across two unrelated files, neither authored for this task, would leave
no single test whose failure specifically means "T026 broke." The new test is small and composes
claims already proven elsewhere rather than re-testing the same code path a third way.

**Revisit if**: this reads as duplicate coverage at review — the counter-evidence is in this
entry and in `progress.md`'s T026 note.

### T049 — "no second registered page" checked by field-set overlap, not by name

**Decision**: `TestExactlyOnePageOffersTheProjectsOwnAttributes` walks every top-level
registration against `Project` plus each one's `get_extra_views()`, and flags any page whose
`form_class.Meta.fields` intersects `{"image", "name", "status", "visibility", "owner"}` — not a
check for a class named `ProjectConfigure` or similar.

**Why**: the acceptance criterion is "no second registered page offers an overlapping field
set," which is a claim about behaviour (what a page edits), not about a name. A name-based check
would pass the moment `ProjectConfigure` is renamed and miss a brand-new page that reintroduces
the same surface under a different name.

**Revisit if**: a future page legitimately needs to expose a subset of these fields for a
different purpose (e.g. a bulk-edit page touching only `status`) — the overlap check would flag
it and the test's own field set may need to shrink to the fields that must stay page-unique.

### T048 — two pre-existing tests removed, and why that is not a weakening

**Decision**: `test_date_form_validates_range` and `test_identifier_form_accepts_valid_data`
were deleted from `tests/test_core/test_project/test_forms.py` along with the two form classes
they exercised. Approved rather than escalated.

**Why**: both tested classes that no longer exist. `ProjectDateForm` and `ProjectIdentifierForm`
were the single-record forms the row sets replace, and T048 is the task that removes them. The
behaviour each test asserted is now covered in more places than before, not fewer:

- The date range rule has three tests over the shared, parameterised version
  (`tests/test_core/test_formsets.py`), including one asserting that record types outside the
  configured pair are left alone — a case the deleted test could not express.
- The same rule is additionally asserted through a real submission, twice
  (`test_a_backwards_pair_both_newly_added_is_refused_and_saves_nothing`,
  `test_a_backwards_pair_with_the_start_already_stored_is_refused_and_saves_nothing`).
- Identifier validity is asserted through the page rather than the form
  (`test_adding_an_identifier_of_a_chosen_type_records_it_against_the_project` and the four
  tests around it), including the two collision cases the deleted test did not reach.

**Revisit if**: a later change removes the row sets — the shared rule's tests would go with them
and the coverage this entry relies on would need re-establishing at the form level.

---

### T062 — `ProjectDescriptionForm` and `TestProjectDescriptionForm` deleted

**Decision**: `ProjectDescriptionForm` (`fairdm/core/project/forms.py`) and its test class
`TestProjectDescriptionForm` (`tests/test_core/test_project/test_forms.py`) were deleted, along
with the now-unused `ValidationError` import the form's `clean()` needed. Named explicitly in the
US4 brief's acceptance criteria for T062, not an escalation.

**Why**: the form was used by no running code — the old, unregistered `Descriptions` plugin class
it backed was itself replaced by the registered page built on `VocabularyDescriptionsForm` at
T051. The per-type uniqueness the deleted test asserted (`test_description_form_enforces_uniqueness`)
is covered more broadly now, through the page rather than the form directly:
`TestSavingTextIntoOneAreaRecordsOnlyThatType` (T055), `TestEditingAnExistingDescriptionPersists`
(T057) and `TestRepeatSubmissionNeverDuplicatesAType` (T060) — the last one asserting the count
per type after a repeat submission, which the deleted test never reached since it only checked
that a second `is_valid()` call failed.

**Revisit if**: a later change reintroduces a form keyed on a single `(type, value)` pair rather
than the vocabulary-driven slot form — the uniqueness behaviour would need a form-level test again.

---

### T083 — `test_project_delete_blocks_public_datasets` rewritten to assert rendered content

**Decision**: `test_project_delete_blocks_public_datasets`
(`tests/test_core/test_project/test_views.py`) was rewritten in place — same test, same name —
to assert the blocking dataset's name appears in the rendered response instead of asserting the
invented `protected_datasets` context key. Named explicitly as the one allowed exception in the
US6 brief's prohibitions, per plan P4.

**Why**: `protected_datasets` was a key `Delete.form_valid()` set on the context but the shared
delete template never reads — the refusal rendered as an ordinary confirmation page in production
regardless of what the test asserted. `Delete.get_context_data()` now populates the shell's own
`is_protected`/`protected_objects` contract from the project's public datasets, evaluated fresh on
each call, which is what the template actually branches on.

**Revisit if**: the shared delete template's protected-object contract changes name or shape again
— the same rewrite discipline applies rather than reintroducing a page-specific context key.

---

### T067/T068 — `Overview` mixes in `mvp.views.detail.CRUDDirectoryMixin` directly

**Decision**: `Overview` (a `TemplateView`-based registration, not a `DetailView`) gained
`mvp.views.detail.CRUDDirectoryMixin` in its own bases, plus `model = Project`, `directory =
["update", "delete"]` and a `crud_views` override reversing those two actions to `Attributes`'
and `Delete`'s registered names (`project:overview-attributes`/`-delete`) rather than the
default `{model_name}-update`/`-delete` shape, which resolves to the standalone routes this
feature retires.

**Why**: the brief's prohibition is to switch the shell's existing action-link mechanism on
rather than write a parallel one, and `detail_view.html` (which `project_detail.html` extends
without overriding `page.actions`) already checks `directory.update_url`/`directory.delete_url`
and draws "Edit"/"Delete" buttons — it was simply never wired up for `Overview`, because
`OverviewPlugin`/`FairDMTemplateView` builds on `MVPTemplateView`, which carries no
`CRUDDirectoryMixin` at all (only `MVPDetailView` does, and `Overview` is not one — it has no
`SingleObjectMixin` of its own; the record comes through `Plugin.base_object`). No existing code
in this repository mixes `CRUDDirectoryMixin` into a plain `TemplateView` this way; it is the
first instance.

**Revisit if**: a later record type's own page (dataset, sample, measurement, per plan P6) needs
the same treatment — the shape here (mixin + `model` + `directory` + `crud_views` override +
one `show_<action>_action` per extra view, reusing that view's own `permission` string rather
than restating it) generalises directly.

---

### T069 — `Delete.get_back_url()` falls back to the project, not the list

**Decision**: overridden rather than left to `MVPDeleteView`'s own `get_back_url()`, which falls
back to `resolve_crud_url("list")`.

**Why**: `Delete`'s own `directory` (inherited default, unset) carries no `"list"` entry, so
`resolve_crud_url("list")` always returns `None` regardless of `show_list_action` — the shell
rendered the "Go Back" control as a destination-less `<button>` (`cotton/button.html` picks the
element by `href|yesno:"a,button"`). Even set to a working list URL, "list" is the wrong
destination: from a project's own deletion page, "back" means back to the project being
considered for deletion, not the collection everyone reaches it through (FR-044/T070). The `?back`
query-string override is preserved unchanged — only the two-step fallback chain's *final* step
changes, from `resolve_crud_url("list")` to `self.base_object.get_absolute_url()`.

**Revisit if**: `Delete` ever gains a genuine `"list"` action of its own — the override would then
need to choose explicitly between the two rather than only ever preferring the project.

---

## Raised separately

Found while checking the specification against the code, real, and not this feature's work.

- **Issue #174** — the attributes page fetches its project without using the queryset the view
  declares, so no prefetching applies and the fetch runs twice on a submission. Already open.
- **Issue #173** — the project's forms and views resolve their translations when the module is
  imported rather than when a page is rendered, so a portal serving more than one language gets
  whichever was active at startup. Already open.
- **The project's own page decides visibility by comparing against a bare number** rather than the
  named value (`views.py:256`). Inside a method this feature does not otherwise touch, and the page
  itself is out of scope. Raised separately.
- **Issue #283** — datasets and measurements keep the singular address prefix that D11 removes from
  projects. A dataset's pages mount under the singular form while the dataset itself is plural, and
  measurements are included under the singular form throughout. Samples are already plural. Raised
  separately so the convention lands across the repository rather than one record type at a time.
- **An extra view's owner `check` is not actually consulted through a real HTTP request** —
  verified while working T067/T068, not this feature's to fix (touches shared
  `fairdm/contrib/plugins/base.py`/`access.py`, and the brief prohibits changing `check`).
  `Plugin.has_permission()` calls `can_open(self.__class__, ...)`, and `can_open` reads
  `owner = getattr(view_class, "plugin_class", None) or view_class` — but `plugin_class` is only
  ever set as an *instance* attribute, by `View.as_view()`'s `cls(**initkwargs)` call inside
  `Plugin.get_urls()`'s `mount()` closure. Reading it off the *class* (`self.__class__`, not
  `self`) therefore always finds the un-set `ClassVar` default (`None`), so `owner` resolves to
  the extra view itself, never its declared owner. Concretely: `Attributes.check` (unset, default
  `True`) is what actually gates a real request to the attributes page — `Overview.check`
  (`project_is_visible`) is never reached — so a private project is reachable through `Attributes`
  or `Delete` by anyone holding the model-level permission alone, with no `view_project` grant at
  all. Reproduced directly: `can_open(Attributes, request, private_project)` returns `True` for a
  user holding only global `change_project`, no per-object grant, on a `Visibility.PRIVATE`
  project. The existing test believed to cover this
  (`TestTheOverviewGuardsAPrivateProjectsVisibility.test_the_attributes_page_inherits_the_visibility_check_from_its_owner`,
  `tests/test_core/test_project/test_plugins.py`) passes for an unrelated reason — its fixture's
  user is refused by the `permission` check alone, so it never exercises whether `check` itself
  was inherited. `tests/test_core/test_project/test_plugins.py::TestAttributesPageOverHTTP::test_a_user_holding_change_permission_at_the_model_level_is_admitted`
  independently demonstrates the same gap is already relied upon as intended behaviour (its
  docstring: "the retiring standalone page's behaviour and must survive"), which is what makes
  this a design question for the registry's own maintainer rather than a one-line fix here.
- **FR-045 — "the attributes page MUST offer the deletion page to a user who may delete the
  project" — has no task in `tasks.md`'s US-5 block (T067-T074) and so was not built here.**
  `form_view.html` (the attributes page's own template, via `MVPUpdateView`) already has a slot
  for exactly this: `{% if delete_url %}` in its `actions` block, fed by
  `MVPUpdateView.get_delete_url()` → `resolve_crud_url("delete")`, gated by
  `show_delete_action`/`crud_views["delete"]` on `Attributes` itself (not `Overview` — a
  different instance of the same mechanism T068 switched on). Left alone rather than added
  speculatively: the brief's acceptance criteria (T067-T071, T073) are what was authorised, and
  the brief's own prohibitions call out scope containment. Flagged here so it is not read as
  forgotten.
