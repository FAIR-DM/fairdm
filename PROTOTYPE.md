# Prototype: the contributors page

The prototype branch `prototype-contributors-page`. It is a reference and is never merged. The
record of decisions is the GitHub issue labelled `prototype` that links to this file.

## What a person can now do

On the Contributors tab of a project, dataset, sample or measurement, someone who manages the
record:

- sees the people credited on it in the main column, in credit order, and the organizations in a
  narrower column beside it (stacked below the people on a narrow screen);
- sees, for each person, their avatar, name, the affiliation recorded on this record (an em dash
  when there is none) and their roles as a row of badges;
- sees the organizations in a set order it can't change: the affiliations of the people who are
  Project Leader on the record first, each with a Project Leader badge, then the rest; an
  organization people are credited from, with no roles of its own, shows Project Member, and one
  with roles of its own shows them;
- adds a person who is already in the portal, by searching for them by name;
- adds someone who isn't in the portal yet, by given and family name;
- picks the person's affiliation on this record: the organizations on their profile first, marked
  Current or Past, then every other organization in the portal, with a search box that filters
  the list;
- picks the person's roles from the roles this kind of record offers, as toggle chips;
- edits a person's affiliation and roles;
- removes a person, with an Undo button in the notice that follows;
- reorders the people in a sheet by their drag handles, and with the eye beside each name chooses
  whether that person appears in the record's citation (on) or is credited but left out of formal
  citations (off); the order and the eyes are saved together;
- adds an organization from the portal or by a new name, with roles;
- edits an organization's roles, or gives roles to an organization that is only there as an
  affiliation;
- removes an organization that no one is credited from.

Someone who can only view the record sees the same two lists with no Add buttons and no actions.

## The shared pieces

**One action toggle per row.** Every row with actions has a single ellipsis button at its top
right, in line with the row's title, even when there is only one action. It opens the row's
actions in an `mvp.sheet`: a bottom sheet on a phone, a centred dialog on a wide screen. Never a
dropdown. This is `c-mvp.list.row` with its dropdown hidden at every width
(`page.css`: `[data-mvp-row-ready] .contrib-face .mvp-row-dropdown{display:none}` and the sheet
trigger forced to `inline-flex`). On a touch screen the same actions are also reachable by swiping
the row; Edit is the long-swipe action.

**Every change answers with the whole region.** Each form posts with htmx and the server returns
`#contrib-region` (both columns, both counts and the notice), so the counts and the Affiliation
badges never drift from the lists. A successful save sends `HX-Trigger: contrib:done`, which closes
the open sheet.

**Forms open in one sheet slot.** Add and Edit fetch a sheet into `#contrib-sheet-slot` and open it
with `HX-Trigger-After-Settle: {"mvp-sheet-open": {"id": "contrib-sheet"}}`. Multi-step adds swap
`#contrib-sheet-step` inside the open sheet. The submit button sits in the sheet's foot and is
bound to `form#contrib-form`; it hides itself on a step with no form.

**Role chips.** Checkbox inputs styled as toggle chips (`.contrib-chips`), used wherever roles are
picked.

**The undo notice.** A fixed notice at the bottom of the screen, raised above the dock below
1024 px, gone after six seconds unless hovered or focused.

## The look, file by file

| File | What it holds |
|---|---|
| `fairdm/contrib/contributors/plugins/page.py` | The plugin, registered on Project, Dataset, Sample and Measurement, and its extra views |
| `templates/contributors/page/page.html` | The page: the region and the sheet slot |
| `templates/contributors/page/region.html` | Both columns, their headings, counts and Add buttons, and the notice |
| `templates/contributors/page/person_row.html` | A person's row and actions |
| `templates/contributors/page/organization_row.html` | An organization's row and actions |
| `templates/contributors/page/sheets/*.html` | Add person (search, new person, details), edit person, add organization, edit organization roles, reorder |
| `static/contributors/page.css` | The two-column container query (52rem and 72rem), row, chip, option list and notice styles |
| `static/contributors/page.js` | Closes the sheet on `contrib:done`, times the notice, focuses the first field on a fine pointer |

A person's row is the contributors package's `c-contributor.item`, given the credit, so it draws
the avatar, the linked name, the affiliation on this record and the role badges. An organization's
row uses `c-contributor.avatar` and `c-contributor.name`, with its own badges. Every avatar in the
page and its sheets is `c-contributor.avatar`, so people are round and organizations are grey
boxes as everywhere else in the portal. The sheets have no art beside their title.

## Screens

Seed with `python manage.py seed_contributors_prototype`, then sign in as
regular.user@example.com (manages the project and dataset) or regular.user2@example.com (can only
view the project). The command prints the three addresses below; they are stable across reseeds.

| Screen | Address |
|---|---|
| A project with eight people and seven organizations | `/projects/pr3HsZMcras5pt3E3SouZXx/contributors/` |
| A dataset with four people and one organization | `/datasets/dEFN9YqjEcVcBCp5oyWEyN6/contributors/` |
| A dataset with only its creator | `/datasets/deiXbcrwzzXwWgVYGnPuaT6/contributors/` |

## The data model

Nothing new. The page reuses `Contribution` (one row per person or organization credited on a
record, with roles, a per-record affiliation, an access level and an order) and the `Crediting`
service for every change, so its rules hold: adding a person with an affiliation lists that
organization, an organization people are credited from can't be removed, and the last manager
can't be removed.

The organizations column starts with the affiliations of the people who hold Project Leader on the
record, in those people's credit order. The rest follow: the organizations credited directly, in
credit order, then those that are only the affiliation of a person on the record, by name.

## Decisions

- 2026-11-26: Every sheet's head is one line. Where the title and the line under it said the same
  thing, the two are now one title, such as "Add a person to this project".
- 2026-11-26: Organizations aren't ordered by hand but have a default order. The affiliations of
  Project Leaders come first with a Project Leader badge. The "Affiliation" badge is gone:
  organizations people are credited from show Project Member, and organizations credited
  directly keep their roles.
- 2026-11-26: The reorder sheet has no up and down buttons. Each row is the name, then an eye that
  puts the person in the citation or leaves them out, then the drag handle.

- The sheet is used at every width, with no dropdown even for a mouse.
- Remove happens at once and offers Undo, rather than asking for confirmation first.
- An organization that people are credited from can't be removed, only given roles.
- Changes need the manage level on the record.
- Organizations aren't reordered.

## Faked or skipped

- The Project Leader and Project Member badges of an organization are worked out when the page is
  drawn, not stored on its credit.

- Whether a person appears in the citation is kept in their `config`, as a list of the records
  they are left out of. The contribution needs a field for it.
- Without the up and down buttons, the reorder list has no way to move a row by keyboard. The
  reorder component's handle needs keyboard moves before the buttons can go for real.

- The affiliation search filters, in the browser, a list of every organization in the portal. A
  real build needs a server-side search once the portal holds many organizations.
- New people and organizations are created by name only, with no ORCID or ROR lookup.
- Undo carries the removed credit's details (contributor, roles, affiliation, level, order) in a
  hidden field and recreates it.
- The existing Contributors tab is hidden on this branch and moved to `contributors-previous/`.
- Nothing is seeded for samples or measurements, though the page is registered on them.
- On a phone, django-mvp's one-time swipe hint on the first row clips the three action labels.

## What it replaces

The Contributors tab on every core record type.
