# The FairDM base images. Neither contains FairDM or any portal code: a portal installs its own
# locked dependencies. Build from the repository root.
#
#   docker build -f docker/Dockerfile --target runtime     -t fairdm:runtime .
#   docker build -f docker/Dockerfile --target development -t fairdm:development .

FROM python:3.13-slim AS runtime

ARG VERSION=dev

LABEL org.opencontainers.image.title="FairDM" \
      org.opencontainers.image.description="Base image for portals built on FairDM" \
      org.opencontainers.image.source="https://github.com/FAIR-DM/fairdm" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="${VERSION}"

# GDAL, GEOS and PROJ come with gdal-bin. Debian's ldconfig cache lets Django find them with no
# library path set.
RUN apt-get update \
    && apt-get install --yes --no-install-recommends gdal-bin gnupg libpq5 postgresql-client-17 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 fairdm \
    && useradd --uid 1000 --gid fairdm --create-home fairdm \
    && mkdir -p /app/static /app/media /opt/venv /docker-entrypoint.d /var/lib/fairdm/backups \
    && chown -R fairdm:fairdm /app /opt/venv /var/lib/fairdm

COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /usr/local/bin/uv

# The environment lives outside /app, so a source tree mounted at /app never hides it.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    DJANGO_ENV=production \
    BACKUP_DIR=/var/lib/fairdm/backups \
    DJANGO_SETTINGS_MODULE=config.settings

COPY --chmod=755 docker/entrypoint.sh /usr/local/bin/fairdm-entrypoint

WORKDIR /app
USER fairdm
EXPOSE 8000

ENTRYPOINT ["fairdm-entrypoint"]
CMD ["web"]


FROM runtime AS development

USER root
RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential libpq-dev git \
    && rm -rf /var/lib/apt/lists/*

ENV DJANGO_ENV=development

USER fairdm
