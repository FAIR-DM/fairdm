# Feature Specification: Find a record from anywhere in the portal

**Feature Branch**: `042-site-search`

**Created**: 2026-11-25

**Status**: Draft

**Goals**: G9: records in the core model can be searched, sorted and filtered from the portal. G5:
a modern, extensible interface that every portal gets by default, with no frontend work. G12:
private and public data sit side by side, controlled per object.

**Roadmap**: none. R17 (records can be found, sorted and filtered) is the nearest item. It is about
the search on each list page, and this feature reuses that search rather than replacing it.

**Input**: https://github.com/FAIR-DM/fairdm/issues/718. Anyone using the portal should be able to
find a record from any page: search the portal's projects, datasets, samples, measurements, people,
organizations and literature from the header, and see the results grouped by kind. Each kind shows
only the records the person may see. The results page, dialog, button and field are django-mvp's
search as it ships, with one search kind per record type.

## What exists, and what this specification changes

On `main` a person can only search one record type at a time, from the search box on that type's
list page: the project list, the dataset list, the people list, the organization list and the
literature catalogue. Samples and measurements have no list page of their own, so they can be
searched only inside the dataset or collection that holds them. Nothing in the header searches, and
nothing searches across record types.

django-mvp ships a site search: a results page, a dialog that shows results as the person types,
and a header field and button that open the dialog. It searches whatever kinds of result a site
registers. FairDM registers none and does not mount the search.

After this feature:

- Every page with the portal's header carries the site search at the right-hand end of the header:
  a field on a wide screen and a button on a phone or tablet. Both open the same dialog with the
  field ready for typing, and the keyboard shortcut django-mvp provides opens it from anywhere.
- The search finds projects, datasets, samples, measurements, people, organizations and literature,
  and shows what it found grouped by record type.
- A record is found by the same text that finds it in the search box of its own list, or of the
  table its samples or measurements sit in.
- Each record type shows only the records the person may open.

## Boundary

- **The header around the search** belongs to https://github.com/FAIR-DM/fairdm/issues/719: removing
  the "Create new" button, the site's name beside its icon, the dock and the sidebar toggle.
- **How the results page, dialog, field and button look and behave** is django-mvp's. A change to
  them, the placement of the results page's icon included, is made in django-mvp
  (https://github.com/django-mvp/django-mvp/issues/721 to
  https://github.com/django-mvp/django-mvp/issues/724), not in FairDM.
- **Better matching and ranking** (partial words, closest match first, an index) belong to R17, which
  improves the search on each list page. Because this feature finds a record by the text its list
  search uses, that work improves both at once.
- **The visitor's landing page** has a header of its own, without the app header, and keeps it. A
  signed-out visitor reaches the search from every other page.
- **Searching other portals** is R29.

## Clarifications

### Session 2026-11-25

- Q: Are records indexed, or matched by name and identifier? → A: Matched, by the same fields each
  record type's own list search matches: names, the portal's identifiers and, where the list search
  takes them, external identifiers and a sample's local ID. No index is built for this feature.
  Recorded in `decisions.md`.
- Q: Does a person who holds a level on a private project find it? → A: Yes. Each record type shows
  the records the person may open, which for a private project or dataset includes the ones they
  hold a level on. Recorded in `decisions.md`.
- Q: What does a person see for a record type that found nothing? → A: What django-mvp's search shows
  for it: the dialog leaves the type out, and the results page lists it with a count of none.
- Q: Which record types are searched, and in what order are their groups shown? → A: Projects,
  datasets, samples, measurements, people, organizations, literature, in that order, the order of
  the issue and the prototype.
- Q: Are samples and measurements of a domain's own types found? → A: Yes. A registered sample or
  measurement type is found as a sample or a measurement, with no step for the portal's developer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A person finds a record from any page (Priority: P1)

Anyone using the portal, signed in or not, types part of a record's name or one of its identifiers
into the header's search, and sees the matching projects, datasets, samples, measurements, people,
organizations and literature, grouped by record type, each one a link to the record's page.

**Why this priority**: it is the whole feature. Without it, finding a record means knowing which
list it is on and going there first, and a sample or measurement can only be found by first opening
the dataset that holds it.

**Independent Test**: seed a portal with records of every type, some private. As a visitor, as a
signed-in person with no levels, and as a person who holds a level on a private project, search from
the header of a list page and of a record page, and check which records come back under which type.

**Acceptance Scenarios**:

1. **Given** any page that shows the portal's header, **When** a person opens the search from the
   header, **Then** the search dialog opens with its field ready for typing, on a wide screen from
   the field and on a phone or tablet from the button.
2. **Given** any page that shows the portal's header, **When** a person presses the search's
   keyboard shortcut, **Then** the same dialog opens.
3. **Given** a public project, dataset, sample, measurement, person, organization and literature
   reference whose names share a word, **When** a person types that word, **Then** each record is
   listed under its own record type and links to the record's page.
4. **Given** a sample with a local ID, **When** a person searches for that local ID, **Then** the
   sample is found. **And** a project, dataset, sample or measurement is found by its portal ID.
5. **Given** a record the person may not open (a private project, a dataset inside a private
   project, a sample of a private dataset), **When** they search for its name, **Then** it is
   neither listed nor counted.
6. **Given** a person who holds a level on a private project, **When** they search for its name,
   **Then** the project is found, and so are its datasets, samples and measurements that they may
   open.
7. **Given** a signed-out visitor, **When** they search, **Then** the search works and finds only
   the records a visitor may open.
8. **Given** a query that matches more records of a type than the dialog or results page shows,
   **When** the person follows that type's link to the rest, **Then** they see every match of that
   type that they may open, a page at a time.
9. **Given** a query that matches nothing, **When** the person searches, **Then** they are told
   nothing was found, and no record type is shown with results.
10. **Given** a person on the search results page, **When** they choose one record type, **Then**
    only that type's matches are shown.
11. **Given** a sample or measurement of a type a domain package registered, **When** a person
    searches for its name, **Then** it is found among the samples or measurements and links to its
    own page.
12. **Given** people who are superusers, **When** anyone searches for their names, **Then** they are
    not found among the people, as they are not listed on the people list.

### Edge Cases

- **An empty or blank query.** The dialog lists the record types it searches, with a line about what
  each holds. The results page shows no results. Both are django-mvp's handling, checked in
  `mvp/search/views.py`.
- **A very long query** is cut to django-mvp's limit before any record type sees it.
- **Unclaimed people.** A person with no account is found, as they are on the people list.
- **The visitor's landing page** has no app header, so it carries no search. The dashboard a signed-in
  person lands on does.
- **A record's visibility changes** between two searches. The second search follows the record's
  visibility as it is then: nothing is cached.
- **A dataset that is public inside a private project** is hidden from someone who holds no level on
  the project, as everywhere else in the portal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The portal MUST mount django-mvp's site search, so its results page and the dialog's
  results are reachable for every visitor, signed in or not. (US1)
- **FR-002**: Every page that shows the portal's header MUST carry django-mvp's search field and
  button at the right-hand end of the header, and its search dialog. (US1)
- **FR-003**: The search MUST find projects, datasets, samples, measurements, people, organizations
  and literature, one record type to a group, in that order. (US1)
- **FR-004**: A record type MUST find a record by the same text that finds it in its own list's
  search: projects and datasets by name, portal ID and external identifier, samples by name, local
  ID and portal ID, measurements by name and portal ID, people and organizations by name, and
  literature by what the literature catalogue's search matches. (US1)
- **FR-005**: Each record type MUST list and count only the records the person may open: projects,
  datasets, samples and measurements by their visibility and the levels the person holds, people as
  the people list does, and organizations and literature as their lists do. (US1)
- **FR-006**: A sample or measurement of a registered type MUST be found as a sample or a
  measurement, and link to its own page, with no step for the portal's developer. (US1)
- **FR-007**: Each result MUST link to the record's own page. (US1)
- **FR-008**: The portal's start-up checks MUST pass with the search mounted: every record type is
  registered and the search's addresses are reachable. (US1)

### Key Entities

- **Record type in the search**: one kind of record the search finds, with the fields that match,
  the records a person may open, and how a match is described in the results. It holds no data of
  its own.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From any page with the portal's header, a person reaches a record they can name in at
  most three actions: open the search, type, choose the result.
- **SC-002**: Every one of the seven record types can be found from the header search.
- **SC-003**: No search, by any person, lists or counts a record that person may not open.
- **SC-004**: For each record type with a list search, every record that list's search finds for a
  query is also found by the site search for the same query.

## Assumptions

- django-mvp's search, as it ships in the version FairDM depends on, provides the results page, the
  dialog, the field, the button and the keyboard shortcut. FairDM adds no look of its own to them.
- The header changes in https://github.com/FAIR-DM/fairdm/issues/719 and this feature touch the same
  place in the header. Whichever lands second keeps both.
