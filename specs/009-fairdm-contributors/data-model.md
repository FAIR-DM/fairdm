# Data Model: FairDM Contributors System

**Date**: 2026-02-18
**Feature**: 009-fairdm-contributors

## Entity Relationship Overview

```
┌───────────────────────────────────────────┐
│           Contributor (polymorphic)        │
│  uuid, name, image, profile, links,       │
│  lang, alternative_names, synced_data,    │
│  last_synced, weight, location,           │
│  privacy_settings, added, modified        │
├───────────────┬───────────────────────────┤
│    Person     │      Organization         │
│  (AbstractUser│  parent (self-FK)         │
│  + Contributor│  city, country            │
│  email, first │                           │
│  last, etc.)  │                           │
└───────┬───────┘───────────┬───────────────┘
        │                   │
        │  ┌────────────┐   │
        ├──│ Affiliation │──┤
        │  │ role, dates │  │
        │  └────────────┘   │
        │                   │
        │  ┌──────────────────────────────┐
        └──│      Contribution            │
           │  contributor (FK→Contributor) │
           │  content_type + object_id    │
           │  (GFK → Project/Dataset/     │
           │   Sample/Measurement)        │
           │  roles (M2M→Concept)         │
           │  affiliation (FK→Org)        │
           │  order                       │
           └──────────────────────────────┘

┌──────────────────────────────┐
│   ContributorIdentifier      │
│  type, value                 │
│  related (FK→Contributor)    │
└──────────────────────────────┘
```

---

## Entity Details

### 1. Contributor (Base — Polymorphic)

**Table:** `contributors_contributor`
**Inheritance:** `PolymorphicMixin`, `PolymorphicModel`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | auto | Django default PK |
| `polymorphic_ctype` | FK → ContentType | auto | django-polymorphic discriminator |
| `uuid` | ShortUUIDField | unique, editable=False, prefix="c" | Stable public identifier |
| `name` | CharField(512) | required | Preferred display name |
| `alternative_names` | ArrayField(CharField(255)) | nullable, default=[] | Aliases, transliterations |
| `image` | ThumbnailerImageField | nullable | Profile photo/logo, resized to 1200×1200 WEBP |
| `profile` | TextField | nullable | Free-text biography / description |
| `links` | ArrayField(URLField) | nullable, default=[] | External profile URLs |
| `lang` | ArrayField(CharField(5)) | nullable, default=[] | ISO 639-1 language codes |
| `synced_data` | JSONField | editable=False, default={} | Raw API response from ORCID/ROR |
| `last_synced` | DateField | editable=False, nullable | Timestamp of last external sync |
| `weight` | FloatField | default=1.0, editable=False | Computed relevance score |
| `location` | FK → fairdm_location.Point | nullable, SET_NULL | Geographic location |
| `privacy_settings` | JSONField | default={} | Per-field privacy controls (NEW) |
| `added` | DateTimeField | auto_now_add | Record creation timestamp |
| `modified` | DateTimeField | auto_now | Last modification timestamp |

**Meta:**
- `ordering = ["name"]`
- `verbose_name = "contributor"`

**Key Methods:**
- `__str__()` → `self.name`
- `get_absolute_url()` → `/contributor/{uuid}/`
- `is_claimed` → computed property (on Person subclass)
- `profile_image()` → image URL or static fallback
- `calculate_weight()` → 50% contributions + 30% profile + 20% identifiers
- `to_datacite()` / `to_schema_org()` → delegate to transform registry
- `get_co_contributors(limit)` → frequency-ranked collaborators
- `add_to(obj, roles)` → create/update Contribution
- `get_visible_fields(viewer)` → privacy-aware field dictionary (NEW)
- `projects` / `datasets` / `samples` / `measurements` → contribution-based reverse queries

---

### 2. Person (Contributor + Auth User)

**Table:** `contributors_person`
**Inheritance:** `AbstractUser`, `Contributor`
**AUTH_USER_MODEL:** `contributors.Person`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `contributor_ptr` | OneToOneField (PK) | auto | Polymorphic parent link |
| **Inherited from AbstractUser:** | | | |
| `password` | CharField(128) | required | Hashed password |
| `last_login` | DateTimeField | nullable | Last login timestamp |
| `is_superuser` | BooleanField | default=False | Django superuser flag |
| `first_name` | CharField(150) | blank | Given name |
| `last_name` | CharField(150) | blank | Family name |
| `email` | EmailField | unique, nullable | Login identifier; NULL = unclaimed |
| `is_staff` | BooleanField | default=False | Admin access flag |
| `is_active` | BooleanField | default=True | Account active flag; False = unclaimed |
| `date_joined` | DateTimeField | auto | Registration timestamp |
| `groups` | M2M → Group | | Django auth groups |
| `user_permissions` | M2M → Permission | | Django auth permissions |

**Class Constants:**
- `DEFAULT_IDENTIFIER = "ORCID"`
- `USERNAME_FIELD = "email"`
- `REQUIRED_FIELDS = ["first_name", "last_name"]`

**Managers:**
- `objects = UserManager()` — email-based user creation (no username)
- `contributors = PersonalContributorsManager()` — excludes superusers and guardian anonymous user; provides `claimed()` and `unclaimed()` queryset methods (NEW)

**Key Methods:**
- `is_claimed` → `@property`: `email is not None and is_active and has_usable_password()`
- `save()` → auto-populates `name` from `first_name + last_name` if blank
- `clean()` → validates email, URLs, ORCID format; prevents claimed users from nulling email; lowercases email fully
- `orcid()` → returns first ORCID identifier
- `primary_affiliation()` → returns primary Affiliation
- `current_affiliations()` → active Affiliations (end_date=NULL)
- `given` / `family` → property aliases for `first_name` / `last_name`
- `from_orcid(orcid_id)` → classmethod factory via ORCIDTransform

**Validation Rules:**
- Unclaimed: `email = NULL`, `is_active = False`, `set_unusable_password()`
- Claimed: `email` required (non-NULL), `is_active = True`, password hash present
- Transition: claiming sets `email`, `is_active = True`, and sets a usable password (via allauth)

---

### 3. Organization (Contributor subclass)

**Table:** `contributors_organization`
**Inheritance:** `Contributor`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `contributor_ptr` | OneToOneField (PK) | auto | Polymorphic parent link |
| `members` | M2M → Person | through=Affiliation | Organization members |
| `parent` | FK → Organization (self) | nullable, CASCADE | Parent institution |
| `city` | CharField(255) | nullable | City name |
| `country` | CountryField | nullable | ISO 3166 country |

**Class Constants:**
- `DEFAULT_IDENTIFIER = "ROR"`

**Meta:**
- `permissions = [("manage_organization", "Can manage organization")]` (NEW)
- `verbose_name = "organization"`

**Key Methods:**
- `clean()` → validates URLs, ROR format
- `update_identifier()` → `@hook(AFTER_CREATE)` extracts ROR ID from synced_data
- `from_ror(ror, commit)` → `@classmethod` factory via RORTransform (FIX: `cls` not `self`)
- `owner()` → returns Affiliation record with role="owner"
- `get_memberships()` → select_related query for all affiliations
- `as_geojson()` → GeoJSON Feature from location

---

### 4. Affiliation (was: OrganizationMember)

**Table:** `contributors_affiliation` (renamed from `contributors_organizationmember`)
**Inheritance:** `models.Model`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | auto | |
| `person` | FK → Person | CASCADE, related_name="affiliations" | Member person |
| `organization` | FK → Organization | CASCADE, related_name="memberships" | Organization |
| `type` | IntegerField | default=0 | Security/verification state: 0=PENDING, 1=MEMBER, 2=ADMIN, 3=OWNER |
| `is_primary` | BooleanField | default=False | Primary affiliation flag (for citations) |
| `start_date` | PartialDateField | nullable | When affiliation began (year, year-month, or full date) |
| `end_date` | PartialDateField | nullable | When it ended; NULL = active |

**Meta:**
- `verbose_name = "affiliation"`
- `unique_together = ("person", "organization")`

**Validation Rules:**
- Only one `is_primary=True` per person (enforced in `save()`)
- Active affiliation: `end_date IS NULL`
- Historical affiliation: `end_date IS NOT NULL`
- PartialDate validation: accepts `{"year": 1987}` or `{"year": 1987, "month": 3}` or `{"year": 1987, "month": 3, "day": 15}`

**Security State Machine (via `type` field):**
```
PENDING (0) ──[verified by existing member]──> MEMBER (1)
                                                    │
                                     [promoted by admin/owner]
                                                    ↓
                                                ADMIN (2)
                                                    │
                                    [ownership transferred]
                                                    ↓
                                                OWNER (3)

All states can transition to historical by setting end_date
```

**Lifecycle Hooks:**
- When `type` changes to/from `3` (OWNER), sync `manage_organization` permission via django-guardian
- When `type=0` (PENDING), exclude from organization member queries (requires verification)

---

### 5. Contribution (Junction — GFK)

**Table:** `contributors_contribution`
**Inheritance:** `LifecycleModelMixin`, `OrderedModel`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | auto | |
| `content_type` | FK → ContentType | CASCADE | GFK target type |
| `object_id` | CharField(23) | | GFK target ID (ShortUUID) |
| `content_object` | GenericForeignKey | | Resolved target (Project/Dataset/Sample/Measurement) |
| `contributor` | FK → Contributor | SET_NULL, nullable | Contributing entity |
| `roles` | ConceptManyToManyField | vocabulary=FairDMRoles | Role(s) on this contribution |
| `affiliation` | FK → Organization | PROTECT, nullable | Affiliation at time of contribution |
| `order` | PositiveIntegerField | auto (OrderedModel) | Display ordering |

**Meta:**
- `verbose_name = "contributor"`
- `unique_together = ("content_type", "object_id", "contributor")`
- `ordering = ["object_id", "order"]`

**Lifecycle Hooks:**
- `BEFORE_CREATE`: auto-set `affiliation` from person's primary org
- `AFTER_DELETE`: clean up object-level permissions

**Key Class Method:**
- `add_to(cls, contributor, obj, roles, affiliation)` — creates contribution + sets roles

---

### 6. ContributorIdentifier

**Table:** `contributors_contributoridentifier`
**Inheritance:** `AbstractIdentifier`, `LifecycleModelMixin`

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | AutoField (PK) | auto | |
| `type` | CharField(50) | | Identifier type (ORCID, ROR, etc.) |
| `value` | CharField(255) | unique, indexed | Identifier value |
| `related` | FK → Contributor | CASCADE | Owner contributor |

**Constraints:**
- `UniqueConstraint("related", "type")` — one identifier per type per contributor

**Vocabulary:** `FairDMIdentifiers` with collections:
- Person: ORCID, ResearcherID
- Organization: ROR, Wikidata, ISNI, Crossref Funder ID

**Lifecycle Hooks:**
- `AFTER_CREATE`: dispatch Celery task `sync_contributor_identifier.delay(self.pk)` via `transaction.on_commit()` (CHANGED from synchronous API call)

---

## Relationship Summary

| From | To | Type | Through | Cardinality |
|------|----|------|---------|-------------|
| Person | Organization | M2M | Affiliation | many-to-many |
| Organization | Organization (self) | FK (parent) | — | many-to-one |
| Contributor | Project/Dataset/Sample/Measurement | GFK | Contribution | many-to-many |
| Contributor | ContributorIdentifier | reverse FK | — | one-to-many |
| Contribution | Organization | FK (affiliation) | — | many-to-one |
| Contribution | Concept (FairDMRoles) | M2M | auto | many-to-many |

---

## Index Strategy

| Table | Index | Fields | Purpose |
|-------|-------|--------|---------|
| contributor | unique | uuid | Public lookup |
| contributor | btree | name | Ordering, search |
| person | unique | email | Auth login (NULLs allowed) |
| affiliation | unique | (person, organization) | Prevent duplicates |
| affiliation | btree | end_date | Active membership queries |
| contribution | unique | (content_type, object_id, contributor) | Prevent duplicates |
| contribution | btree | (content_type, object_id) | GFK reverse queries |
| contributoridentifier | unique | value | Cross-system lookup |
| contributoridentifier | unique | (related, type) | One per type per contributor |
