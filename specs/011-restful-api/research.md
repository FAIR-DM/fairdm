# Research: 011-restful-api

Written 2026-10-09 against `main` at `ffbfb69f`, which carries django-mvp 0.28 and
django-mvp-accounts 0.2.0.

## The maintainer's planning notes

### Tokens through django-mvp-accounts

**Adopted.** django-mvp-accounts 0.2.0 is installed. Its `api` extra is not, so django-rest-knox
and the token pages are absent today. The package's README gives four steps and this feature takes
all four:

1. Depend on `django-mvp-accounts[api]`, which brings django-rest-knox 5.
2. Add `knox` to `INSTALLED_APPS`. `rest_framework` is already there.
3. Include `mvp_accounts.tokens.urls` at `account/tokens/`.
4. Put `knox.auth.TokenAuthentication` in `DEFAULT_AUTHENTICATION_CLASSES`.

The package adds no system check and no default, so the tests of this feature are what prove the
pages resolve and the API accepts their tokens.

What knox gives over the tokens used until now: several tokens per person, a lifetime chosen when
each is created, storage as a digest, and revoking one at a time. The request header keeps the
form `Authorization: Token <token>`, so the documentation for callers barely changes.

Two knox settings are set here. `TOKEN_LIMIT_PER_USER` is 10, because knox sets no limit and the
package's README tells a project to set one. `AUTO_REFRESH` stays off, so a token ends when the
person said it would.

`dj-rest-auth` and `rest_framework.authtoken` are removed. Nothing else in the code imports
either. The old token table is left in place by Django when the app is removed, and no release
carried it, so no data migration is written.

drf-spectacular does not know knox's authentication class and would warn and leave it out of the
schema. Its documented answer is a small `OpenApiAuthenticationExtension` subclass, which goes in
`fairdm/api/schema.py`.

### orjson as the default renderer

**Already adopted, kept.** `drf-orjson-renderer` has been the default renderer and parser since
the April build (`fairdm/api/settings.py`). Its latest release is 1.8.0 of December 2025 and the
lock holds 1.7.5 or later. The package is a thin wrapper of about two hundred lines over `orjson`,
which is what does the work, so the maintenance risk is small. The browsable renderer stays second
for a person in a browser. Nothing to build. The parser is the reason an unparseable body must be
tested: orjson raises its own error type, which the wrapper turns into a 400.

### Limits, access and paging for a small server

**Decided as follows.**

| | Anonymous | Token or session |
|---|---|---|
| Per minute | 30 | 120 |
| Per day | 2,000 | 20,000 |

Django REST Framework's throttles count in the cache. Production already requires Redis
(`fairdm.E200`), so a single server with several workers counts correctly. A throttle holds one
rate, so each cell is a small subclass with its own scope, and the four rates sit in
`REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]` where an operator already looks.

Paging stays by page number with a total. Cursor paging was considered and not taken: it drops the
total and the page links callers expect, and its gain appears on tables far larger than a
single-server portal holds. The default page is 100 records and the ceiling 1,000, each a setting.
With those, a dataset of ten thousand samples is 100 requests at the default and 10 at the ceiling,
which an anonymous caller completes in under four minutes without meeting the daily limit.

Larger pages make the cost of each record matter, so every list prefetches what its serializer
reads and a test holds the query count level as the page grows.

Access from other websites: `django-cors-headers` is already installed and limited to `/api/`.
Setting `CORS_ALLOW_ALL_ORIGINS = True` and leaving `CORS_ALLOW_CREDENTIALS` off lets any page
read, and write with a token it sends itself. A browser will not hand a response to a
cross-origin page that sent cookies unless credentials are allowed, and Django REST Framework's
session authentication also demands a CSRF token, which another origin cannot read.

## What else the plan needed settled

### Why creating a sample fails

`build_model_serializer` in `fairdm/api/serializers.py` writes a new `Meta` with the type's field
list. A subclass's `Meta.fields` replaces its parent's, so `BaseSampleSerializer`'s common fields
vanish and `dataset` is not a field. The fix is to build the field list as the common fields
followed by the type's own.

### Why measurements have no values

`MeasurementConfig.serializer_fields` in `fairdm/core/measurement/config.py` is a fixed list, and a
component's own list wins over `fields`. Removing it lets the type's `fields` through, as
`BaseSampleConfiguration` already does by declaring only `fields`.

### Two serializer builders

`fairdm/registry/factories.py::SerializerFactory` is what `config.get_serializer_class()` returns
and what the registry documents. `fairdm/api/serializers.py::build_model_serializer` is what the
API calls. The factory becomes the only builder and builds on the API's base serializers, and the
viewset asks the configuration for its serializer.

### Why sorting fails

The generated viewset's queryset is polymorphic. `OrderingFilter` with no `ordering_fields`
inspects the serializer, and the ordering then reaches django-polymorphic's field translation with
a model whose base has no primary key resolved. Each generated endpoint serves exactly one
concrete type, so its queryset has no need to be polymorphic. Using the concrete type's plain
queryset and naming `ordering_fields` removes the failure. This reading is to be confirmed by the
failing test before the fix is written.

### References between records

A `SlugRelatedField` on `uuid` accepts and returns the short identifier. The specification asks for
the address as well, so a small subclass returns `{"uuid": …, "url": …}` and accepts either a bare
identifier or that object. It keeps the queryset narrowing that `CreatorCreditMixin` applies today,
which is what makes an unknown parent and a forbidden one answer alike.

### Metadata read with the record

Descriptions, key dates and identifiers are rows with a `type` and a `value`
(`fairdm/core/abstract.py`). Keywords are controlled-vocabulary concepts and free tags.
Contributors are `Contribution` rows with a contributor, roles and an affiliation. Each gets a
small read-only serializer. They are declared on the base record serializer, so a developer's own
serializer inherits them.

### What stops a delete

Two things, both below the view. Foreign keys with `PROTECT` or `RESTRICT` raise from
`Model.delete()`, which covers a sample with measurements. `Project.delete()` raises
`PublicDatasetsProtect` for a project with a public dataset. The API catches both and answers 409
with the reason. No rule is duplicated.

### Telling a developer at start-up

Django's system checks are the place a framework reports a misconfigured project. One check walks
the registry, builds each type's serializer and compares the model's required fields with the
serializer's writable ones. The router stops catching exceptions around registration, so a type
that fails to build stops the portal with the traceback.

### Packages considered

| Package | Verdict |
|---|---|
| django-rest-knox | Adopted, through django-mvp-accounts' extra |
| dj-rest-auth | Removed |
| djangorestframework-guardian | Removed. Its one use was assigning stored permissions on models other than the four record types, and no such endpoint is generated |
| drf-orjson-renderer | Kept |
| django-cors-headers | Kept |
| drf-spectacular | Kept |
| django-filter | Kept |
