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

## See also

- [`Person`](../portal-development/contributors.md) — the account a user logs in with, and
  what "claimed" means.
- [`Organization`](../portal-administration/managing_contributors.md) — managing organisations
  and their members from the admin interface.
