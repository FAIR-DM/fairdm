# Feature Specification: Portal roles and the people who hold them

**Feature Branch**: `017-portal-roles`

**Created**: 2026-09-16

**Status**: Draft

**Goals**: G8 — portal roles and their permissions ship with the framework, so running a portal is
a standard job rather than a bespoke setup. G16 — a research group with no operations staff can
deploy and run its own portal.

**Roadmap**: R15 — portal roles ship with the framework. This feature is the portal-wide half of
it. The per-record half (a record's creator gains rights over what they created, and project or
dataset membership grants rights beneath it) is a separate slice of R15 and is not specified here.

**Input**: Running a portal takes a small team of volunteers, and the framework gives them nothing
to work with. An administrator has to invent their own roles and hand out permissions by hand.
FairDM should arrive with the roles a research portal needs: someone who runs the portal, someone
who looks after the data, someone who looks after the people, and the developers who build and
maintain it. Each role holds the rights its job needs, arrives in every portal without setup, and
survives an accidental deletion in the admin. A page in the portal names who holds which role, so a
visitor can see who is responsible for what and the people who built the portal are credited for
it. Anyone developing on the framework also needs to sign in as each role, so a set of development
accounts ships with FairDM and refuses to load in production.

## Clarifications

### Session 2026-09-16

- Q: Three places in the code decide a person's rights by matching the group name
  `"Data Administrators"`, and the groups shipped in `fairdm/fixtures/groups.json` carry no
  permissions at all. Does this feature keep that arrangement and add to it? → A: No. A portal role
  is a set of permissions, and every decision about what its holder may do is made by asking the
  permission system. Name matching goes. A group whose name confers rights is invisible to every
  other part of the framework and cannot be reasoned about by a portal author.
- Q: What happens when a shipped role is missing from a portal's database? → A: Four answers in
  order. Deleting or renaming one through the administration interface is refused outright, which
  covers the accident that is most likely to happen. Bringing the database up to date installs the
  roles and restores their rights, so a removal that got through some other route is undone. On the
  production baseline a portal whose roles are missing refuses to start and names them, joining the
  production-critical checks FairDM already refuses to boot on. In development nothing blocks, and
  `check --deploy` reports the same condition on demand. What the refusal must never do is block a
  database that has not been migrated yet, or a new portal could not be built at all.
- Q: A data curator correcting a record for a research team that has got stuck — is that edit shown
  to readers as having been made by a curator rather than by the team? → A: No. It is an ordinary
  edit. The curator is acting on the team's behalf at their request, and a visible curator mark on
  the record would tell a reader something they do not need and cannot act on.
- Q: The portal administrator is described as the person who makes announcements, and the framework
  has no announcement capability of any kind — one unused settings key and nothing behind it. Does
  this feature build one? → A: No. Nothing is granted for a capability that does not exist. When a
  portal-wide announcement feature is built it belongs to this role, and the role's documentation
  says so at that point, not before.
- Q: Do the development accounts belong to the demo application? → A: No. They are distributed with
  FairDM itself so that anyone building a portal on the framework can load them into their own
  development environment. The demo is one consumer of them, not their home.
- Q: `docs/portal-administration/roles.md` documents five roles — Portal Admin, Database Admin,
  Site Content, Literature Manager and Reviewer — that have never existed in any version of the
  code. Is that page amended? → A: It is replaced. The page is the administrator's reference for
  what each role can do, and this feature is what first makes it true.
- Q: Should a reviewer role ship, for the checked publication process? → A: No. There is nothing to
  review until that process exists, which is R22's work. A role that grants nothing and names no
  job teaches an administrator the wrong thing about the set.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The roles a portal needs arrive with the framework (Priority: P1)

A research group installs FairDM and brings up a portal. Four portal roles are already there, each
one a job somebody on the team does, with the rights that job needs already attached. Nobody
invents a role, writes down a permission list, or ticks boxes on a form to get to a working
starting point. A portal that has been running since before this feature gains the same four roles
the next time it is brought up to date.

**Why this priority**: Every other story in this feature depends on the roles existing. On its own
it already removes the setup work that R15 exists to remove.

**Independent Test**: From an empty database, bring it up to date and read back the four roles and
the rights each holds. Repeat on a database created before this feature and confirm the same result.

**Acceptance Scenarios**:

1. **Given** an empty database, **When** it is brought up to date, **Then** the Portal
   Administrator, Data Curator, Community Manager and Developer roles exist, and the first three
   hold the rights this specification lists for them.
2. **Given** a portal whose roles are already installed, **When** it is brought up to date again,
   **Then** nothing changes and no duplicate role appears.
3. **Given** a portal created before this feature, holding data and people, **When** it is brought
   up to date, **Then** the four roles appear and no existing person's rights are reduced.
4. **Given** a shipped role whose rights have been edited in the administration interface, **When**
   the portal is brought up to date, **Then** the rights this feature defines are restored.
5. **Given** a shipped role with people in it, **When** the portal is brought up to date, **Then**
   the people in it are exactly the people who were in it before.

---

### User Story 2 - A role decides what its holder can actually do (Priority: P1)

A portal administrator puts a volunteer into the Data Curator role. From that moment the volunteer
can reach the administration interface, see every project, dataset, sample and measurement in the
portal including private ones, and correct any of them on behalf of a research team that has got
stuck. Putting somebody into the Community Manager role instead gives them the people side:
accounts, unclaimed and duplicate profiles, organisations and the merges that go with them, and
nothing over the research records. The Developer role gives nothing at all, and a person holding
only that role has no more access than any other signed-in contributor.

**Why this priority**: A role that does not decide anything is a label. This is the story that
makes the set real, and it is where the group-name matching in the current code is removed.

**Independent Test**: Sign in as one holder of each role and confirm, surface by surface, that the
holder can do what their role covers and is refused what it does not.

**Acceptance Scenarios**:

1. **Given** a person in the Data Curator role, **When** they open the administration interface,
   **Then** they reach it, and they can view and change any project, dataset, sample or measurement
   in the portal regardless of who created it or whether it is private.
2. **Given** a person in the Community Manager role, **When** they open the administration
   interface, **Then** they can view and change person and organisation records and act on profile
   claims and merges, and they cannot change a project, dataset, sample or measurement.
3. **Given** a person in the Portal Administrator role, **When** they open the administration
   interface, **Then** they can change the portal's identity and can add a person to, or remove a
   person from, any portal role.
4. **Given** a person in the Developer role and no other, **When** they attempt to reach the
   administration interface, **Then** they are refused, and their rights over records are those of
   any signed-in contributor.
5. **Given** a person in both the Data Curator and Community Manager roles, **When** their rights
   are assessed, **Then** they hold everything either role holds.
6. **Given** a person removed from every rights-carrying role, **When** they next sign in, **Then**
   the administration interface is closed to them again.
7. **Given** any portal surface that decides whether a person may see or change something, **When**
   it makes that decision, **Then** it asks the permission system, and no surface reaches that
   decision by matching the name of a group.
8. **Given** a data curator who corrects a record belonging to somebody else, **When** a reader
   views that record, **Then** nothing on it marks the correction as a curator's.

---

### User Story 3 - The roles cannot be lost by accident (Priority: P2)

An administrator tidying up the administration interface tries to delete the Data Curator role, or
rename it. The portal refuses and says why. If a role does go missing by some other route, a
production portal will not start with a gap in the set, and the failure names what is missing
instead of leaving the team to work out why curators have stopped being able to curate.

**Why this priority**: The rights are only dependable if the roles are still there. The accident
this guards against is a few clicks away for exactly the person most likely to be clicking.

**Independent Test**: Attempt deletion and renaming of each shipped role through the administration
interface; then remove one behind the portal's back and confirm both the production refusal and the
development report.

**Acceptance Scenarios**:

1. **Given** a shipped role, **When** somebody attempts to delete it through the administration
   interface, **Then** the deletion is refused with an explanation, and the role and its members
   remain.
2. **Given** a shipped role, **When** somebody attempts to rename it through the administration
   interface, **Then** the rename is refused and the name is unchanged.
3. **Given** a role a portal created for itself, **When** somebody deletes or renames it, **Then**
   it is deleted or renamed, because this feature protects only the roles it ships.
4. **Given** a portal on the production baseline whose database is up to date and missing a shipped
   role, **When** it starts, **Then** it refuses to start and the error names every missing role.
5. **Given** the same portal in development, **When** it starts, **Then** it starts, and
   `check --deploy` reports the missing role.
6. **Given** a database that has never been brought up to date, **When** it is brought up to date,
   **Then** the absence of the roles never blocks that from happening.

---

### User Story 4 - Anyone building on the framework can sign in as each role (Priority: P2)

Somebody working on a portal needs to see what a curator sees, then what a community manager sees,
then what an ordinary contributor sees, without creating accounts by hand and without remembering
which password went with which. FairDM distributes five development accounts, one for each role and
one holding none. Their names say what they are, they are ready to sign in with no email to
confirm, and they share one obvious password. They will not load into a portal running on the
production baseline.

**Why this priority**: This is how the rest of the feature gets checked, by its authors and by
every portal developer afterwards. It is not part of the shipped behaviour of a running portal,
which is why it sits below the rights themselves.

**Independent Test**: In a development environment, load the accounts and sign in as each in turn.
On the production baseline, attempt the same load and confirm it fails with nothing created.

**Acceptance Scenarios**:

1. **Given** a development environment with the roles installed, **When** the development accounts
   are loaded, **Then** five accounts exist: Portal Administrator, Data Curator, Community Manager,
   Portal Developer and Regular User, the first four in the matching role and the last in none.
2. **Given** those accounts, **When** somebody signs in as any of them with the password
   `password`, **Then** they are signed in, with no email confirmation step and no account warning.
3. **Given** the accounts are already loaded, **When** they are loaded again, **Then** no duplicate
   account is created.
4. **Given** a portal running on the production baseline, **When** somebody attempts to load the
   development accounts, **Then** the attempt fails, says why, and creates no account.
5. **Given** a portal built on FairDM but not part of it, **When** its developer loads the accounts
   in their own development environment, **Then** it works there exactly as it does for FairDM
   itself.

---

### User Story 5 - A visitor can see who runs the portal (Priority: P3)

Somebody looking at a portal for the first time wants to know who is behind it: who is in charge,
who looks after the data, who to talk to about an account, and who built the thing. A page in the
portal names them, grouped by what they do. The developers are on it alongside everyone else,
because building the portal is part of running it and the people who did it deserve the credit.

**Why this priority**: It is the story that gives the Developer role its purpose, and it is the
only part of the feature a visitor ever sees. It sits last because the roles must exist and mean
something before a page can list them.

**Independent Test**: Put people into roles, open the page as a visitor who is not signed in, and
confirm the right names appear under the right roles.

**Acceptance Scenarios**:

1. **Given** people holding portal roles, **When** a visitor who is not signed in opens the portal
   team page, **Then** they see each role with the people holding it, in the role order this
   specification gives.
2. **Given** that page, **When** a visitor looks for it, **Then** it is reachable from the Community
   group of the main navigation, beside People and Organizations.
3. **Given** a person holding two portal roles, **When** the page is rendered, **Then** they appear
   under each role they hold.
4. **Given** a portal role nobody holds, **When** the page is rendered, **Then** that role is left
   out rather than shown empty.
5. **Given** a person listed on the page, **When** a visitor reads their entry, **Then** they see
   the person's name and can reach their public profile, and no email address is shown.
6. **Given** a person's contribution roles on projects and datasets, **When** the page is rendered,
   **Then** none of them appear on it, because the page is about running the portal and not about
   credit for research records.

---

### Edge Cases

- A shipped role is deleted from a shell or by code rather than through the administration
  interface. Nothing stops it, the portal refuses to start in production until it is restored, and
  bringing the database up to date restores it.
- A person holds three roles. Their rights are everything the three hold together, and the team
  page lists them three times.
- A superuser is unaffected by all of this and continues to hold everything, which is what makes it
  the escape hatch for whoever deploys the portal.
- Somebody is removed from a role while signed in. Their next action is assessed against the rights
  they hold now.
- A portal wants a different split of rights. It creates its own group. The shipped four are not
  the limit of what a portal may define, only what it starts with.
- A person in a rights-carrying role has their account deactivated. A deactivated account holds
  nothing, whatever role it is in.
- The development accounts are loaded into a database where a person already uses one of those
  email addresses. The load fails rather than taking over an existing account.

## Requirements *(mandatory)*

### Functional Requirements

**The role set**

- **FR-001**: FairDM MUST define exactly four portal roles: Portal Administrator, Data Curator,
  Community Manager and Developer.
- **FR-002**: The Portal Administrator role MUST hold the rights to change the portal's identity
  and to add a person to, or remove a person from, any portal role.
- **FR-003**: The Data Curator role MUST hold the rights to view, add, change and delete every
  project, dataset, sample and measurement in the portal, and the records attached to them,
  irrespective of who created them and whether they are private.
- **FR-004**: The Community Manager role MUST hold the rights to view and change person and
  organisation records, to act on profile claims and merges, and to deactivate and reactivate
  accounts. It MUST NOT hold rights over projects, datasets, samples or measurements, and it MUST
  NOT hold the right to delete a person record.
- **FR-005**: The Developer role MUST hold no rights of any kind. Its purpose is to name a person
  as part of the portal's team.
- **FR-006**: Holding any rights-carrying role MUST give access to the administration interface.
  Holding only the Developer role MUST NOT.
- **FR-007**: Where a person holds more than one portal role, their rights MUST be everything those
  roles hold together.
- **FR-008**: Losing the last rights-carrying role MUST close the administration interface to that
  person again.

**Installation and repair**

- **FR-009**: Bringing a portal's database up to date MUST install the four roles and set the
  rights each one holds, on an empty database and on a database that predates this feature alike.
- **FR-010**: FR-009 MUST be repeatable with no further effect: no duplicate roles, no duplicated
  rights.
- **FR-011**: FR-009 MUST restore the rights of a shipped role that have been changed, and MUST NOT
  change which people are in it.
- **FR-012**: Deleting a shipped role through the administration interface MUST be refused, with a
  message naming the role and saying that FairDM requires it.
- **FR-013**: Renaming a shipped role through the administration interface MUST be refused the same
  way.
- **FR-014**: FR-012 and FR-013 MUST apply only to the roles FairDM ships. A group a portal created
  for itself MUST remain deletable and renameable.
- **FR-015**: On the production baseline, a portal whose database is up to date and missing one or
  more shipped roles MUST refuse to start, and the failure MUST name every missing role.
- **FR-016**: FR-015 MUST NOT prevent a database that has not yet been brought up to date from
  being brought up to date.
- **FR-017**: In development the condition in FR-015 MUST NOT stop the portal starting, and MUST be
  reported by the framework's on-demand configuration check.

**How rights are decided**

- **FR-018**: Every decision about what a person may see or change MUST be made through the
  permission system.
- **FR-019**: No portal surface may decide a person's rights by matching the name of a group. The
  three places that do so today MUST be replaced.
- **FR-020**: A portal-wide role's rights MUST be assessed alongside the per-record rights the
  framework already holds, without a right being recorded against every individual record.
- **FR-021**: A change made to a record by a data curator MUST be indistinguishable to a reader from
  a change made by the record's own team.

**Development accounts**

- **FR-022**: FairDM MUST distribute a set of development accounts as part of the package, usable
  by any portal built on it, and not as part of the demo application.
- **FR-023**: The set MUST be five accounts: one in each of the four roles, and one in none.
- **FR-024**: Each account's name MUST say what it is, and its email address MUST follow from that
  name, as listed under *Key entities*.
- **FR-025**: Every development account MUST use the password `password`.
- **FR-026**: Every development account MUST be ready to sign in with: active, email address
  already confirmed, and nothing further to complete.
- **FR-027**: Loading the development accounts MUST fail on the production baseline, say why, and
  create nothing.
- **FR-028**: Loading them twice MUST NOT create a duplicate account.
- **FR-029**: Loading them MUST fail rather than take over an account when one of the email
  addresses already belongs to somebody.

**The portal team page**

- **FR-030**: The portal MUST have a page listing the people holding each portal role, grouped by
  role, in the order given in FR-001.
- **FR-031**: The page MUST be readable by a visitor who is not signed in.
- **FR-032**: The page MUST be reachable from the Community group of the main navigation.
- **FR-033**: Each person on the page MUST be shown by name with a way to reach their public
  profile, and no email address.
- **FR-034**: A role nobody holds MUST be left off the page.
- **FR-035**: The page MUST show portal roles only, and MUST NOT show contribution roles.

**What this replaces**

- **FR-036**: The shipped roles MUST replace the group names the framework carries today, including
  the fixture in `fairdm/fixtures/groups.json` and the group names declared in the contributors
  application.
- **FR-037**: `docs/portal-administration/roles.md` MUST be rewritten to list the four roles and
  what each one can do, and MUST match what the portal enforces.
- **FR-038**: The administrator documentation MUST say that a superuser is the deployer's account
  and that the Portal Administrator role is the portal job, so that a research group does not hand
  out the former in place of the latter.
- **FR-039**: `CONTEXT.md` MUST define **portal role** and **contribution role** as distinct terms,
  and name the four roles.

### Which story owns which requirement

| Story | Requirements |
|---|---|
| US-1 — the roles arrive with the framework | FR-001, FR-002, FR-003, FR-004, FR-005, FR-009, FR-010, FR-011, FR-036, FR-037, FR-038, FR-039 |
| US-2 — a role decides what its holder can do | FR-006, FR-007, FR-008, FR-018, FR-019, FR-020, FR-021 |
| US-3 — the roles cannot be lost by accident | FR-012, FR-013, FR-014, FR-015, FR-016, FR-017 |
| US-4 — signing in as each role | FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-028, FR-029 |
| US-5 — a visitor can see who runs the portal | FR-030, FR-031, FR-032, FR-033, FR-034, FR-035 |

### Key entities

- **Portal role**: One of the four jobs in running a portal. Holds a set of rights, holds people,
  ships with FairDM, and cannot be removed or renamed through the portal. Distinct from a
  contribution role, which records credit on a record and confers nothing.
- **Role holder**: A person in a portal role. A person may hold several. Holding a role is a
  portal-wide fact, not a fact about any one record.
- **Development accounts**: Five accounts distributed with FairDM for use outside production.

  | First name | Last name | Email | Role |
  |---|---|---|---|
  | Portal | Administrator | portal.administrator@fairdm.org | Portal Administrator |
  | Data | Curator | data.curator@fairdm.org | Data Curator |
  | Community | Manager | community.manager@fairdm.org | Community Manager |
  | Portal | Developer | portal.developer@fairdm.org | Developer |
  | Regular | User | regular.user@fairdm.org | none |

## Success Criteria *(mandatory)*

### Measurable outcomes

- **SC-001**: From an empty database, bringing it up to date leaves all four roles present with
  their rights, and doing it again changes nothing.
- **SC-002**: A portal created before this feature gains all four roles on its next update, with no
  manual step and no change to who is in any group.
- **SC-003**: Every attempt to delete or rename a shipped role through the administration interface
  is refused, and the role survives.
- **SC-004**: A production portal missing a shipped role does not start, and its failure names the
  role. The same portal in development starts, and the on-demand check names the role.
- **SC-005**: Each of the five development accounts signs in with the documented password, and each
  reaches every surface its role covers and is refused every surface it does not.
- **SC-006**: Loading the development accounts on the production baseline fails and creates no
  account.
- **SC-007**: A visitor who is not signed in reaches the portal team page from the main navigation
  and reads who holds each role.
- **SC-008**: No code path in the framework decides a person's rights by matching a group name.
- **SC-009**: Each role's entry in the administrator documentation matches the rights the portal
  actually enforces for it.

## Assumptions

- A portal role is portal-wide. Rights that belong to one record, and the rights a person gets by
  creating a record or joining a project or dataset, are the other half of R15 and are specified
  separately.
- Enforcing private and public visibility is R14's work. A role's rights are honoured wherever the
  framework's permission checks are consulted. A surface that does not yet consult them is R14's
  problem, not a defect in the role set.
- A portal may create its own groups. Nothing here narrows what an administrator can define; it
  sets what they start with.
- Rights attached to a shipped role belong to FairDM and are restored on every update. A portal
  wanting a different split creates its own group rather than editing a shipped one.
- The contact form is out of scope. Where portal mail should go is a separate piece of work.
- No announcement capability exists in the framework, so no right over one is granted.
- A superuser continues to hold everything and is unaffected by this feature.
