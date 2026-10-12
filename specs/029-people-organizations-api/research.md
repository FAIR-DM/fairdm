# Research: people, organizations and a record's credits can be read through the API

Written 2026-10-12 against `origin/main` at `5201beed`.

## The maintainer's planning notes

### Mirror DataCite for credits

**Adopted.** DataCite 4.6 describes a creator and a contributor with the same sub-properties
(https://datacite-metadata-schema.readthedocs.io/en/4.6/properties/creator/):

| DataCite | Occurs | What it holds |
|---|---|---|
| `name` with `nameType` | 1 | The full name, written "Family, Given" for a person. `nameType` is `Personal` or `Organizational` |
| `givenName`, `familyName` | 0-1 | A person's two names |
| `nameIdentifiers` | 0-n | `nameIdentifier`, `nameIdentifierScheme` (required with it), `schemeUri` |
| `affiliation` | 0-n | `name`, `affiliationIdentifier`, `affiliationIdentifierScheme`, `schemeUri` |
| `contributorType` | 1, contributors only | One of a fixed list |

A credit in the API carries the same properties, with the names in the API's snake case:
`name`, `name_type`, `given_name`, `family_name`, `name_identifiers` and `affiliation`. Everything
DataCite asks of a creator can be read from one credit without a second request.

Two things differ, both on the maintainer's instruction:

- There is no `contributorType`. A credit carries `roles`, from the portal's own contribution role
  vocabulary, and creators are not separated from contributors.
- A credit adds `uuid` and `url`, the contributor's short identifier and address in the API, and
  each affiliation entry does the same for its organization.

`affiliation` is a list, as in DataCite, though a contribution stores one organization. A list
with nothing or one entry in it reads the same to a harvester as DataCite's own, and leaves room
if a credit ever holds more than one.

### Credits are for attribution only

**Adopted.** A credit carries nothing from the profile beyond the properties above: no biography,
links, languages, image or other names.

### Lists stay light

**Adopted.** `PersonListSerializer` and `OrganizationListSerializer` hold the identifying fields.
`PersonSerializer` and `OrganizationSerializer` extend them for the single record.

### Privacy is a later feature, and nothing private gets out before it

**Adopted.** Every field served is one the public overview page shows a signed-out visitor
(`fairdm/contrib/contributors/plugins/overview.py` and its templates). Affiliations are read
through `Person.get_affiliation_history()`, which already keeps only verified ones, and members
through the same rule `Organization.get_current_memberships()` applies. #246 is not started here.

## What exists

- `fairdm/api/serializers.py`: `ContributorSerializer` (one shape for both kinds),
  `ContributionSerializer` (three fields: two references and the roles), `RecordReferenceField`
  with `route_name()` returning `api:contributor-detail` for any contributor, and
  `RecordSerializer.load_related()`, which prefetches credits with `contributor`, `affiliation`
  and `roles`.
- `fairdm/api/viewsets.py`: `ContributorViewSet`, read-only, over the polymorphic base. It
  prefetches affiliations and parents after the real types are known, because a queryset over the
  base cannot.
- `fairdm/api/filters.py`: `FairDMVisibilityFilter.hidden_contributors()` selects superusers and
  the anonymous account. `ChangedSinceFilterSet` and `FairDMFilterBackend` give every list its
  changed-since filters. Projects and datasets have no filter set of their own.
- `fairdm/contrib/contributors/models.py`: `Person.first_name` and `last_name`,
  `get_full_name_display("family_given")`, `get_affiliation_history()`, `primary_affiliation()`.
  `Organization.type`, `city`, `country`, `parent`, `sub_organizations`,
  `get_current_memberships()`. `Contributor.get_public_projects()` and `get_public_datasets()`,
  which an organization overrides to add the projects it owns.
  `ContributorIdentifier.type`, `value`, `get_root_url()` and `resolver_url`.
- `fairdm/contrib/contributors/plugins/overview.py:117` links a profile page to
  `api:contributor-detail`.
- Tests in `tests/test_api/` use the route names `api:contributor-list` and
  `api:contributor-detail` in about twenty places.
- `docs/portal-development/restful-api.md` and `docs/user-guide/reading-records-with-a-script.md`
  describe the mixed endpoint and the old shape of a credit.

## What the plan needs settled

**Two querysets, not one polymorphic one.** `Person.objects` and `Organization.objects` are plain
querysets over the concrete models, so each viewset can prefetch what its kind has. The
after-the-fact prefetch in `ContributorViewSet.get_serializer` goes away with the mixed list.

**Hidden accounts.** `Person.objects.real()` already leaves out superusers and the anonymous
account. The people viewset uses it. An organization's members are filtered by the same rule.

**A credit held by a hidden account.** FS-011 returned `null` for the contributor. The
specification now asks for the credit to be shown, without an address. The credit serializer reads
the name and identifiers from the contributor and sets `uuid` and `url` to `null` when the
contributor is in the hidden set, which `RecordListSerializer` already loads once for a page.

**Identifiers on credits cost one prefetch.** `load_related()` adds
`contributor__identifiers` and `affiliation__identifiers` to the credit prefetch. Given and family
names live on the `Person` table, while the prefetch selects the `Contributor` base, so the credit
queryset must return real instances. `Contribution.contributor` is a foreign key to a polymorphic
model, and `select_related` on it yields base instances. The plan loads the people of a page in
one extra query, keyed by primary key, and the test for the query ceiling proves the count.

**No new package.** django-filter, DRF and drf-spectacular are already used for everything this
needs.

**No migration.** Nothing is stored that is not stored today.

**Name identifier form.** DataCite's examples give the identifier as its full address. The API
gives `name_identifier` as the resolver address where the scheme has one and as the bare value
otherwise, with the scheme's own address in `scheme_uri`.

**An identifier filter must accept both forms.** The value is stored bare. The filter strips a
known scheme address from the front of what it is given before comparing.

**A contributor's records.** `get_public_projects()` and `get_public_datasets()` are the one source
behind the profile page's tabs. The `contributor` filter on the project and dataset lists calls
them, so the API cannot drift from the page. For an organization that includes the projects it
owns and the datasets in them, as its page does.
