# Implementation Plan: people, organizations and a record's credits can be read through the API

**Branch**: `029-people-organizations-api` | **Date**: 2026-10-12 | **Spec**: [spec.md](spec.md)

**Input**: [spec.md](spec.md), [research.md](research.md), [planning-notes.md](planning-notes.md)

## Summary

Replace the mixed contributors endpoint with a people endpoint and an organizations endpoint, each
with a list serializer and a fuller record serializer. Rewrite the credit a record returns so it
carries what DataCite asks of a creator. Add a `contributor` filter to the project and dataset
lists. Everything is read-only, there is no migration and no new dependency.

## Technical context

- Python 3.13, Django 5.2, Django REST Framework, django-filter, drf-spectacular, django-polymorphic
- Tests: pytest with `APIClient` against the real routes, in `tests/test_api/`
- Constraint: the query ceilings of FS-011 hold for every new list and for records with credits

## Constitution check

- Tests are written first and seen to fail (testing standard). No test pins wording.
- Documentation ships in the same pull request, in each story that introduces a public name.
- No compatibility alias is kept for the removed endpoint or serializer.
- No private or leading-underscore names are added.

## Design

### D1. A credit mirrors a DataCite creator

`ContributionSerializer` in `fairdm/api/serializers.py` is rewritten. Its fields:

| Field | Source |
|---|---|
| `uuid`, `url` | The contributor's short identifier and API address. Both `null` for a hidden account |
| `name` | For a person, whatever `get_full_name_display("family_given")` gives: "Family, Given" with both names, the one name when only one is set, the display name when neither is. For an organization, its `name` |
| `type` | `Personal` or `Organizational`, which is DataCite's `nameType` |
| `given_name`, `family_name` | A person's `first_name` and `last_name`. `null` for an organization |
| `name_identifiers` | One entry per identifier: `name_identifier`, `name_identifier_scheme`, `scheme_uri` |
| `affiliation` | One object, or `null` when the credit records no organization: `uuid`, `url`, `name`, `affiliation_identifier`, `affiliation_identifier_scheme`, `scheme_uri` |
| `roles` | `{"name", "label"}` for each role, unchanged |

`NameIdentifierSerializer` and `CreditAffiliationSerializer` are new, both plain read-only
serializers. An affiliation with several identifiers gives its ROR ID where it has one, else its
first.

`RecordSerializer.load_related()` extends the credit prefetch with `contributor__identifiers` and
`affiliation__identifiers`, and annotates each credit with the person's given and family name
through `contributor__person`, which costs no further query. The credit serializer reads the two
annotated values. A credit serialized without the annotation, as in the body that answers a create
or an update, reads the names from the contributor itself. `type` and the typed route come
from `get_real_instance_class()`, which needs no query. A credit whose contributor has been
deleted is left out of the list.

The level a credit grants is not a field, as now.

### D2. People

`PersonListSerializer(serializers.ModelSerializer)`: `url`, `html_url`, `uuid`, `name`,
`given_name`, `family_name`, `identifiers`, `primary_affiliation`. `added` and `modified` are not returned. They stay
available for ordering and for the changed-since filters.

`PersonSerializer(PersonListSerializer)` adds `alternative_names`, `profile`, `links`,
`languages`, `image`, `affiliations`, `projects`, `datasets`.

- `identifiers` uses the existing `ContributorIdentifierSerializer` (`type`, `value`, `link`).
- `primary_affiliation` and each affiliation's `organization` are `{"uuid", "url", "name"}`,
  from a small `OrganizationReferenceSerializer`. The primary affiliation is the organization of the primary
  entry among `get_affiliation_history()["current"]`, so a pending or ended primary affiliation
  gives none. `Person.primary_organization` is not used, because it does not check either.
- `affiliations` comes from `get_affiliation_history()`, current first and then past. Each entry:
  `organization`, `type` (`member`, `admin` or `owner`), `start`, `end`, `is_primary`. Dates are
  given as recorded, as a year, a month or a day.
- `projects` and `datasets` are the addresses of the project and dataset lists narrowed to this
  person.

`PersonViewSet(ReadOnlyModelViewSet)`: queryset `Person.objects.real()` with `identifiers` and
`affiliations__organization` prefetched, `lookup_field = "uuid"`, `AllowAny`,
`get_serializer_class()` returning the list serializer for the list action, ordering on `name`,
`last_name`, `added`, `modified`, `uuid`.

`PersonFilterSet`: `organization` (short identifier, people with a verified affiliation to it that
has not ended) and `identifier`.

### D3. Organizations

`OrganizationListSerializer`: `url`, `html_url`, `uuid`, `name`, `type`, `country`,
`identifiers`. `type` and `country` are given as the stored codes, which are what the filters
take.

`OrganizationSerializer(OrganizationListSerializer)` adds `alternative_names`, `profile`, `city`,
`links`, `image`, `parent_organization`, `sub_organizations`, `members`, `projects`, `datasets`.

- `parent_organization` and `sub_organizations` are `{"uuid", "url", "name"}`.
- `members` is one entry per verified current affiliation: `person` as `{"uuid", "url", "name"}`
  and `type`. Hidden accounts are left out. The members are loaded with one prefetch on the
  viewset, so the query count does not depend on how many there are.

`OrganizationViewSet(ReadOnlyModelViewSet)` mirrors the people viewset over
`Organization.objects`.

`OrganizationFilterSet`: `type`, `country`, `parent_organization` (short identifier), `top_level` (true for
organizations with no parent) and `identifier`.

### D4. Identifier filter

`IdentifierFilter` in `fairdm/api/filters.py`, a `django_filters.CharFilter` subclass used by both
filter sets. It trims the value, strips a known scheme address from the front
(`IdentifierLookup` in `fairdm/contrib/contributors/choices.py`) and matches
`identifiers__value` exactly, and also with its spaces removed, so that the address a credit
gives for an ISNI finds its holder. The people list is `Person.objects.real()`, so an identifier
a hidden account holds finds nobody.

### D5. A contributor's records

`ContributorRecordsFilterSet` in `fairdm/api/filters.py` with one filter, `contributor`, taking a
short identifier. `ProjectViewSet` and `DatasetViewSet` name it as their `filterset_class`. It
resolves the contributor among people the people list shows and all organizations, and narrows
the list to the records that contributor is credited on: `contributor.projects.get_visible()` or
`contributor.datasets.get_visible()`, by primary key. That is credit only, for a person and an
organization alike. A project an organization owns and is not credited on is not returned, because
the specification asks for the records a contributor is credited on. An identifier that
names nobody, or names a hidden account, gives an empty list and not an error, as the
specification asks.

Because `get_visible()` returns public records only, the narrowed list is public only for every
caller, even one who holds a level on a private record.

### D6. Routes, references and removal

- `fairdm/api/router.py` registers `people` (`basename="person"`) and `organizations`
  (`basename="organization"`) and no longer registers `contributors`.
- `RecordReferenceField.route_name()` returns `api:person-detail` or `api:organization-detail`.
- `ContributorSerializer` and `ContributorViewSet` are deleted, with no alias, and the module
  docstring of `fairdm/api/viewsets.py` is corrected.
- `CORE_HEADINGS` in `fairdm/api/schema.py` gains `people` and `organizations` and loses
  `contributors`. The endpoint table in `fairdm/api/settings.py` follows.
- `fairdm/contrib/contributors/plugins/overview.py` builds the API address from the contributor's
  real type.

### D7. Documentation

- `docs/portal-development/restful-api.md`: the endpoint table, the credit shape with its DataCite
  correspondence, a People section and an Organizations section replacing Contributors, the new
  filters, the serializer reference table, and the documentation headings.
- `docs/user-guide/reading-records-with-a-script.md`: the contributors paragraph.
- `specs/011-restful-api/spec.md`: every statement about the contributors endpoint and the shape
  of a credit, edited to read as the API now behaves.

## Story order

US-1 first, because it changes `route_name()` and the credit every record returns, and it carries
the removal of the mixed endpoint together with minimal people and organizations routes so that a
credit's `url` resolves. US-2 and US-3 then fill in the two endpoints. US-4 adds the filter and
the `projects` and `datasets` addresses.

To keep the tree green between stories, US-1 lands `PersonViewSet` and `OrganizationViewSet` with
their list serializers only. US-2 and US-3 add the record serializers, the filters and the
documentation for each.

## Risks

- Twenty existing tests name the old routes. They are rewritten in US-1 against the new ones, and
  none is deleted without its replacement.
