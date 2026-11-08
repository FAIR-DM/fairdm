# Feature Specification: An operations control room in the administration interface

**Feature Branch**: `035-control-room`

**Created**: 2026-11-08

**Status**: Draft

**Goals**: G16: a research group with no operations staff can deploy and run its own portal. G7:
development and production settings stay out of a portal's way while remaining configurable where
it matters.

**Roadmap**: R26, a research group can deploy the shipped stack. This is the slice that lets the
person running a portal see the state of its supporting services without a shell.

**Input**: Make Django Control Room a default part of FairDM. Every portal gets an operations
dashboard inside its administration interface, showing its Redis instance, its cache and its
background tasks. It is restricted to superusers, it runs inside the portal so no data leaves it,
and the panels meant for developers appear only in development.

## What exists, and what this specification changes

Every FairDM portal depends on Redis, which holds its cache and is the broker and result store for
its Celery background tasks. Scheduled tasks are kept by django-celery-beat and edited in the
administration interface. Errors can be sent to Sentry.

Nothing lets the person running a portal see the live state of those services. Whether the worker
is running, which tasks failed and why, what the cache holds and how much memory Redis uses can
only be found from a shell on the server. A research group with no operations staff may not have
one, or may not know how to use it.

FairDM's administration interface admits holders of a rights-carrying portal role (Portal
Administrator, Data Curator and Community Manager) as well as staff accounts. Those roles manage
records and people. They are not meant to reach the portal's infrastructure.

After this feature:

- Every portal has an operations dashboard in its administration interface, with panels for its
  Redis instance, its cache and its background tasks. The portal writes no configuration to get
  it.
- Only superusers can open the dashboard or any of its panels. Staff accounts and holders of a
  portal role, who can use the rest of the administration interface, cannot.
- In development, the dashboard also offers panels that show the portal's URL routes and its
  signal receivers.
- Nothing on the dashboard sends portal data to any outside service, and the dashboard's
  interface for AI agents stays off.

## Boundary

- **The rest of R26**: the production stack of services, upgrades, log access and the first-run
  path.
- **Other panels**: only the Redis, cache and background-task panels ship for every portal, and
  the URL and signal panels for development. A portal installs any other panel itself.
- **Panels written for FairDM**: none. This feature adopts the published panels as they are.
- **Granting access to anyone but superusers**: a portal that wants to changes the access settings
  itself, through the package's own settings.
- **The AI-agent interface the package offers**: it stays off. A portal that wants it turns it on
  itself.

## Clarifications

### Session 2026-11-08

Each question was answered from the maintainer's request and the reasoning agreed with him before
specifying, without putting it to him again. The longer reasoning is in
[decisions.md](decisions.md).

- Q: Who can open the dashboard? → A: Superusers only. The package's default is any staff
  account, and FairDM's administration interface also admits holders of a rights-carrying portal
  role. The Redis panel can read and delete keys and the background-task panel shows task
  arguments, which may hold personal data, so access is limited to the accounts that already
  control everything else in the portal.
- Q: Which panels are part of every portal? → A: Redis, cache and background tasks, the three
  services every portal already runs. The URL and signal panels describe the code rather than the
  running portal, so they appear only in development.
- Q: Can a portal turn the dashboard off? → A: Yes. A portal that leaves it out of its settings no
  longer has the dashboard, and the rest of the portal is unaffected.
- Q: Can a portal change who has access? → A: Yes, through the package's own settings. A portal's
  values win over FairDM's.
- Q: Where is the dashboard? → A: Inside the administration interface, at whatever address the
  portal gives that interface, so a portal that moves its administration interface moves the
  dashboard with it.
- Q: Does the URL panel send test requests to addresses? → A: No. The package can send a real
  request to an address to show how it answers, which is a request leaving the portal. FairDM turns
  that off and keeps the list of routes.
- Q: Can the Redis panel change or delete keys? → A: No. The package leaves editing, deleting and
  expiry changes off unless a portal turns them on, and FairDM keeps them off. The cache panel's own
  editing stays, for superusers only.
- Q: How does a portal get the URL and signal panels? → A: It adds the two packages to its own
  development dependencies. FairDM does not install them for every portal, because the dashboard
  lists every installed panel and a production portal would then show links to panels it does not
  serve. FairDM's development settings turn them on whenever they are installed.
- Q: What happens when Redis or the worker is down? → A: The dashboard and its panels still open
  and say the service cannot be reached. The rest of the administration interface is unaffected.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A superuser checks the portal's services from the administration interface (Priority: P1)

A superuser running a portal opens the administration interface and goes to the operations
dashboard. From it they open the background-task panel and see whether a worker is running, which
tasks ran, which failed and why. They open the Redis panel to see how much memory it uses and what
keys it holds, and the cache panel to see what the cache holds. They do all of this without a shell
on the server and without any setup in their portal. A Data Curator signed in to the same
administration interface sees no link to the dashboard and cannot open it.

**Why this priority**: this is the feature.

**Independent Test**: start a portal from the documented stack with no control-room settings of
its own. Sign in as a superuser and open the dashboard and each of its three panels. Sign in as a
staff account and as a Data Curator, and check that neither can open the dashboard or any panel.

**Acceptance Scenarios**:

*The dashboard is there by default*

1. **Given** a portal with no control-room settings of its own, **When** a superuser opens the
   administration interface, **Then** it links to the operations dashboard.
2. **Given** the same portal, **When** a superuser opens the dashboard, **Then** it lists the
   Redis, cache and background-task panels, and each one opens.
3. **Given** a portal that gives its administration interface another address, **When** a
   superuser opens the dashboard, **Then** it is reached under that address.

*Only superusers*

4. **Given** a staff account that is not a superuser, **When** it requests the dashboard or any
   panel, **Then** it is refused.
5. **Given** a holder of a rights-carrying portal role who is not a superuser, **When** they
   request the dashboard or any panel, **Then** they are refused.
6. **Given** a visitor who is not signed in, **When** they request the dashboard or any panel,
   **Then** they are sent to the administration sign-in.
7. **Given** a signed-in account that cannot open the dashboard, **When** it views the
   administration interface, **Then** the interface offers no link to the dashboard or its panels.

*Services that cannot be reached*

8. **Given** a portal whose Redis instance cannot be reached, **When** a superuser opens the
   dashboard and the Redis and cache panels, **Then** each page opens and says the service cannot
   be reached, and no server error occurs.
9. **Given** a portal with no background worker running, **When** a superuser opens the
   background-task panel, **Then** it opens and shows no worker.

*Data stays in the portal*

10. **Given** a portal with no control-room settings of its own, **When** an AI-agent client
    requests the package's agent interface, **Then** it is not found.
11. **Given** a portal with no control-room settings of its own, **When** a superuser uses the
    dashboard and its panels, **Then** no request leaves the portal for an outside service.
12. **Given** a portal with no control-room settings of its own, **When** a superuser opens a key
    in the Redis panel, **Then** they can read it, and the panel offers no way to edit it, delete it
    or change its expiry.

*A portal's own choices*

13. **Given** a portal that sets its own control-room access settings, **When** settings resolve,
    **Then** the portal's values win over FairDM's.
14. **Given** a portal that removes the control-room applications from its settings, **When** it
    starts, **Then** it starts normally, the administration interface works, and no dashboard is
    offered.

---

### User Story 2 - A developer inspects a portal's routes and signals while building it (Priority: P2)

A developer building a portal adds the URL and signal panel packages to their development
environment and runs the portal with development settings. Signed in as a superuser, they open the
operations dashboard and find two more panels: one lists every URL route in the portal and the view
each one reaches, and one lists the signal receivers connected in the portal. A production portal
opens neither.

**Why this priority**: it helps the people building portals, but the portal runs without it. It is
P2 because it reuses everything US1 delivers.

**Independent Test**: start the development stack, sign in as a superuser and open both panels
from the dashboard. Start the same portal with production settings and check that neither panel is
offered or reachable.

**Acceptance Scenarios**:

1. **Given** a portal running with development settings and the two panel packages installed,
   **When** a superuser opens the dashboard, **Then** it lists the URL and signal panels along with the three from US1, and both
   open.
2. **Given** a portal running with production settings, **When** a superuser opens the dashboard,
   **Then** it offers no way to open the URL panel or the signal panel, and requests for either are
   not found.
3. **Given** a portal running with development settings, **When** a staff account that is not a
   superuser requests either panel, **Then** it is refused.

---

### Edge Cases

- A portal with an addon that installs a further control-room panel: the panel appears on the
  dashboard, under the portal's access settings.
- A portal that sets the package's access settings itself and leaves out the superuser rule: its
  own settings stand, as FR-008 requires. The documentation says what that opens up.
- A portal that runs without a background worker at all: the background-task panel still opens
  (US1 scenario 9).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every portal MUST offer an operations dashboard inside its administration interface
  with no control-room configuration of its own. (US1)
- **FR-002**: The dashboard MUST offer the Redis, cache and background-task panels in every
  portal. (US1)
- **FR-003**: The dashboard and every panel on it MUST be reachable under the administration
  interface's configured address. (US1)
- **FR-004**: The dashboard and every panel on it MUST be refused to every account that is not an
  active superuser, including staff accounts and holders of rights-carrying portal roles. (US1)
- **FR-005**: The administration interface MUST NOT offer a link to the dashboard or its panels to
  an account that cannot open them. (US1)
- **FR-006**: The dashboard and its panels MUST open, and say so, when Redis or the background
  worker cannot be reached. (US1)
- **FR-007**: The package's AI-agent interface MUST be off in every portal that does not turn it on
  itself, and nothing FairDM configures for the dashboard may send portal data to an outside
  service. (US1)
- **FR-008**: A portal's own control-room settings MUST win over FairDM's. (US1)
- **FR-014**: The Redis panel MUST NOT offer editing, deleting or changing the expiry of a key
  unless a portal turns that on itself. (US1)
- **FR-009**: A portal that removes the control-room applications MUST start and run normally.
  (US1)
- **FR-010**: With development settings and the two panel packages installed, the dashboard MUST
  also offer the URL and signal panels, under the same access rule as FR-004. FairDM MUST NOT
  install them in a portal's production environment. (US2)
- **FR-011**: With production settings, the URL and signal panels MUST NOT be reachable, and the
  dashboard MUST offer no way to open them. (US2)
- **FR-013**: No panel FairDM enables MAY send a request from the portal to another address, in
  development or production. (US1, US2)
- **FR-012**: The documentation MUST describe the dashboard, who can open it, how a portal changes
  access or removes it, and what turning on the AI-agent interface would expose. (US1)

### Key Entities

None. The feature adds no models of FairDM's own.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A superuser of a newly started portal reaches each of the three default panels from
  the administration interface's front page in two clicks or fewer, with no settings written.
- **SC-002**: Every non-superuser account kind (staff, each rights-carrying portal role, anonymous)
  is refused on the dashboard and on every panel address, in production and in development.
- **SC-003**: With Redis stopped, every dashboard and panel page answers without a server error.
- **SC-004**: A production portal answers "not found" for the URL panel, the signal panel and the
  AI-agent interface.

## Assumptions

- The published Django Control Room packages are used as they are, at versions that support the
  Django and Python versions FairDM supports.
- The administration interface keeps its current address setting, and the dashboard follows it.
