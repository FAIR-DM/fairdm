FROM python:3.11-slim-bullseye as builder
ENV POETRY_VERSION=1.8.0

# Install dependencies
RUN apt-get update && apt-get install --no-install-suggests --no-install-recommends && \
    pip install poetry==${POETRY_VERSION} && \
    poetry self add poetry-plugin-bundle

# Copy only poetry.lock and pyproject.toml first to leverage Docker cache
COPY pyproject.toml poetry.lock LICENSE README.md ./
RUN poetry bundle venv $(test "$DJANGO_ENV" == production && echo "--only=main") /venv

# Second stage: Copy application and dependencies to final image
FROM FAIR-DM/fairdm:latest AS run-stage

WORKDIR /app

COPY --from=builder --chown=django:django /venv /venv

# copy application code to WORKDIR
COPY --chown=django:django . /app

