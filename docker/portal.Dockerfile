# A portal's production image, built on the FairDM base images. Build from the portal's root:
#
#   docker build -f Dockerfile --build-arg FAIRDM_IMAGE_VERSION=<image version> -t my-portal .
#
# FAIRDM_IMAGE_VERSION is the version of the base images, which is not FairDM's version. It has no
# default.
ARG FAIRDM_IMAGE=ghcr.io/fair-dm/fairdm
ARG FAIRDM_IMAGE_VERSION

# Install the locked dependencies on the development image, which has git and a compiler.
FROM ${FAIRDM_IMAGE}:${FAIRDM_IMAGE_VERSION}-dev AS build
COPY --chown=fairdm:fairdm pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY --chown=fairdm:fairdm . .
RUN uv sync --locked --no-dev --no-editable

# Run on the runtime image, which has neither.
FROM ${FAIRDM_IMAGE}:${FAIRDM_IMAGE_VERSION}
COPY --from=build /opt/venv /opt/venv
COPY --chown=fairdm:fairdm . /app
