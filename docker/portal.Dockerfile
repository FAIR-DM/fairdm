# A portal's production image, built on the FairDM base images. Build from the portal's root:
#
#   docker build -f Dockerfile --build-arg FAIRDM_VERSION=<release> -t my-portal .
#
# FAIRDM_VERSION is the FairDM release the portal depends on. It has no default.
ARG FAIRDM_IMAGE=ghcr.io/fair-dm/fairdm
ARG FAIRDM_VERSION

# Install the locked dependencies on the development image, which has git and a compiler.
FROM ${FAIRDM_IMAGE}:${FAIRDM_VERSION}-dev AS build
COPY --chown=fairdm:fairdm pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY --chown=fairdm:fairdm . .
RUN uv sync --locked --no-dev --no-editable

# Run on the runtime image, which has neither.
FROM ${FAIRDM_IMAGE}:${FAIRDM_VERSION}
COPY --from=build /opt/venv /opt/venv
COPY --chown=fairdm:fairdm . /app
