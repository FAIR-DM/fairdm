# Decisions — 004 Core Datasets

The original specification was written on 2026-01-15, before most of the dataset app existed. It
described five layers at once: the domain record, the querysets, the forms, the filters and the
admin, plus a set of testing requirements. Its `tasks.md` reports 162 of 163 tasks complete and the
directory carries a file announcing the same, which is what prompted this rewrite.

Two of those five layers have since been specified properly and separately — `014-dataset-crud-views`
owns the pages and the forms, `015-image-field-spec` owns the image field — so most of the
disagreement below is about which document owns what, and the rest is about which of the code and the
text was right.

This file records what the old text said, what the code does, which way each disagreement was
settled, and why. It is the reason the specification now says what it says.

Every decision was taken on 2026-08-18. Where one was settled without the maintainer present it is
marked **self-resolved**, and it stands unless he says otherwise.

## D-001 — Scope: this specification covers the dataset record, not the portal views

**Settled by the maintainer, 2026-08-18.**

The original text owned the `Dataset` model, its related records, its querysets, its forms, its
filters, its admin, its permissions and a list of testing requirements. The portal surface was later
specified properly by `014-dataset-crud-views`, which is narrower and describes what shipped.

The line is the same one drawn for projects in `003-core-projects`:

**In scope** — the `Dataset` model and its fields, the related description, date, identifier,
literature-relation and contribution records, their controlled vocabularies, the visibility default,
the administrative interface, and the record of who created and last changed a dataset.

**Out of scope, owned by 014** — the list, create, update and delete pages, the forms behind them,
the list search box, the filter set attached to the list, and the view-level permission checks.

**Out of scope, owned by 015** — the image field's aspect ratio, dimensions and thumbnails. The old
FR-014 and an entire research note in this directory were written before that specification existed.

**Out of scope, owned by neither** — the detail page, and `DatasetFilter` itself. 014 attaches the
filter and explicitly disclaims its internals. Both are routed out rather than absorbed here.

## D-002 — Metadata export leaves this specification entirely

**Settled by the maintainer, 2026-08-18.**

The old text implied export in two places: FR-041 permitted bulk metadata export from the admin, and
the admin module's own docstring advertises "Bulk metadata export (JSON/DataCite format)" as
available.

No export exists. `admin.py` declares no actions at all, so both statements are false. The one piece
of export machinery in the repository is `templates/publishing/datacite44.xml`, rendered only by
`fairdm/contrib/import_export/views.py:283` and `utils.py:38`, neither of which is reachable —
`fairdm/contrib/import_export/urls.py` has every route commented out and ends with an empty
`urlpatterns`.

The maintainer's ruling is that export is not part of the core record and is expected to become an
addon. The requirement therefore leaves this specification rather than being kept and built, which is
the opposite of how the same question was settled for projects, and deliberately so: projects gained
an export because one was asked for, datasets get none because the mechanism is moving out of the
package.

What the specification keeps is the *reason* export exists — that the record's metadata be complete
and correctly typed, which is goal G14. An addon can only submit what the record holds.

## D-003 — Dataset identifiers use the wrong vocabulary, and the code is wrong

**Self-resolved. This is a defect, not drift.**

`DatasetIdentifier.VOCABULARY` is `FairDMIdentifiers()` unscoped
(`fairdm/core/dataset/models.py:722`), and `Dataset.IDENTIFIER_TYPES` is the same unscoped set
(`:534`). That set contains ORCID, ResearcherID, ROR, Wikidata, ISNI and the Crossref Funder ID,
which identify people and organisations, alongside the DOI, grant number and proposal identifier that
`003-core-projects` added for projects.

So the type list a dataset offers is mostly identifiers for things a dataset is not, and the three
that are plausible were added for a different record. This is the same defect found on projects
(003's D-003) and left unfixed on datasets, because that work stopped at its own model.

The specification keeps its requirement and the code is treated as wrong: a dataset identifier
collection is introduced. It must contain the DOI, because the DOI is the identifier a dataset is
cited by, and it must contain no identifier that names a person or an organisation.

The old model docstring names "DOI, ARK, Handle, etc." Neither ARK nor Handle is added: nothing in
the repository or the roadmap has asked for either, and an unused member is a wrong choice offered to
every user. (**Design review, 2026-08-18**: an earlier draft of this decision added Handle
alongside DOI, on the reasoning that DOIs are built on the handle system. `research.md` R3 reached the
opposite conclusion — DOI alone — and `tasks.md` T001/T002 were already built to that reading. FR-012
requires the collection include DOI and exclude person/organisation identifiers; it is silent on
Handle, so this is a plan-level contradiction, not a spec gap. Corrected to match the two artifacts
that already agree, rather than the one that didn't.)

The pre-existing global uniqueness of an identifier value (`fairdm/core/abstract.py:316`) is kept.

## D-004 — Datasets are private by default, and the guard is switched on

**Settled by the maintainer, 2026-08-18.**

The old FR-015 required the default manager to exclude private datasets. `DatasetManager` exists and
implements exactly that (`models.py:331-371`) and is **commented out** at `:548-550`, with
`objects = DatasetQuerySet.as_manager()` in its place. So `Dataset.objects.all()` returns private
datasets, every default query in the framework included.

Two further faults sit on top of it:

- `with_private()` returns `DatasetQuerySet(self.model, using=self.db).all()` (`:239-241`), which
  discards `self`. Any condition applied before the call is silently dropped, so
  `Dataset.objects.filter(project=p).with_private()` returns every dataset in the table. The class
  docstring at `:127` states that the methods "can be chained in any order", which is not true. The
  one test that would have caught it is skipped (`tests/test_core/test_dataset/test_models.py:895`).
- `for_user()` (`:195`) calls `with_private()` and gates it on `user.has_perm("dataset.view_private")`
  — a permission no model declares, so the check can never be true. It has no callers.

Settled in the specification's favour, and the maintainer put the work in this run rather than
deferring it to the roadmap item that governs visibility across every surface. The record's own
default is the narrowest place the guarantee can be made and the one nothing else can substitute for;
what stays with that roadmap item is enforcement in the views, the API and the collection tables.

## D-005 — Deleting a project deletes its private datasets, and the code is right

**Settled by the maintainer, 2026-08-18. The first reading of this was wrong.**

The old FR-005 required `PROTECT` on the project foreign key so that a project with datasets could
not be deleted. The field is `CASCADE` (`models.py:583`), and the model's own docstring at `:431`
states the opposite of the field a dozen lines below it: "The project field uses PROTECT to prevent
accidental deletion of projects that have associated datasets."

The docstring is the only thing wrong. `fairdm/core/project/models.py:280` registers a `pre_delete`
receiver raising `PublicDatasetsProtect` whenever a project has any publicly visible dataset, tested
at `tests/test_core/test_project/test_models.py:180`. That guard is `013-project-crud-views`' FR-023
and 003 settled it there.

So the behaviour is deliberate and complete: a project with public datasets cannot be deleted at all,
and a project whose datasets are all private deletes and takes them with it. A private dataset is its
author's unpublished work under a project they are removing; `PROTECT` would leave them unable to
delete either.

Settled in the code's favour. The requirement is restated to describe what happens, the guard stays
with 013, and the false docstring is corrected here.

## D-006 — Visibility stays private or public

**Self-resolved.**

The old FR-004 named three levels, and the queryset and filter docstrings describe an `INTERNAL` tier
throughout (`models.py:123`, `:156`, `:224`, `filters.py:9`). `Visibility` has two members
(`fairdm/utils/choices.py:14`).

Settled in the code's favour, for the same reason 003 settled it that way (D-006 there): a third tier
is a genuine feature that reaches into dataset visibility, the API serialisers and every queryset
that filters on public, and it is already routed out as issue #168. The documentation describing a
level that does not exist is corrected here.

This also collapses a distinction the old design leaned on. With two levels, "exclude private" and
"only public" are the same set, so `get_visible()` and the default manager cannot differ, whatever
their docstrings claim.

## D-007 — The licence default is applied at creation, not declared on the column

**Self-resolved.**

The old FR-006 and FR-023 both required a CC BY 4.0 default. `Dataset.license` is
`LicenseField(null=True, blank=True)` with no default (`models.py:603`); the default lives in the
form (`forms.py:180`), which reads `FAIRDM_DEFAULT_LICENSE` and falls back to CC BY 4.0. A dataset
created through the admin, a management command or a fixture gets no licence at all.

Settled in both directions. The default is real and stays, because a dataset that reaches a reader
unlicensed is not reusable, which is the R of the four letters the package is named for. But it is
not a column default: the field points at a `License` row, so a default would resolve a database
lookup at import time and fail wherever the licence fixture has not been loaded.

The requirement is therefore stated as a guarantee about creation rather than about the column, and
this specification owns making it hold in the surfaces it owns. The form's copy of it is 014's.

## D-008 — Dataset date types keep the shipped set, and the factory is wrong

**Self-resolved. This is a defect in the tests, not in the code.**

The dataset date collection is Available, CollectionStart, CollectionEnd, Submitted, Published and
Withdrawn (`fairdm/core/vocabularies.py:431`). `DatasetDateFactory` defaults its type to `"Created"`
(`fairdm/factories/core.py:275`), which is not a member, and four tests use that value as their
example of a *valid* type (`test_models.py:324`, `:387`, `:399`, `:409`). A fifth uses `"ARK"` as a
valid identifier type (`:607`), which is not a member either.

They pass because `objects.create()` does not call `full_clean()` and Django does not validate
`choices` on save — the same blind spot 003 found, arriving here through a different door.

Settled in the vocabulary's favour. The shipped set is the deliberate one: it carries the collection
period, which 003 explicitly moved off projects and onto datasets (its D-004), and the moment a
dataset record was created is already the `added` timestamp. Adding a member to make a wrong test
pass would be the reverse of the argument.

The factory and the tests are corrected. Because nothing pins the vocabularies by name, this drift
was invisible: `test_all_valid_date_types_accepted` iterates whatever the collection holds and would
pass over an empty one. The replacement tests name the members.

## D-009 — Dataset description types keep the shipped set

**Self-resolved.**

The old FR-009 required validation against the vocabulary without saying what it contains. The
collection is Abstract, Methods, SeriesInformation, TechnicalInfo and Other
(`fairdm/core/vocabularies.py:267`).

Settled in the code's favour and made explicit. Methods is the member worth naming: 003's D-015
established that a methods description belongs to the dataset rather than the project, reached
independently from its D-004 on collection dates. This specification is the other side of that line
and states it positively.

## D-010 — The role-to-permission map is dropped from this specification

**Self-resolved.**

`Dataset.ROLE_PERMISSIONS` (`models.py:541-545`) maps three role names to permission lists. Two of
the three — Viewer and Manager — are not members of the dataset role collection, which contains
Creator, ContactPerson, DataCollector, DataCurator, DataManager, Editor, Producer, RelatedPerson,
Researcher, ProjectLeader, ProjectManager, ProjectMember, Supervisor, WorkPackageLeader, RightsHolder
and Other. The attribute has no readers anywhere in the package.

This is the same unbuildable matrix 003 dropped in its D-009, copied one model over. It is dropped
here for the same reason and joins the request already open as issue #169: deciding which
contribution roles confer which rights is a real piece of design and belongs to the goal about portal
roles, not to the dataset model.

The dead attribute is removed rather than left as a claim about a permission model that does not
exist. `for_user()` goes with it (see D-004): it has no callers and its only condition is a
permission that is never declared. What stays is the declared permission list, which 014's create
view is supposed to grant and does not — routed out below.

## D-011 — Dataset names are not unique

**Self-resolved.**

The old text raised duplicate names as an open question and the code allows them.

Settled in the code's favour. Two research groups can legitimately hold a dataset of the same name,
the generated identifier is what names a dataset unambiguously, and uniqueness within a project would
not help since a dataset need not have one. Recorded so it is a decision rather than an oversight.

## D-012 — The second names on the related records go

**Self-resolved.**

`DatasetDescription`, `DatasetDate` and `DatasetIdentifier` each carry two properties aliasing their
two real fields — `description_type` and `description` for `type` and `value`, and so on
(`models.py:652-670`, `:690-708`, `:725-743`). Their docstrings say "API compatibility".

Nothing consumes them. The REST API exposes five scalar fields on a dataset and none of these records
at all (`fairdm/api/viewsets.py:128`). No other core model has them — `ProjectDate`, `SampleDate` and
their siblings carry the field names alone. So the compatibility they are named for does not exist.

They are not merely unused, they are actively harmful: `DatasetFilter.date_type` was written as
`field_name="dates__date_type"` (`filters.py:161`), an ORM path through a Python property, and raises
`FieldError` every time the filter is applied. The alias made a column look like it was there.

Removed. The filter that depends on one of them is routed out with 014's filter set.

## D-013 — Datasets are ordered most-recently-modified first

**Self-resolved.**

`Meta.ordering = ["modified"]` (`models.py:615`) is ascending, so an unordered listing puts the
least-recently-touched dataset first. No test asserts the ordering at all.

Settled against the code. Nothing wants the stalest record first, `Project` was corrected to
`-modified` in 003, and two core models disagreeing on the direction of their default ordering is the
kind of difference that gets discovered from a list page that looks wrong.

## D-014 — The testing requirements leave the specification

**Self-resolved.**

The old FR-046 to FR-052 required unit tests per component, factory-boy factories, and a
`tests/unit/` and `tests/integration/` layout that the repository does not use.

Dropped as requirements. Test-first is the constitution's Article and applies to every feature
without being restated; the directory layout it names was superseded by the repository's own
mirror-the-source-tree standard, so keeping it would specify a violation. What the old requirements
were reaching for survives as SC-009, which is about the tests being real rather than about there
being some.

That distinction is the whole finding of this rewrite. There are 196 tests over the dataset app, 28
skipped and roughly 25 more that pass for a reason other than the behaviour they name — a `bbox`
test whose assertion is true of every possible return value, a `visibility` default test that accepts
either value, a contributor test whose body is `if dataset:` on a form submission that fails. A
requirement to have unit tests was met in full and proved nothing.

## D-015 — The creation record gains a creator

**Self-resolved.**

The old FR-012 asked for timestamps "primarily for audit trail purposes". The record has timestamps
and nothing else — no creator, no history.

Settled the same way as 003's D-010, and for the same reason: attribution is the part that cannot be
reconstructed after the fact, and the create view already writes a Creator contribution that a field
on the record should mirror, since a contribution can be removed and the fact of authorship cannot.
Full revision history stays routed out as issue #170.

## D-016 — The literature relations stay, and acquire their first real test

**Self-resolved.**

`DatasetLiteratureRelation` is built, with the external schema's relationship types, a uniqueness
constraint and an index (`models.py:61-98`). All eleven of its tests are skipped behind four
class-level marks reading "Literature app not yet complete", and they reference a
`LiteratureItemFactory` that does not exist anywhere in the repository — so removing the skips would
raise `NameError` rather than run them.

The literature package is a live dependency and its `LiteratureItem` model exists, so the stated
reason for the skips no longer holds. The requirement is kept and the missing factory is part of the
work.

## D-017 — The directory is rewritten, not just its specification

**Self-resolved, following the finding that closed 003.**

The directory carries thirteen artefacts from January besides `spec.md`: `data-model.md`, `plan.md`,
`tasks.md`, `quickstart.md`, six contract documents, two demo-preparation notes, five research notes,
a requirements checklist, an `IMPLEMENTATION_COMPLETE.md` and a `PR_DESCRIPTION.md`.

Rewriting `spec.md` and leaving those in place was the highest-severity finding when the projects
specification was rewritten, and this directory is a worse case: the two process files announce the work finished and both
call this feature "Spec 006", the contract documents describe the forms and filters this
specification no longer owns, and `research/image-aspect-ratios.md` predates the specification that
now owns the image field.

`IMPLEMENTATION_COMPLETE.md`, `PR_DESCRIPTION.md`, the demo-preparation notes and the six contract
documents are deleted — process residue and design for surfaces owned elsewhere. `data-model.md`,
`plan.md`, `tasks.md`, `quickstart.md` and the research notes are regenerated by this run against the
narrowed scope, and the research notes that belong to 015 go with the requirement.

## Routed out

Findings that are real but are not this feature's work:

| Finding | Where it goes |
|---|---|
| `DatasetFilter.date_type` raises `FieldError` whenever applied (`filters.py:161`) | #186 |
| `DatasetFilter.__init__` has two branches that do the same thing, and its docstrings describe a visibility level that does not exist (`filters.py:181-191`) | #186 |
| A dataset's creator is granted no permissions over it — the assignment is commented out (`views.py:84-94`), against 014's FR-012 | #187 |
| `DatasetCreateForm` omits `project`, and the create view uses `fields` rather than the form and never passes `request`, against 014's FR-011 and its assumptions (`forms.py:277`, `views.py:46`, `:57`) | #187 |
| Dataset views bind translations at import time (`views.py:7`), as do `fairdm/contrib/import_export/views.py:6` and `fairdm/core/utils.py:1` | #188 |
| Every route in `fairdm/contrib/import_export/urls.py` is commented out, so metadata download, data import and package download are unreachable; `import_export/views.py:224` checks a `can_publish` permission no model declares | #189 |
| The dataset detail template counts `project.samples` and `project.measurements` while its context object is the dataset (`templates/dataset/dataset_detail.html:21`, `:25`); `templates/dataset/plugins/overview.html` is registered by no plugin; `templates/dataset/dataset_create.html` is empty and referenced by nothing | #190 |
| Five of the eight dataset user-guide pages are "Coming soon" stubs, three of them linked from the plugin headings that tell a user to read them (`plugins.py:29`, `:48`, `:65`) | #191 |
| The REST API exposes dataset create, update and delete and five scalar fields, describing none of the related records | noted against 011, the API specification |
| Funding recorded against a dataset | #175, which covers projects and datasets together |
| An organisation-scoped visibility level between private and public | #168 |
| Which contribution roles confer which rights (D-010) | #169 |
| Full revision history for core records (D-015) | #170 |
| The deployment pipeline in `apps.py:254` is never invoked, so the `groups` and `django-waffle` fixtures and the vocabulary preload do not reach a deployed portal (D-018) | #193 |

## D-018 — Licences are seeded by the setup pipeline, not by a data migration

**Self-resolved, after the maintainer asked which mechanism was right.**

`Dataset.license` is the only licence field in the package (`models.py:603`). `django-content-license`
ships `fixtures/creativecommons.json.gz` and no data migration, deliberately — curating licences is
not that package's job. Nothing in FairDM loads it. So a portal that has migrated and never run
`loaddata` by hand has no `License` rows at all, and two things follow: the configured default
resolves to `None` and is silently not applied, and the portal's dataset form declares `license` as a
required field over an empty queryset (`forms.py:116`), so a dataset cannot be created through the
portal at all.

Which licences to seed is FairDM's opinion to hold. The set is CC0 1.0, CC BY 4.0 and CC BY-SA 4.0.
The fixture also carries the NC and ND variants; they fail the Open Definition, and a framework named
for reusability should not present "no derivatives" as a recommended licence for research data. A
portal that needs one adds it, which is the pattern the licensing package is built for.

The seeding step is added to the deployment pipeline in `fairdm/conf/settings/apps.py:254-282`,
beside the `groups` and `django-waffle` fixtures and the vocabulary preload, which are three
precedents of exactly this shape. It is idempotent, keyed on the licence name, so it leaves alone a
portal that has curated its own rows.

The alternative considered and rejected was a data migration. It is the more reliable mechanism —
`migrate` runs everywhere and always — but reliability is not what decides this. Curating licences is
a downstream choice, which is precisely why the licensing package declines to make it. A data
migration takes that choice back: every portal receives FairDM's three whether or not it wants them,
and declining them means working against a migration that has already run. A pipeline entry offers
the same list as a default a portal can drop or replace, because it is a setting.

Underneath that, a licence row is content with an administrative interface, meant to be edited.
Seeding recommended content is a policy step rather than a schema step, and Django deprecated the
implicit loading of initial data at migrate time for the same reason.

A separate finding, and not a reason to choose differently: the pipeline is configured, registered in
`INSTALLED_APPS`, and appears never to be invoked. The one deployed portal boots straight into
`migrate`, this repository's compose file names an entrypoint script that does not exist here, and no
documentation mentions the command — so `groups`, `django-waffle` and the vocabulary preload are not
reaching a deployed portal either. That is the pipeline's problem to fix, filed as #193, and this
specification's guarantee holds once it is.

## D-019 — What a design review of this directory changed

**Self-resolved, 2026-08-18**, after the rewritten directory was reviewed against the code before any
of it was built. Three things came out of it. The identifier ruling in D-003 is a fourth and is
recorded there.

**`data-model.md` and `quickstart.md` are regenerated, not patched.** D-017 committed to regenerating
them and that did not happen — both files came through the rewrite describing the January design.
Between them they documented a `PROTECT` project relation (D-005 settled `CASCADE`), a three- and a
four-level visibility (D-006 settled two), `Dataset.objects.with_private()` and `.get_all()` as the
recommended way to reach private datasets (R1 removes both outright), an identifier set containing
ARK, Handle, URL and URN (D-003 settled DOI alone), and links to six contract documents D-017 had
already deleted.

Patching the wrong sentences was rejected. A document that disagrees with the specification in five
places is not a document with five errors in it, and the parts nobody had checked were no more likely
to be right than the parts somebody had. Deleting them outright was also rejected: `models.py:528`,
`fairdm_demo/models.py:265` and `fairdm_demo/factories.py:53` all point a reader at one of these two
files, and T103 requires those pointers to resolve.

The risk this closes is specific rather than tidy. `quickstart.md` presented `with_private()` under
the heading "Understanding Privacy-First QuerySets", as the recommended way to widen a query. That
method is the exact defect D-004 exists to remove — it discards the caller's conditions and returns
every dataset in the table. Whoever opened that file for a usage pattern would have built the
behaviour this specification was written to delete.

**`Meta.base_manager_name` cannot be declared, and the plan said to declare it.** R1's third part
named `all_objects` in `Meta.base_manager_name`, which is Django's own guidance for a filtered
default manager. `fairdm.db.models.PrefetchBase` assigns `_meta.base_manager_name =
"prefetch_manager"` after the class is built (`fairdm/db/models.py:30-55`), overwriting anything
`Meta` declares, and `django-auto-prefetch` raises a system check if the value is anything else.
Confirmed by declaring it on a probe model and reading `_meta` back rather than by reading the
metaclass.

The guarantee survives untouched: `prefetch_manager` is a plain unfiltered manager, so following a
relation to a private dataset and cascading a deletion to one both still work, which is all FR-019a
asks for. What changes is one line of plan and what the tests assert — behaviour, never the
attribute. Left alone, this would have cost whoever wrote that task a silent no-op or a system-check
failure, and the tempting repair is to change the metaclass, which would disable prefetching on every
model in the package.

**Three ticks claimed more than their tests proved.** T028, T033 and T036 each said the one-row-per-
type limit holds "at the database as well as in validation". Each cites a test that writes a
duplicate through `objects.create()` and asserts `IntegrityError`, which never reaches `full_clean()`,
and a code line that is the `constraints` block on the abstract base. Both halves of the evidence are
the database half. The claims are cut back to it. T051 was checked against the same charge and
already claimed only the refusal, so it stands as written.

No test was added to close the gap. The validation half is real — FR-009 requires it, SC-002 measures
it, and `validate_unique()` does check an unconditional `UniqueConstraint`, so the code probably
already satisfies it — but writing the test is implementation work, and a tick earned by reasoning
about the framework rather than by running something is the failure this reconciliation exists to
catch. It is left unclaimed and noted in `tasks.md`.
