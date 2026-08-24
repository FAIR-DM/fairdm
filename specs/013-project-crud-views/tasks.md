# Tasks — 013 Managing a project through the portal

Written from `spec.md` as though none of this feature existed, then checked against the codebase in
a separate pass. Nothing here was written by reading the implementation, and nothing was carried
over from the previous task list.

Every task is tests-first per Article I. A task's test scope is one test class or one test module,
per the repository's testing standard. A task is done when its test passes and the whole suite is
green at the end of its story, not before.

The Project model and its related records (`ProjectDescription`, `ProjectDate`, `ProjectIdentifier`)
are established by earlier specifications and are assumed to exist. Everything a user touches is
assumed not to.

---

## Foundations

- **T001** — Export `ProjectDateFactory` from the factories package alongside its dataset, sample
  and measurement equivalents, so tests import it the same way as the others. Test: the package
  exports all three project related-record factories.
- **T002** — Build the shared row-set declaration carrying the two fields every related record has
  and no blank rows, with one subclass per related model naming only its model. Test, over both
  `Project` and `Dataset`: a page declaring these sets presents each record's existing rows and no
  blank ones, and saving a new row writes it against that record.
- **T003** — Lift the date-ordering rule into a shared formset parameterised on its start type, its
  end type and the noun in its message, and point the project and dataset admin classes at it,
  deleting the duplicate at `dataset/admin.py`. Test: a backwards pair submitted as two rows in one
  submission is refused for a project (`Start`/`End`) and for a dataset
  (`CollectionStart`/`CollectionEnd`), and a record type with no ordered pair is unaffected.
- **T004** — Build the form that generates one text area per concept in a related model's
  vocabulary, labelled with the concept's name and helped by its definition. Test, over both
  `ProjectDescription` and `DatasetDescription`: the field set matches that model's vocabulary
  exactly and in its order, and saving text into one area writes exactly one row of that type
  against that record.
- **T005** — Establish the fixtures this feature needs in the project test package's `conftest`: a
  public project, a private project, a user holding change permission on a project, a user holding
  delete permission, and a user holding neither. Test: each fixture yields a record with the
  permissions claimed.

## US-1 — Find a project

- **T006** — Test: the listing is reachable at `project-list` and returns 200 to an anonymous
  visitor.
- **T007** — Test: only public projects appear in the listing, for an anonymous visitor and for a
  signed-in one who owns a private project. Then the queryset restriction that satisfies it.
- **T008** — Test: searching a distinctive word in a project's name returns that project and
  excludes others. Then the search configuration.
- **T009** — Test: searching a project's identifier returns that project.
- **T010** — Test: ordering by name returns alphabetical order, and the reverse returns the reverse.
  Both directions asserted separately.
- **T011** — Test: ordering by date added returns oldest first, and the reverse returns the reverse.
- **T012** — Test: applying a status filter returns only projects with that status. Then attach the
  portal's existing project filter to the view.
- **T013** — Test: the portal's owner, contributor and tag filters each narrow the listing.
- **T014** — Test: a search matching nothing renders the empty state rather than a blank page.
- **T015** — Test: each listing entry contains a link to its project's page. Then add the link to
  the entry, changing nothing else about it.
- **T016** — Test: the listing view derives from the portal's own list base class rather than
  Django's generic view directly.

## US-2 — Register a project

- **T017** — Test: the creation page is reachable at `project-create`, and an anonymous visitor is
  redirected to sign in.
- **T018** — Test: the creation form offers exactly name, status and visibility, and offers no other
  field. Asserted as an exact field set, not as a presence check.
- **T019** — Test: visibility renders as a visible choice between its options, with Public
  pre-selected.
- **T020** — Test: submitting without a name reports an error and creates nothing.
- **T021** — Test: after creation the creator holds view, change, delete, change-metadata and
  change-settings permission on the new project. Then the permission assignment.
- **T022** — Test: after creation the creator appears among the project's contributors as Creator,
  ProjectMember and ContactPerson. Then the contribution record.
- **T023** — Test: after creation the project records who created it.
- **T024** — Test: a successful creation redirects to the new project's page, at its exact address.
- **T025** — Test: the creation view derives from the portal's own create base class.

## US-3 — Correct a project's own attributes

- **T026** — Test: the attributes page is reachable, keyed by the project's identifier, as a page
  belonging to the project's own registration rather than an address of its own, and an anonymous
  visitor is redirected to sign in.
- **T027** — Test: a signed-in user without change permission on that project is refused.
- **T028** — Test: a user holding the permission at the model level, not only against the individual
  record, is admitted. This is the behaviour of the page being retired and it must survive. Changing
  the permission string alone does not achieve it. The check has to ask twice, model level then
  record, which is what the shared helper does.
- **T029** — Test: the attributes form offers exactly image, name, status, visibility and owner.
  Asserted as an exact field set.
- **T030** — Test: the form offers no description, keyword, tag, contributor or funding field.
- **T031** — Test: changing each of name, status, visibility and owner persists.
- **T032** — Test: uploading an image persists it, and clearing it removes it.
- **T033** — Test: submitting an empty name reports an error and saves nothing.
- **T034** — Test: the page presents the project's existing identifiers, one row each, with no blank
  rows beyond them. Then the identifier set on the page. The attributes page's existing submission
  tests must be updated in this task. They carry no formset bookkeeping and the page will reject
  them once the set is attached.
- **T035** — Test: adding an identifier of a chosen type records it against the project.
- **T036** — Test: changing an existing identifier's value persists.
- **T037** — Test: removing an identifier deletes it from the project.
- **T038** — Test: submitting an identifier value already recorded against a different project
  reports the error on that field and saves nothing, including the project's own attributes.
- **T039** — Test: submitting the same identifier value twice in one submission reports the
  collision and saves nothing.
- **T040** — Test: the page presents the project's existing dates, one row each, with no blank rows
  beyond them. Then the date set on the page, built from the shared declaration in T002, with the date-ordering rule from T003.
- **T041** — Test: adding a date of a chosen type records it against the project.
- **T042** — Test: changing an existing date's value persists.
- **T043** — Test: removing a date row deletes it from the project.
- **T044** — Test: submitting an end date earlier than the start date, both rows in the same
  submission, reports the error and saves nothing, both where the start row is newly added and where it is
  already stored. A per-row check sees neither case, because it looks the sibling up in the
  database.
- **T045** — Test: a project with a start date and no end date is accepted.
- **T046** — Test: when an identifier row is invalid, the project's own attributes are not saved
  either.
- **T047** — Test: a successful submission redirects to the project's page.
- **T048** — Delete `ProjectDateForm` and `ProjectIdentifierForm` and their tests, once the row sets
  carry the behaviour. Neither is used by any running code today.
- **T049** — Test: there is exactly one page for editing a project's own attributes. Assert that no
  second registered page offers an overlapping field set.
- **T050** — Manual check on a running page: adding a row to each set with the add-row control
  yields working fields, including the date widget. Not automatable. The outcome is written down
  with the other results.


## US-4 — Describe a project

- **T051** — Test: the descriptions page is reachable by name through `reverse`, at an address
  following the record-type and action convention and keyed by the project's identifier, and an
  anonymous visitor is redirected to sign in.
- **T052** — Test: a user without change permission on that project is refused, and an anonymous
  visitor is refused rather than admitted. The page declares its own permission. A registered page
  without one is open to everyone.
- **T053** — Test: for a project with no descriptions the page offers one empty area per type in the
  project description vocabulary, and the count matches the vocabulary exactly. Then the form.
- **T054** — Test: each area is labelled with its type's name and carries its definition as help
  text.
- **T055** — Test: saving text into one area records a description of that type and creates no
  others.
- **T056** — Test: a project holding an existing description shows that text in the area for its
  type.
- **T057** — Test: editing an existing description's text persists.
- **T058** — Test: clearing an area removes that description from the project.
- **T059** — Test: an area left empty creates nothing, and an area containing only whitespace is
  treated as empty.
- **T060** — Test: a project never holds two descriptions of the same type through this page.
- **T061** — Test: a successful submission redirects to the project's page.
- **T062** — Delete `ProjectDescriptionForm` and its tests, once the slot form carries the
  behaviour. It is used by no running code today.

## US-5 — Move between a project's pages

- **T063** — Test: the project's page is its own registration against the record, so the portal's
  per-record navigation offers an entry for it. Then the registration. Today no entry exists and no
  tab is ever selected while on that page.
- **T064** — Test: the attributes and deletion pages belong to that registration and take no
  navigation entry of their own, so the strip gains no entry for either.
- **T065** — Test: each of those pages states its own permission, and a signed-in user without it is
  refused. An extra view inherits its owner's predicate but not its permission, so a page that
  states none is open to everyone.
- **T066** — Test: a private project is refused to a user who may not view it, through the
  registration's own check. The record is resolved past the filtered manager, so without this the
  project is readable by anyone holding its address. This is the regression this restructuring is
  most likely to introduce.
- **T067** — Test: a user who may change a project is offered its attributes and descriptions pages;
  one who may not is offered neither.
- **T068** — Test: a user who may delete a project is offered its deletion page; one who may not is
  not.
- **T069** — Test: the deletion page's back control is a working link to a real address, asserted as
  a link and not merely as present.
- **T070** — Test: the attributes, descriptions and deletion pages each offer a working link back to
  the project itself.
- **T071** — Test: every link drawn on each page resolves to a real address, with none empty. One
  test per page.
- **T072** — Test: rendering each page emits no deprecation warning from the interface layer.
  Requires an explicit warning filter on the test, because the suite silences warnings file-wide.
  Then replace the superseded attribute names.
- **T073** — Test: the listing offers a link to the creation page to a signed-in user and not to an
  anonymous one.
- **T074** — Test: the record's own address method resolves, and every place that reversed the
  retired names now reaches the same page.
- **T092** — Test: a project's pages all sit under the plural prefix, so `projects/<uuid>/` is the
  project itself and each of its pages is a segment below it, with nothing left answering under the
  singular form. Then move the mount.
- **T093** — Test: the creation page still resolves under the plural prefix and is not read as a
  record lookup, which is what a route declared after the record include would cause.
- **T094** — Test: the attributes page offers the deletion page to a user who may delete the
  project and to nobody else, and the link returns here rather than to the project when the
  deletion is abandoned. Then name the deletion route on the page, since the interface layer's
  defaults point at the standalone routes this feature retires. Carries FR-045, which no task in
  the original US-5 block covered.

## US-6 — Remove a project

- **T075** — Test: the deletion page is reachable by name as one of the project's own pages, keyed by
  the project's identifier, and an anonymous visitor is redirected to sign in.
- **T076** — Test: a user without delete permission on that project is refused.
- **T077** — Test: typing a name that is not the project's reports an error and the project remains.
- **T078** — Test: typing the project's name with leading and trailing spaces is accepted and the
  deletion proceeds.
- **T079** — Test: a project with no datasets is deleted when confirmed correctly.
- **T080** — Test: a project whose datasets are all private is deleted when confirmed correctly.
- **T081** — Test: a project with one public dataset is not deleted when confirmed correctly, and
  the project still exists afterwards.
- **T082** — Test: the refusal holds when the deletion is attempted directly against the record,
  not only through the page. Then the record-level guard.
- **T083** — Test: the refused page names each blocking public dataset in what the user sees, not in
  the page's internal state. Assert against the rendered content.
- **T084** — Test: the refused page explains why, and offers neither a confirmation field nor a
  delete control.
- **T085** — Test: opening the deletion page for a project with a public dataset already shows the
  refusal, without the user having to submit first.
- **T086** — Test: a dataset made public after the page is opened still blocks the deletion, and is
  named among the blockers.
- **T087** — Test: a successful deletion redirects to the project listing.

## Deliberate omissions

- **T088** — Remove the unreachable funding field declaration from the project form, and the note
  above it. No test of its own: T018 and T029 pin both forms' field sets exactly, which excludes
  funding, keywords and tags by construction.

## Documentation

- **T089** — Document the project management pages in the portal user documentation: what each page
  is for, who may open it, and what the deletion refusal means. Audit every page under `docs/` that
  describes project editing and bring it into line.
- **T090** — Record the decision between the two editing surfaces, and the choice of inline
  mechanism, where the repository records decisions.
- **T091** — Update the roadmap entry's state to reflect what this feature delivered, without
  claiming the half it does not cover.

## Revisions after review on a running portal

Raised by Sam on 2026-08-24 after working the pages locally. D12, D13 and D14 record the
adjudications.

- **T095** — Rename the update page: its visible title becomes "Update project" and its address
  segment becomes `update`, with its registered name following. Every reversal in running code and
  in tests moves with it. Test: the page resolves under its new address and carries its new title,
  and the old address no longer answers.
- **T096** — The descriptions page stops being a registration of its own and becomes one of the
  project's page's own belongings, like the update and deletion pages. Test: the per-record
  navigation carries exactly one entry for the project's pages, and none for descriptions,
  updating, or deletion.
- **T097** — The project's own page draws a link to the descriptions page for a user who may change
  the project, and draws none for a user who may not. Test: the link is asserted as a link in the
  rendered page, at the descriptions page's real address. The existing test for this behaviour
  passes today only because the navigation entry existed, and must be rewritten to assert the link
  the page itself draws.
- **T098** — The update page and the deletion page each state their own visibility rule rather than
  relying on the project's page. Test: for a user holding the model-level right to change projects
  and no grant on one particular private project, every one of that project's pages refuses the
  request — asserted through a real request per page, not through the decision helper. The existing
  test believed to cover this passes for an unrelated reason and must be rewritten.
- **T099** — Raise the registry's owner-resolution defect separately: the visibility rule of an
  owning page is never consulted for anything belonging to it, anywhere in the repository. Not this
  feature's fix. Raised as issue #284.
