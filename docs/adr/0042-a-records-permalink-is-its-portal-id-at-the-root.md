# ADR 0042 — A record's permalink is its portal ID at the portal's root

**Status:** accepted

## Decision

Every project, dataset, sample, measurement, person and organization is reachable at
`<portal>/<portal ID>/`, its permalink. One URL pattern, named `permalink`, matches only an address
shaped exactly like a portal ID, built from the five records' `uuid` fields. It is the last pattern
at the portal's root, so any page the portal or an addon declares there wins over it.

The permalink is a temporary redirect to the overview address for the ID's first letter. It looks
nothing up. The overview page finds the record as its own type and decides who may see it, so a
private record's permalink answers exactly as an ID that belongs to no record.

Citations of records with no DOI or IGSN, the Share menu, the identifiers card and a dataset's
DataCite export give the permalink, through `get_permalink` and the `permalink` template tag. The
API's `url` field stays the address of the record's page.

## Why

A record's page address is built from how a portal lays out its pages, and every link handed out
breaks when that layout changes. The portal ID already names one record and says what kind it is,
so it is the shortest address that can outlive a layout change.

The root needs no prefix, because no word a portal uses for its pages has a portal ID's shape, and
putting the pattern last means a declared page always wins. The redirect is temporary because
browsers keep a permanent redirect with no expiry, so a visitor who had followed the link once would
keep reaching the old address after a move. The link does no lookup because a lookup would answer a
private record with a redirect and an unknown ID with not-found, which tells a visitor the private
record exists. Its page deliberately never does.

## Revisit if

- Portal IDs change their form, or a new kind of record gets a portal ID. The pattern and the
  letter map change with them.
- A portal needs a root page whose path has the shape of a portal ID.
