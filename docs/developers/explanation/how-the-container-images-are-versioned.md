# How the container images are versioned

This page explains why the container images FairDM publishes have a version of their own, what that version tells you, how a portal knows which one to use, and why a published tag never changes. It also explains why the images hold no configuration or secrets. It does not give the tags, the contents or the variables of the images, which are in [Container images](../reference/container-images.md), or the steps to build and run a portal on them, which are in [How to deploy a portal in a container](../how-to/deploy-a-portal-in-a-container.md).

## The images change less often than FairDM

The images hold what FairDM needs wherever Django starts: Python, uv, the PostgreSQL client library, and the GDAL, GEOS and PROJ libraries that PostGIS support depends on. They hold no FairDM and no portal code. A portal pins FairDM and its addons in its own lock file, often to a Git commit. An image that carried FairDM would be overwritten by the portal's copy or would conflict with it.

What the images hold changes when the Python version, a system library, uv or the start sequence changes. That happens a few times a year, while FairDM is released far more often. Tagging the images with FairDM's version would publish the same image again under every new number. It would also tie security updates to the days FairDM happens to release. A version of their own means a new tag only when the image changes, and a patch release for security updates at any time. A portal that pins FairDM to a commit stays free to use the newest image.

A portal that wrote its own image would find out about a new system requirement only when something broke. With shared images, a requirement changes in the same pull request as the code that needs it, and FairDM's own tests run in the development image. A change that breaks the image fails review. See [ADR 0034](../../adr/0034-portals-build-on-the-published-base-images.md) and, for the PostGIS requirement, [ADR 0031](../../adr/0031-portals-run-on-postgis.md).

## What the number tells you

An image version has three parts, and FairDM uses them this way:

- A new **major** version changes something a portal may have to adapt to, such as the Python version, a path, the user or the start command.
- A new **minor** version adds something, such as a system library.
- A new **patch** version changes nothing a portal relies on, such as a rebuild that picks up security updates.

The releases and what changed in each are listed on the repository's releases page as `image-v<version>`.

## The FairDM you install chooses the image

A portal does not choose an image version on its own. The FairDM it installs declares the version of the images it is tested on, and the PostGIS tag it is tested against, in its `pyproject.toml`. The portal reads that table at the release or commit it pins and uses the same versions for its tests, its production image and its database. When the portal moves to a newer FairDM, its image and its database move in the same change.

A portal that chose its own image and database could drift from what FairDM was tested on and find out only when something broke in production. With the versions in FairDM, choosing a FairDM version chooses the rest. The table is in `pyproject.toml` because that file exists at every release and every commit a portal can pin, and any workflow can read it with Python's standard library. See [ADR 0036](../../adr/0036-fairdm-declares-the-image-and-database-a-portal-runs-on.md). The keys of the table are in [Container images](../reference/container-images.md#toolfairdmplatform).

## A published tag never moves

There is no `latest` tag, and FairDM never replaces a tag it has published. A portal's image therefore changes only when its own Dockerfile does.

A moving tag fails without warning. An image published as `latest` from a repository that stops being maintained leaves every portal built on it on an image that no longer updates, and nothing tells the portal. A fixed tag makes the version a portal builds on a visible line in its Dockerfile.

If a portal needs an image that cannot change even in the registry, it can write the digest the registry shows into the `FROM` lines of its Dockerfile.

## How a release is made

A maintainer starts the Image Release workflow from the Actions tab and chooses a patch, minor or major bump, or gives an explicit version above the newest one. The workflow works out the version from the existing `image-v<version>` tags, builds both images, and runs a smoke test that starts a demo portal on them against a new database. Nothing is published unless every check passes.

It then publishes the two tags, creates the `image-v<version>` tag and the GitHub release last, and leaves alone any tag the registry already has. A run that stopped part way works out the same version when run again, and pushes only the tags that are missing.

## The images hold no configuration

The images carry no settings and no secrets. A portal's configuration arrives through the container's environment when it starts. Static files are collected at start for the same reason: settings that come from the environment then apply to them.

The portal Dockerfile copies the portal's whole repository into the image, and anyone who can pull the image can read every file in it. A secret kept in a file in the repository would be in the image. Production secrets come from the container's environment at start, and a `.dockerignore` keeps environment files out of the build. [How to deploy a portal in a container](../how-to/deploy-a-portal-in-a-container.md) shows the file.
