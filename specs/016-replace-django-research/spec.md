# Feature Specification: Controlled vocabularies replace django-research-vocabs

**Feature Branch**: `016-replace-django-research`

**Created**: 2026-08-26

**Status**: Draft

**Serves**: G1, G17

**Roadmap**: —

**Input**: User description: "Replace django-research-vocabs with django-controlled-vocabularies as the controlled-vocabulary layer, splitting the six vocabulary-backed surfaces by what they actually are: sample status, description type, date type and identifier type become closed, self-documenting choice sets that FairDM defines and portals cannot extend; keywords and contribution roles become concept references backed by django-controlled-vocabularies."

## Context

FairDM records six kinds of controlled term: a sample's status, a description's type, a date's type, an identifier's type, a contribution's roles, and a record's keywords. All six are held today by a vocabulary library that declares vocabularies as Python classes and mirrors them into database rows.

Two things drove this feature. The library was written to solve a real problem — a plain choice field carries a stored value and a display label and nothing else, which is not enough for research metadata, where a reader needs to know what a term actually means. And a second, later need appeared that the library does not serve: research teams want to curate their own vocabularies as the science moves, without a developer editing Python and cutting a release.

Those two needs pull in opposite directions, and the six surfaces divide cleanly between them.

- **Four are closed.** Sample status, description type, date type and identifier type are enumerations of FairDM's own metadata model. They change when FairDM cuts a release, nobody curates them, and a portal adding a sixth sample status would break the interoperability the framework exists to provide. What they need is definitions, not a database.
- **Two are open.** Contribution roles carry external identity and definitions that people genuinely argue about. Keywords are open by nature and are exactly what a research team wants to manage. Both are already stored as references to concept rows.

This feature moves the two open surfaces onto the controlled-vocabularies package, converts the four closed ones into self-documenting choice sets that carry their definitions in the package, and retires the old library.

## Clarifications

### Session 2026-08-26

- **Q: Does a portal that has not loaded its vocabularies fail to start, or start and warn?**
  A: It starts and warns. Failing would make a fresh install unusable before its first setup step, and the framework's promise is that a new portal works out of the box. The warning is raised through Django's system check framework at the `WARNING` level, names the vocabularies that are missing, and names the command that loads them. Integrated into FR-010 and the acceptance scenarios of US-2 and US-4.

- **Q: Is the load command FairDM's own, or the vocabulary package's import command run with a file path?**
  A: FairDM's own. A portal maintainer should not have to know where inside an installed package the vocabulary files sit, and FairDM may ship more than one file. The command wraps the package's import and defaults to loading every vocabulary FairDM owns. The existing preload hook, which is wired into the framework's always-run setup tooling for the retired library, is removed with it. Integrated into FR-008 and FR-020.

- **Q: Is the keyword-vocabulary setting portal-wide, or declared per record type?**
  A: Portal-wide. The entry it replaces sat under the dataset configuration, but keywords carry the same meaning wherever they appear, no open issue asks for a per-type keyword set, and one list is the simpler thing to explain and to document. Should a record type ever need its own, narrowing a portal-wide list later is additive. Integrated into FR-014.

- **Q: How does the upgrade behave when several recorded terms cannot be resolved?**
  A: It checks everything before it writes anything. A migration that stops at the first unresolved term forces an operator through one run per bad row, on a live database, with no way to see how much work is ahead. Instead the upgrade resolves every recorded term first, and either reports the complete list of failures and makes no change, or proceeds and converts all of them. Integrated into FR-017 and the US-3 and US-4 acceptance scenarios.

- **Q: Where do the definitions for the four closed sets come from?**
  A: From the definitions those terms already carry in the current vocabularies. They were written deliberately and are the reason this layer exists, so the change carries them across rather than reauthoring them. A term whose current definition is missing or empty gets one written as part of this work, because a set that only half explains itself does not satisfy the story. Integrated into FR-002.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Closed metadata terms explain themselves (Priority: P1)

A researcher filling in a sample record sees the status field offering "Stored", and does not know whether that means the sample is in the group's own freezer or lodged with an external repository. Today the interface can only show the label. After this story, every term in the four closed sets carries a definition alongside its label, and the portal can show that definition at the point someone is choosing.

**Why this priority**: It is the original reason these fields stopped being plain choice fields, and it is the half of the feature that touches no vocabulary database at all, so it can be delivered and verified on its own.

**Independent Test**: Ask the framework for the sample status set and confirm each member returns a value, a label and a definition, then render a form for a sample and confirm the definitions reach the template.

**Acceptance Scenarios**:

1. **Given** the sample status set, **When** its members are read, **Then** each one carries a stored value, a human-readable label and a definition.
2. **Given** a sample saved before this change with status "stored", **When** the record is read afterwards, **Then** it still reads "stored" and no migration of stored data was required.
3. **Given** a description, date or identifier type set for any core record type, **When** its members are read, **Then** each one carries a value, a label and a definition on the same terms as sample status.
4. **Given** a portal running in a non-English locale, **When** a label or definition is displayed, **Then** it is passed through the framework's translation machinery rather than being a fixed English string.
5. **Given** a portal author, **When** they attempt to add a member to any of the four sets, **Then** the framework offers no supported route to do so.

---

### User Story 2 - FairDM's vocabularies ship with the package and load into a portal (Priority: P1)

A research group installs FairDM and prepares a new portal. The controlled vocabularies FairDM owns — contribution roles, and any keyword vocabulary the framework provides — arrive with the package as files, and a documented command loads them into the portal's database. Nobody types a concept in by hand, and nobody fetches anything over the network.

**Why this priority**: Both remaining stories depend on the concepts existing. It also stands alone: a portal can load the vocabularies and inspect them before any field references them.

**Independent Test**: Start from an empty database, run migrations and the documented load command, then confirm the expected schemes and concepts are present with their labels and definitions.

**Acceptance Scenarios**:

1. **Given** a fresh install and an empty database, **When** the documented load command is run, **Then** FairDM's vocabularies are present in the database with their concepts, labels and definitions.
2. **Given** the vocabularies have already been loaded, **When** the command is run a second time, **Then** the result is unchanged and no duplicate concepts are created.
3. **Given** a loaded portal, **When** an administrator opens the administration interface, **Then** the vocabularies and their concepts can be inspected.
4. **Given** the vocabulary files in the package, **When** a term's definition is changed and the command is re-run, **Then** the existing concept is updated rather than duplicated, and records referring to it are unaffected.
5. **Given** a portal that has not run the load command, **When** the portal starts, **Then** it starts successfully and raises a warning naming the missing vocabularies and the command that loads them.

---

### User Story 3 - Contribution roles are vocabulary concepts (Priority: P1)

A person is credited on a dataset as a Data Curator. The role they are given is a concept in a curated vocabulary, carrying a definition and an external identifier, rather than a term the framework knows only as a string. Credit recorded before this change still reads the same afterwards.

**Why this priority**: Roles are the surface where a definition carries the most weight, they are already stored as concept references so the move is a conversion rather than a redesign, and credit on a record is the thing a research group is least willing to lose.

**Independent Test**: Record a contribution with two roles, confirm each resolves to a concept with a definition, then run the upgrade against a database populated before the change and confirm every existing contribution keeps the roles it had.

**Acceptance Scenarios**:

1. **Given** a contribution, **When** roles are assigned to it, **Then** each role is a concept drawn from the contribution-roles vocabulary.
2. **Given** a role concept, **When** it is read from a record, **Then** its definition is available for display.
3. **Given** a portal holding contributions recorded before the upgrade, **When** the framework's migrations are applied, **Then** every contribution keeps exactly the roles it had, resolved to the corresponding concepts.
4. **Given** a portal holding one or more role terms that match no concept, **When** the upgrade runs, **Then** it reports every unresolved term at once, converts nothing, and leaves the credit exactly as it was.
5. **Given** a concept that a contribution refers to, **When** deletion of that concept is attempted, **Then** it is refused rather than silently removing the credit.

---

### User Story 4 - Keywords are vocabulary concepts, scoped by the portal (Priority: P2)

A portal declares which vocabularies its keywords are drawn from. A researcher tagging a dataset is offered terms from those vocabularies and no others, so contributor roles and unrelated domain schemes do not appear among the keyword suggestions.

**Why this priority**: Keywords are the surface a research team most wants to curate, but the interface for editing them is being rebuilt separately, so this story delivers the substrate and the scoping rather than the editing experience.

**Independent Test**: Configure a portal with one keyword vocabulary, confirm keyword selection offers only that vocabulary's concepts, then run the upgrade against a populated database and confirm every existing keyword still resolves to the same term.

**Acceptance Scenarios**:

1. **Given** a portal that names one or more keyword vocabularies, **When** keywords are offered for a record, **Then** only concepts from those vocabularies are offered.
2. **Given** a portal that names no keyword vocabularies, **When** the portal starts, **Then** it starts successfully and raises a warning that keyword selection is unscoped, rather than silently offering every concept in the database.
3. **Given** a project, dataset, sample, measurement or the portal's own identity record, **When** keywords are read, **Then** each one is a concept carrying a label and a definition.
4. **Given** a portal holding keywords recorded before the upgrade, **When** the framework's migrations are applied, **Then** every record keeps exactly the keywords it had, resolved to the corresponding concepts, or nothing is converted and every unresolved term is reported at once.
5. **Given** a concept that a record uses as a keyword, **When** deletion of that concept is attempted, **Then** it is refused rather than silently untagging the record.

---

### User Story 5 - The retired vocabulary library is gone (Priority: P2)

A developer reading FairDM finds one vocabulary layer, not two. The old library is not installed, not imported, not referenced in settings or templates, and the documentation describes what actually ships.

**Why this priority**: It is the point of the feature, but it can only complete once every surface has moved, so it is sequenced last rather than valued least.

**Independent Test**: Search the package for any reference to the retired library and find none, then install FairDM into a clean environment and confirm the library is absent from the resolved dependency set.

**Acceptance Scenarios**:

1. **Given** the package's dependency declarations, **When** they are resolved, **Then** the retired library is absent and the dependency check passes with no unused, missing or transitively-relied-upon dependency.
2. **Given** the framework's settings, **When** a portal starts, **Then** the retired library is not among the installed applications.
3. **Given** the package source, **When** it is searched for imports of the retired library, **Then** none is found, including the class retained solely to keep an old migration importable.
4. **Given** the framework's migrations, **When** they are applied from empty, **Then** they complete without the retired library installed.
5. **Given** the documentation, **When** the pages describing the vocabulary layer are read, **Then** every named field, setting and command exists and every example runs against the current code.
6. **Given** an existing portal, **When** its maintainer follows the upgrade guide, **Then** the steps are sufficient to move that portal without further instruction.

---

### Edge Cases

- A portal upgrades before loading the vocabularies. The upgrade needs concepts to resolve existing terms against, so it reports that the vocabularies are missing and converts nothing.
- Terms stored before the upgrade have no matching concept — typos, hand-edited rows, or vocabulary terms removed since. The upgrade reports all of them together and converts nothing, because guessing which concept was meant would silently rewrite research credit, and stopping at the first would make an operator discover the rest one run at a time against a live database.
- Two vocabularies contain a concept with the same label. Resolution during migration must be scoped to the vocabulary the field draws from, not matched on label across the whole table.
- A record's keywords were drawn from a vocabulary the portal no longer names in its configuration. Existing keywords stay on the record and remain readable; only what is newly offered is narrowed.
- A concept is deleted while records still refer to it. Refused, not cascaded.
- The four closed sets and the two vocabularies share no storage, so a portal that never loads a vocabulary still gets working sample statuses and metadata types.

## Requirements *(mandatory)*

### Functional Requirements

**Closed metadata sets**

- **FR-001**: Sample status, description type, date type and identifier type MUST be closed sets defined by the framework, with no supported route for a portal to add, remove or redefine a member.
- **FR-002**: Every member of those sets MUST carry a stored value, a human-readable label and a definition. Definitions MUST be carried across from the text those terms hold in the current vocabularies; where a term has none today, one MUST be written as part of this change.
- **FR-003**: Labels and definitions MUST be translatable through the framework's existing translation machinery.
- **FR-004**: Those sets MUST NOT require a database read to be enumerated or displayed.
- **FR-005**: The values already stored for those four surfaces MUST remain unchanged, so no record's meaning shifts and no data migration is needed for them.
- **FR-006**: A definition MUST be reachable from a template so the portal interface can show it where a term is chosen or displayed.

**FairDM's own vocabularies**

- **FR-007**: The vocabularies FairDM owns MUST ship as files within the package.
- **FR-008**: A portal MUST be able to load them into its database through a single documented command supplied by FairDM, defaulting to every vocabulary FairDM owns, requiring no network access and requiring the maintainer to know no file paths inside the installed package.
- **FR-009**: Running the load more than once MUST produce the same result as running it once, updating existing concepts in place rather than duplicating them.
- **FR-010**: A portal whose vocabularies are not loaded MUST start, and MUST raise a startup warning that names the missing vocabularies and the command that loads them. It MUST NOT refuse to start, and MUST NOT present an empty selection with no explanation.
- **FR-011**: An administrator MUST be able to inspect loaded vocabularies and their concepts through the administration interface.

**Roles and keywords**

- **FR-012**: Contribution roles MUST reference concepts held in the portal's vocabulary tables.
- **FR-013**: Record keywords MUST reference concepts held in the portal's vocabulary tables, on projects, datasets, samples, measurements and the portal's identity record alike.
- **FR-014**: A portal MUST be able to declare, once and portal-wide, which vocabularies its keywords are drawn from, and keyword selection MUST offer concepts only from those vocabularies on every record type.
- **FR-015**: Deleting a concept that any record refers to MUST be refused.

**Upgrade**

- **FR-016**: Applying the framework's migrations to a portal populated before this change MUST preserve every recorded keyword and every recorded contribution role, resolved to the corresponding concept.
- **FR-017**: The upgrade MUST resolve every recorded term before it writes anything, and MUST either report the complete list of terms it could not resolve and leave the data untouched, or convert all of them. It MUST NOT drop an unresolved term, guess at one, or stop partway through leaving some records converted and others not.
- **FR-018**: Resolution MUST be scoped to the vocabulary the field draws from, never matched on label across unrelated vocabularies.

**Retirement**

- **FR-019**: The framework MUST NOT depend on, install, import or reference the retired library anywhere in the package, its settings, its templates or its migrations.
- **FR-020**: The class retained solely to keep an earlier migration importable MUST be removed along with the reason it existed, as MUST the preload step the retired library required in the framework's always-run setup tooling.
- **FR-021**: The configuration entry that named keyword vocabularies as import paths to Python classes MUST be replaced by one that names vocabularies directly, and the unused project-level keyword entry MUST be removed.
- **FR-022**: Documentation describing the vocabulary layer MUST match what ships, with every named field, setting and command existing and every example running against the current code.
- **FR-023**: The change MUST ship an upgrade guide with concrete step-by-step instructions, sufficient to move an existing portal without further help.

### Key Entities

- **Concept** — a term in a curated vocabulary, held as a row in the portal's database, carrying a label, a definition and an identity that can be referred to from outside the portal. Used for contribution roles and keywords.
- **Vocabulary** — a named, curated set of concepts. FairDM ships its own; a portal may load others for its domain models.
- **Closed metadata set** — a fixed set of terms defined by the framework in code, each carrying a value, a label and a definition, used for sample status and for description, date and identifier types. Not stored in the database and not extensible by a portal.
- **Contribution role** — the capacity in which a contributor is credited on a record, drawn from a vocabulary.
- **Keyword** — a subject term attached to a record, drawn from the vocabularies the portal names.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every term a researcher can choose for a sample's status, a description's type, a date's type or an identifier's type carries a definition the portal can display, and displaying it costs no database query.
- **SC-002**: A portal starting from an empty database reaches working keyword and role selection by running the documented setup steps alone, with no hand-entered data and no network access.
- **SC-003**: A portal populated before the change keeps one hundred per cent of its recorded keywords and contribution roles across the upgrade, with each resolving to the same term it named before.
- **SC-004**: No file in the package refers to the retired library, and the dependency check passes.
- **SC-005**: Every documented example describing the vocabulary layer runs against the code as shipped.
- **SC-006**: The one existing portal is moved by following the upgrade guide, without instructions that are not in it.

## Out of Scope

- **The keyword editing interface.** Rebuilding how a researcher edits keywords in the portal is a separate feature (#298), which depends on this one. This feature delivers the substrate and the scoping, not the page.
- **Offering roles per record type.** Restricting the roles available on a project to a different set than those available on a sample is a deliverable of the portal-contributions roadmap item (R19). The vocabulary declares those groupings today and nothing enforces them, and that remains true after this feature.
- **Rewriting migration history.** Squashing the framework's existing migrations to remove all trace of the retired library is deliberately not done here, so that an upgrade failure cannot be ambiguous between a history rewrite and a data conversion.
- **Publishing vocabularies at resolvable addresses.** Hosting FairDM's vocabularies so portals fetch them over the network is a later move; this feature ships them in the package.
- **Exporting vocabularies.** Producing vocabulary files back out of a portal is not part of this change.
- **Migrating the existing portal.** The upgrade of the one live portal is carried out in that portal's own repository, against the guide this feature ships.

## Assumptions

- The controlled-vocabularies package provides the field types, the file import and the selection widgets this feature needs. Where it does not — a curator interface, and vocabulary export — those gaps are tracked in that package and are not worked around here.
- The one existing portal is the only consumer of FairDM at this point, so this is a breaking change carried by an upgrade guide rather than by compatibility shims.
- Terms recorded before the change correspond to terms in the shipped vocabularies. Where they do not, stopping is preferable to guessing.
- The four closed sets keep their present members. This feature changes what a member carries, not which members exist.
- A portal's own domain vocabularies are its concern. The framework provides the field types for them and does not curate their content.
