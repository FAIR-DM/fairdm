# REST API

This page describes what the portal's HTTP API serves: its addresses, the shape of each record, the query parameters of a list, who may do what, and the status codes it answers with. It does not list the Python classes behind the API, which are in the [Python API](python-api.md). It does not describe the settings that shape the API, which are in [Settings](settings.md), and it does not teach a script to call it, which the [users' API guides](../../users/api/get-an-api-token.md) do.

The examples use a sample type whose plural name is "plant samples" and which declares the fields `species` and `collected_on`. Your portal's types have their own names and fields.

## Addresses

Every address is under `/api/v1/`. A route name is in the `api` namespace, so it never clashes with a page of the portal such as `project-list`.

| Address | Methods | Route name | Serves |
|---|---|---|---|
| `/api/v1/` | GET | `api:api-root` | Links to every list the portal serves |
| `/api/v1/projects/` | GET, POST | `api:project-list` | Projects |
| `/api/v1/projects/{uuid}/` | GET, PUT, PATCH, DELETE | `api:project-detail` | One project |
| `/api/v1/datasets/` | GET, POST | `api:dataset-list` | Datasets |
| `/api/v1/datasets/{uuid}/` | GET, PUT, PATCH, DELETE | `api:dataset-detail` | One dataset |
| `/api/v1/people/` | GET | `api:person-list` | People |
| `/api/v1/people/{uuid}/` | GET | `api:person-detail` | One person |
| `/api/v1/organizations/` | GET | `api:organization-list` | Organizations |
| `/api/v1/organizations/{uuid}/` | GET | `api:organization-detail` | One organization |
| `/api/v1/samples/{type}/` | GET, POST | `api:samples-{type}-list` | The samples of one registered type |
| `/api/v1/samples/{type}/{uuid}/` | GET, PUT, PATCH, DELETE | `api:samples-{type}-detail` | One sample |
| `/api/v1/measurements/{type}/` | GET, POST | `api:measurements-{type}-list` | The measurements of one registered type |
| `/api/v1/measurements/{type}/{uuid}/` | GET, PUT, PATCH, DELETE | `api:measurements-{type}-detail` | One measurement |
| `/api/v1/schema/` | GET | `api:api-schema` | The OpenAPI 3 schema, as YAML, or as JSON with `?format=json` |
| `/api/v1/docs/` | GET | `api:api-docs` | Swagger UI, drawn from the schema |

- `{uuid}` is the record's short identifier.
- `{type}` is the lower-case plural name of the registered type with spaces replaced by hyphens, such as `plant-samples`. [How to change a type's API address](../how-to/change-a-types-api-address.md) explains where the name comes from.
- Registering a sample or measurement type adds its two addresses. Nothing else is needed.
- HEAD and OPTIONS are answered like GET.
- A request body is JSON, form-encoded or multipart.

## Records

A project, dataset, sample or measurement is returned whole, on its own address and in every row of its list. The two carry the same fields.

| Kind | Fields of its own | Its parent |
|---|---|---|
| Project | `url`, `html_url`, `uuid`, `name`, `image`, `status`, `visibility`, `funding`, `added`, `modified` | `owner`, the organization that owns it |
| Dataset | `url`, `html_url`, `uuid`, `name`, `image`, `visibility`, `published`, `added`, `modified` | `project`, and `license` as `{"name", "url"}` |
| Sample | `url`, `html_url`, `uuid`, `name`, `local_id`, `status`, `location`, `location_uncertainty`, `added`, `modified`, then every field its type declares | `dataset` |
| Measurement | `url`, `html_url`, `uuid`, `name`, `location`, `location_uncertainty`, `added`, `modified`, then every field its type declares, measured values included | `sample` and `dataset` |

`url` is the record's address in the API. `html_url` is the absolute address of the record's page on the portal. Without a request to build an address from, `html_url` is the path alone. A person and an organization carry both as well.

`visibility` and a project's `status` are stored numbers.

| Field | Value | Meaning |
|---|---|---|
| `visibility` | `0` | Private |
| `visibility` | `1` | Public |
| `status` | `0` to `4` | Concept, Planning, In progress, Complete, Searching for collaborators |

Every record also carries its metadata, which is read-only.

| Field | Holds |
|---|---|
| `descriptions` | `{"type", "value"}` for each description |
| `dates` | `{"type", "value"}` for each key date, as a year, a month or a day |
| `identifiers` | `{"type", "value"}` for each external identifier, such as a DOI |
| `keywords` | `{"name", "label", "uri", "vocabulary"}` for each controlled keyword |
| `contributors` | One credit for each person or organization credited, in the order the record's team set. See [Credits](#credits) |

A sample of the example type:

```json
{
  "url": "https://portal.example.org/api/v1/samples/plant-samples/sxXGUGgXRVStFw3jbpBWQeM/",
  "html_url": "https://portal.example.org/samples/sxXGUGgXRVStFw3jbpBWQeM/overview/",
  "uuid": "sxXGUGgXRVStFw3jbpBWQeM",
  "name": "PL-14",
  "local_id": "SAMPLE-5165",
  "status": "unknown",
  "dataset": {
    "uuid": "dV4DYUk6ohGJdizhxJotoZ8",
    "url": "https://portal.example.org/api/v1/datasets/dV4DYUk6ohGJdizhxJotoZ8/"
  },
  "location": {"type": "Point", "coordinates": [8.4115, 49.0094, 112.5]},
  "location_uncertainty": 25.0,
  "added": "2026-10-08T23:25:13.384580Z",
  "modified": "2026-10-08T23:25:13.385372Z",
  "species": "Quercus robur",
  "collected_on": "2024-05-02",
  "descriptions": [{"type": "SampleCollection", "value": "Taken from the north edge."}],
  "dates": [{"type": "Created", "value": "2024-05"}],
  "identifiers": [{"type": "IGSN", "value": "10.60516/AU1101"}],
  "keywords": [],
  "contributors": []
}
```

Which of a type's own fields the API returns is chosen in the type's registration. See [How to choose the fields the API returns](../how-to/choose-the-fields-the-api-returns.md).

### Location

`location` is the record's own place as a [GeoJSON](https://datatracker.ietf.org/doc/html/rfc7946) `Point` in WGS 84. The record's reasons are in [ADR 0032](../../adr/0032-a-location-is-a-value-on-each-record.md).

| Part | Holds |
|---|---|
| `coordinates` | Longitude, then latitude, then the elevation in metres above mean sea level when one is recorded. A negative elevation lies below it. A point with no elevation has two coordinates |
| `location_uncertainty` | The distance in metres from the point within which the true place lies |

- A record with no location returns `null` for both fields.
- A measurement returns the location it holds itself. A measurement with none of its own returns `null`, even where its sample has one. To read where it was made, follow its `sample` address and read the sample's `location`. [ADR 0033](../../adr/0033-a-measurement-borrows-its-samples-location-only-for-a-viewer-who-may-open-the-sample.md) records why.
- An organization's `location` is a point without an elevation or an uncertainty. A person has no `location`.
- `location`, `location_elevation` and `location_uncertainty` are read-only. A value sent for one is ignored.

### References

A record names another by its short identifier and its address in the API, and never by a database number. No response contains an `id` or a `pk`, and no request is accepted that carries one. [ADR 0027](../../adr/0027-records-refer-to-each-other-by-short-identifier.md) records why.

```json
"dataset": {
  "uuid": "dV4DYUk6ohGJdizhxJotoZ8",
  "url": "https://portal.example.org/api/v1/datasets/dV4DYUk6ohGJdizhxJotoZ8/"
}
```

- Requesting the `url` returns the record it names.
- A reference is `null` when the caller may not see the record it would name. A public dataset can sit in a private project, and a measurement's sample can be in another, private dataset. Both read `null` for a visitor and name the record for someone who holds at least the view level on it.
- A contributor the people list leaves out, such as a superuser, reads `null` in a reference to them.
- A parent is sent as a bare string or as the `{"uuid", "url"}` object a response carries. A database number is refused.

### Credits

A credit holds what a harvester needs to attribute a record without asking the API anything else. Its fields follow the properties DataCite asks of a creator or contributor. [ADR 0030](../../adr/0030-a-credit-carries-what-datacite-asks-of-a-creator.md) records why, and [Dataset publication, DOIs and DataCite metadata](../../explanation/dataset-publication-dois-and-datacite-metadata.md) explains how credits become DataCite fields.

```json
{
  "uuid": "cLBrpvMLpvBDYAg9xkbt9Z",
  "url": "https://portal.example.org/api/v1/people/cLBrpvMLpvBDYAg9xkbt9Z/",
  "name": "Lovelace, Ada",
  "type": "Personal",
  "given_name": "Ada",
  "family_name": "Lovelace",
  "name_identifiers": [
    {
      "name_identifier": "https://orcid.org/0000-0002-1825-0097",
      "name_identifier_scheme": "ORCID",
      "scheme_uri": "https://orcid.org/"
    }
  ],
  "affiliation": {
    "uuid": "cK3mT9xQwPzV7aUe2nRfHs",
    "url": "https://portal.example.org/api/v1/organizations/cK3mT9xQwPzV7aUe2nRfHs/",
    "name": "Analytical Institute",
    "affiliation_identifier": "https://ror.org/03yrm5c26",
    "affiliation_identifier_scheme": "ROR",
    "scheme_uri": "https://ror.org/"
  },
  "roles": [{"name": "DataCollector", "label": "Data collector"}]
}
```

| Credit field | DataCite property |
|---|---|
| `name` | `creatorName` or `contributorName`. A person is written "Family, Given", or the one name they have, and an organization by its name |
| `type` | `nameType`, either `Personal` or `Organizational` |
| `given_name`, `family_name` | `givenName` and `familyName`. Both are `null` for an organization, and each is `null` for a person who has not recorded it |
| `name_identifiers[].name_identifier` | `nameIdentifier`. The address the identifier resolves to, or its value where the scheme has no resolver |
| `name_identifiers[].name_identifier_scheme` | `nameIdentifierScheme`, such as `ORCID` |
| `name_identifiers[].scheme_uri` | `schemeURI`. `null` where the scheme has no resolver address |
| `affiliation.name` | `affiliation`, the name of the organization |
| `affiliation.affiliation_identifier` | `affiliationIdentifier`. The organization's ROR ID where it has one, and otherwise its first identifier |
| `affiliation.affiliation_identifier_scheme` | `affiliationIdentifierScheme` |
| `affiliation.scheme_uri` | `schemeURI` of the affiliation |
| `roles` | The roles from the portal's own vocabulary as `{"name", "label"}`. An export maps them to DataCite's `contributorType` |
| `uuid`, `url` | None. The short identifier and the API address of the person or organization |
| `affiliation.uuid`, `affiliation.url` | None. The same for the organization |

- A record keeps one list of credits and does not separate creators from other contributors. Which roles make someone a DataCite creator is for an export to decide, and it reads that from `roles`.
- `affiliation` is the one organization recorded on that credit. It is never the organization on the person's profile. It is `null` on a credit that records none, and on one whose organization has since been deleted.
- A credit whose person or organization has been deleted is left out of the list.
- A credit held by an account the people list leaves out, such as a superuser, is returned with its name, identifiers and roles. Its `uuid` and `url` are `null`.
- A credit carries no biography, link, language, image, email address or access level.

## People

`/api/v1/people/` lists the people the portal's own lists show. Superusers and the anonymous account are left out, and are answered as a person that does not exist when requested directly. Organizations are not in it. A profile nobody has claimed is listed like any other. People are read-only.

A list entry holds:

| Field | Holds |
|---|---|
| `url`, `html_url`, `uuid` | The person's address in the API, their page on the portal and their short identifier |
| `name`, `given_name`, `family_name` | The name they are known by, and their given and family name |
| `identifiers` | `{"type", "value", "link"}` for each identifier, such as an ORCID iD |
| `primary_affiliation` | `{"uuid", "url", "name"}` for the organization of their primary affiliation, or `null` when that affiliation is unverified or has ended |

`added` and `modified` are not returned. A list can still be ordered by either and narrowed with `modified_after` and `modified_before`.

`/api/v1/people/{uuid}/` returns every field of a list entry and adds:

| Field | Holds |
|---|---|
| `alternative_names` | Other names the person is known by, as a list of strings |
| `profile` | The biography as the person wrote it |
| `links` | The web addresses on the person's page, as a list of strings. An address that is not `http` or `https` is left out |
| `languages` | The names of their languages in the active language, as a list of strings |
| `image` | The address of their picture, or `null` |
| `affiliations` | Every verified affiliation, the current ones first and the past ones after them |
| `projects` | The address of the project list narrowed to this person. See [Records a contributor is credited on](#records-a-contributor-is-credited-on) |
| `datasets` | The address of the dataset list narrowed to this person |

An entry of `affiliations` holds:

| Field | Holds |
|---|---|
| `organization` | `{"uuid", "url", "name"}` for the organization |
| `type` | `member`, `admin` or `owner` |
| `start`, `end` | When the affiliation began and ended, as a year, a month or a day as it was recorded, or `null` |
| `is_primary` | Whether it is the person's primary affiliation |

Among the current affiliations the primary one comes first and the rest follow by the name of the organization. The past ones come with the most recently ended first. An affiliation that has not been verified is never returned.

No response about a person has an email address, a credential, a flag about their account, a portal role, a sign-in date or a preference. [ADR 0029](../../adr/0029-people-and-organizations-have-their-own-api-endpoints.md) records why people and organizations have endpoints of their own.

## Organizations

`/api/v1/organizations/` lists the organizations the portal holds. People are not in it. Organizations are read-only.

A list entry holds:

| Field | Holds |
|---|---|
| `url`, `html_url`, `uuid` | The organization's address in the API, its page on the portal and its short identifier |
| `name` | The name it is known by |
| `type` | The kind of organization as its stored code, such as `education`, or `null` |
| `country` | The two-letter country code, or `null` |
| `location` | The organization's point as a GeoJSON `Point`, longitude first, or `null`. See [Location](#location) |
| `identifiers` | `{"type", "value", "link"}` for each identifier, such as a ROR ID |

`added` and `modified` are not returned. They are available for ordering and for `modified_after` and `modified_before`.

`/api/v1/organizations/{uuid}/` returns every field of a list entry and adds:

| Field | Holds |
|---|---|
| `alternative_names` | Other names the organization is known by, as a list of strings |
| `profile` | The description as the organization wrote it |
| `city` | The city it is based in, or `null` |
| `links` | The web addresses on its page, as a list of strings. An address that is not `http` or `https` is left out |
| `image` | The address of its picture, or `null` |
| `parent_organization` | `{"uuid", "url", "name"}` for the organization it is part of, or `null` |
| `sub_organizations` | `{"uuid", "url", "name"}` for each organization that is part of it, by name |
| `members` | The people who belong to it, with the kind of affiliation each holds |
| `projects` | The address of the project list narrowed to this organization |
| `datasets` | The address of the dataset list narrowed to this organization |

An entry of `members` holds `person`, as `{"uuid", "url", "name"}`, and `type`, which is `member`, `admin` or `owner`. Only members whose affiliation is verified and has not ended are listed. The people who run the organization come first, owners and then administrators, and each group is in order of name. A pending member, a former member, a superuser and the anonymous account are not listed.

## Query parameters

| Parameter | On | Takes |
|---|---|---|
| `page` | Every list | A page number, starting at 1 |
| `page_size` | Every list | The number of records in a page |
| `ordering` | Every list | A field name, with `-` in front for descending order |
| `modified_after`, `modified_before` | Every list | An ISO 8601 date or date-time |
| `dataset` | Sample and measurement lists | A dataset's short identifier |
| `sample` | Measurement lists | A sample's short identifier |
| `contributor` | Project and dataset lists | A person's or organization's short identifier |
| `organization` | People | An organization's short identifier |
| `identifier` | People, organizations | An identifier's value or the address it resolves to |
| `type` | Organizations | The stored code of an organization type, such as `education`, `company` or `government` |
| `country` | Organizations | A two-letter country code in capitals |
| `parent_organization` | Organizations | An organization's short identifier |
| `top_level` | Organizations | `true` or `false` |
| Filters a type declares | That type's list | Whatever the filter takes |

A value that cannot be read answers `400` and names the parameter. Filters combine, and a record must match every one that is sent.

### Paging

Every list is paged. The response carries:

| Key | Holds |
|---|---|
| `count` | The number of records the caller may see |
| `next`, `previous` | The addresses of the pages either side, or `null` |
| `results` | The records of this page |

A page holds `REST_FRAMEWORK["PAGE_SIZE"]` records unless `?page_size=` asks for another number, and no page holds more than `FAIRDM_API_MAX_PAGE_SIZE` whatever the caller asks. Both are read when a request is answered. Their values are in [Settings](settings.md).

### Ordering

`?ordering=name` sorts ascending and `?ordering=-name` descending. Relations and metadata cannot be sorted on.

| List | Sortable fields |
|---|---|
| Projects | `name`, `added`, `modified`, `status`, `uuid` |
| Datasets | `name`, `added`, `modified`, `uuid` |
| People | `name`, `last_name`, `added`, `modified`, `uuid` |
| Organizations | `name`, `added`, `modified`, `uuid` |
| A sample or measurement type | The stored fields of the type that its serializer returns, such as `name`, `added`, `modified` and the fields the type declares |

### Records of one parent

A sample list takes `?dataset=<short identifier>`. A measurement list takes that and `?sample=<short identifier>`.

```text
GET /api/v1/samples/plant-samples/?dataset=dV4DYUk6ohGJdizhxJotoZ8
GET /api/v1/measurements/leaf-measurements/?sample=sd573eit27hDfnZD98NsqsW
```

A database number, an unknown identifier and the identifier of a dataset the caller may not see are all answered `400`.

### A type's own filters

The filters a type's registration declares apply as well, for example `?species=Quercus%20robur`. They match what the portal's list pages accept, with two differences:

- A filter on a relation, such as a project or a contributor, takes the related record's short identifier and refuses a database number.
- A filter on a relation whose model has no short identifier, such as a content type, is not offered by the API.

The portal's pages keep their own filters unchanged.

### Records a contributor is credited on

The project list and the dataset list take `?contributor=` with the short identifier of a person or an organization. The list then holds the records that contributor is credited on, and no others.

```text
GET /api/v1/datasets/?contributor=cXq7Lw0eR2sNn4KcJ8VdZb3
GET /api/v1/projects/?contributor=cT5mYh1uPq9AaWz6GfCx2Ke
```

- The answer holds public records only, whoever asks. A private project, a private dataset and a public dataset inside a private project are never returned or counted, even for a person with access to them.
- A project an organization owns but is not credited on is not in its list.
- An identifier that names nobody, the identifier of a superuser or of the anonymous account, and a database number all give an empty list with status `200`.
- A single person and a single organization give both addresses, as `projects` and `datasets`. Each is absolute when the request is, and the path alone otherwise.

### People filters

`organization` keeps the people with a verified affiliation to the organization that has not ended. A pending or ended affiliation does not match. A database number, or an identifier that names no organization, is answered `400`.

`identifier` returns the person who holds it. Give the value, such as `0000-0002-1825-0097`, or the address it resolves to, such as `https://orcid.org/0000-0002-1825-0097`. The address of any scheme the portal knows is accepted with `http` or `https` and with or without a trailing slash. An identifier nobody holds, and one held by an account the list leaves out, gives an empty list.

```text
GET /api/v1/people/?organization=cT5mYh1uPq9AaWz6GfCx2Ke
GET /api/v1/people/?identifier=https://orcid.org/0000-0002-1825-0097
```

### Organization filters

- `type` takes a stored code. A value that is not one of the stored codes is answered `400`.
- `parent_organization` keeps the organizations that are part of the one named. A database number, or an identifier that names no organization, is answered `400`.
- `top_level=true` keeps the organizations that are part of no other, and `false` keeps those that are part of one.
- `identifier` works as it does for people. An identifier nobody holds gives an empty list.

```text
GET /api/v1/organizations/?type=education
GET /api/v1/organizations/?country=AU
GET /api/v1/organizations/?parent_organization=cB8nWq3sLd6RtYj1HxVm4Pa
GET /api/v1/organizations/?top_level=true
GET /api/v1/organizations/?identifier=https://ror.org/03yrm5c26
```

### Records changed in a period

`?modified_after=` keeps the records last changed at or after the moment. `?modified_before=` keeps those changed at or before it. Each is compared with the record's `modified` time.

- A date alone means the start of that day.
- A time without an offset is read in the portal's time zone.
- A deleted record is not listed, so a deletion cannot be found this way.

```text
GET /api/v1/datasets/?modified_after=2026-10-01T08:00:00Z
GET /api/v1/samples/plant-samples/?modified_after=2026-10-01&modified_before=2026-11-01
```

## Authentication

The API knows who is calling in one of two ways. Nothing else identifies a caller.

| Way | How it is sent |
|---|---|
| Token | `Authorization: Token <token>` on every request |
| Session | The portal's sign-in cookie, from a page of the portal |

- A person creates a token on their account pages at `/account/tokens/`, which are described in [API tokens](../../users/account/api-tokens.md). The token is shown once, and only a digest of it is stored.
- A token lasts 7 days, 30 days, 90 days, 1 year or until it is revoked, as its creator chose. A revoked, expired or unknown token is answered `401`.
- The number of tokens a person holds and whether using a token extends it are settings. See [Settings](settings.md).
- A request with a token is treated as coming from the person who holds it, with the levels they hold when the request is made. Removing a level takes effect on their next request, and the token keeps working.
- A write made with a session must carry Django's CSRF token and is refused with `403` without it. A request with a token needs none.
- No address of the API exchanges a password for a token, signs a caller out, resets or changes a password, or edits an account. [ADR 0028](../../adr/0028-api-tokens-are-created-on-the-account-pages.md) records why.

[How to restrict API tokens to some people](../how-to/restrict-api-tokens-to-some-people.md) limits who may create one.

## Permissions

For a project, dataset, sample or measurement, the level a person holds on the record, or on a record above it, decides what they may do. [How access to a record is decided](../../explanation/how-access-to-a-record-is-decided.md) explains the levels.

| Level | May |
|---|---|
| View | Read a private record |
| Edit | Change the record and create records inside it. The edit level on a dataset creates its samples and measurements, and the edit level on a project creates its datasets |
| Manage | Everything the edit level may, and delete the record, change its visibility and move it |

Any signed-in person may create a project. The answer to a caller who holds no level, or too low a level, depends on whether they can see the record.

| Request | Answer |
|---|---|
| Anonymous GET of a public record | `200` |
| Anonymous GET of a private record | `404` |
| Anonymous POST, PUT, PATCH or DELETE | `401` |
| Signed-in GET of a private record without the view level | `404` |
| Signed-in change or delete of a public record without the level it needs | `403` |
| Signed-in change or delete of a private record at the view level | `403` |
| Signed-in change or delete of a private record without any level | `404` |
| Change, or create inside, at the edit level | `200` or `201` |
| Delete, change visibility or move at the manage level | `200` or `204` |

The `404` for a private record is deliberate. A caller cannot tell a private record from one that does not exist.

- A sample or measurement is public when its dataset is public and published.
- A dataset that is public but not yet published answers to everyone for its own record. Its samples and measurements are listed, counted and returned only to a person with a level on them, and everyone else gets `404`.

Three rules about what a request may change apply to projects, datasets, samples and measurements, as they do to the portal's update forms.

- **Visibility and the record a record sits under need the manage level.** A `PUT` or `PATCH` that sets `visibility`, `owner`, or a `project`, `dataset` or `sample` field to a value different from the stored one answers `403` and stores nothing, unless the caller can manage the record. Sending the stored value is not a change.
- **A move that would leave the record with nobody to manage it answers `400`.** The error is on the parent field and carries the code `no_manager`.
- **A record is created only inside a parent the caller holds the edit level on.** The `project`, `dataset` and `sample` fields accept only records the caller can edit, so a `POST` naming any other answers `400`.

The person who creates a record is listed on it at the manage level, which makes them its creator. A superuser who creates one is not listed, because a superuser cannot be a contributor. No django-guardian permission is stored.

## Writing records

Projects, datasets and every registered sample and measurement type accept `POST`, `PUT`, `PATCH` and `DELETE` on the addresses they are read from.

### What can be written

A record's own fields, its visibility and its parent are writable. Everything else is read-only.

| Kind | Writable | Read-only |
|---|---|---|
| Project | `name`, `status`, `visibility`, `funding`, `owner` | `image`, `url`, `html_url`, `uuid`, `added`, `modified` and the metadata |
| Dataset | `name`, `visibility`, `project` | `image`, `published`, `license`, `url`, `html_url`, `uuid`, `added`, `modified` and the metadata |
| Sample | `name`, `local_id`, `status`, `dataset` and every field its type declares | `url`, `html_url`, `uuid`, `location`, `location_elevation`, `location_uncertainty`, `added`, `modified` and the metadata |
| Measurement | `name`, `sample`, `dataset` and every field its type declares, measured values included | `url`, `html_url`, `uuid`, `location`, `location_elevation`, `location_uncertainty`, `added`, `modified` and the metadata |

A value sent for a read-only field is ignored, not refused. The request succeeds and the field keeps the value it had. `created_by` is not a field of the API, so a value sent for it is ignored in the same way. The creator is always the person who sent the request.

### Create

```text
POST /api/v1/samples/plant-samples/
Content-Type: application/json

{
  "name": "PL-14",
  "dataset": "dV4DYUk6ohGJdizhxJotoZ8",
  "species": "Quercus robur",
  "collected_on": "2024-05-02"
}
```

- The answer is `201` and the complete new record, as a `GET` of its address returns it.
- A measurement names its `sample` and its `dataset`. A dataset names its `project`.
- A project or dataset created through the API is private unless the body sets `visibility`.

### Replace and change

`PATCH` sends only the fields to change and leaves every other field as it was. `PUT` replaces the record. It carries every required field, and an optional field it leaves out keeps its stored value. The answer is `200` and the record as it stands.

```text
PATCH /api/v1/samples/plant-samples/sxXGUGgXRVStFw3jbpBWQeM/
Content-Type: application/json

{"dry_weight_g": 12.5}
```

Two writes that reach the same record at once are applied in turn, and the later one wins.

### Delete

The answer is `204`, and a later request for the record is answered `404`. The portal refuses to delete a record in two states, and the API refuses with it. Both are answered `409 Conflict` with a `detail` that gives the reason, and nothing is deleted:

- A project with a public dataset.
- A sample with measurements made on it.

The reason names no other record, because the caller may not be allowed to see them.

## Status codes

| Code | Meaning |
|---|---|
| `200` | A read or a change succeeded. The body is the record or the page |
| `201` | A record was created. The body is the record |
| `204` | A record was deleted. There is no body |
| `400` | The body cannot be parsed, a required field is missing, a value is not acceptable, or a query parameter cannot be read. The answer names each field at fault and says why, and nothing is saved |
| `400` on a parent field | The parent does not exist, or the caller may not add to it. Both are answered alike, so the API does not confirm that a private record exists. A move that would leave nobody able to manage the record carries the code `no_manager` |
| `401` | No token and no session, or a token that is revoked, expired or unknown |
| `403` | The caller can see the record and holds too low a level to do this |
| `404` | The caller cannot see the record, or it does not exist |
| `409` | A delete the portal refuses |
| `429` | The caller is past a limit. A `Retry-After` header gives the seconds to wait |

No request is answered with a server error because of what it contains.

## Limits and other origins

- Each kind of caller has a limit over a minute and a limit over a day. A caller with a token or a session is allowed more than an anonymous caller. The rates are in [Settings](settings.md). [How API callers are limited](../explanation/how-api-callers-are-limited.md) explains the design, and [How to change the API rate limits](../how-to/change-the-api-rate-limits.md) changes them.
- Pages on other websites may call the API under `/api/` and nowhere else. Credentials are not allowed, so a browser does not send the portal's sign-in cookie from another site, and such a page must send a token. [How to allow only some sites to call the API](../how-to/allow-only-some-sites-to-call-the-api.md) narrows the list of sites.

## Interactive documentation

`/api/v1/docs/` is Swagger UI, generated by [drf-spectacular](https://drf-spectacular.readthedocs.io/) from the routes the portal is running. A type you register appears in it with the fields its serializer carries. The portal's sidebar has one link to it, **API**, in the **Documentation** group. The screen is described in [API documentation](../../users/api/api-docs.md).

- The schema names two ways of authenticating: `tokenAuth`, the `Authorization` header, and `cookieAuth`, the session cookie.
- To try a request that needs a token, choose **Authorize** and enter `Token <your-token>`. Signing in to the portal first makes the page send your session.
- A list in the schema offers the filters the API applies. It does not offer a filter the API refuses, such as a content-type filter or a relation filter that takes a database number.
- The documentation has six headings: **Projects**, **Datasets**, **People**, **Organizations**, **Samples** and **Measurements**. Every sample type's operations are under **Samples** and every measurement type's under **Measurements**.
- Each operation of a type is titled with the type's plural name, written as the model gives it, and what it does: `plant samples: list`, `read`, `create`, `replace`, `change` and `delete`.
- The description at the top of the page ends with sections on authentication, limits and paging, written from the portal's settings when the schema is generated.
- Schema component names drop the `Serializer` suffix of the class. A type's record is `PlantSample`, and its `PATCH` body is `PatchedPlantSample`.

[How to customise the API documentation](../how-to/customise-the-api-documentation.md) changes the text.
