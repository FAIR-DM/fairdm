# Decisions: people, organizations and a record's credits can be read through the API

Questions the specification answered without putting them to the maintainer, with the reasoning
that is too long for the specification itself. Each says what would reopen it.

## Two endpoints, and the mixed one is removed

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

## A list entry is compact and a single record is complete

FS-011 returns a project, dataset, sample or measurement in full in a list, because a script
walking a dataset wants every value. A directory of people is different. A biography, a set of
links and a history of affiliations for every person on a page makes the page large for a caller
who wants names and identifiers. The maintainer said the list should not carry the whole profile.
The list entry therefore holds what identifies someone, and it is a subset of the single record,
so a caller reading both never meets a field that means two things.

*Revisit if:* callers routinely request every person one by one after listing them.

## One list of credits, with the portal's own roles

The maintainer ruled that creators and contributors are not separated. A record holds one ordered
list of contributions, each with its roles from the portal's contribution role vocabulary. Deciding
which roles make someone a DataCite creator, and which DataCite contributor type each other role
becomes, is a mapping an export owns. Putting it in the API would freeze it into every response.

## The affiliation on a credit never falls back to the profile

A contribution stores the organization the person is credited from, and that value is kept with
the record. It does not follow the person when they change institution. Filling an empty one from
the person's current primary affiliation would attribute old work to an institution that had no
part in it, and the answer would change over time without the record changing.

*Revisit if:* portals report that most credits are entered without an organization.

## A credit held by a hidden account is still shown

The people list leaves out superusers and the anonymous account, as the portal's own lists do. A
superuser can still be an author. The record's page shows that credit to every visitor, so the API
shows it too, with the name, identifiers and roles. It gives no address, because no profile is
served at one. The alternative, dropping the credit, would make a record's attribution wrong.

## A contributor's records are public only, for every caller

FS-019 ruled that a contributor's page lists public projects and datasets only, even to the person
themself, so that a profile reads the same to everyone. The lists narrowed to a contributor follow
that rule and not the usual one, under which a caller also sees private records they hold a level
on. A caller who wants their own private records asks the ordinary lists.

## Samples and measurements are not listed by contributor

A contributor's page has tabs for projects and datasets and none for samples or measurements. The
API offers the same two. Samples and measurements have one endpoint per registered type, so a list
of everything a person is credited on would be a new kind of endpoint spanning types, which is more
than this feature needs.

*Revisit if:* a contributor's page gains samples or measurements.
