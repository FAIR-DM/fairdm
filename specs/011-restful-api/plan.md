# Plan: The REST API reads and writes complete records

**Specification**: [spec.md](spec.md) · **Research**: [research.md](research.md) ·
**Decisions**: [decisions.md](decisions.md)

## Summary

The API package stays where it is, `fairdm/api/`, and keeps its shape: serializers, viewsets, a
router, permissions, a visibility filter, pagination and settings. The work is to make the
serializers carry the whole record and accept writes, to build them in one place, to swap the
token mechanism, and to set limits. No model changes and no migration of FairDM's own.

## Technical context

- Python 3.13, Django 5.2, Django REST Framework 3.18, drf-spectacular, django-filter.
- New dependency: django-rest-knox 5, through `django-mvp-accounts[api]`.
- Removed dependencies: dj-rest-auth, djangorestframework-guardian.
- Tests: pytest, under `tests/test_api/` mirroring `fairdm/api/`, and `tests/test_registry/` for
  the factory. API tests call the real routes with `APIClient`, never a hand-built viewset.
- Demonstration types in `demo/` are the registered types the tests use.

## Constitution check

| Article | How the plan meets it |
|---|---|
| I, testing | Every story's tests are written and seen to fail first |
| II and III, simplicity and no speculative abstraction | One reference field class, one builder, four throttle subclasses. No new registry, no settings object |
| V, security | Token for a password is removed. Non-disclosure and the FS-022 levels are tested on the real routes |
| VI and XVI, documentation | Each story carries its documentation task |
| VII, dependencies | One added through a package already used, two removed |
| XIII, configuration over plumbing | Every limit and page size is a plain Django setting |
| XIV, production-grade defaults | Limits and paging chosen for one small server |

## Design

### D1. Serializers (`fairdm/api/serializers.py`)

- `RecordReferenceField(SlugRelatedField)`: `slug_field="uuid"`. Returns
  `{"uuid": …, "url": …}`, or null when the caller may not see the record referred to, by the same
  rule the list filter applies. A public dataset can sit in a private project, and a measurement's
  sample can be in another dataset, so a reference must not name what the caller could not open.
  Accepts a bare identifier or that object. `view_name` is given per use.
- Read-only metadata serializers: `DescriptionSerializer`, `DateSerializer`,
  `IdentifierSerializer` (`type`, `value`), `KeywordSerializer`, `ContributionSerializer`
  (contributor reference, roles, affiliation reference).
- `RecordSerializer(CreatorCreditMixin, ModelSerializer)`: declares `url`, `uuid`, `added`,
  `modified` and the five metadata fields, all read-only. Its `get_fields` keeps today's narrowing
  of parent choices.
- `ProjectSerializer`, `DatasetSerializer`: written out, not generated. Dataset carries `project`
  and `license`. Project carries `owner`.
- `BaseSampleSerializer`, `BaseMeasurementSerializer`: subclasses of `RecordSerializer` with a
  `common_fields` tuple each. `polymorphic_ctype` is a database number and is not among them.
- `ContributorSerializer`: read-only, one class for people and organisations with a `type` field,
  carrying what the profile page shows. Never `email`.
- `build_model_serializer` and the cache around it are deleted.

### D2. One builder (`fairdm/registry/factories.py::SerializerFactory`)

Builds `type(f"{Model}Serializer", (base,), …)` where `base` is the sample or measurement base and
`Meta.fields` is `base.common_fields` followed by the resolved field list, without repeats. Parent
fields are `RecordReferenceField`. `MeasurementConfig.serializer_fields` is removed.

### D3. Viewsets (`fairdm/api/viewsets.py`)

- `generate_viewset(config)` sets `serializer_class = config.get_serializer_class()` and checks
  whatever that returns against the sample or measurement base, raising `ImproperlyConfigured`
  when it does not build on it. The check stays here, as today, because a named `serializer_class`
  and an overridden `get_serializer_class` both bypass the factory, and the base is what carries
  the parent narrowing, the creator credit and the manage-level rules. It also sets the concrete
  type's plain queryset with parents selected and metadata prefetched, `filterset_class` from the
  configuration, and `ordering_fields`.
- Every generated list accepts `dataset` by short identifier, and a measurement list also accepts
  `sample`, whatever filters the type declares. Relation filters served by the API match on the
  short identifier and never on a database number.
- `ContributorViewSet` lists what the portal's people and organisation lists show
  (`Person.objects.real()` leaves out superusers and the anonymous account).
- `ProjectViewSet`, `DatasetViewSet` use the written serializers and matching querysets.
- `perform_destroy` turns `ProtectedError`, `RestrictedError` and `PublicDatasetsProtect` (raised by a `pre_delete` receiver) into a
  409 with a reason the API writes for each case, never the exception's own text.
- The catalogues use `reverse()` for addresses, the flattened field list, and the visibility
  filter for counts.

### D4. Start-up reporting (`fairdm/api/checks.py`, `fairdm/api/router.py`)

One system check, registered in the app's `ready()`: for each registered type, a required model
field missing from the serializer's writable fields is an `Error` naming the type and the field.
The router's two `try`/`except` blocks go.

### D5. Tokens and sessions

- `pyproject.toml`: `django-mvp-accounts[api]`. Drop `dj-rest-auth` and
  `djangorestframework-guardian`.
- `fairdm/conf/settings/apps.py`: add `knox`, drop `rest_framework.authtoken` and `dj_rest_auth`.
- `fairdm/conf/urls.py`: `path("account/tokens/", include("mvp_accounts.tokens.urls"))`.
- `fairdm/api/urls.py`: drop the `v1/auth/` include.
- `fairdm/api/settings.py`: authentication classes are knox's token class, then session.
  `REST_KNOX = {"TOKEN_LIMIT_PER_USER": 10, "AUTO_REFRESH": False}`.
  `CORS_ALLOW_ALL_ORIGINS = True`.
- `fairdm/api/schema.py`: the drf-spectacular extension describing knox's header.

### D6. Limits and paging

- `fairdm/api/throttling.py`: `AnonBurstThrottle`, `AnonDailyThrottle`, `UserBurstThrottle`,
  `UserDailyThrottle`, each a two-line subclass with a scope.
- Rates in `DEFAULT_THROTTLE_RATES`: `anon_burst`, `anon_day`, `user_burst`, `user_day`.
- `fairdm/api/pagination.py`: default from `REST_FRAMEWORK["PAGE_SIZE"]` (100), ceiling from
  `FAIRDM_API_MAX_PAGE_SIZE` (1,000).

### D7. Generated documentation

A drf-spectacular postprocessing hook in `fairdm/api/schema.py` appends the live limits and page
sizes to the schema's description, so the text cannot drift from the settings. The static
description loses its numbers and its login instructions. `FAIRDM_API_DOCS_URL` is deleted.

### D8. Order

US-1, US-2, US-3, US-4, US-5, US-6, one after another, each from the previous story's accepted
commit. US-1 lays the serializers every later story stands on.

## What is not rebuilt

The permission class, the visibility filter, the namespace, the documentation routes, the
creator-credit and manage-level rules from FS-022, and the sidebar link exist and are tested.
The task list is written as if they did not, and then reconciled: a task is marked done only where
the code is cited and a passing test covers it.

## Watch items

- The existing write tests build a viewset by hand and send database numbers. They do not prove
  the real routes. Tests for this feature use the routes.
- Tests that assert the old login endpoint, the old page sizes, the old field lists or the docs
  setting describe behaviour this feature replaces. Each is updated in the task that changes the
  behaviour and named in `progress.md`.
- The cause of the sorting failure is a reading. The failing test comes first.
- `fairdm/conf/settings/api.py` imports the API settings by name. A new setting such as
  `REST_KNOX` or `FAIRDM_API_MAX_PAGE_SIZE` reaches Django only when it is listed there.
- `ContributorSerializer` must be checked field by field against what a profile page shows a
  visitor. Anything not shown there stays out.
