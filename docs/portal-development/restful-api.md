# RESTful API

FairDM automatically generates a fully documented RESTful API for every model you register. You do not need to write any Django REST Framework views, serializers, routers, or URL patterns — the framework handles everything.

## Automatic Endpoint Generation

When you register a Sample or Measurement model, FairDM creates the following endpoints automatically:

```
GET  /api/v1/samples/<model-slug>/          — list all publicly visible records
GET  /api/v1/samples/<model-slug>/{uuid}/   — detail for a specific record
POST /api/v1/samples/<model-slug>/          — create (signed-in users with the edit level on the dataset)
PUT /api/v1/samples/<model-slug>/{uuid}/    — replace (edit level)
PATCH /api/v1/samples/<model-slug>/{uuid}/  — partial update (edit level)
DELETE /api/v1/samples/<model-slug>/{uuid}/ — delete (manage level)
```

The `<model-slug>` is derived from your model's `verbose_name_plural` (lowercased, spaces replaced with hyphens). For example, a model with `verbose_name_plural = "rock samples"` becomes `rock-samples`. See [URL Slugs and verbose_name_plural](#url-slugs-and-verbose-name-plural) for details.

Registering the type is all it takes. The list and record routes exist, the type is in the
[catalogue](#the-catalogues), and its records can be read and written, with the fields
described under [Customizing Serializer Fields](#customizing-serializer-fields).

Core model endpoints are also available:

| Endpoint | Methods |
|----------|---------|
| `/api/v1/projects/` | GET, POST |
| `/api/v1/projects/{uuid}/` | GET, PUT, PATCH, DELETE |
| `/api/v1/datasets/` | GET, POST |
| `/api/v1/datasets/{uuid}/` | GET, PUT, PATCH, DELETE |
| `/api/v1/contributors/` | GET |
| `/api/v1/contributors/{uuid}/` | GET |
| `/api/v1/samples/` | GET (catalogue of sample types) |
| `/api/v1/measurements/` | GET (catalogue of measurement types) |

## What a Record Contains

A project, dataset, sample or measurement is returned whole, on its record route and in every row of
its list. The same fields appear in both.

| Kind | Fields of its own | Its parent |
|------|-------------------|------------|
| Project | `url`, `uuid`, `name`, `image`, `status`, `visibility`, `funding`, `added`, `modified` | `owner`, the organization that owns it |
| Dataset | `url`, `uuid`, `name`, `image`, `visibility`, `published`, `added`, `modified` | `project`, and `license` as `{"name", "url"}` |
| Sample | `url`, `uuid`, `name`, `local_id`, `status`, `added`, `modified`, then every field its type declares | `dataset` |
| Measurement | `url`, `uuid`, `name`, `added`, `modified`, then every field its type declares, measured values included | `sample` and `dataset` |

Every one of the four also carries its metadata, which is read-only:

| Field | Holds |
|-------|-------|
| `descriptions` | `{"type", "value"}` for each description |
| `dates` | `{"type", "value"}` for each key date, as a year, a month or a day |
| `identifiers` | `{"type", "value"}` for each external identifier, such as a DOI |
| `keywords` | `{"name", "label", "uri", "vocabulary"}` for each controlled keyword |
| `contributors` | `{"contributor", "roles", "affiliation"}` for each credit, in the order the record's team set |

A credit names the person or organization, the roles they hold on the record as `{"name", "label"}`
and the organization they are credited from. The level a person holds on the record is not shown,
as the record's page does not show it.

A rock sample looks like this:

```json
{
  "url": "https://portal.example.org/api/v1/samples/rock-samples/sxXGUGgXRVStFw3jbpBWQeM/",
  "uuid": "sxXGUGgXRVStFw3jbpBWQeM",
  "name": "RS-14",
  "local_id": "SAMPLE-5165",
  "status": "unknown",
  "dataset": {
    "uuid": "dV4DYUk6ohGJdizhxJotoZ8",
    "url": "https://portal.example.org/api/v1/datasets/dV4DYUk6ohGJdizhxJotoZ8/"
  },
  "added": "2026-10-08T23:25:13.384580Z",
  "modified": "2026-10-08T23:25:13.385372Z",
  "rock_type": "igneous",
  "collection_date": "2024-05-02",
  "descriptions": [{"type": "SampleCollection", "value": "Taken from the north face."}],
  "dates": [{"type": "Created", "value": "2024-05"}],
  "identifiers": [{"type": "IGSN", "value": "10.60516/AU1101"}],
  "keywords": [],
  "contributors": []
}
```

## How Records Refer to Each Other

A record names another by its short identifier and its address in the API, and never by a database
number. No response contains an `id` or a `pk`, and no request is accepted that carries one.

```json
"dataset": {
  "uuid": "dV4DYUk6ohGJdizhxJotoZ8",
  "url": "https://portal.example.org/api/v1/datasets/dV4DYUk6ohGJdizhxJotoZ8/"
}
```

Requesting the `url` returns the record it names. A reference is `null` when the caller may not
see the record it would name. A public dataset can sit in a private project, and a measurement's
sample can be in another, private dataset. Both references read `null` for a visitor and name the
record for someone who holds at least the view level on it, so a response never reveals a record
the caller could not open.

`fairdm.api.serializers.RecordReferenceField` is the field that does this. Use it in a serializer
of your own for a relation to a project, dataset, sample, measurement or contributor:

```python
from fairdm.api.serializers import RecordReferenceField

class RockSampleSerializer(BaseSampleSerializer):
    # A foreign key from RockSample to another sample.
    reference_sample = RecordReferenceField(read_only=True)

    class Meta(BaseSampleSerializer.Meta):
        model = RockSample
        fields = BaseSampleSerializer.Meta.fields + ["reference_sample"]
```

A relation you leave to Django REST Framework's defaults is returned as a database number. Declare
every relation you add as a `RecordReferenceField` or a `StringRelatedField`.

## Creating, Changing and Deleting Records

Projects, datasets and every registered sample and measurement type accept `POST`, `PUT`, `PATCH`
and `DELETE` on the same routes they are read from. A request is judged by the level the caller
holds on the record, exactly as the portal's own pages judge it (see
[Permission Model](#permission-model)).

### What can be written

A record's own fields, its visibility and its parent are writable. Everything else is read-only.

| Kind | Writable | Read-only |
|------|----------|-----------|
| Project | `name`, `status`, `visibility`, `funding`, `owner` | `image`, `url`, `uuid`, `added`, `modified` and the metadata |
| Dataset | `name`, `visibility`, `project` | `image`, `published`, `license`, `url`, `uuid`, `added`, `modified` and the metadata |
| Sample | `name`, `local_id`, `status`, `dataset` and every field its type declares | `url`, `uuid`, `added`, `modified` and the metadata |
| Measurement | `name`, `sample`, `dataset` and every field its type declares, measured values included | `url`, `uuid`, `added`, `modified` and the metadata |

The metadata (`descriptions`, `dates`, `identifiers`, `keywords` and `contributors`) is edited in the
portal. A value sent for a read-only field is ignored, not refused: the request succeeds and the
field keeps the value it had. `created_by` is not a field of the API, so a value sent for it is
ignored in the same way, and the record's creator is always the person who sent the request.

A parent is named by its short identifier, as a bare string or as the `{"uuid", "url"}` object a
response carries. A database number is refused.

### Creating

```http
POST /api/v1/samples/rock-samples/
Content-Type: application/json

{
  "name": "RS-14",
  "dataset": "dV4DYUk6ohGJdizhxJotoZ8",
  "rock_type": "igneous",
  "collection_date": "2024-05-02"
}
```

The answer is `201` and the complete new record, as a `GET` of its address returns it. A measurement
names its `sample` and its `dataset` and carries its measured values the same way. A dataset names
its `project`. Any signed-in person may create a project.

A project or dataset created through the API is private unless the body sets `visibility`. The
person who created a record is listed on it at the manage level, which makes them its creator. A superuser who
creates one is not listed.

### Replacing and changing part of a record

`PATCH` sends only the fields to change and leaves every other field as it was. `PUT` replaces the
record: it carries every required field, and an optional field it leaves out keeps its stored value.

```http
PATCH /api/v1/samples/rock-samples/sxXGUGgXRVStFw3jbpBWQeM/
Content-Type: application/json

{"weight_grams": 12.5}
```

The answer is `200` and the record as it now stands. Repeating the parent a record already has is
not a move, and neither is repeating its current visibility.

### Deleting

```http
DELETE /api/v1/samples/rock-samples/sxXGUGgXRVStFw3jbpBWQeM/
```

The answer is `204`, and a later request for the record is answered `404`.

The portal refuses to delete a record in two states, and the API refuses with it. Both are answered
`409 Conflict` with a `detail` that gives the reason, and nothing is deleted:

- A project with a public dataset. Make its datasets private or delete them first.
- A sample with measurements made on it. Delete or move the measurements first.

The reason names no other record, because the caller may not be allowed to see them. A viewset of
your own that deletes a record the portal protects can raise `fairdm.api.viewsets.DeleteRefused`
with a reason to answer the same way.

### Refused requests

| Answer | When |
|--------|------|
| `400` | The body cannot be parsed, a required field is missing, or a value is not acceptable. The answer names each field at fault and says why, and nothing is saved. |
| `400` on a parent field | The parent does not exist, or the caller may not add to it. Both are answered alike, so the API does not confirm that a private record exists. A move that would leave nobody able to manage the record carries the code `no_manager`. |
| `401` | No token and no session. |
| `403` | The caller can see the record and holds too low a level to do this. |
| `404` | The caller cannot see the record. |
| `409` | A delete the portal refuses, described above. |

No request is answered with a server error because of what it contains. Two writes that reach the
same record at once are applied in turn and the later one wins.

## Contributors

`/api/v1/contributors/` lists the people and organizations the portal's own lists show, so
superusers and the anonymous account are left out. A contributor is returned with what their
profile page shows a visitor:

| Field | Holds |
|-------|-------|
| `url`, `uuid`, `type`, `name`, `image`, `profile` | The profile, with `type` set to `person` or `organization` |
| `identifiers` | `{"type", "value", "link"}`, such as an ORCID iD or a ROR ID |
| `links`, `languages` | The web links and the languages the profile lists |
| `affiliation` | A person's primary organization, or an organization's parent |
| `location` | The city and country of that organization |
| `organization_type` | The kind of organization, `null` for a person |

Nothing about the account behind a person is ever returned: no email address, credential, flag or
sign-in date. Contributors are read-only.

## Filtering, Ordering and Paging

Every list is paged. The response carries `count`, the total number of records the caller may see,
and `next` and `previous`, the addresses of the pages either side. A page holds 100 records unless
`?page_size=` asks for another number, and no page holds more than 1,000 whatever the caller asks.
Both figures are settings, described under [Limits on Use](#limits-on-use).

A sample list takes `?dataset=<short identifier>`, and a measurement list takes that and
`?sample=<short identifier>`, whatever filters the type declares. A database number, an unknown
identifier and the identifier of a dataset the caller may not see are all answered `400`.

```http
GET /api/v1/samples/rock-samples/?dataset=dV4DYUk6ohGJdizhxJotoZ8
GET /api/v1/measurements/xrf-measurements/?sample=sd573eit27hDfnZD98NsqsW
```

A type's own filters, the ones its registration declares, apply as well, for example
`?rock_type=igneous`. These match what the portal's list pages accept, with one difference:
a filter on a relation, such as a project or a contributor, takes the related record's short
identifier here and refuses a database number. A filter on a relation whose model has no short
identifier, such as a content type, is not offered by the API. The portal's pages keep their own
filters unchanged.

`?ordering=name` sorts ascending and `?ordering=-name` descending. A list sorts on the stored
fields it returns, such as `name`, `added` and `modified`, and on the fields the type declares.
Relations and metadata cannot be sorted on.

## The Catalogues

`GET /api/v1/samples/` and `GET /api/v1/measurements/` each answer with the registered types of
their kind, so a script can ask what a portal holds and where each type's records are. A portal
with no registered sample types answers `{"types": []}` for the first, and likewise for
measurements.

```json
{
  "types": [
    {
      "name": "SoilSample",
      "verbose_name": "Soil Sample",
      "verbose_name_plural": "Soil Samples",
      "app_label": "demo",
      "endpoint": "https://portal.example.org/api/v1/samples/soil-samples/",
      "fields": ["url", "uuid", "name", "local_id", "status", "dataset", "added", "modified",
                 "soil_type", "ph_level", "depth_cm", "descriptions", "dates", "identifiers",
                 "keywords", "contributors"],
      "filters": ["soil_type", "ph_level", "depth_cm", "dataset", "image"],
      "count": 42
    }
  ]
}
```

| Key | Holds |
|-----|-------|
| `name` | The model's class name. |
| `verbose_name`, `verbose_name_plural` | The names the model declares. |
| `app_label` | The Django app the model belongs to. |
| `endpoint` | The absolute address of the type's list, found by reversing its route. It follows the model's `verbose_name_plural` and the way the portal is mounted. |
| `fields` | A flat list of the names of the fields the type's serializer carries, in the order a record returns them. |
| `filters` | The names of the filters the type's list accepts, as the API builds them for the request. A filter on a range, such as `ph_level`, is also offered as `ph_level_min` and `ph_level_max`. A relation filter takes a short identifier, and the content-type filter is not offered. |
| `count` | The number of the type's records the caller may see. |

The `count` is the one the type's list reports for the same caller. A visitor and a signed-in
person with no level on a private dataset count the records in public datasets. A person with a
level on a private dataset counts its records as well.

## Interactive Documentation

FairDM serves interactive documentation generated by
[drf-spectacular](https://drf-spectacular.readthedocs.io/) from the routes the portal is running,
so a type you register appears in it with the fields its serializer carries. The portal's sidebar
has one link to it, **API**, in the **Documentation** group.

| Address | Route name | Description |
|---------|------------|-------------|
| `/api/v1/docs/` | `api:api-docs` | Swagger UI, where every address, field and filter is listed, a field is marked required or read-only, and a request can be tried and its response read |
| `/api/v1/redoc/` | `api:api-redoc` | ReDoc, the same reference to read |
| `/api/v1/schema/` | `api:api-schema` | The OpenAPI 3 schema both pages are drawn from, as YAML, or as JSON with `?format=json` |

The schema describes the two ways of authenticating: the `Authorization` header that carries a
token, and the session cookie. To try a request that needs a token, choose **Authorize** on the
documentation page and enter `Token <your-token>`, or sign in to the portal first and the page
sends your session.

The description at the top of the page is written when the schema is generated. After the text you
set in `FAIRDM_API_DESCRIPTION` it adds how to authenticate, the rates in
`REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]` (each one that is configured, under its own name) and
the default and largest page size of the pagination class. Change a setting and the page says so;
there is nothing to keep in step.

A list in the schema offers the filters the API applies, so it does not offer a filter the API
refuses, such as a content-type filter or a relation filter that takes a database number.
`fairdm.api.schema.FairDMFilterExtension`, a drf-spectacular extension that asks the filter set
which filters it drops, does this; it is loaded when the API app starts.

## Authentication

The API knows who is calling in two ways. A script sends a token, and a person using the portal in
a browser sends their sign-in session. No address of the API exchanges a password for a token,
signs a caller out, resets or changes a password, or edits an account.

### Tokens

A person creates a token on their account pages, after signing in the usual way with their second
factor if they use one. The pages are provided by django-mvp-accounts, which keeps the tokens with
[django-rest-knox](https://jazzband.co/projects/django-rest-knox). FairDM turns them on for every
portal, at `/account/tokens/`, and the Account Center links to them.

The create page asks how long the token should last: 7 days, 30 days, 90 days, 1 year or never.
The token is shown once, on the page the person returns to, and only a digest of it is stored. A
person who loses a token revokes it and creates another. Each token can be revoked on its own, and
a revoked, expired or unknown token is answered `401`.

The script sends the token in the `Authorization` header of every request:

```http
GET /api/v1/projects/
Authorization: Token abc123def456...
```

A request with a current token is treated as coming from the person who holds it, with the levels
they hold when the request is made. Removing a person's level on a record takes effect on their
next request, and the token keeps working.

Two settings shape the tokens. Both are in `REST_KNOX`, which FairDM sets to:

```python
REST_KNOX = {"TOKEN_LIMIT_PER_USER": 10, "AUTO_REFRESH": False}
```

`TOKEN_LIMIT_PER_USER` is how many working tokens a person may hold. At the limit the create page
creates nothing and says so. `AUTO_REFRESH` stays off so that a token expires on the day the person
chose, however often it is used. Override either one in your portal's settings after
`fairdm.setup()` returns:

```python
REST_KNOX["TOKEN_LIMIT_PER_USER"] = 5
```

### Who may hold tokens

Every signed-in person may. To give tokens to some people only, name a function that takes the
person and says whether they may:

```python
# In your portal's settings.py
MVP_ACCOUNTS_API_TOKEN_ACCESS = "myportal.access.staff_only"
```

```python
# myportal/access.py
def staff_only(user):
    return user.is_staff
```

A person it says no to gets `403` from the three token pages and sees no link to them. They can
still read public records without a token. The function decides who may reach the pages. It does
not revoke tokens a person already holds, and it is not asked when a token is used, so delete the
tokens of someone you remove from the group.

### Sessions

A person signed in to the portal in a browser is known to the API by their session. The Swagger UI
page makes its requests this way, as the person. A write made with a session must carry Django's
CSRF token, as any form post does, and is refused with `403` without it. A script that sends a token
does not need one.

## Permission Model

FairDM's API enforces the same permissions as the web interface. For a project, dataset, sample or
measurement, the level a person holds on the record, or on a record above it, decides what they may
do:

| Level | May |
|-------|-----|
| View | Read a private record |
| Edit | Change the record and create records inside it. The edit level on a dataset creates its samples and measurements, and the edit level on a project creates its datasets |
| Manage | Everything the edit level may, and delete the record, change its visibility and move it |

Any signed-in person may create a project. The result for a caller who holds no level, or too low
a level, depends on whether they can see the record:

| Scenario | Result |
|----------|--------|
| Anonymous GET on public object | 200 OK |
| Anonymous GET on private object | 404 Not Found (non-disclosure) |
| Anonymous POST/PUT/PATCH/DELETE | 401 Unauthorized |
| Authenticated GET on private object without the view level | 404 Not Found |
| Authenticated change or delete on a public object without the level it needs | 403 Forbidden |
| Authenticated change or delete on a private object at the view level | 403 Forbidden |
| Authenticated change or delete on a private object without any level | 404 Not Found |
| Edit level: change, create inside | 200/201 |
| Manage level: delete, change visibility, move | 200/204 |

Non-disclosure (404 instead of 403) is used for unauthorized access to detail endpoints to avoid leaking whether a private object exists.

Three rules about what a request may change apply to projects, datasets, samples and measurements,
and they are the ones the update forms apply:

- **Visibility and the record a record sits under need the manage level.** A `PUT` or `PATCH` that
  sets `visibility`, `owner`, or a `project`, `dataset` or `sample` field, to a value different from
  the stored one answers 403 and stores nothing unless the requester can manage the record. Sending the
  value already stored is not a change.
- **A move that would leave the record with nobody to manage it answers 400.** The error is on the
  parent field and carries the code `no_manager`.
- **A record is created only inside a parent the requester holds the edit level on.** The
  `project`, `dataset` and `sample` fields of a serializer accept only the records the requester can
  edit, so a `POST` naming any other answers 400 as it does for any value that is not a choice,
  creates nothing and lists nobody.

### Permission Assignment on Create

When you create a project, dataset, sample or measurement via the API, the requesting user is
listed on it at the manage level, which makes them its creator. A superuser who creates one is not
listed, because a superuser cannot be a contributor. No django-guardian permission is stored.

## Customizing Serializer Fields

A sample or measurement type always carries the fields common to its kind (see
[What a Record Contains](#what-a-record-contains)) and its metadata. The fields you declare are
added to them, and a field you name that is already common appears once. FairDM picks the list in
this order, and the first one that applies is used.

1. `serializer_fields`, the list for the API alone.
2. `fields`, the list every component of the type shares.
3. The framework's defaults, when the registration names neither.

The defaults are the type's editable fields, the ones the forms, tables and filters start from,
with `options` and `tags` left out. `options` is an internal field and `tags` is not returned as a
list of tags, so neither is useful to a caller. Name either in `serializer_fields` or `fields` to
have the API carry it.

### Tier 1 — `fields` (default)

If only `fields` is specified in the registry config, those fields are added:

```python
@fairdm.register
class RockSampleConfig(BaseSampleConfiguration):
    model = RockSample
    fields = ["name", "rock_type", "collection_date", "weight_grams"]
    # The API returns the common fields, then rock_type, collection_date and weight_grams,
    # then the metadata.
```

A measurement type declares the fields that hold its measured values the same way, and every one
of them is returned:

```python
@fairdm.register
class XRFMeasurementConfig(BaseMeasurementConfiguration):
    model = XRFMeasurement
    fields = ["element", "concentration_ppm", "detection_limit_ppm"]
```

### Tier 2 — `serializer_fields` (API-specific override)

Use `serializer_fields` when you want a different set of fields for the API compared to tables and
forms:

```python
@fairdm.register
class RockSampleConfig(BaseSampleConfiguration):
    model = RockSample
    fields = ["name", "rock_type", "collection_date", "weight_grams"]  # for forms and tables
    serializer_fields = ["rock_type", "collection_date"]               # added to the common fields
```

Every field the model requires must be in the list that applies, or a record cannot be created
through the API. [The start-up check](#the-start-up-check) tells you when one is missing.

### Tier 3 — `serializer_class` (full custom override)

For complete control, provide your own serializer class. **Custom serializers must subclass `BaseSampleSerializer` (or `BaseMeasurementSerializer` for Measurement models).** The portal refuses to load its API routes otherwise, with a `django.core.exceptions.ImproperlyConfigured` error that names the serializer and the base to build on.

```python
from fairdm.api.serializers import BaseSampleSerializer

class RockSampleSerializer(BaseSampleSerializer):
    class Meta(BaseSampleSerializer.Meta):
        model = RockSample
        fields = BaseSampleSerializer.Meta.fields + ["rock_type", "lab_code"]
        read_only_fields = ["lab_code"]

@fairdm.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    serializer_class = RockSampleSerializer
```

If the serializer has to be worked out in code, override `get_serializer_class` on the
configuration instead. The API uses whatever it returns, and the same rule applies to it:

```python
@fairdm.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample

    def get_serializer_class(self):
        return RockSampleSerializer
```

The base serializers carry what keeps the API safe: the narrowing of the parent a caller may choose,
the credit given to the person who creates a record, and the manage-level rule for changing a
record's visibility or parent. That is why a serializer built on a plain `ModelSerializer` is
refused whichever way it is supplied.

Extending `Meta` from the base class keeps the common fields (`url`, `uuid`, `name`, `dataset`, `added`, `modified`, and `local_id` and `status` for a sample, `sample` for a measurement) and the metadata that FairDM depends on. You can add, reorder, or override fields, but you cannot remove the common ones without risking broken API clients.

```{warning}
Passing a serializer that does not inherit from `BaseSampleSerializer` or `BaseMeasurementSerializer` raises:

    ImproperlyConfigured: Custom serializer_class 'RockSampleSerializer' for a Sample type must
    subclass 'fairdm.api.serializers.BaseSampleSerializer'.
```

### The start-up check

A registration whose API fields leave out a field the model requires cannot create a record. The
check `fairdm.E600` reports it when the portal starts, and in `manage.py check`, before any caller
meets the failure. It names the type and the field:

```text
demo.RockSample: (fairdm.E600) The API serializer for demo.RockSample does not accept the
required field 'rock_type', so no record of this type can be created through the API.
    HINT: Add 'rock_type' to serializer_fields (or fields) in the type's registration, or to the
    serializer it names.
```

A required field is one that is editable, has no default, and may be neither blank nor null. It
needs a writable field in the type's serializer, so a field the serializer returns as read-only is
reported too. The check looks at the serializer the API will
use, whether FairDM builds it or you supply it. See [Configuration Checks](../portal-administration/configuration-checks.md).

## Serializer and Filter Classes

The classes below are in `fairdm.api.serializers` and `fairdm.api.filters`. A serializer of your own
can build on any of them.

| Class | Use |
|-------|-----|
| `RecordSerializer` | Base of the four record serializers. Adds `url`, the five metadata fields and the creator credit |
| `ProjectSerializer`, `DatasetSerializer` | Written out, not generated. A dataset carries its `project` and `license`, a project its `owner` |
| `BaseSampleSerializer`, `BaseMeasurementSerializer` | Base of every generated sample and measurement serializer. `common_fields` lists the fields every record of the kind carries |
| `RecordReferenceField` | A relation to a record, returned as `{"uuid", "url"}` or `null` |
| `RecordURLField` | The address of a record, whatever its type |
| `RecordListSerializer` | Checks every reference on a page of records in one query. `RecordSerializer` uses it for lists |
| `DescriptionSerializer`, `DateSerializer`, `IdentifierSerializer`, `KeywordSerializer` | The read-only metadata rows of a record |
| `ContributionSerializer`, `RoleSerializer` | A credit on a record and the roles in it |
| `LicenseSerializer` | The licence of a dataset as `{"name", "url"}` |
| `ContributorSerializer`, `ContributorIdentifierSerializer` | A person or organization as their profile page shows them |
| `FairDMFilterBackend` | Adds the `dataset` and `sample` filters to a generated list |
| `DatasetFilterSet`, `SampleFilterSet` | The two filters, matching on short identifiers over the records the caller may see |

`fairdm.api.viewsets.sortable_fields(model, serializer_class)` returns the names a list can be
sorted on: the stored, non-relational fields the serializer returns. Set `ordering_fields` on a
viewset of your own to the result, or name the fields yourself.

## URL Slugs and verbose_name_plural

FairDM derives the `<model-slug>` component of every endpoint from the model's `verbose_name_plural` metadata (lowercased, spaces → hyphens). This gives you full control over URL structure without touching router configuration.

A sample type is served under `samples/` and a measurement type under `measurements/`, and the
route names carry the same prefix, so `reverse("api:samples-rock-samples-list")` gives
`/api/v1/samples/rock-samples/` and `reverse("api:measurements-xrf-measurements-list")` gives
`/api/v1/measurements/xrf-measurements/`. Because of the prefix, a sample type and a measurement
type with the same plural name do not collide. The names also live in the `api` namespace, so
they never clash with the portal's own page names such as `project-list`.

### Default derivation

The `verbose_name_plural` is set automatically by Django using the `Meta.verbose_name` (or the class name if not specified):

| Model class | Derived slug |
|-------------|--------------|
| `RockSample` (no Meta) | `rock-samples` |
| `SoilSample` (no Meta) | `soil-samples` |
| `XRFMeasurement` (no Meta) | `xrf-measurements` |

### Overriding the slug

Set `Meta.verbose_name_plural` in your model class:

```python
class ThinSection(Sample):
    """Petrographic thin section sample."""

    class Meta(Sample.Meta):
        verbose_name = "thin section"
        verbose_name_plural = "thin sections"  # → endpoint: /api/v1/samples/thin-sections/
```

### Renaming a type

Changing `verbose_name_plural` moves the type's endpoints and renames its routes. The old address
stops answering and nothing redirects from it, so tell the people who use the API before you
rename a type that has been published.

### Migration note for existing portals

If you are upgrading from a FairDM version that used CamelCase-decomposed slugs, your URL names and endpoint paths have changed. The table below shows the old and new slugs for common patterns:

| Model class | Old slug (CamelCase) | New slug (verbose_name_plural) |
|-------------|----------------------|--------------------------------|
| `RockSample` | `rock-sample` | `rock-samples` |
| `SoilSample` | `soil-sample` | `soil-samples` |
| `WaterSample` | `water-sample` | `water-samples` |
| `XRFMeasurement` | `x-r-f-measurement` | `xrf-measurements` |
| `ICP_MS_Measurement` | `i-c-p-m-s-measurement` | `icp-ms-measurements` |

Update any hardcoded API clients, `{% url %}` references, or OpenAPI schema snapshots after upgrading.

## Extending the Router with Custom Viewsets

The router is public as `fairdm_api_router`. A viewset registered on it is served at
`/api/v1/<prefix>/` beside the generated endpoints and appears in the
[interactive documentation](#interactive-documentation) and the schema at `/api/v1/schema/`.

```python
from fairdm.api.router import fairdm_api_router
from fairdm.api.viewsets import BaseViewSet
from myportal.models import SpecialSample
from myportal.serializers import SpecialSampleSerializer

class SpecialSampleViewSet(BaseViewSet):
    queryset = SpecialSample.objects.all()
    serializer_class = SpecialSampleSerializer

fairdm_api_router.register(r"special-samples", SpecialSampleViewSet, basename="special-samples")
```

The router reads its routes once, when `fairdm.api.urls` is first loaded. Register from your app's
`ready()` method, or from any module that is imported before the URL configuration is used, and
the route is there from the first request. A viewset registered later is not served until that
module is loaded again.

`BaseViewSet` finds a record by its short identifier (`lookup_field = "uuid"`) and requires a
signed-in person to write. Its permissions and filters come from the API's settings, so a viewset
of your own is held to the same visibility rules as the generated ones. The route name is
`<basename>-list` and `<basename>-detail` in the `api` namespace.

A type registered with the registry does not need this. Its endpoints are generated, and
registration stops the portal with the real error when they cannot be built, so a mistake in a
type's configuration is not hidden behind a missing route.

## Limits on Use

Each kind of caller has two limits, one over a minute to stop a burst and one over a day. A caller
with a token or a session is allowed several times what an anonymous caller is. The throttles are
in `fairdm.api.throttling` and the rates are entries of `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]`:

| Throttle | Rate name | Default |
|----------|-----------|---------|
| `AnonBurstThrottle` | `anon_burst` | 30/minute |
| `AnonDailyThrottle` | `anon_day` | 2000/day |
| `UserBurstThrottle` | `user_burst` | 120/minute |
| `UserDailyThrottle` | `user_day` | 20000/day |

An anonymous caller is counted by the two anonymous throttles only, by address. A signed-in caller
is counted by the two others only, as the person. Change a rate in your portal's settings after
`fairdm.setup()` returns, and restart:

```python
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user_day"] = "100000/day"
```

A rate is a number, a slash and `second`, `minute`, `hour` or `day`. `None` removes a limit. A
replaced dictionary must hold all four names. Django REST framework reads the dictionary once, when
its throttling module is first imported, so the change belongs in the settings file, not in code
that runs later.

A caller past a limit receives `429 Too Many Requests` with a `Retry-After` header giving the
seconds to wait. Counts are kept in Django's default cache, so a production portal needs the shared
cache it already requires, and the limits count per address only once
`REST_FRAMEWORK["NUM_PROXIES"]` holds the number of proxies in front of the portal. Without it, the
address comes from a header the caller controls. The portal administration guide gives the same
settings for an administrator: see [Limits on the API](../portal-administration/api-limits.md).

The page size follows the same pattern. A list holds `REST_FRAMEWORK["PAGE_SIZE"]` records (100)
unless `?page_size=` asks for another number, up to `FAIRDM_API_MAX_PAGE_SIZE` (1000).
`FairDMPagination` reads both when it answers, so a changed setting changes the API.

## CORS

Pages on other websites may call the API, to read and to write with a token. FairDM answers any
origin under `/api/`, and no other address:

```python
CORS_ALLOW_ALL_ORIGINS = True
CORS_URLS_REGEX = r"^/api/.*$"
```

A preflight that asks to send the `Authorization` header is allowed. Credentials are not allowed
(`CORS_ALLOW_CREDENTIALS` is left unset), so a browser does not send the portal's sign-in cookie
from another site and the API would not accept it. A page on another site must send a token.

To answer only some sites, override both settings in your portal's settings after
`fairdm.setup()` returns:

```python
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://my-portal-frontend.example.com",
]
```

## OpenAPI Schema Customisation

Override the API title, description, and version in your portal settings:

```python
SPECTACULAR_SETTINGS = {
    "TITLE": "My Research Portal API",
    "DESCRIPTION": "RESTful API for the My Research Portal research data portal.",
    "VERSION": "2.0.0",
}
```

## Customizing the API Description

FairDM ships with a rich default API description and title that appear in Swagger UI and the raw OpenAPI schema. You can override them without modifying the framework:

```python
# In your portal's settings.py
FAIRDM_API_TITLE = "Palaeo-Climate Data Portal API"
FAIRDM_API_DESCRIPTION = """\
## Palaeo-Climate Data Portal API

Programmatic access to all published palaeo-climate data in this portal.

### Resources

- `/api/v1/projects/` — Research projects
- `/api/v1/datasets/` — Sampled datasets
- `/api/v1/samples/` — Discover all sample types

See the [Developer Guide](https://my-portal.example.com/docs/api/) for full details.
"""
```

FairDM merges these settings into `SPECTACULAR_SETTINGS` automatically at startup. You can also override `SPECTACULAR_SETTINGS['VERSION']` directly if you need to change the API version string.

Whatever you write, the schema's description ends with FairDM's own sections on authentication, limits and paging, read from your settings when the schema is generated (see [Interactive Documentation](#interactive-documentation)). The `fairdm.api.schema.ApiDescription` class writes them, and `fairdm.api.schema.describe_api` appends them. Do not write those numbers into your own text. If you replace `SPECTACULAR_SETTINGS` altogether, keep `fairdm.api.schema.describe_api` in its `POSTPROCESSING_HOOKS` list, after `drf_spectacular.hooks.postprocess_schema_enums`, to keep them.

## Schema Naming Conventions

FairDM auto-generates serializer classes for all registered models. The serializer class names follow the pattern `{ModelName}Serializer` (e.g. `RockSampleSerializer`, `XRFMeasurementSerializer`). drf-spectacular strips the `Serializer` suffix when deriving OpenAPI schema component names, so the components appear as clean names in Swagger:

| Model class | Serializer class | Schema component |
|-------------|-----------------|------------------|
| `RockSample` | `RockSampleSerializer` | `RockSample` |
| `XRFMeasurement` | `XRFMeasurementSerializer` | `XRFMeasurement` |
| `Project` | `ProjectSerializer` | `Project` |

`Patched*` components (from `COMPONENT_SPLIT_PATCH=True`) follow the same clean naming pattern:

| Operation | Schema component |
|-----------|-----------------|
| `PATCH /samples/rock-samples/{uuid}/` | `PatchedRockSample` |

:::{note}
**Migration note**: If you were code-generating API clients from an older FairDM OpenAPI schema,
schema component names have changed — `RockSampleAPI` → `RockSample`, `PatchedProjectAPI` →
`PatchedProject`. Regenerate your client code after upgrading.
:::

## Model Descriptions in the API Docs

Swagger UI shows a description for each endpoint group. For auto-generated viewsets, FairDM
resolves the description from the registry configuration using the following priority order:

1. `ModelConfiguration.description` (top-level attribute)
2. `ModelConfiguration.metadata.description` (from `ModelMetadata`)
3. Model class docstring
4. Fallback: `"Endpoints for managing {verbose_name_plural}."`

To provide a meaningful description visible in Swagger, add it to your registry config:

```python
@fairdm.register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    metadata = ModelMetadata(
        description=(
            "Geological rock samples collected from field sites. Each sample records "
            "lithology, collection date, weight, and mineralogical observations."
        ),
        # ... other metadata ...
    )
    fields = [...]
```

The description is displayed in Swagger UI when users expand the endpoint group for `RockSample`.

## API Navigation Sidebar

FairDM adds one **API** entry to the **Documentation** group of the portal sidebar. It leads to the
interactive documentation (`view_name="api:api-docs"`, `/api/v1/docs/`), and the group and its entry
are rendered without any template change. To link to documentation of your own as well, add an entry
to the sidebar menu as for any other page.
