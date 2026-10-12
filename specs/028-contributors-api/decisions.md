# Decisions: people and organizations can be created and changed through the API

Questions the specification answered without putting them to the maintainer, with the reasoning
that is too long for the specification itself. Each says what would reopen it.

## Adding a profile gives no right to change it

FS-020 names who keeps each profile, and "the person who added it" is not on that list. Giving the
adder a lasting right would create a second rule about who edits a profile, held only by the API,
and would let whoever first typed a researcher's name keep control of that researcher's public
page. So a caller who adds a person and then spots a typo cannot correct it. A community manager
can, and so can the person once they claim the profile.

*Revisit if:* loading scripts turn out to need a short window in which to correct what they have
just added.

## Identifiers are written here although the editing pages leave them out

FS-020 FR-010 keeps ORCID iDs, ROR IDs and other identifiers off the editing pages. The
maintainer's confirmed reading of this feature includes them, because a script that adds an author
without their ORCID iD has added a name and nothing that distinguishes it from another person of
the same name.

Two limits keep this from undermining what FS-020 was protecting:

- An identifier a contributor already holds is never changed or removed through the API. An
  unclaimed person's ORCID iD is what lets the right person claim the profile, so swapping it would
  hand the profile to someone else.
- A person with an active account cannot add an ORCID iD to their own profile. In the portal an
  ORCID iD on an account is proved by signing in with ORCID. A value typed into a request is a
  claim with no proof.

*Revisit if:* the portal gains a page for correcting a wrong identifier, at which point the API
should follow it.

## An identifier already held refuses the request and names the holder

The alternative was to return the existing contributor as though the request had succeeded. That
hides from the caller that nothing they sent was saved: a script that sent a different spelling of
the name would believe the portal now holds its spelling. Refusing and naming the holder tells the
caller the truth and still gives them the record to use, in one round trip.

*Revisit if:* callers ask for a single request that means "give me this contributor, adding them if
needed".

## Any signed-in caller may add, with a limit of its own

Confirmed by the maintainer. The risk is an account that fills the portal with invented people, or
writes a biography for a real person who has not agreed to it. Three things bound it: the caller
must be signed in, so every addition has an account behind it; adding has its own, lower limit; and
the community managers keep every unclaimed profile and can correct one. A switch restricting adding
to community managers was considered and left out, because the operator can already set the limit
to nothing allowed, and no portal has asked for anything finer.

*Revisit if:* a portal with open registration reports abuse the limit does not contain.

## The photo or logo is included

FS-011 put file upload out of scope and said JSON is the only format. That was written about
records, which hold no files. A contributor's editing page offers a photo or logo, and the
maintainer confirmed the API should offer what the page offers. How the image is sent is a planning
question. The specification requires only that it can be set, replaced and removed.

## No endpoint for affiliations

A person's affiliations decide who administers an organization, so writing them is writing access
rights. FS-020 keeps them off the editing page for that reason and the API follows it. They are
still read with the contributor.
