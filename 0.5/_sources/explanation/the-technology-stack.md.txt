# The technology stack

This page explains what a FairDM portal is built on and why each part is there. It covers the parts FairDM chooses for you. It does not cover the parts it leaves to you, such as the server, the reverse proxy and backups, and it does not list settings, which are on the [settings reference](../developers/reference/settings.md).

FairDM is opinionated about its stack. A fresh portal is meant to be deployable and reproducible with few choices, so the framework fixes the parts that every portal needs and leaves open only the parts that depend on where you host it.

## Python and Django

FairDM is a Django framework. It targets Python 3.13 or later and Django 6.0. Django supplies the models, migrations, admin, forms, authentication and templating that the rest of FairDM builds on. Researchers who already use Python for analysis can read and extend a portal's models without learning a second language.

A portal's data structures are ordinary Django models. FairDM adds base models, a registry and a set of fields for research data, and it does not replace Django's model layer. The choice follows from the aim of letting a community declare its schema in familiar syntax. See [Configuration over code](configuration-over-code.md).

## PostgreSQL with PostGIS

Every portal runs on PostgreSQL with the PostGIS extension, in development, in tests and in production. FairDM uses GeoDjango to store and query locations, so the server or image needs the GDAL, GEOS and PROJ libraries as well.

PostGIS is required because every sample and measurement holds a location, and a portal needs to ask which records lie inside an area or near one another without loading every location into Python. Making PostGIS optional would mean two code paths for every spatial feature, and a portal would find out which one it was on only when a query failed. A production check refuses any other database engine. The reasoning is in [ADR 0031](../adr/0031-portals-run-on-postgis.md).

## Redis and Celery

Redis serves two purposes, both read from a single `REDIS_URL`. It is the cache, and it is the broker and result backend for Celery.

Celery runs work that should not hold up a page. FairDM's own tasks look up and refresh contributor details from ORCID and ROR, and look for duplicate people. A portal can add its own tasks. The container images start a worker with their `worker` command.

In development, a portal with no `REDIS_URL` runs tasks in the web process and keeps caches in memory, so you can work without a Redis server. That setup is for development only, and the configuration checks report it in production. See the [configuration checks](../administrators/reference/configuration-checks.md).

## The interface

The interface is rendered on the server. FairDM builds it on django-mvp, a shared application shell, with Tailwind CSS and daisyUI for styling and Cotton components for reusable template pieces. HTMX provides small enhancements. There is no separate single-page application, and a portal's pages work without custom templates or JavaScript.

This follows from the goal that a researcher who can write a model should not also need to be a frontend developer. The shell, the navigation and the look are the same in every portal unless a portal chooses to change them.

## Authentication

Sign-in uses django-allauth. Email verification is mandatory, and ORCID sign-in is configured by default. A portal can add other providers.

## The REST API

The API is built on Django REST Framework, with a generated schema and interactive documentation from drf-spectacular. It covers the core records and every registered sample and measurement type. See the [REST API reference](../developers/reference/rest-api.md).

## Static and media files

Static files are collected with `collectstatic` and served by WhiteNoise, with no extra web server for assets. FairDM does not bundle or minify them with django-compressor. A portal that wants django-compressor installs it and adds its own start step. The reasoning is in [ADR 0035](../adr/0035-fairdm-does-not-compress-static-files.md).

Uploaded files are stored on the local filesystem by default. When an access key, a secret key and a bucket name are all set, they go to S3 object storage instead.

## Container images and the platform

FairDM publishes two base images, a runtime image and a development image, that carry Python, the system libraries PostGIS needs and the start sequence. They contain neither FairDM nor your portal. A portal installs its own locked dependencies on the development image and runs on the runtime image. The runtime image applies migrations, collects static files, runs any start steps you add and starts gunicorn. See [ADR 0034](../adr/0034-portals-build-on-the-published-base-images.md) and [Container images](../developers/reference/container-images.md).

FairDM records the image version and the PostGIS version it was tested on in its own `pyproject.toml`. A portal runs on the versions declared by the FairDM it installs, so choosing a FairDM version chooses the platform with it. See [ADR 0036](../adr/0036-fairdm-declares-the-image-and-database-a-portal-runs-on.md).

## Configuration through the environment

Deployment-specific values such as the database address, the secret key, the Redis address and the allowed hosts come from environment variables, read with django-environ. This keeps secrets and per-server values out of the code and lets one image run in development, testing and production. See [How FairDM configures a portal](how-fairdm-configures-a-portal.md).

## Error tracking

Sentry starts when a `SENTRY_DSN` is present in the environment. Without it, nothing is sent anywhere.

## What FairDM leaves to you

FairDM fixes the application and its platform. It does not choose:

- the reverse proxy or the way TLS is terminated in front of gunicorn
- how the database and uploaded files are backed up
- how you monitor the server and the containers

These depend on your institution's policies and hosting, and nothing in the images assumes one choice.
