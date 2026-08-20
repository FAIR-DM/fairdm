# Tasks: Contributors and contributions

**Feature Branch**: `009-fairdm-contributors`

**Spec**: [spec.md](spec.md) — 46 functional requirements, 10 user stories, 15 success criteria.

This list builds the feature from nothing: a new Django app under `fairdm/contrib/contributors/`,
its models, managers, validation, migrations, admin screens, factories, tests and documentation.
It stops where the spec's **Out of scope** section stops — there are no tasks here for views,
plugins, forms, widgets, components, ORCID/ROR synchronisation, metadata export, citations,
privacy enforcement, portal-wide administrative roles, profile claiming, duplicate merging, bulk
import or the REST API.

## Reconciliation

This list was written against the specification alone, as if the repository held no implementation
of this feature. It was then walked against the code. A task is ticked only where the code that
satisfies it can be cited **and** an existing test genuinely exercises the behaviour — code with no
test leaves its task open, and the remaining work is the test.

**30 of 145 reconciled done. 112 remain open. 3 were struck as wrong tasks.**

Those numbers are after the design review, which challenged every tick under a lens of its own and
un-ticked six of them. Its findings are recorded in `decisions.md` under D21.

Every open task carries the reason it is open and, where something exists, the nearest code. The
two struck tasks ask for a stored permission record, which FR-027 forbids and a migration already
removed; they were written in good faith from the specification and are wrong, which is worth
recording rather than quietly deleting.

## Format

```
- [ ] T001 [P] [US1] Description including the exact file path to create or change
  - **Open — built-without-tests.** Nearest code `fairdm/contrib/contributors/apps.py:5`. No default_auto_field; nothing asserts the app config.
```

- **`T###`** — the task number. Sequential from T001, never reused.
- **`[P]`** — present only when the task can run in parallel with its neighbours, meaning it
  touches no file that another task marked `[P]` in the same group touches. A task with no `[P]`
  shares a file with a sibling and waits its turn.
- **`[US#]`** — the user story the task serves, numbered as the spec numbers them. **`[SETUP]`**
  marks shared groundwork that precedes every story, and the cross-cutting work in the final phase
  that belongs to no single story.
- Every task names at least one exact file path.
- Every task is one sitting's work for one person.

Within each story phase, `### Tests` comes before `### Implementation`, because Article I of the
constitution requires a failing test before the code that satisfies it.

---

## Phase 1: Setup and shared groundwork

- [ ] T001 [SETUP] Create the app package: `fairdm/contrib/contributors/__init__.py`,
  `fairdm/contrib/contributors/apps.py` (a `ContributorsConfig` with `label = "contributors"`, a
  translatable `verbose_name` and `default_auto_field`) and
  `fairdm/contrib/contributors/migrations/__init__.py`.
  - **Open — built-without-tests.** Nearest code `fairdm/contrib/contributors/apps.py:5`. No default_auto_field; nothing asserts the app config.
- [ ] T002 [SETUP] Register `"fairdm.contrib.contributors"` in `INSTALLED_APPS` in
  `fairdm/conf/settings/apps.py`, positioned so it loads before the core apps that hold generic
  relations to it.
  - **Open — built-without-tests.** Nearest code `fairdm/conf/settings/apps.py:62`. No test asserts the app is installed or its position.
- [ ] T003 [SETUP] Set `AUTH_USER_MODEL = "contributors.Person"` in
  `fairdm/conf/settings/auth.py`, with a comment recording that the person record *is* the account
  and no second account model exists (FR-008).
  - **Open — built-without-tests.** Nearest code `fairdm/conf/settings/auth.py:19`. No test asserts AUTH_USER_MODEL resolves to the person record.
- [X] T004 [P] [SETUP] Create the mirroring test package
  `tests/test_contrib/test_contributors/__init__.py` (Article X).
  - **Reconciled done.** Code `tests/test_contrib/test_contributors/__init__.py:1` · test `tests/test_contrib/test_contributors/test_models.py:38 TestPersonClaimedUnclaimedSemantics::test_claimed_person_has_email_and_is_active`
- [ ] T005 [P] [SETUP] Create `tests/test_contrib/test_contributors/conftest.py` with a
  `contribution_roles` fixture that seeds the framework's controlled role vocabulary
  (`FairDMRoles`, `fairdm/core/vocabularies.py`) so credit tests have real concepts to attach.
  Object fixtures are added to this file by the story that introduces the model.
  - **Open — partial.** Nearest code `tests/test_contrib/test_contributors/conftest.py:1`. No contribution_roles fixture seeding the role vocabulary.
- [ ] T006 [P] [SETUP] Create `fairdm/factories/contributors.py` with its module docstring and
  export it from `fairdm/factories/__init__.py`, matching the layout of
  `fairdm/factories/core.py`. Model factories are added to this file by the story that introduces
  the model.
  - **Open — partial.** Nearest code `fairdm/factories/contributors.py:1`. Module docstring missing.
---

## Phase 2: US1 — One record for everyone credited

Covers FR-001 to FR-007, SC-001 and SC-002.

### Tests

- [X] T007 [US1] Add `TestContributorPolymorphism` to
  `tests/test_contrib/test_contributors/test_models.py`: a person and an organisation are created,
  queried back through `Contributor.objects`, and each returns as its own class without the caller
  asking which it is (FR-001, SC-001).
  - **Reconciled done.** Code `fairdm/contrib/contributors/models.py:48` · test `tests/test_contrib/test_contributors/test_models.py:108 TestPersonClaimedUnclaimedSemantics::test_person_polymorphic_query`
- [ ] T008 [US1] Add `TestContributorIdentity` to
  `tests/test_contrib/test_contributors/test_models.py`: the public identifier is generated on
  first save, carries the contributor prefix, is unique across both concrete types, and a second
  save leaves it unchanged (FR-002, SC-001).
  - **Open — never-built.** Nearest code `fairdm/contrib/contributors/models.py:90`. Public identifier untested: generation, prefix, cross-type uniqueness, stability.
- [ ] T009 [US1] Add `TestContributorProfileFields` to
  `tests/test_contrib/test_contributors/test_models.py`: the preferred name is required, and other
  names, description, image, related online resources, location and language preferences are each
  optional and round-trip (FR-003).
  - **Open — never-built.** Nearest code `fairdm/contrib/contributors/models.py:97`. Optional profile fields never round-tripped; name not asserted required.
- [ ] T010 [P] [US1] Add `TestISO6391Validator` to
  `tests/test_contrib/test_contributors/test_validators.py`: a code outside ISO 639-1 raises
  `ValidationError` whose message contains the offending value, and a valid code passes (FR-004,
  SC-002).
  - **Open — never-built.** No test_validators.py exists.
- [ ] T011 [US1] Add `TestContributorTimestamps` to
  `tests/test_contrib/test_contributors/test_models.py`: the creation timestamp is set once and the
  modification timestamp moves on a later save (FR-005).
  - **Open — never-built.** Nearest code `fairdm/contrib/contributors/models.py:193`. No test references the timestamps.
- [ ] T012 [US1] Add `TestContributorConfiguration` to
  `tests/test_contrib/test_contributors/test_models.py`: the per-contributor configuration store
  accepts and returns arbitrary JSON, defaults to empty, and imposes no schema (FR-006).
  - **Open — never-built.** No general configuration store exists.
- [ ] T013 [US1] Add `TestFieldMetadata` to
  `tests/test_contrib/test_contributors/test_models.py`: every concrete field on every model the
  app defines declares a non-empty `verbose_name` and `help_text`, and both are lazy translation
  proxies (FR-007, Articles VIII and IX).
  - **Open — never-built.** Nothing sweeps the app's fields for verbose_name and help_text.
### Implementation

- [ ] T014 [US1] Add the ISO 639-1 language validator to
  `fairdm/contrib/contributors/validators.py`, raising `ValidationError` with the offending value
  interpolated through the message's parameters (FR-004).
  - **Open — built-without-tests.** Nearest code `fairdm/contrib/contributors/validators.py:7`. Validator defined and imported by nothing.
- [ ] T015 [US1] Define the `Contributor` polymorphic base in
  `fairdm/contrib/contributors/models.py` — `PolymorphicModel` first in the inheritance list per
  the warning in `fairdm/core/abstract.py`, a required `name`, a `ShortUUIDField` public identifier
  with a contributor prefix, `editable=False`, `unique=True`, and `Meta` verbose names,
  `default_related_name` and ordering (FR-001, FR-002).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:48`. No default_related_name; uuid and required-name untested.
- [ ] T016 [US1] Add the optional profile fields to `Contributor` in
  `fairdm/contrib/contributors/models.py` — other names, free-text description, image
  (`ThumbnailerImageField`, matching `BaseModel.image`), related online resources, and a location
  foreign key to `fairdm.contrib.location.models.Point` with `on_delete=SET_NULL`. Each field
  carries `verbose_name`, `help_text` and its indexing decision (FR-003, Article IX).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:174`. Profile has no help_text, name's is commented out, none round-tripped.
- [ ] T017 [US1] Add the language-preferences field to `Contributor` in
  `fairdm/contrib/contributors/models.py`, wired to the validator from T014 so that every element
  is checked (FR-003, FR-004).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:135`. The language validator is never attached, so invalid codes are accepted.
- [ ] T018 [US1] Add the created and modified timestamps to `Contributor` in
  `fairdm/contrib/contributors/models.py`, with the modified field indexed for ordering
  (FR-005, Article IX).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:193`. Modified is not indexed.
- [ ] T019 [US1] Add the general-purpose configuration field to `Contributor` in
  `fairdm/contrib/contributors/models.py`, documented in its `help_text` and docstring as holding
  contents this specification deliberately does not define (FR-006).
  - **Open — never-built.** The configuration field does not exist.
- [ ] T020 [US1] Add `fairdm/contrib/contributors/migrations/0001_create_contributor.py` creating
  the contributor table, its public-identifier unique index and its location foreign key.
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/migrations/0001_initial.py:31`. Location foreign key arrives only in 0008.
- [ ] T021 [US1] Add `ContributorFactory` to `fairdm/factories/contributors.py` as the shared base
  the person and organisation factories build on, declaring only the fields common to both and
  using `factory.Sequence` for the name (Article X).
  - **Open — built-differently.** Nearest code `fairdm/factories/contributors.py:44`. ContributorFactory builds a Person and the two concrete factories do not inherit from it.
- [ ] T022 [US1] Create `docs/data_models/contributors.md` documenting the `Contributor` base — its
  fields, its two concrete types, its public identifier and its configuration store — with a
  minimal working example, and list the page in the toctree in `docs/data_models/index.md`
  (Articles VI and XVII).
  - **Open — never-built.** Docs/data_models/ holds only index and samples.

### Removals the greenfield list could not contain

A task list written as though the repository were empty cannot ask for anything to be deleted. Two
of the settled decisions require exactly that, so these two tasks were added after reconciliation
rather than derived from the specification.

- [ ] T144 [US1] Replace `Contributor.privacy_settings` with the general-purpose `config` store in
  `fairdm/contrib/contributors/models.py` — a `RenameField` and an `AlterField` for the new help
  text, plus a data migration clearing the column, per research R3. Remove
  `Contributor.get_visible_fields` (`models.py:473`) and the privacy-seeding branch in
  `Person.save()` (`models.py:546`), and delete the tests that cover them
  (`test_models.py:86`, `:93`, `:115`, `:825`, `:840`, `:854`, `:881`, `:924`) — these are tests of
  behaviour this specification removes, so deleting them is the task, not tampering (D9).
  - **Open — never-built.** Added after reconciliation; a greenfield list cannot express a deletion.
- [ ] T145 [US1] Remove `Contributor.weight` (`models.py:165`), `calculate_weight`
  (`models.py:305`) and `calculate_profile_completion` (`models.py:292`) from
  `fairdm/contrib/contributors/models.py`, with a `RemoveField` migration, and correct the class
  docstring (`models.py:60`), which advertises an `avatar` field, a `keywords` field, an `owner`
  field, a `permissions` field, a `created` field and an `update_weight` lifecycle hook, none of
  which exist (D16).
  - **Open — never-built.** Added after reconciliation; a greenfield list cannot express a deletion.

---

## Phase 3: US2 — A person is also the account

Covers FR-008 to FR-011, FR-015, SC-003 and SC-005.

### Tests

- [ ] T023 [US2] Add `TestPersonIsTheAccount` to
  `tests/test_contrib/test_contributors/test_models.py`: `django.contrib.auth.get_user_model()`
  is `Person`, asserted by name, and no separate account model is registered anywhere in the app
  registry (FR-008, SC-003).
  - **Open — never-built.** Nearest code `fairdm/conf/settings/auth.py:19`. No test asserts the account model or the absence of a second one.
- [ ] T024 [US2] Add `TestAttributionOnlyPerson` to
  `tests/test_contrib/test_contributors/test_models.py`: a person created for attribution alone has
  no email address, reports `has_usable_password()` as false, and `authenticate()` against them
  fails (FR-010, SC-003).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/managers.py:45`. Nothing ever attempts to authenticate as an attribution-only person.
- [ ] T025 [US2] Add `TestPersonActivationEligibility` to
  `tests/test_contrib/test_contributors/test_models.py`: an attribution-only person remains active
  and therefore reachable by a later invitation or password reset (FR-011, SC-003).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/managers.py:66`. The only assertion holds by Django's own default.
- [ ] T026 [US2] Add `TestPersonEmailUniqueness` to
  `tests/test_contrib/test_contributors/test_models.py`: a second person cannot take an address
  already in use, refused at validation and at the database, while any number of people may carry
  no address at all (FR-009, SC-005).
  - **Open — never-built.** Nearest code `fairdm/contrib/contributors/models.py:525`. No test asserts a duplicate address is refused.
- [ ] T027 [US2] Add `TestClaimedPersonEmailRemoval` to
  `tests/test_contrib/test_contributors/test_models.py`: a claimed person clearing their email
  address is refused by `full_clean()` with a message attached to the email field (FR-015, SC-005).
  - **Open — built-differently.** Nearest code `fairdm/contrib/contributors/models.py:572`. The refusal reads `has_usable_password()` and `is_active` rather than the stored claim value, and the existing test never claims anyone, so it passes either way (design review RECON-001).
- [ ] T028 [P] [US2] Add `TestPersonManagerCreation` to
  `tests/test_contrib/test_contributors/test_managers.py`: `create_user`, `create_superuser` and
  the attribution-only creation path each produce the account shape they promise, and email
  addresses are normalised (FR-009, FR-010).
  - **Open — never-built.** Nearest code `fairdm/contrib/contributors/managers.py:23`. No manager-creation tests at all; create_user does not exist.
### Implementation

- [ ] T029 [US2] Define `Person` in `fairdm/contrib/contributors/models.py` as a subclass of both
  `Contributor` and Django's `AbstractUser`: given and family names for DataCite, the email address
  as `USERNAME_FIELD` (nullable, blank-permitting), `username` removed, `REQUIRED_FIELDS` emptied,
  and `is_active` defaulting to true (FR-008, FR-009, FR-010, FR-011).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:518`. REQUIRED_FIELDS is not empty and username is shadowed rather than removed.
- [ ] T030 [US2] Add `PersonQuerySet` and a `PersonManager` built with
  `Manager.from_queryset(PersonQuerySet)` and mixing in `BaseUserManager` to
  `fairdm/contrib/contributors/managers.py`, with `create_user`/`create_superuser` setting an
  unusable password when none is supplied (FR-009, FR-010, FR-040).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/managers.py:9`. Hand-written proxies rather than from_queryset; no create_user.
- [ ] T031 [US2] Add the email uniqueness constraint to `Person.Meta.constraints` in
  `fairdm/contrib/contributors/models.py` — a case-insensitive `UniqueConstraint` with a
  `condition` excluding null, so that attribution-only people do not collide (FR-009, Article IX).
  - **Open — built-differently.** Nearest code `fairdm/contrib/contributors/models.py:525`. Uniqueness is a field flag; case-insensitivity relies on clean() lowercasing, which a direct create bypasses.
- [ ] T032 [US2] Add `Person.clean()` to `fairdm/contrib/contributors/models.py` refusing removal of
  the email address when `Person.is_claimed` is true — not when the account merely has a usable
  password and is active, which is what it reads today — raising a field-keyed `ValidationError`
  (FR-015).
  - **Open — built-differently.** Nearest code `fairdm/contrib/contributors/models.py:572`. A fourth site deciding claim status from something other than the stored value (design review RECON-001).
- [ ] T033 [US2] Add `fairdm/contrib/contributors/migrations/0002_create_person.py` creating the
  person table, its email constraint and the permissions Django's auth app expects of a swapped
  user model.
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/migrations/0001_initial.py:192`. No migration-level constraint.
- [ ] T034 [US2] Add `PersonFactory` to `fairdm/factories/contributors.py`, sequencing the email
  address, defaulting to an unusable password, and leaving the account unclaimed so the default
  instance is the common case (Article X).
  - **Open — partial.** Nearest code `fairdm/factories/contributors.py:60`. No unusable password; is_active is a random boolean (issue #227).
- [X] T035 [US2] Add a `person` fixture to `tests/test_contrib/test_contributors/conftest.py` as a
  thin wrapper over `PersonFactory` (Article X).
  - **Reconciled done.** Code `tests/test_contrib/test_contributors/conftest.py:31` · test `tests/test_contrib/test_contributors/test_models.py:42 TestPersonClaimedUnclaimedSemantics::test_claimed_person_has_email_and_is_active`
- [ ] T036 [US2] Create `docs/portal-development/contributors.md` documenting the person record as
  the portal's account — why there is one row rather than two, how to add a person for attribution
  alone, and what such a person can and cannot do — and list it in the "Defining models" toctree in
  `docs/portal-development/index.md` (Articles VI and XVII).
  - **Open — partial.** Nearest code `docs/portal-development/contributors.md:1`. Documents create_user, which does not exist, and states the wrong active default.
---

## Phase 4: US3 — Know whether a profile has been claimed

Covers FR-012 to FR-014 and SC-004.

### Tests

- [ ] T037 [US3] Add `TestAccountState` to
  `tests/test_contrib/test_contributors/test_models.py`: a person in each of the four states
  reports exactly that state, and no person reports two (FR-013, SC-004).
  - **Open — never-built.** No account state accessor exists.
- [ ] T038 [US3] Add `TestAccountStatePrecedence` to
  `tests/test_contrib/test_contributors/test_models.py`: a deactivated person reports inactive
  whatever their claim status and whether or not they carry an email address (FR-013, SC-004).
  - **Open — never-built.**
- [ ] T039 [US3] Add `TestClaimIsStoredOnce` to
  `tests/test_contrib/test_contributors/test_models.py`: the claim flag is the only stored
  expression of claim status, and the derived state has no database column of its own (FR-012,
  FR-013).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:527`. No test asserts the state is not stored.
- [ ] T040 [P] [US3] Add `TestAccountStateFilters` to
  `tests/test_contrib/test_contributors/test_managers.py`: each of the four state filters returns
  exactly the people in that state, and the four together return the whole population exactly once,
  asserted against a fixture holding every case (FR-014, SC-004).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/managers.py:150`. No test covers ghost or invited, and none covers the partition.
### Implementation

- [ ] T041 [US3] Add an `AccountState` choices class to
  `fairdm/contrib/contributors/choices.py` — ghost, invited, claimed and inactive, with
  translatable labels (FR-013).
  - **Open — never-built.** No account state enumeration.
- [ ] T042 [US3] Add the stored claim flag to `Person` in
  `fairdm/contrib/contributors/models.py`, indexed because it is what the state filters and the
  administrative filter both read (FR-012, Article IX).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:527`. The claim field is not indexed.
- [ ] T043 [US3] Add `Person.account_state` to `fairdm/contrib/contributors/models.py` as a derived,
  unstored property returning exactly one `AccountState` member, testing deactivation first, then
  claim, then the presence of an email address (FR-013).
  - **Open — never-built.**
- [ ] T044 [US3] Add the four state filters to `PersonQuerySet` in
  `fairdm/contrib/contributors/managers.py`, written as mutually exclusive `Q` expressions that
  partition the table and mirror the precedence in `account_state` (FR-014, FR-040).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/managers.py:128`. No inactive filter and no deactivation-first precedence.
- [ ] T045 [US3] Add `fairdm/contrib/contributors/migrations/0003_person_claim_flag.py` adding the
  claim column and its index.
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/migrations/0014_add_is_claimed_field.py:12`. No index migration.
- [ ] T046 [US3] Create `docs/portal-administration/managing-unclaimed-profiles.md` describing the
  four account states, how a person arrives in each, and how to filter for them, and list it in the
  toctree in `docs/portal-administration/index.md` (Articles VI and XVII).
  - **Open — partial.** Nearest code `docs/portal-administration/managing-unclaimed-profiles.md:1`. Documents claim pathways, not the four states.
---

## Phase 5: US4 — Institutions and their hierarchy

Covers FR-016 to FR-019, SC-006 and SC-007.

### Tests

- [ ] T047 [P] [US4] Add `TestOrganizationTypeVocabulary` to
  `tests/test_contrib/test_contributors/test_choices.py`: every member of the ROR organisation-type
  set is asserted by name, rather than by iterating whatever the choices class happens to hold
  (SC-006).
  - **Open — never-built.** No test_choices.py.
- [ ] T048 [US4] Add `TestOrganizationTypeValidation` to
  `tests/test_contrib/test_contributors/test_models.py`: a type outside the ROR set is refused by
  `full_clean()`, and each member of the set is accepted (FR-016, SC-006).
  - **Open — never-built.** No organisation type field exists.
- [X] T049 [US4] Add `TestOrganizationHierarchy` to
  `tests/test_contrib/test_contributors/test_models.py`: a department naming a university as parent
  is reachable from the university's sub-organisations and the university from the department
  (FR-017).
  - **Reconciled done.** Code `fairdm/contrib/contributors/models.py:894` · test `tests/test_contrib/test_contributors/test_models.py:184 TestOrganizationCreationAndValidation::test_organization_parent_child`
- [ ] T050 [US4] Add `TestOrganizationParentDeletion` to
  `tests/test_contrib/test_contributors/test_models.py`: deleting the parent leaves the
  sub-organisation alive with no parent, its members and its credits intact (FR-018, SC-007).
  - **Open — built-differently.** Nearest code `fairdm/contrib/contributors/models.py:894`. Parent cascades, so deleting a parent deletes its children.
- [ ] T051 [US4] Add `TestOrganizationLocation` to
  `tests/test_contrib/test_contributors/test_models.py`: the city and the country an organisation
  is based in are optional and round-trip (FR-019).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:904`. Nothing refreshes from the database or asserts the fields are optional.
### Implementation

- [ ] T052 [US4] Add an `OrganizationType` choices class to
  `fairdm/contrib/contributors/choices.py` with one member per ROR organisation type and
  translatable labels, citing the registry as the source in the module docstring (FR-016).
  - **Open — never-built.** No ROR organisation-type set exists.
- [ ] T053 [US4] Define `Organization(Contributor)` in `fairdm/contrib/contributors/models.py` with
  its type field bound to `OrganizationType`, indexed because it is a listing filter, plus `Meta`
  verbose names and `default_related_name` (FR-016, Article IX).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:876`. No type field, no index, no default_related_name.
- [ ] T054 [US4] Add the self-referential parent foreign key to `Organization` in
  `fairdm/contrib/contributors/models.py` — `on_delete=SET_NULL`, null and blank permitted, and a
  `related_name` that reads as the sub-organisations of the parent (FR-017, FR-018).
  - **Open — built-differently.** Nearest code `fairdm/contrib/contributors/models.py:894`. On_delete is CASCADE where SET_NULL is required.
- [ ] T055 [US4] Add the city and country fields to `Organization` in
  `fairdm/contrib/contributors/models.py`, the country as a `django_countries` `CountryField`, both
  indexed as listing filters (FR-019, Article IX).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:904`. Neither city nor country is indexed.
- [ ] T056 [US4] Add `fairdm/contrib/contributors/migrations/0004_create_organization.py` creating
  the organisation table and its parent foreign key.
  - **Open — built-without-tests.** Nearest code `fairdm/contrib/contributors/migrations/0001_initial.py:314`.
- [X] T057 [P] [US4] Add `OrganizationFactory` to `fairdm/factories/contributors.py`, with the
  parent left unset by default and expressed at the call site when a hierarchy is wanted
  (Article X).
  - **Reconciled done.** Code `fairdm/factories/contributors.py:75` · test `tests/test_factories/test_contributors.py:82 TestContributorFactoryCreation::test_organization_factory_creates_organization`
- [X] T058 [P] [US4] Add an `organization` fixture to
  `tests/test_contrib/test_contributors/conftest.py` wrapping `OrganizationFactory` (Article X).
  - **Reconciled done.** Code `tests/test_contrib/test_contributors/conftest.py:70` · test `tests/test_contrib/test_contributors/test_models.py:145 TestOrganizationCreationAndValidation::test_create_organization`
- [ ] T059 [US4] Document `Organization` in `docs/data_models/contributors.md` — its type, its
  hierarchy, what happens to children when a parent is deleted, and its location fields — with a
  worked example of a department beneath a university (Articles VI and XVII).
  - **Open — never-built.** The organisation documentation page does not exist.
---

## Phase 6: US5 — Membership of an institution over time

Covers FR-020 to FR-025 and SC-008.

### Tests

- [X] T060 [US5] Add `TestAffiliation` to
  `tests/test_contrib/test_contributors/test_models.py`: one membership record carries the person,
  the organisation, a period and a membership type (FR-020).
  - **Reconciled done.** Code `fairdm/contrib/contributors/models.py:778` · test `tests/test_contrib/test_contributors/test_models.py:238 TestAffiliationUniqueConstraints::test_affiliation_start_end_dates`
- [ ] T061 [US5] Add `TestAffiliationUniqueness` to
  `tests/test_contrib/test_contributors/test_models.py`: a second membership of the same
  organisation by the same person is refused, at validation with a readable message and at the
  database by constraint (FR-021, SC-008).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:857`. No clean(), so no readable validation message.
- [X] T062 [P] [US5] Add `TestAffiliationCurrency` to
  `tests/test_contrib/test_contributors/test_managers.py`: a membership with no end date is
  current and one with an end date is not, through both the current and the past filters (FR-022,
  FR-042, SC-008).
  - **Reconciled done.** Code `fairdm/contrib/contributors/managers.py:194` · test `tests/test_contrib/test_contributors/test_managers.py:267 TestAffiliationQuerysetMethods::test_affiliation_current_method`
- [X] T063 [US5] Add `TestAffiliationDatePrecision` to
  `tests/test_contrib/test_contributors/test_models.py`: a year alone, a year and a month, and a
  full date all round-trip at their own precision on both the start and the end of a membership
  (FR-023, SC-008).
  - **Reconciled done.** Code `fairdm/contrib/contributors/models.py:838` · test `tests/test_contrib/test_contributors/test_models.py:602 TestPartialDatePrecision::test_affiliation_year_month_precision`
- [X] T064 [US5] Add `TestPrimaryAffiliation` to
  `tests/test_contrib/test_contributors/test_models.py`: a person has at most one primary
  membership, and marking a second primary unmarks the first (FR-024, SC-008).
  - **Reconciled done.** Code `fairdm/contrib/contributors/models.py:859` · test `tests/test_contrib/test_contributors/test_models.py:653 TestPrimaryAffiliationConstraint::test_setting_new_primary_unsetsolds`
- [X] T065 [P] [US5] Add `TestAffiliationTypeVocabulary` to
  `tests/test_contrib/test_contributors/test_choices.py`: the four membership types exist and are
  ordered so that a pending membership sorts apart from the confirmed ones (FR-025).
  - **Reconciled done.** Code `fairdm/contrib/contributors/models.py:799` · test `tests/test_contrib/test_contributors/test_models.py:229 TestAffiliationUniqueConstraints::test_affiliation_type_choices`
### Implementation

- [X] T066 [US5] Add an `AffiliationType` choices class to
  `fairdm/contrib/contributors/choices.py` — pending, member, administrator and owner — with
  integer values that put pending below the confirmed types, and translatable labels (FR-025).
  - **Reconciled done.** Code `fairdm/contrib/contributors/models.py:799` · test `tests/test_contrib/test_contributors/test_models.py:229 TestAffiliationUniqueConstraints::test_affiliation_type_choices`
- [ ] T067 [US5] Define `Affiliation` in `fairdm/contrib/contributors/models.py` with foreign keys
  to `Person` and `Organization`, the membership type bound to `AffiliationType` and indexed
  because ownership lookups filter on it, plus `Meta` verbose names and `default_related_name`
  (FR-020, FR-025, Article IX).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:821`. Membership type is not indexed; no default_related_name.
- [X] T068 [US5] Add the start and end of the membership period to `Affiliation` in
  `fairdm/contrib/contributors/models.py` as `PartialDateField`s
  (`fairdm/db/fields.py`), so a year, a year and month, or a full date are all recordable (FR-023).
  - **Reconciled done.** Code `fairdm/contrib/contributors/models.py:838` · test `tests/test_contrib/test_contributors/test_models.py:238 TestAffiliationUniqueConstraints::test_affiliation_start_end_dates`
- [ ] T069 [US5] Add the person-and-organisation `UniqueConstraint` to `Affiliation.Meta` and the
  matching `clean()` message in `fairdm/contrib/contributors/models.py` (FR-021).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:857`. Unique_together rather than a named constraint; no clean() message.
- [ ] T070 [US5] Add the primary-membership flag to `Affiliation` and the save-time demotion of any
  other primary membership the same person holds, inside a transaction, in
  `fairdm/contrib/contributors/models.py` (FR-024).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:859`. The demotion and the save are not atomic.
- [ ] T071 [US5] Add a partial `UniqueConstraint` to `Affiliation.Meta` in
  `fairdm/contrib/contributors/models.py` limiting a person to one primary membership, conditioned
  on the flag, so a concurrent write cannot slip past the save-time demotion (FR-024, Article IX).
  - **Open — never-built.** No database constraint protects the primary-membership invariant.
- [X] T072 [US5] Add `AffiliationQuerySet` with `current()` and `past()` to
  `fairdm/contrib/contributors/managers.py` (FR-022, FR-042). Composing them onto the manager
  belongs to T124.
  - **Reconciled done.** Code `fairdm/contrib/contributors/managers.py:173` · test `tests/test_contrib/test_contributors/test_managers.py:302 TestAffiliationQuerysetMethods::test_affiliation_past_method`
- [ ] T073 [US5] Add `fairdm/contrib/contributors/migrations/0005_create_affiliation.py` creating
  the membership table and both of its constraints.
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/migrations/0012_rename_to_affiliation.py:1`. No primary-membership constraint is migrated.
- [ ] T074 [P] [US5] Add `AffiliationFactory` to `fairdm/factories/contributors.py` with
  `SubFactory` relations to the person and organisation factories, a current period and a plain
  member type by default (Article X).
  - **Open — partial.** Nearest code `fairdm/factories/contributors.py:86`. The factory declares no period.
- [X] T075 [P] [US5] Add an `affiliation` fixture to
  `tests/test_contrib/test_contributors/conftest.py` wrapping `AffiliationFactory` (Article X).
  - **Reconciled done.** Code `tests/test_contrib/test_contributors/conftest.py:96` · test `tests/test_contrib/test_contributors/test_models.py:238 TestAffiliationUniqueConstraints::test_affiliation_start_end_dates`
- [ ] T076 [US5] Document memberships in `docs/portal-development/contributors.md` — the period and
  its precision, what makes a membership current, the primary membership and what it is used for —
  with a worked example spanning two institutions (Articles VI and XVII).
  - **Open — partial.** Nearest code `docs/portal-development/contributors.md:203`. No worked example spanning two institutions.
---

## Phase 7: US6 — Who owns an organisation

Covers FR-026 to FR-029 and SC-009.

### Tests

- [X] T077 [US6] Add `TestOwnershipConfersRights` to
  `tests/test_contrib/test_contributors/test_permissions.py`: a person holding an owner membership
  holds the organisation's management permission on that organisation (FR-026, SC-009).
  - **Reconciled done.** Code `fairdm/contrib/contributors/permissions.py:102` · test `tests/test_contrib/test_contributors/test_permissions.py:24 TestAssignOrganizationOwner::test_owner_affiliation_grants_manage_permission`
- [ ] T078 [US6] Add `TestOwnershipIsScoped` to
  `tests/test_contrib/test_contributors/test_permissions.py`: the owner of one organisation holds
  nothing over a different one (FR-026, SC-009).
  - **Open — built-without-tests.** Nearest code `fairdm/contrib/contributors/permissions.py:102`. No test puts an owner against a second organisation.
- [ ] T079 [US6] Add `TestOwnershipDemotion` to
  `tests/test_contrib/test_contributors/test_permissions.py`: demoting the owner withdraws the
  right on the very next check with no intervening revocation step, and no object-permission row is
  written at any point (FR-027, SC-009).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/permissions.py:102`. The demotion half is covered at `tests/test_contrib/test_contributors/test_permissions.py:38`; the clause proving FR-027 — that no object-permission row is ever written — is asserted nowhere, and it is the requirement on which two tasks were struck (design review RECON-005).
- [X] T080 [US6] Add `TestOrganizationWithNoOwner` to
  `tests/test_contrib/test_contributors/test_permissions.py`: an organisation with no owner confers
  management rights on nobody by membership, and no member is promoted automatically (FR-028,
  SC-009).
  - **Reconciled done.** Code `fairdm/contrib/contributors/permissions.py:102` · test `tests/test_contrib/test_contributors/test_permissions.py:161 TestNonOwnerCannotEdit::test_non_owner_lacks_permission`
- [ ] T081 [P] [US6] Add `TestOwnershipTransfer` to
  `tests/test_contrib/test_contributors/test_models.py`: the transfer leaves the incumbent an
  administrator and the successor the owner in one operation, and refuses a person who is not
  already a member (FR-029, SC-009).
  - **Open — built-differently.** Nearest code `fairdm/contrib/contributors/views/organization.py:58`. The administrative action performs no transfer; the working view is unrouted.
### Implementation

- [ ] ~~T082~~ [US6] Declare the organisation management permission in `Organization.Meta.permissions`
  in `fairdm/contrib/contributors/models.py` (FR-026).
  - **Struck.** contradicts FR-027 — a declared permission is a stored permission record, which migration 0017 deliberately removed. Not built, not counted.
- [X] T083 [US6] Add `OrganizationPermissionBackend` to
  `fairdm/contrib/contributors/permissions.py`, re-parented onto
  `fairdm.core.permissions.PolymorphicObjectPermissionBackend` and answering `has_perm` for an
  organisation by reading the asking person's owner membership at check time, storing, granting and
  revoking nothing (FR-026, FR-027, FR-028).
  - **Reconciled done.** Code `fairdm/contrib/contributors/permissions.py:10` · test `tests/test_contrib/test_contributors/test_permissions.py:24 TestAssignOrganizationOwner::test_owner_affiliation_grants_manage_permission`
- [X] T084 [US6] Register `fairdm.contrib.contributors.permissions.OrganizationPermissionBackend`
  in `AUTHENTICATION_BACKENDS` in `fairdm/conf/settings/auth.py`, after the polymorphic object
  backend (FR-026).
  - **Reconciled done.** Code `fairdm/conf/settings/auth.py:56` · test `tests/test_contrib/test_contributors/test_permissions.py:24 TestAssignOrganizationOwner::test_owner_affiliation_grants_manage_permission`
- [ ] T085 [US6] Add `Organization.transfer_ownership()` to
  `fairdm/contrib/contributors/models.py` — atomic, demoting the incumbent owner to administrator
  and promoting the named member in the same operation, and raising when the named person is not a
  member (FR-029).
  - **Open — built-differently.** Nearest code `fairdm/contrib/contributors/views/organization.py:58`. No atomic transfer operation on the model.
- [ ] ~~T086~~ [US6] Add `fairdm/contrib/contributors/migrations/0006_organization_permissions.py` for
  the permission declared in T082.
  - **Struck.** contradicts FR-027, as the migration for T082. Not built, not counted.
- [ ] T087 [US6] Create `docs/portal-administration/managing_contributors.md` with the ownership
  section — that the right is derived from the owner membership and nothing is stored, that
  demotion is immediate, and how to transfer ownership — and list it in the toctree in
  `docs/portal-administration/index.md` (Articles VI and XVII).
  - **Open — partial.** Nearest code `docs/portal-administration/managing_contributors.md:185`. Documents lifecycle-hook synchronisation, a mechanism that was deleted.
---

## Phase 8: US7 — Credit on a record

Covers FR-030 to FR-036, SC-010, SC-011 and SC-012.

### Tests

- [ ] T088 [US7] Add `TestContributionTargets` to
  `tests/test_contrib/test_contributors/test_models.py`: a contributor of either kind is creditable
  on a project, a dataset, a sample and a measurement through the one generic entry (FR-030).
  - **Open — partial.** The sample case is covered at `tests/test_core/test_sample/test_models.py:626` and can be cited rather than rewritten. The dataset, measurement and organisation-as-contributor cases are not covered (design review RECON-004).
- [ ] T089 [US7] Add `TestContributionUniqueness` to
  `tests/test_contrib/test_contributors/test_models.py`: one credit per contributor per object; a
  second entry for the same pairing is refused, and a further role accumulates on the existing
  entry so a person who both collected and analysed appears once (FR-031, SC-010).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:1109`. The uniqueness half is covered; the accumulation half is not, and the code contradicts it (design review SPEC-001).
- [ ] T090 [US7] Add `TestContributionRoles` to
  `tests/test_contrib/test_contributors/test_models.py`: roles come from the framework's controlled
  role vocabulary and a concept outside it is refused (FR-032).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:1088`. Nothing refuses a term from another vocabulary.
- [X] T091 [US7] Add `TestContributionAffiliation` to
  `tests/test_contrib/test_contributors/test_models.py`: a person credited with no organisation
  named on the entry carries their primary membership's organisation, and a named organisation is
  left alone (FR-033, SC-010).
  - **Reconciled done.** Code `fairdm/contrib/contributors/models.py:1151` · test `tests/test_contrib/test_contributors/test_models.py:321 TestContributionGFKRelationships::test_contribution_default_affiliation`
- [ ] T092 [US7] Add `TestContributorCredits` to
  `tests/test_contrib/test_contributors/test_models.py`: a contributor credited across all four
  kinds of research output reports each of them and reports counts by kind (FR-034, SC-011).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:273`. Datasets, samples and measurements untested; counts by kind not on the record.
- [ ] T093 [US7] Add `TestCoContributors` to
  `tests/test_contrib/test_contributors/test_models.py`: the contributors credited alongside a
  given contributor come back most frequent first (FR-035, SC-011).
  - **Open — built-without-tests.** Nearest code `fairdm/contrib/contributors/models.py:417`. Referenced nowhere outside its own definition.
- [X] T094 [P] [US7] Add `TestCreditWithdrawal` to
  `tests/test_contrib/test_contributors/test_receivers.py`: an object-level right a person holds is
  checked before and after their credit on that object is deleted, and is gone afterwards
  (FR-036, SC-012). Include a queryset-delete case, not only an instance delete.
  - **Reconciled done.** Code `fairdm/contrib/contributors/models.py:1168` · test `tests/test_core/test_sample/test_permissions.py:186 TestContributionRevocationIsNormalised::test_deleting_the_contribution_removes_the_grant`
- [X] T095 [P] [US7] Add `TestContributionRoleFilter` to
  `tests/test_contrib/test_contributors/test_managers.py`: filtering credits by role returns only
  the credits carrying it (FR-042).
  - **Reconciled done.** Code `fairdm/contrib/contributors/managers.py:245` · test `tests/test_contrib/test_contributors/test_managers.py:83 TestContributionByRole::test_by_role_filters_correctly`
### Implementation

- [X] T096 [US7] Define `Contribution` in `fairdm/contrib/contributors/models.py` with a foreign key
  to `Contributor`, a content type and object id generic foreign key (FR-030). The reverse accessor is
  supplied explicitly on the contributor foreign key, so no `Meta.default_related_name` is needed
  (design review RECON-006).
  - **Reconciled done.** Code `fairdm/contrib/contributors/models.py:1068` · test `tests/test_contrib/test_contributors/test_models.py:297 TestContributionGFKRelationships::test_contribution_links_person_to_project`
- [ ] T097 [US7] Add the content-type, object-id and contributor `UniqueConstraint` and its
  supporting composite index to `Contribution.Meta`, with the matching `clean()` message, in
  `fairdm/contrib/contributors/models.py` (FR-031, Article IX).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:1109`. Unique_together rather than a named constraint; no clean() message.
- [ ] T098 [US7] Add the roles many-to-many from `Contribution` to `research_vocabs.Concept` in
  `fairdm/contrib/contributors/models.py`, bound to the framework's roles vocabulary, with
  validation refusing a concept from outside it (FR-032). Crediting MUST **accumulate** roles rather than replace them: both entry points call `roles.set()` (`models.py:470` and `models.py:1127`), which silently discards a role recorded earlier, against FR-031 and `CONTEXT.md`. Change both (design review SPEC-001).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:1088`. The vocabulary binding exists; the validation does not.
- [X] T099 [US7] Add the crediting-organisation foreign key to `Contribution` and the save-time
  default taken from the person's primary membership when none is named, in
  `fairdm/contrib/contributors/models.py` (FR-033).
  - **Reconciled done.** Code `fairdm/contrib/contributors/models.py:1094` · test `tests/test_contrib/test_contributors/test_models.py:321 TestContributionGFKRelationships::test_contribution_default_affiliation`
- [ ] T100 [US7] Add the credited-outputs reporting methods to `Contributor` in
  `fairdm/contrib/contributors/models.py` — the projects, datasets, samples and measurements it is
  credited on, and the counts by kind, each resolved in a bounded number of queries (FR-034).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:273`. Counts by kind live on a plugin, not the record; no query-count guard.
- [ ] T101 [US7] Add the co-contributor reporting method to `Contributor` in
  `fairdm/contrib/contributors/models.py`, returning the contributors credited alongside it ordered
  most frequent first (FR-035).
  - **Open — built-without-tests.** Nearest code `fairdm/contrib/contributors/models.py:417`.
- [ ] T102 [US7] Add the post-delete receiver withdrawing a person's object-level rights over an
  object when their credit on it is deleted to `fairdm/contrib/contributors/receivers.py`, and
  connect it from `ContributorsConfig.ready()` in `fairdm/contrib/contributors/apps.py` (FR-036). The withdrawal must also fire when credits are deleted through the queryset.
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/models.py:1168`. The behaviour exists and is tested for an instance delete, but a lifecycle hook runs from the model's own `delete()` and so never fires for a queryset delete, which a post-delete receiver would (design review RECON-002).
- [X] T103 [US7] Add `ContributionQuerySet` with the role filter to
  `fairdm/contrib/contributors/managers.py` (FR-042). Composing it onto the manager belongs to
  T124.
  - **Reconciled done.** Code `fairdm/contrib/contributors/managers.py:242` · test `tests/test_contrib/test_contributors/test_managers.py:83 TestContributionByRole::test_by_role_filters_correctly`
- [X] T104 [US7] Add `fairdm/contrib/contributors/migrations/0007_create_contribution.py` creating
  the credit table, its roles join table and its uniqueness constraint.
  - **Reconciled done.** Code `fairdm/contrib/contributors/migrations/0001_initial.py:565` · test `tests/test_contrib/test_contributors/test_models.py:305 TestContributionGFKRelationships::test_contribution_unique_per_entity_contributor`
- [X] T105 [P] [US7] Add `ContributionFactory` to `fairdm/factories/contributors.py`, with the
  credited object supplied at the call site and roles left empty by default (Article X).
  - **Reconciled done.** Code `fairdm/factories/contributors.py:96` · test `tests/test_contrib/test_contributors/test_models.py:305 TestContributionGFKRelationships::test_contribution_unique_per_entity_contributor`
- [X] T106 [P] [US7] Add a `contribution` fixture to
  `tests/test_contrib/test_contributors/conftest.py` wrapping `ContributionFactory` (Article X).
  - **Reconciled done.** Code `tests/test_contrib/test_contributors/conftest.py:126` · test `tests/test_contrib/test_contributors/test_models.py:297 TestContributionGFKRelationships::test_contribution_links_person_to_project`
- [ ] T107 [US7] Document crediting in `docs/portal-development/contributors.md` — one entry per
  contributor per object, roles accumulating on it, the crediting organisation default, and the
  reporting methods — and state plainly that deleting a credit withdraws that person's object-level
  rights while creating one grants none (FR-036, Articles VI and XVII).
  - **Open — partial.** Nearest code `docs/portal-development/contributors.md:254`. Says nothing about one credit per pairing, role accumulation, or the rights withdrawal.
---

## Phase 9: US8 — Carry external identifiers

Covers FR-037 to FR-039 and SC-013.

### Tests

- [X] T108 [US8] Add `TestContributorIdentifier` to
  `tests/test_contrib/test_contributors/test_models.py`: an identifier carries a type and a value
  and attaches to either kind of contributor (FR-037).
  - **Reconciled done.** Code `fairdm/contrib/contributors/models.py:1200` · test `tests/test_contrib/test_contributors/test_models.py:374 TestContributorIdentifierUniqueness::test_create_ror_identifier`
- [ ] T109 [US8] Add `TestIdentifierUniquePerType` to
  `tests/test_contrib/test_contributors/test_models.py`: a second identifier of a type the
  contributor already carries is refused, at validation with a message naming the type and at the
  database by constraint (FR-038, SC-013).
  - **Open — built-without-tests.** Nearest code `fairdm/contrib/contributors/migrations/0007_add_unique_type_constraints.py:13`. The class named for uniqueness contains no uniqueness assertion.
- [ ] T110 [US8] Add `TestDefaultIdentifier` to
  `tests/test_contrib/test_contributors/test_models.py`: a person's expected type is ORCID and an
  organisation's is ROR, and each contributor reports the identifier of its expected type as its
  default, returning nothing when it carries none (FR-039, SC-013).
  - **Open — built-without-tests.** Nearest code `fairdm/contrib/contributors/models.py:240`. Nothing calls the default-identifier accessor.
### Implementation

- [ ] ~~T111~~ [US8] Add the identifier resolver lookup to
  `fairdm/contrib/contributors/choices.py`, mapping each identifier type to its resolver root URL —
  this is the mapping `fairdm.core.abstract.AbstractIdentifier.get_root_url()` imports, so the core
  identifier records depend on it existing.
  - **Struck.** No requirement asks for it and the mapping already exists. Not built, not counted (design review SPEC-002).
- [X] T112 [US8] Define `ContributorIdentifier` in `fairdm/contrib/contributors/models.py` with a
  foreign key to `Contributor`, a type drawn from the framework identifier vocabulary
  (`FairDMIdentifiers`, `fairdm/core/vocabularies.py`) and an indexed value (FR-037, Article IX).
  - **Reconciled done.** Code `fairdm/contrib/contributors/models.py:1200` · test `tests/test_contrib/test_contributors/test_models.py:391 TestContributorIdentifierVocabulary::test_available_types_are_the_union_of_person_and_organization_types`
- [ ] T113 [US8] Add the contributor-and-type `UniqueConstraint` to
  `ContributorIdentifier.Meta` and the matching `clean()` message naming the type, in
  `fairdm/contrib/contributors/models.py` (FR-038).
  - **Open — partial.** Nearest code `fairdm/core/abstract.py:334`. The constraint is inherited; no clean() message names the type.
- [ ] T114 [US8] Declare the expected identifier type on each concrete contributor — ORCID on
  `Person`, ROR on `Organization` — and add the default-identifier accessor to `Contributor`, in
  `fairdm/contrib/contributors/models.py` (FR-039).
  - **Open — built-without-tests.** Nearest code `fairdm/contrib/contributors/models.py:519`. The tests assert the constants, never the accessor.
- [ ] T115 [US8] Add
  `fairdm/contrib/contributors/migrations/0008_create_contributor_identifier.py` creating the
  identifier table and its uniqueness constraint.
  - **Open — built-without-tests.** Nearest code `fairdm/contrib/contributors/migrations/0001_initial.py:381`. No test inserts a duplicate type to prove the constraint bites.
- [ ] T116 [US8] Add `ContributorIdentifierFactory` to `fairdm/factories/contributors.py`, using
  `factory.Sequence` on the value because it is uniqueness-guarded (Article X).
  - **Open — never-built.** No identifier factory.
- [ ] T117 [US8] Document external identifiers in `docs/data_models/contributors.md` — the record,
  one per type, and the default type per kind — noting that fetching and refreshing their contents
  belongs to the external identifier synchronisation specification (Articles VI and XVII).
  - **Open — never-built.** The identifier documentation page does not exist.
---

## Phase 10: US9 — Ask questions about contributors

Covers FR-040 to FR-042 and SC-014.

### Tests

- [ ] T118 [US9] Add a `contributor_population` fixture to
  `tests/test_contrib/test_contributors/conftest.py` covering every case these queries distinguish:
  a superuser, the anonymous placeholder, one person in each of the four account states, current
  and ended memberships, and credits under several roles (SC-014).
  - **Open — never-built.** No shared population fixture.
- [ ] T119 [US9] Add `TestRealContributors` to
  `tests/test_contrib/test_contributors/test_managers.py`: the real-contributors query excludes
  superusers and the anonymous placeholder and keeps everyone else (FR-041, SC-014).
  - **Open — never-built.**
- [ ] T120 [US9] Add `TestActiveAccounts` to
  `tests/test_contrib/test_contributors/test_managers.py`: the active-accounts query returns only
  active people (FR-041, SC-014).
  - **Open — never-built.**
- [ ] T121 [US9] Add `TestQuerysetManagerParity` to
  `tests/test_contrib/test_contributors/test_managers.py`: every query named in FR-041 and FR-042
  is reachable both from the queryset and from the manager and returns the same rows from each
  (FR-040, SC-014).
  - **Open — never-built.**
### Implementation

- [ ] T122 [US9] Add the real-contributors filter to `PersonQuerySet` in
  `fairdm/contrib/contributors/managers.py`, excluding superusers and the anonymous placeholder
  (FR-041).
  - **Open — built-without-tests.** Nearest code `fairdm/contrib/contributors/managers.py:109`. Real() is called by no test.
- [ ] T123 [US9] Add the active-accounts filter to `PersonQuerySet` in
  `fairdm/contrib/contributors/managers.py` (FR-041).
  - **Open — built-without-tests.** Nearest code `fairdm/contrib/contributors/managers.py:120`.
- [ ] T124 [US9] Sweep `fairdm/contrib/contributors/managers.py` and
  `fairdm/contrib/contributors/models.py` so that every query in FR-041 and FR-042 is defined once
  on its queryset and reaches the manager through `Manager.from_queryset`, matching the pattern
  `fairdm/core/dataset/models.py` uses, with no manager-side reimplementation left behind (FR-040). `AffiliationQuerySet.primary()` (`managers.py:180`) returns `.first()` rather than a queryset, so it cannot be composed as it stands.
  - **Open — built-differently.** Nearest code `fairdm/contrib/contributors/managers.py:76`. Twelve hand-written forwarding methods across three managers; from_queryset appears nowhere.
- [ ] T125 [US9] Document the manager and queryset API in
  `docs/portal-development/contributors.md`, one minimal working example per query, describing each
  in testable terms — what goes in, what comes back, what is excluded (Articles VI and XVII).
  - **Open — partial.** Nearest code `docs/portal-development/contributors.md:60`. Documents real() as excluding ghosts, which is not what it does.
---

## Phase 11: US10 — Administer contributors

Covers FR-043 to FR-046 and SC-015.

### Tests

- [ ] T126 [US10] Add `TestPersonAdmin` to
  `tests/test_contrib/test_contributors/test_admin.py`: the person change form's fieldsets present
  account fields and profile fields together, and no separate account model is registered in the
  admin site (FR-043, SC-015).
  - **Open — never-built.** Nothing inspects the admin fieldsets or the site registry.
- [ ] T127 [US10] Add `TestOrganizationAdminInlines` to
  `tests/test_contrib/test_contributors/test_admin.py`: the organisation change form carries an
  editable member inline and a sub-organisation inline, asserted by the presence of the inline
  classes themselves rather than by any field name appearing in the rendered page (FR-044, SC-015).
  - **Open — built-differently.** The existing test passes off the ordinary parent form field.
- [ ] T128 [US10] Add `TestClaimStatusFilter` to
  `tests/test_contrib/test_contributors/test_admin.py`: the claim-status filter derives from the
  stored claim value and agrees, for all four states, with the state each record reports (FR-045,
  SC-015).
  - **Open — partial.** The filter under test keys on the email address rather than the stored claim value.
- [ ] T129 [US10] Add `TestOwnershipTransferAction` to
  `tests/test_contrib/test_contributors/test_admin.py`: the ownership transfer action performs the
  transfer rather than returning a message describing how to do it by hand (FR-046, SC-015).
  - **Open — never-built.**
- [ ] T130 [US10] Add `TestContributorAdminSmoke` to
  `tests/test_contrib/test_contributors/test_admin.py`: the changelist, add and change views of
  every model the app registers return the expected status for a superuser (Article I).
  - **Open — partial.** No add view is ever requested.
### Implementation

- [ ] T131 [US10] Add `PersonAdmin` to `fairdm/contrib/contributors/admin.py` with fieldsets that
  merge account fields and profile fields into one screen, the public identifier and timestamps
  read-only, search on name, email and public identifier, and list display reporting the account
  state (FR-043).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/admin.py:92`. The public identifier and timestamps are not read-only; search is on the wrong key.
- [ ] T132 [US10] Add the membership inline (editable, keyed on the organisation) and the
  sub-organisation inline to `fairdm/contrib/contributors/admin.py` (FR-044).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/admin.py:69`. No sub-organisation inline; the only candidate is commented out.
- [ ] T133 [US10] Add `OrganizationAdmin` to `fairdm/contrib/contributors/admin.py` registering both
  inlines, with fieldsets, list filters on type and country, and the read-only public identifier
  (FR-044).
  - **Open — partial.** Nearest code `fairdm/contrib/contributors/admin.py:363`. No fieldsets, no list filters, no read-only identifier.
- [ ] T134 [US10] Add the claim-status `SimpleListFilter` to
  `fairdm/contrib/contributors/admin.py`, built on the stored claim value and the same precedence
  `Person.account_state` uses, and attach it to `PersonAdmin.list_filter` (FR-045).
  - **Open — built-differently.** Nearest code `fairdm/contrib/contributors/admin.py:23`. Filters on the email address and offers two lookups rather than four states.
- [ ] T135 [US10] Add the ownership transfer admin action to
  `fairdm/contrib/contributors/admin.py`, calling `Organization.transfer_ownership()` and reporting
  the outcome through `django.contrib.messages` (FR-046). Preserve the existing object-level check `request.user.has_perm("contributors.manage_organization", org)` (`admin.py:451`) before the transfer runs — without it any account holding the model-level change permission could transfer any organisation (design review SEC-001).
  - **Open — built-differently.** Nearest code `fairdm/contrib/contributors/admin.py:425`. The action emits an instruction and performs no transfer.
- [ ] T136 [US10] Add `AffiliationAdmin` to `fairdm/contrib/contributors/admin.py`, with
  autocomplete on its person and organisation relations (US10). No requirement asks for a credit or
  an identifier screen, and a credit screen would add a bulk-delete surface reaching the gap T102
  closes (design review SPEC-002).
  - **Open — never-built.** No administrative entry for affiliations, credits or identifiers.
- [ ] T137 [US10] Document the administrative screens in
  `docs/portal-administration/managing_contributors.md` — what each screen presents, the
  claim-status filter, the member and sub-organisation lists, and the ownership transfer action
  (Articles VI and XVII).
  - **Open — partial.** Nearest code `docs/portal-administration/managing_contributors.md:122`. Documents screens that do not exist.
---

## Phase 12: Cross-cutting completion

- [ ] T138 [SETUP] Add `tests/test_factories/test_contributors.py` asserting that every factory in
  `fairdm/factories/contributors.py` produces an instance that passes `full_clean()`, and that
  `create_batch` stays unique where a field is uniqueness-guarded (Article X).
  - **Open — partial.** Nearest code `tests/test_factories/test_contributors.py:21`. Never calls full_clean; three factories untouched.
- [ ] T139 [SETUP] Consolidate the branch's migrations into a single
  `fairdm/contrib/contributors/migrations/0001_initial.py`, deleting the intermediate files, since
  they are branch-local and unapplied (Article IX).
  - **Open — never-built.** Nineteen migrations remain unsquashed.
- [ ] T140 [SETUP] Run `python manage.py makemigrations --check --dry-run` across all apps and
  `python manage.py check`, and fix whatever they report — the swapped user model and the generic
  relations from the core apps are the likely sources of drift.
  - **Open — never-built.**
- [ ] T141 [SETUP] Add the feature's entry to `CHANGELOG.md`, naming every public name the app
  introduces (quality bar, Article VI).
  - **Open — never-built.** No changelog entry.
- [ ] T142 [SETUP] Build the documentation (`docs/`) and fix any warning the new pages raise, and
  confirm every public name introduced by this feature appears in
  `docs/data_models/contributors.md`, `docs/portal-development/contributors.md`,
  `docs/portal-administration/managing_contributors.md` or
  `docs/portal-administration/managing-unclaimed-profiles.md` (Articles VI and XVII).
  - **Open — partial.** The data-model page does not exist and two others document names not in the code.
- [ ] T143 [SETUP] Run the whole suite (`pytest`) and the app's own module
  (`pytest tests/test_contrib/test_contributors`), and confirm the coverage floors in `codecov.yml`
  are met for the new package (Article I, quality bar).
  - **Open — partial.** Coverage floors cannot be met while the manager and admin surfaces are untested.
---

## Dependencies

- **Phase 1 (Setup) blocks every other phase.** Nothing can be imported until the app package
  exists (T001), is installed (T002) and the account model is swapped in (T003); T003 in particular
  must land before any migration is generated, because Django writes the swappable dependency into
  every migration that touches a person.
- **Phase 2 (US1) blocks Phases 3 to 11.** `Person`, `Organization`, `Affiliation`,
  `Contribution` and `ContributorIdentifier` all hang off the `Contributor` base, and the base's
  migration must precede theirs.
- **Phase 3 (US2) blocks Phases 4, 5, 6, 8 and 11.** Account state derives from the person's stored
  fields; memberships, credits and the person admin screen all need the model.
- **Phase 4 (US3) blocks Phase 11.** The claim-status admin filter (T134) reads the stored claim
  flag added in T042 and mirrors the precedence written in T043.
- **Phase 5 (US4) blocks Phases 6, 7 and 11.** Memberships and the organisation admin screen need
  `Organization`; the ownership backend reads it.
- **Phase 6 (US5) blocks Phases 7 and 8.** Ownership is a membership type (T066, T067), and the
  crediting-organisation default (T099) reads the primary membership (T070).
- **Phase 7 (US6) blocks Phase 11.** The transfer action (T135) calls the model method (T085).
- **Phase 8 (US7) blocks Phase 9 only for the shared population fixture** — otherwise US8 is
  independent of it.
- **Phase 10 (US9) depends on Phases 3 to 8**, because the parity test (T121) enumerates every
  query those phases introduce.
- **Phase 12 depends on every earlier phase.** T139 in particular must be the last migration work
  done, and T143 the last thing run.
- **Within every phase, `### Tests` precedes `### Implementation`** (Article I): the test is written
  and watched failing before the code that satisfies it.

---

## Parallel execution

Tasks carrying `[P]` in the same group below touch disjoint files and can run concurrently. Tasks
without `[P]` share a file with a sibling in the same phase — chiefly
`fairdm/contrib/contributors/models.py` and
`tests/test_contrib/test_contributors/test_models.py`, which almost every phase touches — and must
be taken in order.

- **Group A (Phase 1, after T003):** T004, T005, T006. Three different files, no shared imports
  yet.
- **Group B (Phase 2 tests):** T010 alongside the `test_models.py` run T007 → T008 → T009 → T011 →
  T012 → T013.
- **Group C (Phase 3 tests):** T028 alongside the `test_models.py` run T023 → T027.
- **Group D (Phase 4 tests):** T040 alongside the `test_models.py` run T037 → T039.
- **Group E (Phase 5 tests):** T047 alongside the `test_models.py` run T048 → T051.
- **Group F (Phase 5 implementation):** T057 and T058, once T053 has landed.
- **Group G (Phase 6 tests):** T062, T065 and the `test_models.py` run T060 → T061 → T063 → T064,
  all three streams concurrent.
- **Group H (Phase 6 implementation):** T074 and T075, once T067 has landed.
- **Group I (Phase 7 tests):** T081 alongside the `test_permissions.py` run T077 → T080.
- **Group J (Phase 8 tests):** T094, T095 and the `test_models.py` run T088 → T093, all three
  streams concurrent.
- **Group K (Phase 8 implementation):** T105 and T106, once T096 has landed.
- **Group L (documentation):** the documentation task closing each phase — T022, T036, T046, T059,
  T076, T087, T107, T117, T125, T137 — can be deferred and run concurrently with the next phase's
  tests, since each writes a different page. They may not be deferred past T142.

The two phases most nearly independent of each other are **Phase 9 (US8, identifiers)** and
**Phase 7 (US6, ownership)**: identifiers touch neither memberships nor permissions, so once Phase
2 and Phase 5 have landed the two can be built side by side by two people.
