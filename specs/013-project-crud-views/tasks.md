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
- **T002** — Build the mixin that gives a record's editing page its related-record row sets,
  resolving the date and identifier models from the record type itself rather than from a per-model
  register. Test: given a record type, the mixin yields sets bound to that type's own related
  models, with no blank rows and the date set carrying the sibling rule.
- **T003** — Build the form that generates one text area per concept in a related model's
  vocabulary, labelled with the concept's name and helped by its definition. Test: for a given
  related model the field set matches its vocabulary exactly, in vocabulary order.
- **T004** — Establish the fixtures this feature needs in the project test package's `conftest`: a
  public project, a private project, a user holding change permission on a project, a user holding
  delete permission, and a user holding neither. Test: each fixture yields a record with the
  permissions claimed.

## US-1 — Find a project

- **T005** — Test: the listing is reachable at `project-list` and returns 200 to an anonymous
  visitor.
- **T006** — Test: only public projects appear in the listing, for an anonymous visitor and for a
  signed-in one who owns a private project. Then the queryset restriction that satisfies it.
- **T007** — Test: searching a distinctive word in a project's name returns that project and
  excludes others. Then the search configuration.
- **T008** — Test: searching a project's identifier returns that project.
- **T009** — Test: ordering by name returns alphabetical order, and the reverse returns the reverse.
  Both directions asserted separately.
- **T010** — Test: ordering by date added returns oldest first, and the reverse returns the reverse.
- **T011** — Test: applying a status filter returns only projects with that status. Then attach the
  portal's existing project filter to the view.
- **T012** — Test: the portal's owner, contributor and tag filters each narrow the listing.
- **T013** — Test: a search matching nothing renders the empty state rather than a blank page.
- **T014** — Test: each listing entry contains a link to its project's page. Then add the link to
  the entry, changing nothing else about it.
- **T015** — Test: the listing view derives from the portal's own list base class rather than
  Django's generic view directly.

## US-2 — Register a project

- **T016** — Test: the creation page is reachable at `project-create`, and an anonymous visitor is
  redirected to sign in.
- **T017** — Test: the creation form offers exactly name, status and visibility, and offers no other
  field. Asserted as an exact field set, not as a presence check.
- **T018** — Test: visibility renders as a visible choice between its options, with Public
  pre-selected.
- **T019** — Test: submitting without a name reports an error and creates nothing.
- **T020** — Test: after creation the creator holds view, change, delete, change-metadata and
  change-settings permission on the new project. Then the permission assignment.
- **T021** — Test: after creation the creator appears among the project's contributors as Creator,
  ProjectMember and ContactPerson. Then the contribution record.
- **T022** — Test: after creation the project records who created it.
- **T023** — Test: a successful creation redirects to the new project's page, at its exact address.
- **T024** — Test: the creation view derives from the portal's own create base class.

## US-3 — Correct a project's own attributes

- **T025** — Test: the attributes page is reachable at `project-update` keyed by the project's
  identifier, and an anonymous visitor is redirected to sign in.
- **T026** — Test: a signed-in user without change permission on that project is refused.
- **T027** — Test: a user holding the permission at the model level, not only against the individual
  record, is admitted. This is the behaviour of the page being retired and it must survive. Changing
  the permission string alone does not achieve it. The check has to ask twice, model level then
  record, which is what the shared helper does.
- **T028** — Test: the attributes form offers exactly image, name, status, visibility and owner.
  Asserted as an exact field set.
- **T029** — Test: the form offers no description, keyword, tag, contributor or funding field.
- **T030** — Test: changing each of name, status, visibility and owner persists.
- **T031** — Test: uploading an image persists it, and clearing it removes it.
- **T032** — Test: submitting an empty name reports an error and saves nothing.
- **T033** — Test: the page presents the project's existing identifiers, one row each, with no blank
  rows beyond them. Then the identifier set on the page. The attributes page's existing submission
  tests must be updated in this task. They carry no formset bookkeeping and the page will reject
  them once the set is attached.
- **T034** — Test: adding an identifier of a chosen type records it against the project.
- **T035** — Test: changing an existing identifier's value persists.
- **T036** — Test: removing an identifier deletes it from the project.
- **T037** — Test: submitting an identifier value already recorded against a different project
  reports the error on that field and saves nothing, including the project's own attributes.
- **T038** — Test: submitting the same identifier value twice in one submission reports the
  collision and saves nothing.
- **T039** — Test: the page presents the project's existing dates, one row each, with no blank rows
  beyond them. Then the date set on the page, built by the mixin from T002.
- **T040** — Test: adding a date of a chosen type records it against the project.
- **T041** — Test: changing an existing date's value persists.
- **T042** — Test: removing a date row deletes it from the project.
- **T043** — Test: submitting an end date earlier than the start date, both rows in the same
  submission, reports the error and saves nothing. A per-row check cannot see this, because the
  sibling row is unsaved; the rule belongs to the set.
- **T044** — Test: submitting an end date earlier than a start date already stored reports the error
  and saves nothing.
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

- **T051** — Test: the related-records mixin and the descriptions form work against `Dataset` as
  well as `Project`, without adding any dataset page in this work. Each yields the dataset's own
  related models and its own vocabulary. This is what distinguishes a reusable piece from a
  project-shaped one, and it is the guard that keeps the next three record types cheap.

## US-4 — Describe a project

- **T052** — Test: the descriptions page is reachable by name through `reverse`, at an address
  following the record-type and action convention and keyed by the project's identifier, and an
  anonymous visitor is redirected to sign in.
- **T053** — Test: a user without change permission on that project is refused, and an anonymous
  visitor is refused rather than admitted. The page declares its own permission. A registered page
  without one is open to everyone.
- **T054** — Test: for a project with no descriptions the page offers one empty area per type in the
  project description vocabulary, and the count matches the vocabulary exactly. Then the form.
- **T055** — Test: each area is labelled with its type's name and carries its definition as help
  text.
- **T056** — Test: saving text into one area records a description of that type and creates no
  others.
- **T057** — Test: a project holding an existing description shows that text in the area for its
  type.
- **T058** — Test: editing an existing description's text persists.
- **T059** — Test: clearing an area removes that description from the project.
- **T060** — Test: an area left empty creates nothing, and an area containing only whitespace is
  treated as empty.
- **T061** — Test: a project never holds two descriptions of the same type through this page.
- **T062** — Test: a successful submission redirects to the project's page.
- **T063** — Delete `ProjectDescriptionForm` and its tests, once the slot form carries the
  behaviour. It is used by no running code today.

## US-5 — Move between a project's pages

- **T064** — Test: a user who may change a project sees links to its attributes page and its
  descriptions page on the project's page. Then declare the actions on the detail view.
- **T065** — Test: a user who may delete a project sees a link to its deletion page on the project's
  page.
- **T066** — Test: a user who may do neither sees neither link.
- **T067** — Test: an anonymous visitor to a public project sees neither link.
- **T068** — Test: the attributes page offers a link to the deletion page to a user who may delete,
  and not to one who may not.
- **T069** — Test: the deletion page's back control is a working link to a real address, asserted as
  a link and not merely as present. This is the failure the specification calls out.
- **T070** — Test: the attributes page, the descriptions page and the deletion page each offer a
  working link back to the project itself, not only to the listing.
- **T071** — Test: every link drawn on each of the five pages resolves to a real address, with none
  empty. One test per page.
- **T072** — Test: rendering each of the five pages emits no deprecation warning from the interface
  layer. Requires an explicit warning filter on the test, because the suite silences warnings
  file-wide. Then replace the superseded attribute names.
- **T073** — Test: the listing offers a link to the creation page to a signed-in user and not to an
  anonymous one.

## US-6 — Remove a project

- **T074** — Test: the deletion page is reachable at `project-delete` keyed by the project's
  identifier, and an anonymous visitor is redirected to sign in.
- **T075** — Test: a user without delete permission on that project is refused.
- **T076** — Test: typing a name that is not the project's reports an error and the project remains.
- **T077** — Test: typing the project's name with leading and trailing spaces is accepted and the
  deletion proceeds.
- **T078** — Test: a project with no datasets is deleted when confirmed correctly.
- **T079** — Test: a project whose datasets are all private is deleted when confirmed correctly.
- **T080** — Test: a project with one public dataset is not deleted when confirmed correctly, and
  the project still exists afterwards.
- **T081** — Test: the refusal holds when the deletion is attempted directly against the record,
  not only through the page. Then the record-level guard.
- **T082** — Test: the refused page names each blocking public dataset in what the user sees, not in
  the page's internal state. Assert against the rendered content.
- **T083** — Test: the refused page explains why, and offers neither a confirmation field nor a
  delete control.
- **T084** — Test: opening the deletion page for a project with a public dataset already shows the
  refusal, without the user having to submit first.
- **T085** — Test: a dataset made public after the page is opened still blocks the deletion, and is
  named among the blockers.
- **T086** — Test: a successful deletion redirects to the project listing.

## Deliberate omissions

- **T087** — Remove the unreachable funding field declaration from the project form, and the note
  above it. No test of its own: T017 and T028 pin both forms' field sets exactly, which excludes
  funding, keywords and tags by construction.

## Documentation

- **T088** — Document the project management pages in the portal user documentation: what each page
  is for, who may open it, and what the deletion refusal means. Audit every page under `docs/` that
  describes project editing and bring it into line.
- **T089** — Record the decision between the two editing surfaces, and the choice of inline
  mechanism, where the repository records decisions.
- **T090** — Update the roadmap entry's state to reflect what this feature delivered, without
  claiming the half it does not cover.
