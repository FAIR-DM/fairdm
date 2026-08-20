# Contributors

Every person or organisation credited on a project, dataset, sample or measurement is a
**Contributor** (`fairdm.contrib.contributors.models.Contributor`). It is the base model
for two concrete types:

- **Person** — an individual, and also the account a user logs in with (`AUTH_USER_MODEL`).
- **Organization** — an institution, such as a university, research institute or funding body.

`Contributor` is a polymorphic model with its own table. Querying it returns each row as its
own concrete class, without the caller needing to know in advance which type it is.

## Fields

Every field below is declared once on `Contributor` and shared by both concrete types.

| Field | Type | Notes |
|---|---|---|
| `uuid` | `ShortUUIDField` | The contributor's public identifier. Generated on first save, carries the `c` prefix, and is unique across both concrete types. |
| `name` | `CharField` | The contributor's preferred name. Required. |
| `alternative_names` | `JSONField` | Other names by which the contributor is known. Optional. |
| `profile` | `TextField` | A free-text description. Optional. |
| `image` | `ThumbnailerImageField` | A profile image. Optional. |
| `links` | `JSONField` | Related online resources. Optional. |
| `lang` | `JSONField` | Language preferences, each an ISO 639-1 code. Refused if any code isn't. |
| `location` | `ForeignKey` to `fairdm.contrib.location.Point` | The contributor's geographic location. Optional. |
| `config` | `JSONField` | General-purpose configuration data. This specification does not define its contents. |
| `added` | `DateTimeField` | Set once, on creation. |
| `modified` | `DateTimeField` | Moves on every save. |

`last_synced` and `synced_data` also exist on `Contributor`, but they belong to external
identifier synchronisation, a separate specification — see
[`portal-development/contributors.md`](../portal-development/contributors.md) for that surface.

## The public identifier

`uuid` is generated the first time a contributor is saved and never changes after that,
whichever concrete type the contributor is:

```python
from fairdm.contrib.contributors.models import Organization, Person

person = Person.objects.create_unclaimed(first_name="Jane", last_name="Doe")
organization = Organization.objects.create(name="Example University")

assert person.uuid.startswith("c")
assert organization.uuid.startswith("c")
```

No two contributors, of either type, ever share one — `uuid` carries a database-level
uniqueness constraint across the whole `Contributor` table.

## Querying by the base type

Because `Contributor` is polymorphic, a queryset against it returns each row as its actual
concrete class:

```python
from fairdm.contrib.contributors.models import Contributor, Organization, Person

person = Person.objects.create_unclaimed(first_name="Jane", last_name="Doe")
organization = Organization.objects.create(name="Example University")

assert isinstance(Contributor.objects.filter(pk=person.pk).first(), Person)
assert isinstance(Contributor.objects.filter(pk=organization.pk).first(), Organization)
```

## The configuration store

`config` is a general-purpose JSON store. This specification deliberately does not define
what belongs in it — that is left to whatever later work needs a place to keep contributor-level
settings. It defaults to an empty dict and imposes no schema:

```python
person.config = {"anything": "this specification does not define"}
person.save()

person.refresh_from_db()
assert person.config == {"anything": "this specification does not define"}
```

## Organization

`Organization` is the institutional concrete type — a university, research institute, funding
body, company or similar. In addition to the fields every `Contributor` carries, it has:

| Field | Type | Notes |
|---|---|---|
| `type` | `CharField`, choices `OrganizationType` | The kind of institution. Optional. Refused if set to anything outside ROR schema 2.1's nine values: `education`, `funder`, `healthcare`, `company`, `archive`, `nonprofit`, `government`, `facility`, `other`. Indexed, since listing and filtering by institution kind is its purpose. |
| `parent` | `ForeignKey` to `Organization` | The organisation this one is a part of, such as a department's university. Optional. |
| `city` | `CharField` | The city the organisation is based in. Optional, indexed. |
| `country` | `CountryField` | The country the organisation is based in. Optional, indexed. |

ROR itself permits an organisation several types at once. This model deliberately narrows that
to a single selection — a portal displaying and filtering by institution kind wants one answer.

### Hierarchy, and what happens when a parent is deleted

An organisation may name another organisation as its parent, and is reachable from that parent
through `sub_organizations`:

```python
from fairdm.contrib.contributors.models import Organization

university = Organization.objects.create(name="Example University", type="education")
department = Organization.objects.create(
    name="Department of Geology", parent=university, type="education"
)

assert department.parent == university
assert department in university.sub_organizations.all()
```

Deleting a parent organisation does **not** delete its sub-organisations, their members or
their credits. A surviving sub-organisation simply loses its parent:

```python
university.delete()

department.refresh_from_db()
assert department.parent is None
```

## External identifiers

Either concrete type may carry external identifiers —
`ContributorIdentifier` (`fairdm.contrib.contributors.models.ContributorIdentifier`), a record
with a `type` and a `value`, linked to the contributor it belongs to:

```python
from fairdm.contrib.contributors.models import ContributorIdentifier, Person

person = Person.objects.create_unclaimed(first_name="Jane", last_name="Doe")
ContributorIdentifier.objects.create(related=person, type="ORCID", value="0000-0001-2345-6789")

assert person.identifiers.count() == 1
```

A contributor never carries two identifiers of the same type. It is refused at the database and
at `clean()`, whose message names the type:

```python
from django.core.exceptions import ValidationError

duplicate = ContributorIdentifier(related=person, type="ORCID", value="0000-0001-0000-0000")
try:
    duplicate.clean()
except ValidationError as exc:
    assert "ORCID" in str(exc)
```

Each concrete type expects one identifier type by default — `Person.DEFAULT_IDENTIFIER` is
`"ORCID"`, `Organization.DEFAULT_IDENTIFIER` is `"ROR"` — and reports the identifier of that type
as its default through `get_default_identifier()`, returning nothing when it carries none:

```python
from fairdm.contrib.contributors.models import Organization

assert person.get_default_identifier().value == "0000-0001-2345-6789"

organization = Organization.objects.create(name="Example University")
assert organization.get_default_identifier() is None
```

Fetching an identifier's contents from ORCID or ROR, and keeping them current, belongs to the
external identifier synchronisation specification, not this one — this record only carries the
type and the value.

## See also

- [`Person`](../portal-development/contributors.md) — the account a user logs in with, and
  what "claimed" means.
- [`Organization`](../portal-administration/managing_contributors.md) — managing organisations
  and their members from the admin interface.
