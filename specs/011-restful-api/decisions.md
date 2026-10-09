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

**ADR:** [`docs/adr/0027-records-refer-to-each-other-by-short-identifier.md`](../../docs/adr/0027-records-refer-to-each-other-by-short-identifier.md)

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

**ADR:** none — a defect.

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

**ADR:** `docs/adr/` — to be written at the build: how a caller authenticates is inherited by
everything that touches the API.

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

**ADR:** none — defects.

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
