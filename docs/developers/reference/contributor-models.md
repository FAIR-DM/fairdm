# Contributor models

This page lists the models, fields, managers, methods and helper modules of `fairdm.contrib.contributors` that describe people and organizations: `Contributor`, `Person`, `Organization`, `Affiliation`, `Contribution` and `ContributorIdentifier`. It also covers the profile helper functions, the profile editing forms and the transform classes. It does not cover the contribution levels and the permission checks built on them, which are in [Contribution levels and record access](contribution-levels-and-record-access.md), the methods that change who is credited on a record, which are in [Crediting](crediting.md), or the claiming functions, which are in [Profile claiming](profile-claiming.md). The reasons behind the design are in [How contributor accounts and credits work](../../explanation/how-contributor-accounts-and-credits-work.md).

Every class below is imported from `fairdm.contrib.contributors.models` unless a section says otherwise. The generated [Python API](python-api.md) holds the docstrings.

## Contributor

`Contributor` is the polymorphic base of `Person` and `Organization`. It has a table of its own. A query on `Contributor` returns each row as its concrete class.

| Field | Type | Default | What it holds | What it accepts |
|---|---|---|---|---|
| `uuid` | `ShortUUIDField`, prefix `c` | Generated on first save | The public identifier. Unique across both concrete types and never changed. Not editable | Not set by hand |
| `image` | `ThumbnailerImageField` | `None` | The profile image. The stored source is resized to at most 1200 by 1200 pixels as WebP | An image file |
| `name` | `CharField(max_length=512)` | None, required | The name the contributor is publicly known by | Text |
| `alternative_names` | `JSONField` | `[]` | Other names the contributor is known by | A list of strings |
| `profile` | `TextField` | `None` | A free-text description | Text |
| `links` | `JSONField` | `[]` | Online resources about the contributor | A list of web addresses. `Person.clean()` and `Organization.clean()` check each with Django's `URLValidator` |
| `lang` | `JSONField` | `[]` | The contributor's languages | A list of ISO 639-1 codes, checked by `validate_iso_639_1_language_codes` |
| `last_synced` | `DateField` | `None` | The date `synced_data` last changed. Set on save. Not editable | Not set by hand |
| `synced_data` | `JSONField` | `{}` | The raw record from the external provider. Not editable | Not set by hand |
| `config` | `JSONField` | `{}` | A general-purpose store. Nothing in FairDM reads it or enforces anything from it | Any JSON value |
| `added` | `DateTimeField` | Set once, on creation | When the row was created | Not set by hand |
| `modified` | `DateTimeField` | Set on every save | When the row was last saved. Indexed | Not set by hand |

`Contributor.Meta` orders rows by `name` and sets `default_related_name` to `contributors`.

| Attribute | Value | What it does |
|---|---|---|
| `is_organization` | `False` on `Contributor` and `Person`, `True` on `Organization` | Lets a template branch on the concrete type |
| `DEFAULT_IDENTIFIER` | `"ORCID"` on `Person`, `"ROR"` on `Organization` | The identifier type that `get_default_identifier()` returns |

| Member | Returns | What it does |
|---|---|---|
| `get_absolute_url()` | `str` | The address of the overview page |
| `get_update_url()` | `str` | The address of the profile editing page |
| `is_editable_by(user)` | `bool` | Whether `user` may edit the profile. `False` on `Contributor`, overridden by `Person` and `Organization`. See [Who may edit a profile](#who-may-edit-a-profile) |
| `get_default_identifier()` | `ContributorIdentifier` or `None` | The identifier of type `DEFAULT_IDENTIFIER`. Reads `identifiers.all()`, so a queryset that prefetches `identifiers` costs no query per contributor |
| `default_identifier` | Property, same as above | |
| `get_identifier_icon()` | The rendered icon | The icon for the default identifier type |
| `primary_organization` | Property, `None` | Overridden by `Person` |
| `profile_image()` | `str` | The image address, or the portal's brand icon when there is no image |
| `get_initials()` | `str` | The first letters of the first two words of `name`, or `""` without a name |
| `type_of` | Class property, `Contributor` | The polymorphic base type |
| `projects`, `datasets` | Properties, querysets | The projects and datasets the contributor is credited on |
| `samples`, `measurements` | Properties, querysets | The samples and measurements the contributor is credited on, whatever their registered type |
| `credited_object_ids(base_model)` | A values queryset of ids | The ids of the contributor's credits on `base_model` or one of its subclasses |
| `get_public_projects()` | Queryset | The public projects the contributor is credited on. `Organization` adds the ones it owns |
| `get_public_datasets()` | Queryset | The public datasets the contributor is credited on, outside private projects. `Organization` adds the ones in its projects |
| `get_credit_counts()` | `dict` | The number of credits for each credited model, keyed by the model's plural verbose name |
| `get_visible_contributions(user)` | `list` of `Contribution` | The credits a profile may name, newest first. A project or dataset counts when it is one of the two public lists above. A sample or measurement counts when `visible_to(user)` lets the user see it and its dataset's project, if it has one, is public. Each credit carries `kind` (`project`, `dataset`, `sample` or `measurement`). Projects and datasets also carry `record` |
| `get_role_counts(contributions=None)` | `Counter` | The number of credits each contribution role is held on, keyed by label. Counts every credit when `contributions` is omitted |
| `get_recent_contributions(limit=5)` | Queryset slice | The newest credits |
| `get_contributions_by_type(model_name)` | Queryset | The credits on one model, such as `"project"` |
| `has_contribution_to(obj)` | `bool` | Whether the contributor is credited on `obj` |
| `get_collaborators(limit=None, contributions=None)` | Queryset | The other contributors credited on the same records, most frequent first and ties by name. Each carries `collaboration_count` |
| `add_to(obj, roles=None)` | `Contribution` | Credits the contributor on `obj`, adding `roles` (names from the roles vocabulary) to any credit already there. A person credited for the first time starts at the view level. An organization has no level |
| `get_links_display()` | `list` of `{"url", "host"}` | One entry for each `http` or `https` link, in the order recorded. Other links are left out |
| `get_language_names()` | `list` of `str` | The names of the recorded languages in the active language. An unknown code is kept as written |
| `to_datacite()` | `dict` | The contributor as a DataCite creator or contributor object |
| `to_schema_org()` | `dict` | The contributor as a Schema.org `Person` or `Organization` |
| `to_public_schema_org()` | `dict` | `to_schema_org()` without the email address |

### Language codes

`fairdm.contrib.contributors.validators` holds the checks behind `lang`:

| Name | Type | What it does |
|---|---|---|
| `ISO_639_1_CODES` | `frozenset` | The accepted codes |
| `validate_iso_639_1_language_code(value)` | Validator | Refuses a value outside `ISO_639_1_CODES`, naming the value |
| `validate_iso_639_1_language_codes(value)` | Validator | Applies the single-code check to each element of a list. An empty value passes |

Attach `validate_iso_639_1_language_codes` to a field of your own that holds a list of language codes.

## Person

`Person` extends Django's `AbstractUser` and `Contributor`. It is the portal's user model. `fairdm.setup()` sets `AUTH_USER_MODEL` to `contributors.Person` and people sign in with their email address. The `username` field is removed.

| Field | Type | Default | What it holds | What it accepts |
|---|---|---|---|---|
| `email` | `EmailField`, unique, nullable | `None` | The sign-in address. Empty for a profile made for attribution alone | A valid address. `clean()` stores an empty string as `None` and lowercases the address |
| `is_claimed` | `BooleanField`, indexed | `False` | Whether the person has claimed the profile | `True` or `False` |

The `AbstractUser` fields (`first_name`, `last_name`, `is_active`, `is_staff`, `is_superuser`, `password`, `last_login`, `date_joined`, `groups`, `user_permissions`) are inherited. `USERNAME_FIELD` is `email` and `REQUIRED_FIELDS` is empty. A constraint, `unique_person_email_ci`, makes addresses unique regardless of case.

`save()` fills a blank `name` from `first_name` and `last_name`. `clean()` also refuses a claimed person with no email, a link that is not a web address, and an ORCID identifier that does not match the form `0000-0000-0000-0000`.

| Member | Returns | What it does |
|---|---|---|
| `account_state` | `AccountState` | One of `GHOST`, `INVITED`, `CLAIMED` or `INACTIVE`, worked out from `is_active`, `is_claimed` and `email`. Inactive wins, then claimed, then invited when there is an email, else ghost |
| `can_sign_in()` | `bool` | Whether the account is active and the person has claimed it or has signed in (`last_login` is set) |
| `is_editable_by(user)` | `bool` | See [Who may edit a profile](#who-may-edit-a-profile) |
| `orcid()` | `ContributorIdentifier` or `None` | The person's ORCID identifier |
| `orcid_is_authenticated` | `bool` property | Whether the person has signed in with ORCID. Reads `socialaccount_set.all()` |
| `get_provider(provider)` | Social account or `None` | The person's allauth social account for a provider id such as `"orcid"` |
| `primary_affiliation()` | `Affiliation` or `None` | The primary affiliation, when it is verified (member or above) and has no end date. Reads `affiliations.all()` |
| `primary_organization` | `Organization` or `None` | The organization of `primary_affiliation()` |
| `current_affiliations()` | Queryset | Affiliations with no end date and a type of member or above, with the organization loaded |
| `get_affiliation_history()` | `dict` | `current` (the primary affiliation first, the rest by organization name) and `past` (most recently ended first). Pending affiliations are left out |
| `portal_roles` | `list` of labels | The labels of the portal roles the person holds, in declaration order. Empty for an inactive person. Reads `groups.all()` |
| `get_initials()` | `str` | The initials of `first_name` and `last_name`, else of `name` |
| `given`, `family` | Properties | `first_name` and `last_name` |
| `get_full_name_display(name_format="given_family")` | `str` | The name as `given_family` ("John Doe"), `family_given` ("Doe, John"), `family_initial` ("Doe, J.") or `initials_family` ("J. Doe"). Any other value gives `given_family`. Returns `name` when both names are empty |
| `member_since` | Property | `date_joined`, or `None` for a profile nobody has claimed |
| `get_profile_completeness()` | `dict` | A flag for each of `image`, `orcid`, `profile`, `primary_affiliation` and `links` |
| `get_location_display()` | `str` or `None` | The city and country of the primary affiliation's organization |
| `as_geojson()` | `str` or `None` | A GeoJSON feature placed at the primary affiliation's organization. `None` when that organization has no location |
| `icon()` | `str` | `"orcid"` or `"orcid_unauthenticated"` |

`Person.objects` is a `UserManager`. `Person.objects.all().<method>()` and `Person.objects.<method>()` give the same result.

| Method | Returns | What it does |
|---|---|---|
| `create_user(email, password=None, **extra_fields)` | `Person` | Makes a person who is neither staff nor superuser. Does not set `is_claimed`. A `password` of `None` sets an unusable password. Raises `ValueError` without an email |
| `create_superuser(email, password=None, **extra_fields)` | `Person` | Makes a staff superuser. Raises `ValueError` when `is_staff` or `is_superuser` is passed as false |
| `create_unclaimed(first_name, last_name, **extra_fields)` | `Person` | Makes a ghost profile: active, unclaimed, no email, an unusable password. `name` defaults to the two names joined |

The queryset methods of `PersonQuerySet`:

| Method | Keeps |
|---|---|
| `real()` | Everyone except superusers and the anonymous placeholder (email `AnonymousUser`). Ghost and invited profiles stay in |
| `active()` | `is_active=True` |
| `inactive()` | `is_active=False`, whatever the claim status |
| `claimed()` | `is_active=True` and `is_claimed=True` |
| `unclaimed()` | `is_claimed=False`, which covers ghost, invited and inactive unclaimed profiles |
| `ghost()` | Active, unclaimed, no email |
| `invited()` | Active, unclaimed, with an email |
| `for_cards()` | Everyone, with `identifiers`, `socialaccount_set`, `affiliations__organization` and `groups` prefetched, so a card or list row costs no query per person |

`AccountState` is in `fairdm.contrib.contributors.choices` with the values `ghost`, `invited`, `claimed` and `inactive`.

```python
from fairdm.contrib.contributors.models import Person

people = Person.objects.real().claimed().for_cards()
```

### Who may edit a profile

`Contributor.is_editable_by(user)` is the one rule that decides who may open and save the profile editing page. It is not a Django permission, because the answer depends on the record.

| Profile | `is_editable_by(user)` is true for |
|---|---|
| A person | The person, while their account is active. An active holder of the Community Manager role, when `can_sign_in()` is false for the person |
| An organization | An active user who passes `is_managed_by(user)` (a current administrator or owner), and an active holder of the Community Manager role, whether or not the organization has an owner |

An anonymous visitor, a superuser and the holder of any other portal role get no right from that alone. The rule asks `PortalRoles.is_held_by`, never a Django permission. See [Portal roles in code](portal-roles.md).

## Organization

`Organization` extends `Contributor`.

| Field | Type | Default | What it holds | What it accepts |
|---|---|---|---|---|
| `type` | `CharField`, indexed | `None` | The kind of institution | A value of `OrganizationType` |
| `members` | `ManyToManyField` to `Person` through `Affiliation` | | The affiliated people. Has no reverse accessor | Add members through `Affiliation` |
| `parent` | `ForeignKey` to `self` | `None` | The organization this one is part of. Reached from the parent as `sub_organizations`. Deleting the parent sets this to `None` | An organization other than itself or one beneath it |
| `city` | `CharField(max_length=255)`, indexed | `None` | The city | Text |
| `country` | `CountryField`, indexed | `None` | The country | A two-letter country code |
| `location` | `PointField`, SRID 4326 | `None` | A point in WGS 84 with no elevation or uncertainty | A point |

`OrganizationType` is in `fairdm.contrib.contributors.choices`. Its values are `education`, `funder`, `healthcare`, `company`, `archive`, `nonprofit`, `government`, `facility` and `other`. ROR allows several types for one organization and FairDM keeps one.

`clean()` refuses a `parent` that is the organization itself or any organization beneath it, with an error on `parent` and the code `parent_loop`. It also checks each link and that a ROR identifier has the form `0xxxxxx00`, with or without the `https://ror.org/` prefix. An index, `organization_location_geog_idx`, supports location lookups.

| Member | Returns | What it does |
|---|---|---|
| `lat`, `lon` | Properties | The latitude and longitude of `location`, or `None` |
| `from_ror(ror, commit=True)` | `Organization` | Creates or updates an organization from a ROR record through `RORTransform.update_or_create`. With `commit`, it also queues a sync after the transaction commits |
| `get_memberships()` | Queryset | The organization's affiliations with `person` loaded |
| `get_current_memberships()` | `list` of `Affiliation` | Verified affiliations with no end date, the owner first, then administrators, then members, each group by name |
| `owner()` | `Person` or `None` | The person with a current owner affiliation |
| `has_member(user)` | `bool` | Whether the user has a current affiliation of member or above. A visitor is never a member |
| `is_managed_by(user)` | `bool` | Whether the user has a current affiliation of administrator or owner. A portal role does not count |
| `is_editable_by(user)` | `bool` | See [Who may edit a profile](#who-may-edit-a-profile) |
| `transfer_ownership(new_owner)` | `None` | Demotes every current owner to administrator and makes `new_owner` the owner, in one transaction. See below |
| `get_descendant_ids()` | `set` of ids | The primary keys of every organization beneath this one, at any depth. Empty before the first save |
| `get_hierarchy()` | `dict` | `parent` (or `None`), `siblings` (the parent's sub-organizations by name, this one included, empty without a parent) and `children` (the direct sub-organizations by name) |
| `get_public_projects()` | Queryset | The public projects the organization owns or is credited on, none twice |
| `get_public_datasets()` | Queryset | The public datasets the organization is credited on or that sit in its projects, none twice. A dataset in a private project is left out |
| `get_record_completeness()` | `dict` | A flag for each of `ror`, `image`, `type`, `location` (needs a city and a country), `profile` and `links` |
| `get_location_display()` | `str` or `None` | The city and country |
| `summary` | `str` property | The type and place joined by a middle dot, or `""` |
| `get_initials()` | `str` | The leading acronym when the name starts with one (`"GFZ Helmholtz Centre"` gives `"GFZ"`), else up to two capital letters |
| `as_geojson()` | `str` or `None` | A GeoJSON feature for `location` |
| `icon()` | `str` | `"organization"` |

`transfer_ownership` raises `ValidationError` and changes nothing when the new owner:

- holds no affiliation with the organization
- has an affiliation that has ended
- has an affiliation that is still pending
- has not claimed their account
- has a deactivated account

`OrganizationQuerySet` adds the location lookups described in [Location fields](location-fields.md).

### Management of an organization

`manage_organization` is derived, not stored. `OrganizationPermissionBackend` answers `user.has_perm("contributors.manage_organization", organization)` as follows:

- For an inactive user or a visitor, it answers false.
- For a superuser, it answers true.
- For anyone else, it answers true only when they hold a current `OWNER` affiliation with the organization.

A stored django-guardian grant of this permission is never consulted. Setting `end_date` on an affiliation, changing its type away from `OWNER`, or deactivating the account removes the right on the next check.

## Affiliation

`Affiliation` links a `Person` to an `Organization`. An affiliation is current when it has no `end_date`. An end date in the future still makes it past.

| Field | Type | Default | What it holds | What it accepts |
|---|---|---|---|---|
| `person` | `ForeignKey` to `Person` | None, required | The person. Reached from the person as `affiliations` | A person |
| `organization` | `ForeignKey` to `Organization` | None, required | The organization. Reached from the organization as `affiliations` | An organization |
| `type` | `IntegerField`, indexed | `MembershipType.MEMBER` | The verification state and role | A value of `Affiliation.MembershipType` |
| `is_primary` | `BooleanField` | `False` | Whether this is the person's primary affiliation | `True` or `False` |
| `start_date` | `PartialDateField` | `None` | When the affiliation began | A year, a year and month, or a full date, as in [Model fields](model-fields.md) |
| `end_date` | `PartialDateField` | `None` | When it ended. Empty means current | As `start_date` |

`Affiliation.MembershipType` has four values. Each includes the rights of the ones before it, so they compare as integers.

| Name | Value | Meaning |
|---|---|---|
| `PENDING` | 0 | Declared and not yet verified |
| `MEMBER` | 1 | A regular member |
| `ADMIN` | 2 | Can manage memberships |
| `OWNER` | 3 | Full control of the organization |

Two database constraints apply:

- `unique_affiliation_person_organization` allows one affiliation for each person and organization. `clean()` refuses a second with the message `<person> is already a member of <organization>.` on `organization`.
- `unique_primary_affiliation_per_person` allows one primary affiliation for each person. `save()` demotes the person's other primary affiliation in the same transaction.

| Member | Returns | What it does |
|---|---|---|
| `start_display`, `end_display` | `str` properties | The date as precisely as it was recorded, or `""` |

`Affiliation.objects` is an `AffiliationManager` with these methods, also available on `person.affiliations`:

| Method | Returns | What it does |
|---|---|---|
| `current()` | Queryset | Affiliations with no end date |
| `past()` | Queryset | Affiliations with an end date |
| `primary()` | `Affiliation` or `None` | The affiliation marked primary. Cannot be chained further |
| `owners()` | Queryset | Current affiliations of type `OWNER`. The one definition of ownership |

## Contribution

`Contribution` is a contributor's credit on one project, dataset, sample or measurement. It is an `OrderedModel`, so each row has an `order`.

| Field | Type | Default | What it holds | What it accepts |
|---|---|---|---|---|
| `content_type` | `ForeignKey` to `ContentType` | None, required | The type of the credited record | A content type |
| `object_id` | `CharField(max_length=23)` | None, required | The credited record's primary key as text | A key |
| `content_object` | `GenericForeignKey` | | The credited record | |
| `contributor` | `ForeignKey` to `Contributor` | `None`, nullable | The person or organization credited. Deleting the contributor sets this to `None`. Reached from the contributor as `contributions` | A contributor |
| `roles` | `ConceptManyToManyField` to `FairDMRoles` | Empty | The roles on this credit | Concepts of the `fairdm-roles` vocabulary |
| `affiliation` | `ForeignKey` to `Organization` | `None` | The organization a person is credited from on this record. Kept on the credit and not read from the profile. Deleting the organization sets this to `None`. No reverse accessor | An organization, or `None` |
| `level` | `PositiveSmallIntegerField` | `None` | What a person may do on the record. Empty for an organization | A value of `ContributionLevel`. See [Contribution levels and record access](contribution-levels-and-record-access.md) |

`Contribution.Meta` orders rows by `object_id` and `order`.

Two rules protect the data:

- A named constraint, `unique_contribution_per_contributor_object`, allows one row for each contributor and record. `clean()` refuses a second row with the message `This contributor is already credited on this object.`
- A role from any vocabulary other than `fairdm-roles` is refused when it is written. A receiver on `Contribution.roles.through` raises `ValidationError` for `roles.add()` and `roles.set()`. `clean()` also refuses a stored off-vocabulary role.

The roles a record's type offers are in its `CONTRIBUTOR_ROLES` attribute, a collection of `FairDMRoles`.

| Member | Returns | What it does |
|---|---|---|
| `Contribution.add_to(contributor, obj, roles=None, affiliation=None)` | `Contribution` | Credits `contributor` on `obj`. A credit already there is kept and `roles` (names) are added to it. `affiliation` is set only on a credit created by this call. A person credited for the first time starts at the view level. A sample or measurement held as its base class is credited under its real type |
| `Contribution.starting_level(contributor)` | `ContributionLevel` or `None` | `VIEW` for a person, `None` for an organization |
| `is_person()` | `bool` | Whether the contributor is a `Person` |
| `get_absolute_url()` | `str` | The contributor's profile address |

`add_to` on the contribution, `Contributor.add_to` and the `add_contributor(contributor, with_roles=None)` method that every project, dataset, sample and measurement has all call the same code. Crediting the same contributor again adds roles and does not make a second row.

`Contribution.objects` is a `ContributionManager`. A record's `contributors` relation uses the same manager, so `dataset.contributors.people()` works. The methods:

| Method | Returns | What it does |
|---|---|---|
| `by_role(role_name)` | Queryset | Credits whose roles include the named concept |
| `for_entity(obj)` | Queryset | Credits on one record |
| `by_contributor(contributor)` | Queryset | Credits by one contributor across all records |
| `people()` | Queryset | Credits of people, ordered by `order` then `pk`. Reads the contributor's polymorphic type and loads no contributor |
| `organizations()` | Queryset | Credits of organizations, ordered by `order` then `pk` |

Move a credit through `Crediting.move`. Do not use `contribution.up()` or `contribution.down()` from `OrderedModel`. A contribution has no `order_with_respect_to`, so they swap places with a row on another record. See [Crediting](crediting.md).

## ContributorIdentifier

`ContributorIdentifier` is an external identifier of a contributor.

| Field | Type | Default | What it holds | What it accepts |
|---|---|---|---|---|
| `related` | `ForeignKey` to `Contributor` | None, required | The contributor. Reached as `identifiers` | A contributor |
| `type` | `CharField(max_length=50)` | None, required | The identifier scheme | One of the types below |
| `value` | `CharField(max_length=255)`, unique, indexed | None, required | The identifier | Text. No two identifiers of any record type share a value |

`VOCABULARY` is `FairDMIdentifiers.from_collection("Contributor")`, which offers `ORCID`, `RESEARCHER_ID`, `ROR`, `WIKIDATA`, `ISNI` and `CROSSREF_FUNDER_ID`. A contributor holds at most one identifier of each type. A second is refused at the database and by `clean()`, with a message naming the type.

`resolver_url` is the address the identifier resolves to, or `None` for a type with no resolver. ORCID, ROR, Wikidata, ISNI and Crossref Funder ID identifiers have one. A ResearcherID has none.

Creating an identifier queues a sync with the external provider once the transaction commits. The sync is a Celery task, `sync_contributor_identifier`. See [How to sync a profile from ORCID or ROR without Celery](../how-to/sync-a-profile-from-orcid-or-ror-without-celery.md).

## Profile helpers

`fairdm.contrib.contributors.profiles` holds the pure functions behind a profile page. None reads the database or a request.

| Function | Returns | What it does |
|---|---|---|
| `link_host(url)` | `str` | The host without a leading `www.`, or the link as written when it has no host |
| `language_names(codes)` | `list` of `str` | One name per ISO 639-1 code in the active language, in the order given. An unknown code is kept as written |
| `ranked_shares(counts)` | `list` of `dict` | Ranks a mapping of counts, largest first, as `{"label", "count", "percent"}` where the largest is 100 |
| `fill_slots(items, slots, reserve=False)` | `dict` | Fits a list into `slots` places and returns `shown`, `more` and `total`. With `reserve`, the last place is kept for a "+n more" entry when the list overflows |
| `checklist(items)` | `dict` | Sums up items that each carry a `done` flag: `items`, `done`, `total` and `ready` |
| `active_then_recent(items, modified, active=None)` | `list` | Orders items with the active ones first, each group most recently updated first. `modified` and `active` take one item |

```python
from fairdm.contrib.contributors.profiles import fill_slots, link_host, ranked_shares

link_host("https://www.github.com/someone")  # "github.com"
ranked_shares({"Creator": 4, "Editor": 2})
# [{"label": "Creator", "count": 4, "percent": 100},
#  {"label": "Editor", "count": 2, "percent": 50}]
fill_slots(list(range(12)), 10, reserve=True)
# {"shown": [0, 1, 2, 3, 4, 5, 6, 7, 8], "more": 3, "total": 12}
```

## Profile forms

`fairdm.contrib.contributors.forms.profile` holds the forms behind the profile editing page and the field their lists are typed into. The page is the `Update` plugin in `fairdm.contrib.contributors.plugins.update`. It reads `FAIRDM_PROFILE_FORMS` (see [Settings](settings.md)) for the kind of contributor, `person` or `organization`, and falls back to the shipped form when the setting names none. It declares its own `check`, `contributor_is_editable`, so a visitor is sent to sign in and a signed-in user who may not edit gets a 403. The check runs on every request, so a right lost while the page is open refuses the save.

### ProfileForm

`ProfileForm` is the base of the two shipped forms. A portal's own form can extend it. It draws no `<form>` tag, because the editing page supplies the tag and the buttons.

| Attribute | Type | Default | What it does |
|---|---|---|---|
| `sections` | `tuple` of `(heading, rows)` | `()` | Groups the fields in page order. A row is one field name, or a tuple of names drawn side by side on a wide screen. A heading of `None` draws the rows with no heading |

A field the form does not carry is left out of its section. A section left with no field is not drawn. A field that no section names is drawn after the last section.

A stored record can fail the model's validation on a field the form does not carry, such as an identifier stored in a malformed state. `ProfileForm` reports that failure as an error on the form as a whole, in `form.non_field_errors()`, and saves nothing.

### PersonProfileForm

| Field | Type | Accepts |
|---|---|---|
| `image` | `ImageField` | `jpg`, `jpeg`, `png` or `webp`, within the size limit. A clear box removes the photo |
| `first_name`, `last_name` | Model fields | The names that citations and exported metadata use |
| `name` | Model field | The display name. Required |
| `alternative_names` | `LinesField` | Other names, one per line |
| `profile` | Model field | The biography |
| `links` | `LinesField` | Web addresses, one per line. Only `http` and `https` are accepted |
| `lang` | `MultipleChoiceField` | ISO 639-1 codes, named in the active language. Each code is stored once |

The email, password, identifiers, affiliations, portal roles and account state are never on this form. Its `sections` are the unheaded group of `first_name` and `last_name` side by side, `name` and `alternative_names`, and the group "About you" with `image`, `profile`, `lang` and `links`.

### OrganizationProfileForm

| Field | Type | Accepts |
|---|---|---|
| `image` | `ImageField` | The logo, as for the person's photo |
| `name`, `alternative_names` | Model field, `LinesField` | As on the person form |
| `type`, `country` | Model fields | A value from their lists |
| `parent` | `OrganizationChoiceField` | An organization other than itself or one beneath it. The picker searches every organization by name, alternative name or ROR identifier |
| `city` | Model field | A city |
| `location` | `LocationField` | A latitude and a longitude as signed decimal degrees in WGS 84. Both empty removes the point. See [Location fields](location-fields.md) |
| `profile` | Model field | The description |
| `website` | `CharField` | An `http` or `https` address |
| `links` | `LinesField` | Other `http` or `https` addresses, one per line |

`website` and `links` are two fields over the one stored list `Organization.links`. The website is stored first and the other links follow it, and an address typed in both places is stored once. When the form opens, `website` shows the first stored link and `links` shows the rest. A form that keeps `website` must keep `links` as well. Without `website`, `links` shows every stored link.

The ROR identifier, the members and the owner are never on this form. Its `sections` are an unheaded group, "Location", "About" and "Online".

### LinesField

`LinesField(entry_validator=None, max_entries=50, **kwargs)` is a `CharField` on a text area whose cleaned value is a list. It trims each line, drops empty lines and keeps a repeated entry once, where it was first typed. A list given as the initial value is shown one entry per line.

| Argument | Type | Default | What it does |
|---|---|---|---|
| `entry_validator` | callable or `None` | `None` | Called with each entry. The first entry it rejects is reported with the code `invalid_entry`, and the entry is available to the message as `%(entry)s` |
| `max_entries` | `int` | `50` | The most entries accepted. More are refused with the code `too_many`, and `%(max)d` is available to the message |

```python
from django.core.validators import URLValidator

from fairdm.contrib.contributors.forms.profile import LinesField

websites = LinesField(
    required=False,
    entry_validator=URLValidator(schemes=["http", "https"]),
    error_messages={"invalid_entry": "%(entry)s is not a web address."},
)
websites.clean("https://example.org\n\nhttps://example.org\nhttps://example.net")
# ['https://example.org', 'https://example.net']
```

`language_choices()` in the same module returns the `(code, name)` pairs that `lang` offers, sorted by name.

## Transforms

The classes in `fairdm.contrib.contributors.utils.transforms` convert between a `Contributor` and an external format. A transform is an instance, and the contract is `export()` and `import_data()`.

| Member of `BaseTransform` | Returns | What it does |
|---|---|---|
| `export(contributor)` | `dict` | Converts a contributor to the external format. Raises `NotImplementedError` unless overridden |
| `import_data(data, instance=None, save=True)` | `Contributor` | Converts external data to a contributor, updating `instance` when given. Raises `NotImplementedError` unless overridden |
| `validate(data)` | `bool` | Whether `data` is a `dict`. Override to check more |
| `dictget(data, path, default="")` | Any | Reads a nested value by a list of keys and indexes. Returns `default` when the path does not exist |

The built-in transforms:

| Class | Format | Notes |
|---|---|---|
| `DataCiteTransform` | DataCite Metadata Schema 4.4 creator or contributor | Export adds the default identifier, the given and family names, and the primary affiliation |
| `SchemaOrgTransform` | Schema.org `Person` or `Organization` JSON-LD | Export includes the email address of a person. Use `to_public_schema_org()` for a page |
| `CSLJSONTransform` | CSL-JSON author | Import looks up an existing contributor by ORCID when no `instance` is given |
| `ORCIDTransform` | ORCID Public API v3.0 record | Exports and imports `Person` only. Export raises `TypeError` for an organization |
| `RORTransform` | ROR schema version 2 record | Exports and imports `Organization` only. Export raises `TypeError` for a person |

`ORCIDTransform` and `RORTransform` also talk to the registry:

| Member | Returns | What it does |
|---|---|---|
| `fetch_from_api(identifier)` | `dict` | Fetches the public record with a 30 second timeout. Raises `requests.RequestException` on failure |
| `update_or_create(identifier, force=False, **kwargs)` | `(contributor, created)` | Finds a contributor by `kwargs` or by identifier value. Fetches and updates it when `force` is true or it was last synced more than a day ago. Creates one when none is found |
| `get_or_create(identifier)` | `(contributor, created)` | Finds a contributor by identifier value, or fetches the record and creates one |

`RORTransform` adds three more:

| Member | Returns | What it does |
|---|---|---|
| `clean_ror_id(ror_id_or_link)` | `str` | The bare ID without the `https://ror.org/` prefix |
| `display_name(data)` | `str` | The name ROR displays, or `""` |
| `import_location(data, org)` | `None` | Sets `city`, `country` and `location` on `org` from the record's first location, without saving. Changes nothing when the record names no place |

The functions `contributor_to_datacite`, `contributor_to_schema_org`, `contributor_to_csljson` and `csljson_to_contributor` wrap the three format transforms. To write your own, see [How to add a transform for another format](../how-to/add-a-transform-for-another-format.md).

## Related pages

- [Settings](settings.md) describes `FAIRDM_PROFILE_FORMS`, which names the profile editing forms.
- [How to customise the profile form](../how-to/customise-the-profile-form.md) changes the fields of the editing page.
- [How to create a ghost person](../how-to/create-a-ghost-person.md) makes a profile for attribution alone.
