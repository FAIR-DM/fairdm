# Prototype notes: 022-record-contributors-and-access

A working prototype of the Contributors tab, built to be looked at before the feature is planned.
The screens are what is being proposed. The code behind them has no tests and is to be rebuilt.

Seed the data with `DJANGO_ENV=development python manage.py seed_contributors`. It prints the
address of each example record and signs in through `regular.user`, `staff.user` and `super.user`
at `example.com`, password `password`.

## What exists

- A `Contribution` links one contributor to one record. It already carries contribution roles, an
  affiliation and a place in an order. It carries nothing about what the contributor may do.
- All four record types have a `contributors` relation and a `CONTRIBUTOR_ROLES` group taken from
  the roles vocabulary: 6 roles for a project, 16 for a dataset, 5 for a sample, 3 for a
  measurement.
- Record-level rights are stored per person per record as separate permissions. Creating a project
  or a dataset through the portal grants its creator five of them. A sample takes view and change
  rights from its dataset. Nothing takes rights from a project, and a measurement takes none from
  its dataset.
- A Contributors tab was registered on projects only. Its list page drew the generic filter form,
  and its add form was written for a component library the portal no longer uses.
- Components that fit and were reused: `c-list` and `c-list.row`, `c-contributor.item` (avatar,
  name, affiliation, role badges), `c-card`, `c-badge`, `c-alert`, `c-button`. Nothing was missing
  for these screens. One small component was added, `c-contribution.access`, which says in words
  what one contributor may do.
- A record's tabs are drawn in the page header by the plugin menu, so the tab is an ordinary page.

## The screens

| Screen | What it shows |
|---|---|
| Contributors tab, reader | People in a wide column, numbered in their order, with roles. Organizations as cards in a narrow column beside them, in their own order. Below the large breakpoint the organizations drop beneath the people. Search by name covers both. No controls |
| Contributors tab, manager | The same two columns. Under each person, what they may do, with Move up, Move down, Edit and Remove. Each organization card carries the same controls. An "Add a contributor" button in the page title. Under the people, a card naming those who hold access from the record above |
| Add a contributor | One card with two rows of tabs. The first row chooses a person or an organization. The second chooses how to find them: already in the portal, by ORCID (a person) or in ROR (an organization), or entered by hand. Adding by any route goes straight to the edit page |
| Edit a contributor | Roles as checkboxes, then the three levels as radio buttons with a line under each saying what it allows. Saved together. An organization gets the roles and a sentence saying it holds no access |
| Remove a contributor | What goes with them, then Remove and Cancel. When they are the only manager the page says why and offers only the way back |

## What the screens need from the code

1. A level per person per record (view, edit, manage) that can be read for a whole list of
   contributors without a query per row.
2. The level a person holds from the records above, and which record it comes from, for every
   listed person and for people who are not listed on the record at all.
3. The set of people who count as able to manage a record, for the last-manager rule, checked at
   save time in a way that holds when two changes arrive together.
4. Whether a person can sign in and act, so the tab can say a level has not taken effect yet.
5. A record's people in one order and its organizations in another, which the overview, the
   citation and the tab all read.
6. Moving one contributor up or down one place among their own kind. The numbers shown are
   positions, not stored values.
7. Search over a record's contributors by name, and separate searches over the people and over the
   organizations in the portal that mark the ones already listed.
8. The roles a record type offers, in the vocabulary's order.
9. The link from each overview's People card to this tab. Only the project overview has it today.
10. The tab on every registered sample and measurement type with no configuration.
11. A search of ORCID by name or iD, and of ROR by name or ID, returning for each match a name, one
    line that tells namesakes apart, and the identifier.
12. Making a person from an ORCID record and an organization from a ROR record, with the identifier
    kept, and recognising one that is already in the portal by that identifier.
13. Making a person or an organization from a few typed fields, after checking for profiles with the
    same name.

## What the sketch faked

- Levels are not stored as levels. They are read from and written to the existing record
  permissions: view, change and delete on the record stand for view, edit and manage. Other stored
  permissions (metadata, settings, import, publish, add and modify contributor) are ignored.
- Nothing enforces who may open a record. A private record's Contributors tab opens for anyone,
  signed in or not. Only the pages for adding, editing, removing and reordering are refused.
- Rights from the record above are worked out for display and for the manager check only. Being
  given "Can edit" on a project does not yet let a person edit its datasets.
- A level set for a person without an account is stored like any other. Nothing delays it.
- The last-manager rule is checked without any guard against two changes at once.
- A person holding the Data Curator portal role is treated as a manager only through the portal-wide
  delete permission. Nothing checks that a curator is left off the record or unmarked.
- Creating a record does not yet make its creator a contributor at the manage level on samples and
  measurements, and on projects and datasets it still grants the older set of five permissions.
- Nothing is migrated. Existing rights show up as whichever level their view, change and delete
  permissions amount to.
- Moving a record to another project or dataset is not checked.
- The add search is a plain name match limited to 20 results, with no paging.
- ORCID and ROR are not contacted. Each search answers from four fixed records after a short pause,
  so the searching state can be seen. For people, try "garcia", "carberry" or an iD shown in the
  results. For organizations, try "potsdam" or "jülich". Anything else finds nothing.
- A contributor added from ORCID or ROR is saved with a name only. The identifier, the affiliation
  and the place are shown on the confirmation and then dropped. A match already in the portal is
  recognised by name, not by identifier.
- A person or organization entered by hand is saved with a name only. The email address, city,
  country and website are asked for and not kept. Nobody is invited.
- People and organizations share one stored order. The two lists on the tab are that order split
  by kind.
- The list is not paged. The long example has 37 contributors.
- The order shown on the tab is not yet what the overview and the citation read.
- The affiliation recorded with a contribution, which the old edit form offered, has no place on
  the new edit page. The specification leaves it "editable where it is today", and this prototype
  removes that place.
- Removing someone while they have the page open, and losing the manage level mid-edit, are not
  handled beyond the refusal on the next request.

## What was ruled by eye

Asked for in review, and done:

- People and organizations are two lists, not one. People are in the main column. Organizations
  are cards stacked in one narrower column to the right, and drop below the people on a narrow
  screen. Each list has its own order. The alternative named in review was a filter in the page's
  actions that switches between people and organizations. It was not built and can be asked for if
  the two columns do not sit right.
- Adding has two pathways, a person and an organization, kept in one card with tabs. Each has three
  ways in: search the portal, search ORCID or ROR, or enter by hand.
- The empty state has no button of its own. "Add a contributor" in the page title is the one way in.

Not yet reviewed. These are the choices that have no right answer, as built:

- The add card's tabs are two rows. The top row is underlined tabs for "A person" and "An
  organization". Under it a smaller boxed row holds the three ways in, so the two choices look
  different and both stay in view. Every tab is a link, so a search or a chosen record keeps its
  place in the address.
- A match from ORCID or ROR is chosen first and confirmed on a second step that shows the name, one
  line of detail and the identifier. A match in the portal is added in one step.
- When someone typed in by hand has the same name as a profile in the portal, the form comes back
  with those profiles offered first and a button to make the new profile anyway.
- An organization entered by hand is asked for name, city, country and website. A person is asked
  for given name, family name and an optional email address.
- A manager sees one line under the organizations saying they hold no access. It is no longer
  repeated on every organization.
- Adding is a page, not a dialog over the list.
- Adding one contributor at a time, then straight to their edit page.
- A manager's row for a person has two lines at every width: who and roles above, access and
  controls below.
- Reordering is Move up and Move down buttons. Dragging is not offered. (Buttons are needed anyway
  for people who cannot drag, so dragging would be an addition and not a replacement.)
- Roles are a grid of checkboxes, two columns from the small breakpoint up, including the dataset's
  16.
- The level names shown are "Can view", "Can edit" and "Can manage". The manage badge is filled and
  the other two are outlined.
- People who hold access from the record above and are not listed get their own card under the
  people, shown to managers only, with a link to where it is changed.
- A listed person whose effective level comes from above shows that level with "from the project"
  or "from the dataset" beside it.
- Remove is reached from the row and from the foot of the edit page.
- The reader's view shows no levels at all, not even the reader's own.

## Where the points still to be confirmed would move a screen

- **Three levels.** The edit page's radio group is the three levels. A list of separate permissions
  would replace it with a set of checkboxes and the row's single badge with several.
- **Rights flow downward.** Without it the "Access from the project" card goes, the "from the
  dataset" notes go, and no level on the edit page is ever disabled. Every sample and measurement
  would need its own people listed.
- **Everything on the tab needs manage.** If the edit level could change credit, an editor would
  see Add, Edit and the move buttons, and the edit page would show them the roles and hide the
  levels.
- **Access-only contributors are listed.** Noor Haddad on the private example dataset is one: she
  appears in the reader's list with no role. Hiding such people would need a second list that only
  managers see.
- **Upgrade keeps access by listing people.** No screen changes. It decides who is in the list on
  the day a portal upgrades.

## Where review has moved past the specification

The specification's assumptions say a person to be added must already have a profile in the
portal, and put creating a person or an organization from the tab outside its scope. The add card
now offers both, and looks people up by ORCID and organizations in ROR. The specification needs
that assumption replaced and requirements added for the three ways in before it is approved. It
also speaks of one order of contributors, where the tab now keeps one for people and one for
organizations.
