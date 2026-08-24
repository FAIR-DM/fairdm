# Tasks — 013 Managing a project through the portal

Written from `spec.md` as though none of this feature existed, then reconciled against the codebase
in a separate pass. Nothing here was written by reading the implementation, and nothing was carried
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
- **T002** — Establish a test helper asserting that a named address appears as a link in a rendered
  page, and its negative. The suite has no such assertion today and this feature needs it in three
  stories. Test: the helper passes on a page containing the link and fails on one that does not.
- **T003** — Establish the fixtures this feature needs in the project test package's `conftest`: a
  public project, a private project, a user holding change permission on a project, a user holding
  delete permission, and a user holding neither. Test: each fixture yields a record with the
  permissions claimed.

## US-1 — Find a project

- **T004** — Test: the listing is reachable at `project-list` and returns 200 to an anonymous
  visitor.
- **T005** — Test: only public projects appear in the listing, for an anonymous visitor and for a
  signed-in one who owns a private project. Then the queryset restriction that satisfies it.
- **T006** — Test: searching a distinctive word in a project's name returns that project and
  excludes others. Then the search configuration.
- **T007** — Test: searching a project's identifier returns that project.
- **T008** — Test: ordering by name returns alphabetical order, and the reverse returns the reverse.
  Both directions asserted separately.
- **T009** — Test: ordering by date added returns oldest first, and the reverse returns the reverse.
- **T010** — Test: applying a status filter returns only projects with that status. Then attach the
  portal's existing project filter to the view.
- **T011** — Test: the portal's owner, contributor and tag filters each narrow the listing.
- **T012** — Test: a search matching nothing renders the empty state rather than a blank page.
- **T013** — Test: each listing entry contains a link to its project's page. Then add the link to
  the entry, changing nothing else about it.
- **T014** — Test: the listing view derives from the portal's own list base class rather than
  Django's generic view directly.

## US-2 — Register a project

- **T015** — Test: the creation page is reachable at `project-create`, and an anonymous visitor is
  redirected to sign in.
- **T016** — Test: the creation form offers exactly name, status and visibility, and offers no other
  field. Asserted as an exact field set, not as a presence check.
- **T017** — Test: visibility renders as a visible choice between its options, with Public
  pre-selected.
- **T018** — Test: submitting without a name reports an error and creates nothing.
- **T019** — Test: after creation the creator holds view, change, delete, change-metadata and
  change-settings permission on the new project. Then the permission assignment.
- **T020** — Test: after creation the creator appears among the project's contributors as Creator,
  ProjectMember and ContactPerson. Then the contribution record.
- **T021** — Test: after creation the project records who created it.
- **T022** — Test: a successful creation redirects to the new project's page, at its exact address.
- **T023** — Test: the creation view derives from the portal's own create base class.

## US-3 — Correct a project's own attributes

- **T024** — Test: the attributes page is reachable at `project-update` keyed by the project's
  identifier, and an anonymous visitor is redirected to sign in.
- **T025** — Test: a signed-in user without change permission on that project is refused.
- **T026** — Test: a user holding the permission at the model level, not only against the individual
  record, is admitted. This is the behaviour of the page being retired and it must survive.
- **T027** — Test: the attributes form offers exactly image, name, status, visibility and owner.
  Asserted as an exact field set.
- **T028** — Test: the form offers no description, keyword, tag, contributor or funding field.
- **T029** — Test: changing each of name, status, visibility and owner persists.
- **T030** — Test: uploading an image persists it, and clearing it removes it.
- **T031** — Test: submitting an empty name reports an error and saves nothing.
- **T032** — Test: the page presents the project's existing identifiers, one row each, with no blank
  rows beyond them. Then the identifier set on the page.
- **T033** — Test: adding an identifier of a chosen type records it against the project.
- **T034** — Test: changing an existing identifier's value persists.
- **T035** — Test: removing an identifier deletes it from the project.
- **T036** — Test: submitting an identifier value already recorded against a different project
  reports the error on that field and saves nothing, including the project's own attributes.
- **T037** — Test: submitting the same identifier value twice in one submission reports the
  collision and saves nothing.
- **T038** — Test: the page presents the project's start and end dates. Then the date set on the
  page.
- **T039** — Test: setting a start date and an end date together persists both.
- **T040** — Test: submitting an end date earlier than the start date, **both in the same
  submission**, reports the error and saves nothing. This is the case a per-row check cannot see.
- **T041** — Test: submitting an end date earlier than a start date already stored reports the error
  and saves nothing.
- **T042** — Test: a project with a start date and no end date is accepted.
- **T043** — Test: when an identifier row is invalid, the project's own attributes are not saved
  either.
- **T044** — Test: a successful submission redirects to the project's page.
- **T045** — Test: there is exactly one page for editing a project's own attributes. Assert that no
  second registered page offers an overlapping field set.
- **T046** — Manual check on a running page: adding a date row with the add-row control yields a
  working date widget. Recorded in the run record, not automatable.

## US-4 — Describe a project

- **T047** — Test: the descriptions page is reachable at its own address keyed by the project's
  identifier, and an anonymous visitor is redirected to sign in.
- **T048** — Test: a user without change permission on that project is refused.
- **T049** — Test: for a project with no descriptions the page offers one empty area per type in the
  project description vocabulary, and the count matches the vocabulary exactly. Then the form.
- **T050** — Test: each area is labelled with its type's name and carries its definition as help
  text.
- **T051** — Test: saving text into one area records a description of that type and creates no
  others.
- **T052** — Test: a project holding an existing description shows that text in the area for its
  type.
- **T053** — Test: editing an existing description's text persists.
- **T054** — Test: clearing an area removes that description from the project.
- **T055** — Test: an area left empty creates nothing, and an area containing only whitespace is
  treated as empty.
- **T056** — Test: a project never holds two descriptions of the same type through this page.
- **T057** — Test: a successful submission redirects to the project's page.

## US-5 — Move between a project's pages

- **T058** — Test: a user who may change a project sees links to its attributes page and its
  descriptions page on the project's page. Then declare the actions on the detail view.
- **T059** — Test: a user who may delete a project sees a link to its deletion page on the project's
  page.
- **T060** — Test: a user who may do neither sees neither link.
- **T061** — Test: an anonymous visitor to a public project sees neither link.
- **T062** — Test: the attributes page offers a link to the deletion page to a user who may delete,
  and not to one who may not.
- **T063** — Test: the deletion page's back control is a working link to a real address, asserted as
  a link and not merely as present. This is the failure the specification calls out.
- **T064** — Test: the attributes page and the descriptions page each offer a way back to the
  project.
- **T065** — Test: every link drawn on each of the five pages resolves to a real address, with none
  empty. One test per page.
- **T066** — Test: rendering each of the five pages emits no deprecation warning from the interface
  layer. Requires an explicit warning filter on the test, because the suite silences warnings
  file-wide. Then replace the superseded attribute names.
- **T067** — Test: the listing offers a link to the creation page to a signed-in user and not to an
  anonymous one.

## US-6 — Remove a project

- **T068** — Test: the deletion page is reachable at `project-delete` keyed by the project's
  identifier, and an anonymous visitor is redirected to sign in.
- **T069** — Test: a user without delete permission on that project is refused.
- **T070** — Test: typing a name that is not the project's reports an error and the project remains.
- **T071** — Test: typing the project's name with leading and trailing spaces is accepted and the
  deletion proceeds.
- **T072** — Test: a project with no datasets is deleted when confirmed correctly.
- **T073** — Test: a project whose datasets are all private is deleted when confirmed correctly.
- **T074** — Test: a project with one public dataset is not deleted when confirmed correctly, and
  the project still exists afterwards.
- **T075** — Test: the refusal holds when the deletion is attempted directly against the record,
  not only through the page. Then the record-level guard.
- **T076** — Test: the refused page names each blocking public dataset in what the user sees, not in
  the page's internal state. Assert against the rendered content.
- **T077** — Test: the refused page explains why, and offers neither a confirmation field nor a
  delete control.
- **T078** — Test: opening the deletion page for a project with a public dataset already shows the
  refusal, without the user having to submit first.
- **T079** — Test: a dataset made public after the page is opened still blocks the deletion, and is
  named among the blockers.
- **T080** — Test: a successful deletion redirects to the project listing.

## Deliberate omissions

- **T081** — Test: no page in this feature offers funding for editing. Then remove the unreachable
  funding field declaration.
- **T082** — Test: no page in this feature offers keywords or tags for editing.

## Documentation

- **T083** — Document the project management pages in the portal user documentation: what each page
  is for, who may open it, and what the deletion refusal means. Audit every page under `docs/` that
  describes project editing and bring it into line.
- **T084** — Record the decision between the two editing surfaces, and the choice of inline
  mechanism, where the repository records decisions.
- **T085** — Update the roadmap entry's state to reflect what this feature delivered, without
  claiming the half it does not cover.
