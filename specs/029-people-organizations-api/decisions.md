# Decisions: people, organizations and a record's credits can be read through the API

Questions the specification answered without putting them to the maintainer, with the reasoning
that is too long for the specification itself. Each says what would reopen it.

## D1. Two endpoints, and the mixed one is removed

The maintainer asked for this to be thought through and agreed with the outcome.

A single contributors endpoint keeps the API's root short, and a caller can narrow it to one kind
with a filter. Against that:

- A mixed list has two shapes. The generated documentation has to describe each entry as one of
  two, and every client written against it branches on a type field before reading anything.
- Keeping the mixed list beside two typed ones gives every person two addresses. Each reference to
  a person then has to choose one, and callers cannot tell whether two addresses are the same
  person without requesting both.
- The one question only a mixed list answers is who is credited on a record, people and
  organizations together. The record now answers that itself, through its nested credits.

DataCite draws the same line with its personal and organizational name types. No release has
carried the API, so removing the mixed endpoint breaks nobody.

*Revisit if:* a caller needs one request that returns people and organizations together for a
reason a record's credits do not cover.

## D2. A list entry is compact and a single record is complete

FS-011 returns a project, dataset, sample or measurement in full in a list, because a script
walking a dataset wants every value. A directory of people is different. A biography, a set of
links and a history of affiliations for every person on a page makes the page large for a caller
who wants names and identifiers. The maintainer said the list should not carry the whole profile.
The list entry therefore holds what identifies someone, and it is a subset of the single record,
so a caller reading both never meets a field that means two things.

*Revisit if:* callers routinely request every person one by one after listing them.

## D3. One list of credits, with the portal's own roles

The maintainer ruled that creators and contributors are not separated. A record holds one ordered
list of contributions, each with its roles from the portal's contribution role vocabulary. Deciding
which roles make someone a DataCite creator, and which DataCite contributor type each other role
becomes, is a mapping an export owns. Putting it in the API would freeze it into every response.

## D4. The affiliation on a credit never falls back to the profile

A contribution stores the organization the person is credited from, and that value is kept with
the record. It does not follow the person when they change institution. Filling an empty one from
the person's current primary affiliation would attribute old work to an institution that had no
part in it, and the answer would change over time without the record changing.

*Revisit if:* portals report that most credits are entered without an organization.

## D5. A credit held by a hidden account is still shown

The people list leaves out superusers and the anonymous account, as the portal's own lists do. A
superuser can still be an author. The record's page shows that credit to every visitor, so the API
shows it too, with the name, identifiers and roles. It gives no address, because no profile is
served at one. The alternative, dropping the credit, would make a record's attribution wrong.

## D6. A contributor's records are public only, for every caller

FS-019 ruled that a contributor's page lists public projects and datasets only, even to the person
themself, so that a profile reads the same to everyone. The lists narrowed to a contributor follow
that rule and not the usual one, under which a caller also sees private records they hold a level
on. A caller who wants their own private records asks the ordinary lists.

## D7. Samples and measurements are not listed by contributor

A contributor's page has tabs for projects and datasets and none for samples or measurements. The
API offers the same two. Samples and measurements have one endpoint per registered type, so a list
of everything a person is credited on would be a new kind of endpoint spanning types, which is more
than this feature needs.

*Revisit if:* a contributor's page gains samples or measurements.

## Design review, 2026-10-12


One reviewer read the plan through three lenses before any code was written: one high finding,
six medium and seven low. Each was applied as an edit to the plan or the task list, except the two
below.

## D8. Design review: a contributor's records are the ones they are credited on

**A contributor's records are the ones they are credited on, and nothing else.** The plan first
used the methods behind an organization's page, which add the projects the organization owns. The
specification asks for the records a contributor is credited on, so the filter narrows by credit
alone and an owned project with no credit is left out.
*Revisit if:* the maintainer wants the API's list to match the organization page's tabs.
**ADR:** none — local to this feature, nothing outside it inherits the choice.

## D9. Design review: other names and the kind of affiliation are returned

**Other names and the kind of affiliation are returned although a person's page does not show
them.** The specification asks for a person's other names and for the kind of each affiliation.
Neither is on the person's own page today. Other names are entered under the label "Other names
you publish under", so they are public by intent, and the kind of affiliation is shown on the
organization's page, where owners and administrators are named. Both stay, as the approved
specification lists them. The maintainer is told at the merge gate so that either can be removed.
*Revisit if:* #246 gives a person control over what is shared.
**ADR:** none — a reading of this feature's own requirements.

## D10. Design review: neither list returns added or modified

**Neither list returns `added` or `modified`.** The specification's lists of fields do not name
them, and the endpoint being replaced returned neither. Both remain usable for ordering and for the
changed-since filters.
**ADR:** none — local to this feature.

## D11. Design review: type and country are stored codes only

**An organization's type and country are returned as stored codes only.** Labels beside them would
go beyond what the specification lists, and the codes are what the filters take.
**ADR:** none — local to this feature.

## D12. Design review: names on a credit come from an annotation

**Given and family name on a credit come from an annotation.** `Contribution.contributor` points at
the polymorphic base, so the credit queryset annotates the two names through `contributor__person`
in the same query. The reviewer's probe confirmed one query for a page of credits.
**ADR:** none — a detail of how one serializer is fed.

## D13. Implementer US1: a list serializer holds the credits

**The credits of a record go through `ContributionListSerializer`.** The plan names the two small
serializers for an identifier and an affiliation and the rewritten credit serializer. A credit
whose contributor was deleted has to be absent on every path, and the body that answers a create or
an update reads the record's credits from the database with no annotation on them. A list
serializer can drop the credit that names nobody and fill the given and family name of the
credits that arrive without them with one query for the whole list, so the credit serializer reads
one attribute whichever way the record was loaded.
*Revisit if:* the credit queryset gains a second path that makes the annotation unnecessary.
**ADR:** none, local to this feature.

## D14. Implementer US1: assertions the new shapes leave with nothing to read

**Two moved tests lose assertions about keys the list shape does not carry.** The person test no
longer asserts `type`, `profile` and `links`, and the organization test no longer asserts `type`
and the parent. The brief serves the list shape for a single record in this story, so the keys are
not there to assert. The assertions that remain are the ones the new shape supports, and the fuller
record serializers carry the rest. Two other pre-existing tests read the old credit keys and read
the new ones. Each change is named in progress.md.
*Revisit if:* the fuller serializers do not arrive with the assertions on those keys.
**ADR:** none, local to this feature.

## D15. Implementer US1: stable order for the two lists

**Both viewsets order by name and then by primary key.** The people queryset had no default
ordering of its own, and the old mixed list was ordered by name. Name is not unique, and pages cut
from an order with ties can repeat or skip an entry.
*Revisit if:* a caller needs another default order.
**ADR:** none, local to this feature.


## D16. Implementer US2: the people filters and the moved profile test

**`organization` does not use `distinct()`, `identifier` does.** A person has at most one
affiliation to an organization (the model's uniqueness constraint), and the three conditions are
applied in one `filter()` call so they hold on the same row, so the join cannot repeat a person.
An identifier is matched on its value and on the value with its spaces removed, and a person
holding both forms would be listed twice without it.
*Revisit if:* an organization can hold a person through more than one affiliation.

**The assertions on `profile` and `links` that D14 took out of the moved person test are in
`TestPerson`, and the moved test is untouched.** The brief names the single record as where they
return. They sit in new tests of the new class, so no pre-existing test changed in this story.
*Revisit if:* the moved test should carry them as well.
**ADR:** none, local to this feature.

## D17. Implementer US3: members, the affiliation type and the organization filters

**The serializer decides who is a member, and the viewset's prefetch only bounds what is
loaded.** `OrganizationSerializer.get_members()` keeps affiliations of at least the member level
with no end date whose person is not a superuser or the anonymous account, whatever was
prefetched. The single-record queryset prefetches only the current verified affiliations with
their people, so the query count is constant, and a serializer used on a queryset with no prefetch
still leaves a pending or ended member out. The hidden accounts come from
`RecordReferenceField.hidden_contributor_pks()`, one query per request.
*Revisit if:* a second consumer of the serializer needs the members loaded another way.

**The kind of an affiliation is one field class, `AffiliationTypeField`.** A person's affiliation
and an organization's member give it the same wording, so the method that wrote it moved out of
`AffiliationSerializer` into a field both use. The values a person's affiliation returns are
unchanged.
*Revisit if:* an affiliation level other than member, admin or owner is exposed.

**`sub_organizations` follow the model's default order, by name; `type` is a choice filter and
`country` an exact match on the two-letter code.** The type filter documents its values in the
generated schema. An unknown type is therefore answered 400, which the specification does not
describe and no test pins. A lower-case country code finds nothing.
*Revisit if:* callers send country codes in lower case.
**ADR:** none, local to this feature.

## D18. Implementer US4: the contributor filter and the two addresses

**`contributor` is a `CharFilter` with a method, and the lookup is two queries.** The identifier
is looked up among `Person.objects.real()` and then `Organization.objects`, and a miss returns
`queryset.none()`, so an unknown identifier, a superuser's, the anonymous account's and a database
number all answer 200 with an empty list. A `ModelChoiceFilter` would have answered 400.
*Revisit if:* a caller needs to tell "no such contributor" from "no records".

**The narrowing is by primary key through `projects.get_visible()` or `datasets.get_visible()`,
never `get_public_projects()`.** `Organization` overrides the latter to add the projects it owns,
which the specification does not call credit. `FairDMVisibilityFilter` still runs first, so the
result is the public credited records for every caller, including a member of a private record's
team.
*Revisit if:* the specification widens the list to what the caller may see.

**The two addresses come from one mixin, `ContributorRecordsMixin`, not from each serializer.**
`PersonSerializer` and `OrganizationSerializer` have different list bases and need identical
fields, so the two method fields and the helper that builds the address are written once. The
mixin is a `Serializer`, so the declared fields are collected.
*Revisit if:* a third serializer needs the addresses with different routes.
**ADR:** none, local to this feature.
