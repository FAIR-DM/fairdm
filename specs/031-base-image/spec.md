# Feature Specification: Publish a FairDM base image that portals build their containers on

**Feature Branch**: `031-base-image`

**Created**: 2026-10-16

**Status**: Draft

**Goals**: G16: a research group with no operations staff can deploy and run its own portal. G7:
development and production settings stay out of a portal's way while remaining configurable where
it matters.

**Roadmap**: R26, a research group can deploy the shipped stack. This is one slice of it: a
container that a portal builds on. The production stack of services, backups, upgrades and the
first-run path stay with the rest of R26.

**Input**: #520. FairDM publishes a base image that a portal builds its containers on, instead of
each portal writing its own Dockerfile from scratch. It carries Python, uv, the system libraries
FairDM needs and the usual start sequence. When FairDM's system requirements change, the image
changes in the same pull request, and a portal picks the change up by moving one version.

## What exists, and what this specification changes

Since #509, FairDM needs PostGIS and the GDAL, GEOS and PROJ libraries wherever Django starts. The
repository has one container definition, `compose/django/Dockerfile`, which builds a local
development image for `docker-compose.yml` and is published nowhere. Every portal writes its own
production and development images from `python:3.13-slim`, and chooses for itself:

- which system packages GeoDjango needs
- how uv is installed
- where the virtual environment lives
- which user the server runs as
- the start command

The GHFDB portal's production image still installs no GDAL, because its Dockerfile was written
when FairDM had no geospatial dependency. Nothing told it otherwise. The deployment guide,
`docs/portal-development/production.md`, describes a `compose/production/django` directory that
does not exist.

An image was once published as `ghcr.io/fair-dm/fairdm:latest`, from a separate repository. That
repository was archived in February 2025 and the image stopped being updated. A portal that built
on it broke, with no warning.

After this feature:

- Each FairDM release publishes two images: a runtime image for production and a development
  image for building and for local work. Both are tagged with the release's version.
- A portal's production Dockerfile installs its dependencies on the development image and runs
  on the runtime image. It installs no system packages of its own.
- The runtime image starts a portal with the usual sequence, and a portal can add its own steps
  to it.
- FairDM's own `docker-compose.yml` runs on the development image.
- A change to FairDM that leaves either image unable to run FairDM fails a check on its pull
  request.
- The deployment guide describes building a portal on the images.

## Boundary

- **The rest of R26**: the production stack of services (web, database, cache, worker, storage),
  backups, upgrades, log access and the first-run path from an empty database.
- **#193**: whether the setup pipeline configured through `django-setup-tools` should run at start.
  The image runs the sequence portals use today. If #193 changes the sequence, the image follows.
- **#525**: GitHub releases for FairDM. This feature tags its images by release and depends on
  releases working.
- **Shared CI workflows for portals**: proposed separately, as a shared workflow repository built
  on these images.
- **Moving an existing portal onto the images**: each portal's own work. That includes the GHFDB
  portal's production database moving to PostGIS.
- **Documentation inside the image**: the FairDM user guide is not shipped in the image.
- **Architectures other than amd64**: added when a portal or contributor needs one.

## Clarifications

### Session 2026-10-16

Each question was answered from the maintainer's replies while the feature was agreed, without
putting it to him again. The longer reasoning is in [decisions.md](decisions.md).

- Q: Does the image contain FairDM itself? → A: No. It contains Python, uv, the system libraries
  and the start sequence. The portal's own lock file installs FairDM, so a portal that pins FairDM
  to a commit can still use the image.
- Q: Are images tagged by commit or by release? → A: By release only. Each release publishes both
  images under its version number, and no tag moves once published. There is no `latest` tag.
  This needs FairDM's GitHub releases to run (#525).
- Q: Which architectures are built? → A: amd64 only.
- Q: Does the default start run the `django-setup-tools` pipeline? → A: No. It runs the sequence
  portals use today: apply migrations, collect static files, compress, then serve. #193 decides
  whether that changes.
- Q: Does a portal's production image need the development image? → A: Yes, as the stage where
  its dependencies are installed. Portals install FairDM and its addons from git, and some
  dependencies compile, so that stage needs git and build tools that the runtime image leaves out.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A portal developer builds their portal's production image on FairDM's images (Priority: P1)

A portal developer writes a short production Dockerfile. It installs the portal's locked
dependencies on the development image, then copies them and the portal's code onto the runtime
image. The container they build applies migrations, collects and compresses static files and
serves the portal. They install no system packages and choose no user, paths or start command.

**Why this priority**: this is the whole point of the feature. Without it every portal keeps
writing and repairing its own image.

**Independent Test**: build a minimal portal on the two images with the Dockerfile from the
deployment guide, start it against a PostGIS database, and request a page.

**Acceptance Scenarios**:

1. **Given** a portal whose Dockerfile installs its locked dependencies on the development image
   and runs on the runtime image of the same release, **When** the developer builds it, **Then**
   the build succeeds without the Dockerfile installing any system package.
2. **Given** that image and a reachable PostGIS database, **When** the container starts, **Then**
   migrations are applied, static files are collected and compressed, and the portal answers HTTP
   requests.
3. **Given** a running container, **When** the portal uses GeoDjango, **Then** GDAL, GEOS and PROJ
   load without any library path being set.
4. **Given** a running container, **When** its processes are inspected, **Then** the server does
   not run as root.
5. **Given** the same image, **When** the developer starts it as a background worker instead of a
   web server, **Then** the worker starts and the web start sequence does not run.
6. **Given** a database that cannot be reached, **When** the container starts, **Then** it exits
   with a failure and never starts the server.
7. **Given** the image, **When** the developer starts it with a different port set in its
   environment, **Then** the server listens on that port without the image being rebuilt.

---

### User Story 2 - A portal developer adds their own steps to the start sequence (Priority: P2)

The GHFDB portal runs `refresh_quality` after migrating and before serving. A portal developer
adds a step like that to the image's start sequence without copying out and restating the steps
the image already runs.

**Why this priority**: most portals will have at least one step of their own. If adding one means
rewriting the start command, they lose the benefit of FairDM keeping that command current.

**Independent Test**: build a portal that adds one management command to the start, start it, and
check that the command ran after migrations and before the server answered.

**Acceptance Scenarios**:

1. **Given** a portal that adds one step to the start sequence, **When** the container starts,
   **Then** the step runs after migrations are applied and before the server starts.
2. **Given** a portal's step that fails, **When** the container starts, **Then** it exits with a
   failure and never starts the server.
3. **Given** a later FairDM release that changes the default steps, **When** the portal moves to
   it, **Then** the portal gets the new default steps and its own step still runs, with no change
   to the portal.

---

### User Story 3 - A developer runs a local development environment on the development image (Priority: P2)

A FairDM contributor runs `docker compose up` in the FairDM repository and gets the development
server on the development image, with the source mounted. A portal developer does the same in
their portal, using the image instead of a development Dockerfile of their own.

**Why this priority**: development and production built from different definitions are where
"works locally, fails in production" library differences come from.

**Independent Test**: start FairDM's `docker-compose.yml`, edit a source file, and see the
development server reload with the change.

**Acceptance Scenarios**:

1. **Given** FairDM's repository, **When** a contributor runs its compose stack, **Then** the
   development server runs on the development image against PostGIS.
2. **Given** the source tree mounted into the container, **When** the server starts, **Then** the
   installed dependencies are still available. The mount does not hide them.
3. **Given** a portal that uses the development image in its own compose file, **When** its
   developer starts it, **Then** the portal's development server runs, and the portal has no
   development Dockerfile of its own.

---

### User Story 4 - A portal developer moves FairDM and its images to a new release together (Priority: P2)

A portal developer moves their portal to a new FairDM release. They change the FairDM version in
their dependencies and the image version in their Dockerfile to the same number. Images for that
number exist as soon as the release is announced.

**Why this priority**: tying FairDM's version to the image's version means a change to FairDM's
system requirements reaches a portal at the moment it upgrades, and never between upgrades.

**Independent Test**: publish a release and pull both images by that release's version number.

**Acceptance Scenarios**:

1. **Given** a published FairDM release, **When** a developer pulls the runtime and development
   images by that release's version, **Then** both exist and anyone can pull them without signing
   in.
2. **Given** a published image tag, **When** later releases are published, **Then** that tag still
   names the same image.
3. **Given** a release whose images fail to build, **When** the release workflow runs, **Then** the
   failure is visible on the release run, and no partly built image is published under that
   version.

---

### User Story 5 - A FairDM contributor learns at review that their change breaks the images (Priority: P2)

A FairDM contributor opens a pull request that needs a new system library, or that changes the
image definition. If either image can no longer run FairDM, a check on their pull request fails
before anyone merges it.

**Why this priority**: the old image stopped working and nobody knew. A broken image has to be
caught where the change is made.

**Independent Test**: open a pull request that removes a library the development image needs, and
see the check fail.

**Acceptance Scenarios**:

1. **Given** a pull request, **When** its checks run, **Then** both images are built from the
   branch and FairDM's test suite runs in the development image.
2. **Given** a pull request that leaves either image unable to run FairDM, **When** its checks run,
   **Then** a check fails.
3. **Given** a pull request, **When** its checks build the images, **Then** nothing is published.

---

### Edge Cases

- **A portal pins FairDM to a commit between releases.** It uses the images of the latest release
  before that commit. This works while the commit has not changed FairDM's system requirements,
  and the deployment guide says so.
- **A portal needs a system library FairDM does not.** It installs the library in its own
  Dockerfile on top of the image. The image does not prevent that.
- **Static files depend on settings injected at runtime.** Collecting and compressing static files
  happens when the container starts, not when it is built.

## Requirements *(mandatory)*

### Functional Requirements

**The runtime image**

- **FR-001**: FairDM MUST publish a runtime image to the GitHub Container Registry under the
  FAIR-DM organisation, pullable by anyone without signing in. *(US1, US4)*
- **FR-002**: The runtime image MUST provide the Python version FairDM supports, uv, and the
  PostgreSQL client library, GDAL, GEOS and PROJ. GeoDjango MUST load in it without any library
  path being set. *(US1)*
- **FR-003**: The runtime image MUST NOT contain FairDM or any portal code. The portal's own
  locked dependencies decide which FairDM it runs. *(US1)*
- **FR-004**: The runtime image MUST run the server as a user other than root, MUST use `/app`
  as the portal's working directory, and MUST keep the virtual environment outside `/app`.
  *(US1, US3)*
- **FR-005**: The runtime image's default start MUST apply migrations, collect static files,
  compress them, then serve the portal with gunicorn. If any step fails, it MUST exit with a
  failure and not start the server. *(US1)*
- **FR-006**: The port the server listens on MUST be changeable without rebuilding the image.
  *(US1)*
- **FR-007**: The same image MUST be able to start a background worker instead of the web server,
  without running the web start sequence. *(US1)*
- **FR-008**: A portal MUST be able to add steps that run after migrations and before the server
  starts, without restating the default steps. A failing step MUST stop the start. *(US2)*

**The development image**

- **FR-009**: FairDM MUST publish a development image that provides everything the runtime image
  does, plus git and the tools needed to build Python packages that compile. A portal's locked
  dependencies, including those installed from git, MUST install in it. *(US1, US3)*
- **FR-010**: The development image MUST be able to run a portal's development server with the
  portal's source mounted at `/app`, and the mount MUST NOT hide the installed dependencies.
  *(US3)*
- **FR-011**: FairDM's own `docker-compose.yml` MUST run its development server and worker on
  the development image, built from the same definition that is published. *(US3)*

**Versions and publishing**

- **FR-012**: Each FairDM release MUST publish both images tagged with the release's version.
  *(US4)*
- **FR-013**: A published tag MUST NOT be moved or reused. FairDM MUST NOT publish a tag that
  follows the newest release. *(US4)*
- **FR-014**: A release whose images fail to build MUST fail visibly and MUST NOT publish a partly
  built image under its version. *(US4)*
- **FR-015**: Images MUST be built for amd64. *(US4)*

**Checks**

- **FR-016**: Every pull request MUST build both images from its branch and run FairDM's test
  suite in the development image. A failure MUST fail a check. *(US5)*
- **FR-017**: Building the images on a pull request MUST NOT publish anything. *(US5)*

**Documentation**

- **FR-018**: The deployment guide MUST describe building a portal's production image on the two
  images, with a complete example Dockerfile, how to add start steps, how to start a worker, and
  how to use the development image for local work. It MUST no longer describe
  `compose/production/django`. *(US1, US2, US3)*
- **FR-019**: The deployment guide MUST say which image version goes with which FairDM version,
  and what a portal pinned to a commit between releases should use. *(US4)*

### Key Entities

- **Base image**: an image FairDM publishes for portals to build their containers on. There are
  two: the runtime image and the development image. Neither contains FairDM.
- **Runtime image**: the base image a portal's production container runs on. It carries what
  FairDM needs at runtime and the start sequence, and no build tools.
- **Development image**: the runtime image plus git and build tools. A portal installs its
  dependencies in it, and developers run a local development server on it.
- **Start sequence**: what the runtime image does when a container starts in its default mode:
  apply migrations, collect and compress static files, run any steps the portal added, then serve.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A portal's production Dockerfile built on the images, as the deployment guide shows
  it, installs no system package.
- **SC-002**: Moving a portal to a new FairDM release changes one image version in its Dockerfile,
  plus the FairDM version in its dependencies and lock file. Nothing else changes.
- **SC-003**: Both images for a release can be pulled within one hour of the release being
  published.
- **SC-004**: A pull request that leaves either image unable to run FairDM's test suite fails a
  check every time.
- **SC-005**: A portal following the deployment guide, starting from an empty database, answers
  requests with no step beyond those the guide lists.

## Assumptions

- The Python version is the floor of FairDM's `requires-python`, which is 3.13 today.
- The images are published to the GitHub Container Registry under the FAIR-DM organisation. The
  archived image name, `ghcr.io/fair-dm/fairdm`, can be reused.
- The database, the cache and object storage are never in the image. Portals run them as separate
  services.
- FairDM's releases are published as GitHub releases (#525). Publishing to PyPI is not needed.

## Breaking changes

- None for portals. A portal adopts the images when it chooses to.
- `compose/django/Dockerfile` is replaced by the image definition, and `docker-compose.yml` is
  changed to use it.
