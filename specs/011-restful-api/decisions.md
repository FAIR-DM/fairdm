# Decisions: 011-restful-api

This specification was first written on 2026-03-31 and built in April 2026. On 2026-10-08 it was
audited against the code and rewritten. This file records what the audit found, what was decided
about each difference and why, and what a person using or building on the API gets as a result.

The maintainer read the audit's summary on 2026-10-08 and approved it, adding three notes that are
kept in [planning-notes.md](planning-notes.md). Each decision below says whether it was put to him.

## How the audit was done

Every requirement of the earlier specification was checked against the code on `main` at
`ef5de5f7`, and the API was exercised against the demonstration portal's models with a throwaway
test: reading every endpoint, then creating, changing, sorting, filtering and deleting as a
superuser. Where the code differed from the specification, the history of the lines involved was
read to see whether the code had once matched and been changed on purpose.

The earlier task list had all 99 tasks ticked. Four test files it cited do not exist.

## D1. Writing is kept, and the code is made to do it

**Before.** The earlier specification required create, read, update and delete on projects,
datasets, samples and measurements. The code accepts all four on every one of them, and:

- Creating a sample of any registered type fails with a database error, because the type's field
  list replaces the base serializer's and the dataset is no longer a field.
- Creating a measurement fails the same way, because the measurement configuration fixes the API
  fields to a common list and the type's required values are not among them.
- Creating a dataset returns success and discards the project sent with it, because the dataset
  serializer has no project field.

The code never matched. It was built this way in the original run.

**Decided.** The requirement stands (FR-015, FR-022) and closing it is the main work of the build.

**Why.** The maintainer asked for full create, read, update and delete when he called the audit.
The API is read-only in practice only because writing does not work.

**What changes.** A caller can create and change every record type. No request is answered with a
server error.

**Ruled by.** The maintainer, when he called the audit.

**ADR:** none — restores a requirement the feature always had, nothing downstream inherits a new
decision.

## D2. The feature is split in two

**Before.** One specification covered the whole API. Reading returned five or six fields of a
project or dataset, and none of a record's descriptions, key dates, identifiers, keywords,
contributors, licence or owner.

**Decided.** This specification covers reading the complete record and writing its own fields, its
visibility and its parent (FR-003, FR-016). Writing descriptions, key dates, identifiers, keywords
and contributors through the API, and creating contributors, is a separate feature request, filed
when this specification is approved. The number 011 is kept.

**Why.** Five other specifications and roadmap item R11 refer to 011 for the API's representation
of their record. Writing nested metadata and crediting people who have no account are a different
piece of work with decisions of their own, and holding the repairs back for them would leave the
API broken for longer.

**What changes.** A caller reads everything a record's page shows. Until the second feature lands,
a record's metadata is edited in the portal.

**Ruled by.** Proposed by the audit, approved by the maintainer.

**ADR:** none — a scoping decision between two specifications, recorded in both.

## D3. Records name each other by short identifier

**Before.** The earlier specification settled that addresses use the short identifier. It said
nothing about how one record refers to another. The code returns a sample's dataset and a
measurement's sample as internal database numbers, and measurements also return their own.

**Decided.** A record refers to another by short identifier and address, and no database number
appears in the API (FR-005).

**Why.** A caller holding a dataset's number has no endpoint to look it up with. Database numbers
also differ between two portals holding the same data, which the short identifier does not.

**What changes.** The `id` field goes, and `dataset`, `sample` and `project` change from numbers to
identifiers. Nothing has been released that carried the old form.

**Ruled by.** The audit, approved by the maintainer.

**ADR:** `docs/adr/0027-records-refer-to-each-other-by-short-identifier.md`

## D4. Every sample and measurement carries the common fields

**Before.** The earlier specification required a base serializer for samples and one for
measurements, each guaranteeing a set of fields. The classes exist. The guarantee has never held,
because a generated serializer's field list replaces the base's: a rock sample is returned without
its identifier or its dataset.

**Decided.** The requirement stands (FR-004). A type's own field list adds to the common fields.

**Why.** Without it a caller cannot tell which dataset a sample belongs to, and cannot create one.

**What changes.** Every sample and measurement has the same core, whatever its type declares.

**Ruled by.** The audit, approved by the maintainer.

**ADR:** none — restores a requirement, local to this feature.

## D5. Measurements carry their measured values

**Before.** The earlier specification said a type's API fields come from its registration. The
measurement configuration sets a fixed API field list for every measurement, so no measurement
type returns the values it exists to record.

**Decided.** A measurement type's declared fields are in the API (FR-004, FR-023).

**Why.** The values are the data. An API for a research portal that omits them serves no one.

**What changes.** A measurement is returned with its values, and can be created with them.

**Ruled by.** The audit, approved by the maintainer.

**ADR:** none — a defect put right, no decision for anything downstream to inherit.

## D6. Sorting works, and searching waits for R17

**Before.** The earlier specification required filtering and ordering on lists. Filtering by a
registered type's declared filters works. Ordering any list of samples or measurements fails with a
server error. Projects and datasets ignore a search term.

**Decided.** Ordering is required on every list and filtering where a type declares filters
(FR-008). Search is left to roadmap item R17.

**Why.** R17 delivers one search for the portal and the API together. Building a second one here
would be replaced by it.

**What changes.** Lists can be sorted. Nothing about search.

**Ruled by.** The audit, approved by the maintainer.

**ADR:** none — a defect, and a boundary the roadmap already draws.

## D7. The sidebar keeps one API link

**Before.** The earlier specification required a group of three links in the sidebar and a setting
for the address of an external guide. The code was built that way on 2026-04-02 (`2d460b1e`). The
maintainer reduced it to one link under the documentation group on 2026-08-06 (`2a6106f3`). The
setting is still defined and nothing reads it.

**Decided.** The specification follows the code (FR-038). The setting is removed.

**Why.** The code matched the specification and was changed on purpose.

**What changes.** Nothing a visitor sees. A portal that set the removed setting loses nothing,
because it had no effect.

**Ruled by.** The audit, on the history. Approved by the maintainer.

**ADR:** none — follows a change already made.

## D8. Tokens come from the account pages

**Before.** The earlier specification chose one permanent token per person, obtained by posting a
username and password to the API. The code mounts that login endpoint together with endpoints for
resetting and changing a password and editing the account. The login takes an email address and a
password and nothing else, and the portal has two-factor sign-in installed.

**Decided.** The API has no login, password or account endpoints (FR-031). A person creates a token
on their account pages after signing in normally (FR-029, FR-030). The pages are the ones
django-mvp-accounts provides from version 0.2.0, which uses django-rest-knox.

**Why.** A token that can be had for a password alone undoes two-factor sign-in for anyone who
turned it on. Tokens from the account pages can be several per person, expire, are stored hashed
and can be revoked one at a time. The maintainer named django-mvp-accounts for this.

**What changes.** A script can no longer sign in with a password. A person holds as many tokens as
they need, each with a lifetime they choose, and revokes one without disturbing the others. Tokens
issued the old way stop working.

**Ruled by.** The audit proposed removing the login endpoint. The maintainer approved and named the
package.

**ADR:** `docs/adr/0028-api-tokens-are-created-on-the-account-pages.md`

## D9. One way to build a serializer

**Before.** Nothing in the earlier specification covered it. The registry builds a serializer for
each registered type, and its documentation tells a developer to override that to supply their own.
The API ignores it and builds a second serializer by another route.

**Decided.** The API uses what the registry gives it, and there is one builder (FR-024).

**Why.** A documented override that has no effect is a trap for the developer who follows it.

**What changes.** A developer who overrides how the configuration obtains its serializer sees the
result in the API.

**Ruled by.** The audit, approved by the maintainer.

**ADR:** none — removes a duplicate, no new decision.

## D10. The write rules of FS-022 are stated here by reference

**Before.** The earlier specification predates FS-022. The code now credits the creator at the
manage level, requires that level to change visibility or move a record, limits the parents a
caller may name, and refuses a move that strands a record. These are tested.

**Decided.** This specification requires them (FR-017 to FR-019) and points to FS-022 as their
source.

**Why.** They are part of how the API behaves and a reader of this specification should find them.
Defining them twice would let the two drift.

**What changes.** Nothing in behaviour.

**Ruled by.** The audit, approved by the maintainer.

**ADR:** none — FS-022 owns the decision.

## D11. Route names keep their sample and measurement prefix

**Before.** The earlier specification said a generated route is named from the type's plural name
alone. The code has always prefixed it with `samples-` or `measurements-`.

**Decided.** The specification follows the code (FR-027).

**Why.** Without the prefix a sample type and a measurement type with the same plural name would
take the same route name.

**What changes.** Nothing.

**Ruled by.** The audit. Not put to the maintainer separately, being an internal name.

**ADR:** none — local to this feature.

## D12. Deleting follows the portal's refusals

**Before.** Not covered. The code deletes whatever the caller has the right to delete.

**Decided.** Where the portal refuses a delete because of the record's state, the API refuses it
too (FR-020).

**Why.** FS-024 keeps a project with a public dataset and a sample with measurements from being
deleted. The API would otherwise be a way round both.

**What changes.** Those two deletes are refused through the API with a reason.

**Ruled by.** The audit. For the maintainer to veto.

**ADR:** none — applies an existing rule to a second surface.

## D13. Other websites may call the API

**Before.** Not covered. The code refuses every cross-origin request unless the operator lists the
origin.

**Decided.** Any origin may read and may write with a token. A sign-in cookie is never accepted
from another origin (FR-033).

**Why.** The maintainer asked for sensible decisions on access. The data is open by design, and a
dashboard or notebook hosted elsewhere is an ordinary way to use it. A token is sent deliberately
by the caller, so accepting it from anywhere exposes nothing a script could not already do.

**What changes.** A browser application on another site can use a portal's API with no change to
the portal's settings.

**Ruled by.** The audit, under the maintainer's instruction to decide. For him to veto.

**ADR:** none — a default an operator can change.

## D14. Limits and page sizes

**Before.** The earlier specification required separate limits for anonymous and signed-in callers
and a configurable page size. The code allows an anonymous caller 100 requests an hour and a
signed-in caller 1,000, with 25 records to a page and at most 100.

**Decided.** Each kind of caller has a short-window limit and a daily one, pages are larger, and
all of it is settable (FR-040, FR-042, SC-007). The figures proposed to planning are:

| | Anonymous | With a token or session |
|---|---|---|
| Short window | 30 a minute | 120 a minute |
| Daily | 2,000 | 20,000 |

Pages hold 100 records by default and at most 1,000.

**Why.** At 25 to a page and 100 requests an hour, an anonymous caller needs four hours to read a
dataset of ten thousand samples, which pushes people towards scraping the pages instead. Fewer,
larger responses cost a small server less than many small ones. A per-minute limit is what stops a
burst from taking the server down, and a daily one is what bounds a slow crawler. Paging stays by
page number with a total, which is what callers expect and is cheap at the sizes a single-server
portal holds.

**What changes.** A harvest that took hours takes minutes. A burst is cut off sooner than before.

**Ruled by.** The audit, under the maintainer's instruction to decide. Planning may adjust the
figures on evidence.

**ADR:** none — defaults, each a setting.

## D15. Smaller defects taken in without a ruling each

Each is a requirement of the rewritten specification:

- A catalogue's count of records included private records for a signed-in caller (FR-036).
- A catalogue listed a type's fields in nested groups as the registration wrote them (FR-036).
- A catalogue built each type's address from a fixed string and not from the route (FR-036).
- The generated description told callers to log in with a username at an endpoint that took an
  email address (FR-035, and the endpoint goes under D8).
- A type that failed to get its endpoints was logged as a warning and the portal started without it
  (FR-026).
- A registration whose API fields left out a required field was found only when a caller tried to
  create a record (FR-026).
- The contributor endpoint returned an identifier and a name, empty for some people (FR-006).

**ADR:** none — defects put right, no decision for anything downstream to inherit.

## Removed from the specification directory

The earlier plan, task list, research notes, data model, quick-start, contract and bug note were
deleted in the same change. They described the April build and its 99 ticked tasks. The plan and
task list are written again from this specification, and the history keeps the old ones.

**ADR:** none — housekeeping.

## D16. What the design review changed

One reviewer read the plan, the task list and the code they name before anything was built, and
reported 17 findings. The four that changed the design:

- **A reference never names a record the caller may not see.** A public dataset can sit in a
  private project, and a measurement's sample can be in another dataset. Such a reference is
  returned as null (plan D1). The portal's own pages already leave a hidden project unnamed.
- **Lists filter by the parent's short identifier.** With database numbers gone from the output,
  the existing filters, which match on them, would have been unusable, and a type that declares
  its own filters had no dataset filter at all (plan D3).
- **The check that a developer's serializer builds on the base stays where the endpoint is
  built.** Both ways of supplying a serializer bypass the factory, and the base is what carries
  the access rules for writing (plan D3).
- **The old serializer builder is deleted in the second story.** Tests for the write rules still
  import it until their replacements on the real routes exist.

The reviewer also checked each of the seven tasks marked as already done. None was overturned.
Two were found to rest on tests that miss one clause each, and the missing cases were added to
open tasks in the same test files.

**ADR:** none — a record of review, the decisions it led to are in the plan.

## D17. Choices made while building the first story

**A reference works out its own address.** The plan gave `RecordReferenceField` a `view_name` for
each use. A measurement's sample can be of any registered type, and each type has its own route, so
one route name per field cannot be right. The field takes the route from the record it is given
and has no `view_name` argument.
*Revisit if:* the sample routes collapse into one.

**A page of references is checked in one query.** `RecordListSerializer` hands the whole page to
each reference field before any record is written out, so deciding what a caller may see costs one
query per reference field and not one per record. A reference outside a list is checked on its own.
*Revisit if:* a reference field is used inside a nested list, which is not primed.

**The dataset and sample filters are the API's own.** The filter sets the registry generates match
`dataset` and `sample` on database numbers and are shared with the portal's pages. The API builds a
subclass of the type's filter set with those two filters matching `uuid`, offering only records the
caller may see, and drops the content-type filter, which also takes a number and means nothing on
an endpoint that serves one type. The portal's pages are untouched.
*Revisit if:* the portal's pages move to identifiers, when the API's copies can go.

**Sorting failed in the ordering filter, not in the queryset.** With no `ordering_fields`, Django
REST Framework reads every property of the model class, and django-polymorphic's
`polymorphic_primary_key_name` raises on a sample or measurement subclass. Each generated endpoint
now names its sortable fields: the stored, non-relational fields its serializer returns.
*Revisit if:* django-polymorphic stops raising.

**A profile shows no account state.** A contributor is returned with what the profile page shows:
name, image, biography, identifiers, links, languages, primary organization and location. The
page also shows portal roles, whether the profile is claimed and when the person joined. Those
describe the account, so the API leaves them out.
*Revisit if:* the maintainer wants any of them public.

**ADR:** none — choices local to how this feature is built, nothing outside it inherits them.

## D18. The hand-built write tests go with the first story

Seventeen tests of the write rules built an endpoint by hand from a stand-in configuration and
sent parents as database numbers. With references by short identifier and the registry as the one
builder, they cannot pass, and making them pass would mean accepting database numbers again. They
are deleted in the first story. The second story tests the same rules on the real routes, so the
rules are untested for the span of one story on a branch that is not released.

The plan had the deletion in the second story. This entry was made by the maintainer's side of
the build and not by the story's implementer, who reported the conflict and stopped.

**ADR:** none — a sequencing choice inside this feature.

## D19. Choices made while building the second story

**A parent is compared by primary key.** The sample field of a measurement offers the base `Sample`
class, and the stored sample is the type's own class. Django does not call a model instance equal
to one of its subclass's, so a request that repeated the current sample was read as a move and
needed the manage level. `CreatorCreditMixin.differs` compares a related record by primary key.
*Revisit if:* the field offers the sample as its own type.

**A refused delete is a 409 with a sentence the API writes.** `perform_destroy` turns
`PublicDatasetsProtect` into one sentence and `ProtectedError` and `RestrictedError` into another,
raised as `DeleteRefused`. The sentences name no record, because the caller may not be allowed to
see the ones that block the delete, and the exceptions' own text counts them.
*Revisit if:* the portal gives each refusal a user-facing reason of its own to reuse.

**Creating needed no new code.** The create tests (T016, T017, T020, T022) passed when first run.
The first story's serializers carry the parents and the creator credit. They stay as the proof
that every registered type can be created through its route, and each was checked by breaking the
mechanism it covers.
*Revisit if:* the way a type's serializer is built changes.

**A dependency goes with the builder.** Nothing under `fairdm/` imports `djangorestframework-guardian`
once `build_model_serializer` is gone, so it is removed from `pyproject.toml` and the lock file.
*Revisit if:* a portal needs stored object permissions on a model served by the API.

**ADR:** none — choices local to how this feature is built, nothing outside it inherits them.

## D20. Choices made while building the third story

**The API's defaults are the shared defaults minus two names.** A type with no field list takes
the framework's default fields, which include `options` and `tags`. The API returned `options`, an
internal JSON field, and `tags` as null whatever the record holds. `Component.default_exclude`
names them for the serializer alone, and only when nothing is declared, so a field list a portal
writes (including `options`) is always honoured and the forms, tables and filters keep the full
defaults.
*Revisit if:* `tags` is serialised as a list, when it can come back in.

**Relation filters change in two places.** The API's copy of a type's filter set rewrites every
relation filter whose model has a `uuid` to match it, on the class, so the generated schema
describes the identifier. A relation filter whose model has no `uuid` is removed when the filter
set is built for a request, not on the class, because the type's own filter set (the sample
mixin's `__init__`) reads `polymorphic_ctype` while it is built. A multiple-choice filter also has
`__uuid` added to its field name, since django-filter filters on the field name as given.
*Revisit if:* the sample mixin stops reading `polymorphic_ctype`, when the removal can move to the
class and out of the schema.

**The start-up check is a plain system check.** `fairdm.E600` is registered under the `models`
tag from the API app's `ready()`, so `manage.py check`, `runserver` and `migrate` report it. It is
not in the production-critical set, because the registrations are written by the developer and
reported long before a deploy. It compares the writable fields of the type's own serializer with
the model's required fields, so a serializer the developer names is held to the same rule.
*Revisit if:* a portal wants a registration mistake to stop a production boot.

**Registering the types is a router method.** `FairDMAPIRouter.register_types` replaces the two
module-level loops and their `try`/`except`, so a type whose endpoints cannot be built stops the
import with the real error and a test can call it on a fresh router. The router's addresses are
read once, when `fairdm.api.urls` is first imported, so a viewset registered after that is served
only once the module is loaded again. The tests do exactly that, and the module's docstring says
where to register.
*Revisit if:* the URL configuration reads the router on every request.

**ADR:** none — choices local to how this feature is built, nothing outside it inherits them.

## D21. Choices made while building the fourth story

**No schema extension of our own.** The plan called for a small drf-spectacular extension so the
schema describes knox's header. drf-spectacular 0.30 already ships one for knox
(`drf_spectacular.contrib.knox_auth_token`), so the generated schema carries a `knoxApiToken` header
scheme and raises no warning about an unknown authenticator. A test generates the schema and fails
on such a warning, and was seen to fail with an authenticator drf-spectacular does not know. No
`fairdm/api/schema.py` was added.
*Revisit if:* drf-spectacular drops its knox extension.

**The token pages sit at `account/tokens/`, outside the Account Center prefix.** The address is the
one in django-mvp-accounts' guide. The pages' route names (`account_api_tokens` and the two beside
it) are what the Account Center's menu entry and card reverse, so they do not depend on the prefix.
*Revisit if:* the Account Center moves and the tokens pages should follow it.

**Tests build tokens through knox's manager.** `AuthToken.objects.create` returns the record and the
secret together, so the tests need no endpoint to get a token. Revoking is deleting the record and
expiring is moving its expiry into the past, the same two things the pages and knox do.

**ADR:** none — choices local to how this feature is built, nothing outside it inherits them.

## D22. Choices made while building the fifth story

**The schema leaves out a filter through an extension, not by removing it from the class.** The
schema reads a filter set's filters from the class, while the API removes a relation filter that
does not match on the short identifier when it builds the filter set for a request, because the
type's own filter set still reads `polymorphic_ctype` while it is built. `fairdm.api.schema` has a
small extension of drf-spectacular's django-filter extension, ahead of it in priority, that asks
the filter set whether it drops a filter (`DatasetFilterSet.drops`, the same test the request-time
removal uses) and describes only the rest. The portal's own pages, which share the type's filter
set, are untouched.
*Revisit if:* the sample mixin stops reading `polymorphic_ctype`, when the filter can leave the
class and the extension can go.

**A catalogue entry takes everything from the type's list route.** Its address is the list route
made absolute, the viewset found by resolving that route supplies the serializer, the queryset and
the filter set, and the count runs that queryset through the visibility filter for the caller. The
entry's keys are `name`, `verbose_name`, `verbose_name_plural`, `app_label`, `endpoint`, `fields`,
`filters` and `count`. `filterable_fields`, which listed a registration setting the API does not
read, is replaced by `filters`. `fields` was the registration's list, which could hold nested groups
and left out what the base serializer adds; it is now the serializer's flat list.
*Revisit if:* a portal replaces a type's list route with a viewset that has no class-level queryset.

**The description reads the limits and page sizes when the schema is generated.** The hook lists
whichever rates are configured under whatever names they carry, and reads the default and largest
page size and the size parameter's name from an instance of the configured pagination class, so
the story that renames the rates and moves the page sizes into settings needs no change here.
*Revisit if:* a rate needs words of its own beside its number.

**ADR:** none — choices local to how this feature is built, nothing outside it inherits them.

## D23. Choices made while building the sixth story

**The two signed-in throttles count only signed-in callers.** Django REST framework's
`UserRateThrottle` also counts an anonymous caller, by address. With it unchanged, every
anonymous request would also count against the signed-in rates, and an operator who set a signed-in
rate below the anonymous one would stop anonymous callers early. `fairdm.api.throttling` has a
small shared parent, `SignedInThrottle`, whose only change is to return no key for a caller who is
not signed in, so the two anonymous throttles are the only ones that count anonymous callers. This is
three more lines than the two-line subclasses D14 describes.
*Revisit if:* Django REST framework adds an option to count only signed-in callers.

**The rates are read from the dict the settings hold.** Django REST framework reads
`DEFAULT_THROTTLE_RATES` once, when its throttling module is first imported, and keeps that dict.
A portal changes a rate by assigning into that dict (`REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user_day"] = ...`)
in its settings, which is read before the module is imported. The tests change entries in the same
dict, and one test proves the two are the same object.
*Revisit if:* a rate needs to change while the portal runs.

**The page sizes are properties read from the settings.** `FairDMPagination.page_size` returns
`REST_FRAMEWORK["PAGE_SIZE"]` and `max_page_size` returns `FAIRDM_API_MAX_PAGE_SIZE` each time they
are read, so a changed setting is followed with no restart of the class. The schema's description
reads the same two properties from an instance.
*Revisit if:* none.

**Contributors load their affiliations and parents once the real types are known.** The list is a
queryset over the base contributor type, which cannot prefetch what only a person (affiliations) or
only an organisation (parent) has. `ContributorViewSet.get_serializer` prefetches those two for
the records about to be described, with Django's `prefetch_related_objects`, in a list, a detail
and an unpaged list alike. To make the prefetch count, `Person.get_affiliation_history` reads
`affiliations.all()` like the model's other affiliation readers do and selects the organisation
itself only when the affiliations were not prefetched; its result is unchanged.
*Revisit if:* django-polymorphic can prefetch a relation of a subtype from the base queryset.

**The catalogues' response serializers describe the response and do not render it.** The two
serializers are given to the schema generator with `extend_schema`. A test compares the keys the
schema lists with the keys a catalogue answers, so the two cannot drift apart unnoticed.
*Revisit if:* the catalogue view becomes a generic view.

**ADR:** none — choices local to how this feature is built, nothing outside it inherits them.

## D24. Choices made while fixing the findings of the code review

**A sample's or measurement's records are public when their dataset is public and published.**
The portal's own pages decide this with the dataset's `data_is_public`, and the API now asks the
same question in the list filter and in the object permission. The dataset's own record is judged
by its visibility alone and stays readable. The test fixtures that built a public dataset to hold
records now also set `published=True`, because the dataset factory leaves it unset.
*Revisit if:* publishing and visibility are merged into one flag.

**The contributors a list leaves out are named once, and a reference reads that list.**
`FairDMVisibilityFilter.hidden_contributors` selects the superusers and the anonymous account. The
contributor list excludes them with it, and `RecordReferenceField` reads the same selection, once
per request, keeping the result on the serializer context. Asking once matters because a record
can carry many credits and each reference is checked on its own.
*Revisit if:* the contributor list gains a rule of its own that is not about accounts.

**A many-to-many to a record type is checked for the whole page.** A serializer FairDM builds gives
such a relation a `RecordReferenceField(many=True)`. The list serializer primes the child field
with the related records of the page, which the viewset has prefetched, so the check is one query as
it is for a foreign key.
*Revisit if:* none.

**The sample description and date filters use the measurement filter set's date filter.** A sample's
key date is a partial date, which a plain date filter cannot compare against, so the sample filter
set imports `PartialDateFilter` from the measurement filter set instead of defining a second one.
*Revisit if:* a third filter set needs it, when it moves to a shared module.

**The proxy warning has the id `fairdm.W601`.** It sits in the API range with a `W` for its
severity, runs only under `check --deploy`, and is outside the production-critical subset, so it
cannot stop a portal from starting. Any value in `REST_FRAMEWORK["NUM_PROXIES"]` ends it.
*Revisit if:* a default number of proxies can be chosen safely, which depends on the deployment.

**ADR:** none — choices local to how this feature is built, nothing outside it inherits them.

## D25. Three changes the maintainer asked for when he read the finished work

**The token scheme has a plain name.** The documentation page's authorisation dialog showed
`knoxApiToken`, the name drf-spectacular gives django-rest-knox's scheme. It is `tokenAuth` now.

**Every record links to its page on the portal.** A record and a contributor carry `html_url`
beside `url`. Someone who harvests records and shows them on another website then has a link back
to the portal, which makes the portal's page the canonical one. The name follows the convention
of APIs that return both an API address and a web address. References to other records stay as
they are, an identifier and an API address.

**The catalogues are short.** An entry had the type's fields and filters, which the generated
documentation already gives for every type, in a form tools can read. Keeping them in two places
means two things to keep true. An entry is now the type's name, its display names, the address of
its records and a count. `app_label` goes too, since it is a name from the portal's code and tells
a caller nothing.

The specification is changed to match: FR-003, FR-036, a new FR-044 and the fifth scenario of the
fifth story.

**Ruled by.** The maintainer, at review. The field name and what stays in an entry were chosen
here.

**ADR:** none — small changes to this feature's own output, made before any release.

## D26. The catalogues go, lists can be asked for what changed, and the documentation carries each type's own words

Decided with the maintainer at review, after the catalogues had been trimmed (D25).

**The two catalogues of registered types are removed.** Once their fields and filters were gone an
entry held a name, an address and a count. The API's root already links every list, and every
list's first page already carries its count. What is left did not justify two endpoints to keep
true.

**Every list takes `modified_after` and `modified_before`.** The case for a catalogue was telling a
harvester whether anything is new. APIs answer that on the list: the caller remembers when it last
read and asks for what changed since. Sorting by `modified` already worked. The filters did not
exist, and an unknown parameter was silently ignored.

**The generated documentation uses each type's own name and description.** All sample types were
grouped under one heading, a type's display name appeared nowhere, and the description shown for a
type's record was a docstring written for the framework's developers. Each registered type now has
a section under its plural name, with the description, authority, citation, keywords and
repository link from its registration. A maintainer's name and email address are left out, since
the documentation is public and those are a person's details. The description in a registration's
metadata is used before the registration's own `description`, because the base configuration for
measurements carries a `description` that stands for every measurement type and would otherwise
hide what each type says about itself.

Left for later, each as work of its own: figures about a type over time, an `ETag` or
`Last-Modified` on responses, and a record of what was deleted.

The specification is changed to match: the fifth story's narrative and scenarios, FR-036, FR-037,
a new FR-045, and the catalogue is no longer among the key entities.

**Ruled by.** The maintainer, at review, on a recommendation made there.

**ADR:** none — changes to this feature's own output, made before any release.


## D27. How the changed-since filters reach every list

**Decision.** `modified_after` and `modified_before` are declared once, on
`ChangedSinceFilterSet`, and `FairDMFilterBackend` mixes that class into the filter set it builds
for every list. The backend takes the place of django-filter's own in
`REST_FRAMEWORK["DEFAULT_FILTER_BACKENDS"]`, so projects, datasets and contributors, which have no
filter set of their own, get it too. The generated sample and measurement lists already name the
backend. The cache of built filter sets is keyed by the model as well, since a list with no filter
set of its own and no parent filter would otherwise share one class with every other such list.
A viewset that has its own filter set and no parent filter keeps matching relations by database
number, as before; only the two new filters are added to it.

**Why.** One declaration, one place the lists go through, and the filter sets the portal's pages use
are not touched, because the backend builds a new class.

**Revisit if.** A portal replaces `DEFAULT_FILTER_BACKENDS` and lists a viewset of its own that
does not name the backend; that list then lacks the filters.

**`modified` and indexes.** Every served model has a `modified` field. Only the contributor's has
`db_index=True`. Project, dataset, sample and measurement have none, and no migration is added
for it in this change.

## D28. How each type's own words reach the generated documentation

**Decision.** `fairdm.api.schema.TypeDescription` reads a registration once and answers for the
three places the documentation names the type: `summary()` (the registration's description, else
the one in its metadata, else the model's docstring, else a plain sentence) for the operations and
the type's record, and `tag()` for the section, which adds the authority, citation, keywords and a
repository link and never the maintainer's name or address. `generate_viewset` sets the operation
description and tags the six actions with `extend_schema_view`. The top-level `tags` and the
record descriptions are written by the existing `describe_api` postprocessing hook, so a portal
that keeps that hook keeps them. A record's component is found from its serializer's `Meta.ref_name`
or class name, the way drf-spectacular names it. The operation tag is the lazy plural name and is
turned into text by drf-spectacular when the schema is built.

**Why.** One function answers for the description, so the operations, the section and the record
cannot disagree, and no new setting or hook is needed.

**Revisit if.** Two registered types share one plural name: a tag name must be unique in the
schema, so they would share a section. Also revisit if a serializer is shared by two types, since
one component then carries one type's words.
