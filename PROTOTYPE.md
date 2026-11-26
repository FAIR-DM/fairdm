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
  Project Leader on the record first, then organizations that are Project Leader themselves, each
  with a Project Leader badge, then the rest; an
  organization people are credited from, with no roles of its own, shows Project Member, and one
  with roles of its own shows them;
- adds a person who is already in the portal, by searching for them by name or ORCID iD; a name
  that isn't in the portal shows as one more row of the results, marked New, and choosing it goes
  straight to the people ORCID has under that name ("Do you mean?", powered by ORCID); there is no
  separate "Add someone new" button;
- types an ORCID iD in the same search: the person holding it in the portal is listed, or, when
  nobody does, their public ORCID record shows as a New row (name, employer, the iD with the ORCID
  iD icon), which goes straight to their affiliation;
- on "Do you mean?", narrows ORCID's matches with a Name field (prefilled with the name typed) and
  an Affiliation field, both full width and kept at the top of the sheet while the list scrolls;
  the list is asked again as they type;
- picks someone from ORCID's matches, or chooses Add by name alone (the foot's main button), which
  asks them to check the given names and family name, guessed from the name (the last word is the
  family name), before the affiliation step;
- finds the person's affiliation on this record in a step drawn like Add an organization, under
  "Select their affiliation on this project": a search kept at the top, then, as rows with an
  avatar and a chevron, every organization on their ORCID record (past ones and education
  included, the current ones marked with a grey Current badge) or on their portal profile, then
  the portal's other organizations; the search filters them all;
- finds an affiliation that isn't in the portal from the same step: the name typed shows as a New
  row, which goes to what ROR has under that name ("Do you mean?", powered by ROR), to pick from
  or to add by name alone; it is made in the portal, with its ROR ID when picked from ROR, when
  the person is added;
- chooses No affiliation (the affiliation step's main button) instead;
- picks the person's roles on the last step, which shows the affiliation chosen (marked New when
  it isn't in the portal yet) above the roles, and adds them with a button that names them
  ("Add Aiko"); Back returns to the step the affiliation was picked on;
- picks the roles from the roles this kind of record offers, as toggle chips, with
  Project Member ticked and locked for anyone being added;
- edits a person's affiliation and roles;
- removes a person, with an Undo button in the notice that follows;
- reorders the people in a sheet by their drag handles, and with the eye beside each name chooses
  whether that person appears in the record's citation (on) or is credited but left out of formal
  citations (off); the order and the eyes are saved together;
- adds an organization from the portal, with roles; a name that isn't in the portal shows as one
  more row of the results, drawn like the portal's own rows and marked New, and choosing it goes straight to what ROR
  has under that name ("Do you mean?");
- adds an organization that isn't in the portal yet, starting from its ROR ID: the field searches
  the ROR registry, starting with the name typed in the portal search, and picking a match fills
  the name; with a name alone, Continue opens "Do you mean?", powered by the Research Organization
  Registry (ROR): what ROR has under that name, with Add by name alone as the foot's main button; one picked from ROR is added with its ROR ID, or is the portal's own when the
  portal already holds that ID;
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
`#contrib-sheet-step` inside the open sheet. Every sheet's foot is the same: Back, small, on the
left on a later step, and the step's main button filling the rest of the width (`sheets/foot.html`). A button
that leads on to another step has a right arrow after its words: Continue and Add by name alone. Each step
answers with its own foot too, swapped in out of band as `#contrib-sheet-actions`, so a step with
nothing to send has an empty foot. There is no Cancel: tapping outside, dragging the sheet down or
its close button closes it. A step about one person or organization also swaps the sheet's
title for their avatar and name (`sheets/head.html`, into `#contrib-sheet-title`), and a match
step swaps it for "Do you mean?" with the registry named in a muted line under it. A later step's
foot has Back, which fetches the previous step into `#contrib-sheet-step`; the search steps are
their own templates (`sheets/person_search.html`, `sheets/organization_search.html`) so Back can
return to them.

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
| `templates/contributors/page/sheets/*.html` | Add person (search, ORCID matches with their Name and Affiliation fields, name check, affiliation search and results, roles with the affiliation chosen), edit person, add organization, edit organization roles, reorder. The ROR matches (`ror_matches.html`) and the New row (`new_row.html`) serve both add sheets |
| `static/contributors/page.css` | The two-column container query (52rem and 72rem), row, chip, option list and notice styles |
| `static/contributors/page.js` | Closes the sheet on `contrib:done`, times the notice, focuses the first field on a fine pointer, runs the ORCID and ROR searches |

A person's row is the contributors package's `c-contributor.item`, given the credit, so it draws
the avatar, the linked name, the affiliation on this record and the role badges. An organization's
row uses `c-contributor.avatar` and `c-contributor.name`, with its own badges. Every avatar in the
page and its sheets is `c-contributor.avatar`, so people are round and organizations are grey
boxes as everywhere else in the portal. A row's actions sheet has the contributor's avatar before
their name, and for a person the affiliation on this record under it. The other sheets have no
art beside their title.

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
record, in those people's credit order, then any organization that holds Project Leader itself. The
rest follow: the organizations credited directly, in
credit order, then those that are only the affiliation of a person on the record, by name.

## Decisions

- 2026-11-26: The affiliation step of Add a person is its own step, drawn like Add an
  organization: a search at the top, organizations as rows, a typed name that isn't in the portal
  as a New row leading to ROR's "Do you mean?", and Add by name alone. Picking any row goes on to
  the roles step, which shows the affiliation chosen. Someone added by name alone can now be given
  an organization that isn't in the portal; it is made in the portal when they are added.
- 2026-11-26: The affiliation step's main button is No affiliation, with an arrow, since it leads
  on to the roles. There is no radio list: a person's affiliation is picked by tapping its row.
- 2026-11-26: The organizations on someone's ORCID record keep the heading "From their ORCID
  record". Current ones carry a small grey Current badge. Past ones carry none. The edit sheet
  marks the organizations on a person's profile the same way.
- 2026-11-26: Only what a person has made public on ORCID can be offered. Sam's own record lists
  one employment (GFZ), so no past affiliation shows for him; a record with past ones, such as
  0000-0002-2700-4605, shows them.
- 2026-11-26: The person search has no "Add someone new" button. The New row replaces it, and an
  ORCID iD typed in the search shows its person as a row, so starting from an iD still works.
- 2026-11-26: ORCID is searched on its name fields only. ORCID read the bare name against every
  field of a record and joined the words with OR, so "Kirsten Elger" found 3,737 people with her
  last. The search now asks for the name as a phrase in given and family names, then, when that
  finds nobody, for every word in any order with the last one as a prefix. An iD is still asked
  as `orcid:<iD>`. The iD field's live search and "Do you mean?" both use it.
- 2026-11-26: "Do you mean?" for a person has a Name and an Affiliation field above the matches,
  which narrow ORCID's search to people with an organization of that name on their record.
- 2026-11-26: Add by name alone goes to a step, titled "Check their name", with Given names and
  Family name guessed from the name (the last word as the family name) for the user to correct,
  before the affiliation and roles.
- 2026-11-26: Choosing a New row skips the step that asks for an ORCID iD or ROR ID and the name,
  since the name is already typed, and goes straight to "Do you mean?". Back from there returns to
  the search with the name still in it.
- 2026-11-26: A name typed in Add a person or Add an organization that isn't in the portal shows as a
  row drawn like the portal's own, with avatar initials, the name, a green New badge and a chevron,
  in place of the "Add as a new organization" button.
- 2026-11-26: Someone from ORCID is offered every organization on their public ORCID record, ended
  ones, education, qualifications, invited positions, memberships and services included, current
  ones first.
- 2026-11-26: No sheet has a Cancel button. Its foot is Back where there is a step to go back to,
  and the main button.
- 2026-11-26: Every button that leads on to another step has a right arrow on its right.
- 2026-11-26: The ORCID and ROR match steps are titled "Do you mean?", with "Powered by ORCID" or
  "Powered by the Research Organization Registry (ROR)" muted under the title and no question line
  in the body. Add by name alone is the foot's main button.
- 2026-11-26: Picking a match in the ORCID or ROR field closes its list.
- 2026-11-26: ORCID matches in the iD field's list fill the list's width, and each iD has the
  ORCID iD icon before it.
- 2026-11-26: A row's actions sheet shows the avatar again, then the name and, for a person, their
  affiliation on this project.
- 2026-11-26: Adding an organization that isn't in the portal works the same way against ROR: its
  ROR ID first, searched live, then its name, and a name alone leads to ROR's matches with a way to
  skip.
- 2026-11-26: Adding someone new starts with their ORCID iD, then given names and family name. The
  ORCID field searches the public ORCID registry live and lists the matches under it. Picking one
  fills the names. Names alone lead to a step listing ORCID's matches, with a way to skip and add
  them by name. Someone from ORCID is offered the affiliations on their ORCID record.
- 2026-11-26: Anyone added, person or organization, gets Project Member, ticked and not
  removable. Someone who already holds it keeps it when edited, and so does an organization that
  is only there as someone's affiliation, since its row shows Project Member.
- 2026-11-26: The multi-step sheets have a Back button in the foot, before the main button, that
  returns to the previous step.
- 2026-11-26: Once a person or organization is picked, the next step's head shows their avatar
  and name in place of "Add a person to this project".
- 2026-11-26: The affiliation step reads "Select their affiliation on this project". Its button
  carries the add icon and the person's first name ("Add Aiko"). The main button of every
  sheet's foot fills the width beside Back, including Continue on the step that adds someone new.
- 2026-11-26: In Add a person and Add an organization the search box stays at the top of the
  sheet while the results scroll under it. "Not in the portal yet? Add someone new" stays below
  the results.
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

- django-mvp's Tom Select theme pads the list and each option. `page.css` outranks it by pinning
  the registry list's rules to `#contrib-sheet`.
- A focused field's outline was cut off at the sides of a sheet, because the sheet body scrolls
  with no inline padding (https://github.com/django-mvp/django-mvp/issues/735). `page.css` gives
  `[data-mvp-sheet-body]` 0.25rem of inline padding and the same negative margin until django-mvp
  fixes it. The rule goes once it does.
- django-mvp's list row has no way to give its sheet art, so the contributors app carries a copy of
  `cotton/mvp/list/row/index.html` that passes an `art` slot through. The copy applies to every list
  row in the portal while the app is installed.
- The muted line under "Do you mean?" is drawn inside the sheet's title, since django-mvp's sheet
  draws its own line under the title only when it opens.
- Back is the prototype's own button in the sheet's foot. django-mvp's sheet has no Back of its
  own.

- The Project Leader and Project Member badges of an organization are worked out when the page is
  drawn, not stored on its credit.

- Whether a person appears in the citation is kept in their `config`, as a list of the records
  they are left out of. The contribution needs a field for it.
- Without the up and down buttons, the reorder list has no way to move a row by keyboard. The
  reorder component's handle needs keyboard moves before the buttons can go for real.

- The edit sheet's affiliation search filters, in the browser, a list of every organization in the
  portal. Add a person's affiliation step searches on the server and lists twelve at most.
- An organization from an ORCID record is matched to the portal's by its ROR ID or its exact name,
  and a portal organization with the same ROR ID is left out of Other organizations. ORCID often
  identifies an organization another way: Sam's record gives GFZ a Funder Registry ID, so
  "Helmholtz-Zentrum Potsdam - Deutsches GeoForschungsZentrum GFZ" can't be matched to the portal's
  "GFZ Helmholtz Centre for Geosciences". Both are listed, and picking ORCID's makes a second GFZ.
  The rebuild needs to match ORCID's other identifiers (Funder Registry, Ringgold, GRID) through ROR.
- ROR renamed the University of Adelaide to Adelaide University, so a search for "University of
  Adelaide" finds it under the new name.
- The affiliation steps carry everything the earlier steps knew in their address, and ask ORCID
  again (from the cache) on each of them.
- An avatar's initials in the affiliation step are cut to three letters, since a one-word acronym
  ("ORCID") overflows the small avatar. The portal's own rule allows five.
- The step that asks for a ROR ID and a name can no longer be reached: a new organization starts
  from its New row. The step, and its live ROR search, are still on the branch.
- The ROR matches for a name alone are ROR's own search, so a partial name can rank poorly.
- The affiliations offered from an ORCID record come from all its public affiliation sections
  (employments, educations, qualifications, invited positions, memberships, services), each
  organization once by name or ROR ID, current ones first, then by the year they ended. Each is
  matched to a portal organization by its ROR ID or its name, and created when there is none.
  Only what a person has made public on ORCID can be offered.
- The ORCID search asks the public ORCID API from the server on each keystroke past two
  characters, with no rate limiting of its own. A name search can ask ORCID twice (the phrase,
  then every word), and "Do you mean?" asks again as its Name and Affiliation are typed.
- The affiliation narrowing needs every word of the affiliation in an organization name on the
  record, the last one as a prefix. "Oxford" finds "University of Oxford"; an abbreviation such as
  "GFZ" only finds records whose organization name contains it.
- The step that asks for an ORCID iD and names (`sheets/new_person.html`), with its live ORCID
  dropdown, can no longer be reached from the person search. It is still on the branch.
- The guess at given and family names takes the last word as the family name. Names with a
  multi-part family name ("al Haddad", "van der Berg") have to be corrected by hand on the check
  step.
- Undo carries the removed credit's details (contributor, roles, affiliation, level, order) in a
  hidden field and recreates it.
- The existing Contributors tab is hidden on this branch and moved to `contributors-previous/`.
- Nothing is seeded for samples or measurements, though the page is registered on them.
- On a phone, django-mvp's one-time swipe hint on the first row clips the three action labels.

## What it replaces

The Contributors tab on every core record type.
