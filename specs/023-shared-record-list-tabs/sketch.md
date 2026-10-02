# Sketch: 023-shared-record-list-tabs

A working prototype of the six list tabs, built so the screens can be judged before anything is
planned. Nothing here is tested. The templates, markup and wording are what was shown. The views
and queries behind them are the plan's to keep, change or rebuild.

## What exists

- A dataset's samples and measurements are polymorphic. The base managers already answer "which of
  these may this viewer see" (`visible_to`) and can count records per type. A measurement has a
  dataset of its own, which may differ from its sample's.
- The portal-wide listing of one type (`DataTableView` in `fairdm/contrib/collections`) builds a
  type's table, filters and search from its registration and draws them in a full-height table
  page. It lists published records only and moves between types through a dropdown.
- Projects and datasets have card lists with search, filters and ordering (`ProjectListView`,
  `DatasetListView`). People have a card grid (`PersonListView`).
- An organization's current members, ordered owner, administrators, others, come from
  `Organization.get_current_memberships()`. The overview's Members card draws each as an avatar,
  a name, the year they joined and a badge for owner or administrator.
- The plugin system gives each registration a tab, an order and a predicate that hides and refuses
  it together. One plugin can be registered against several models. A plugin has one address
  segment, and nothing in it serves a second address beneath the first.
- Person and organization pages share one model for registration (`Contributor`), so a tab that
  belongs to organizations only is narrowed by its predicate.
- The sample overview shows ten measurements and a disabled "All measurements" button. The
  organization overview counts the members it does not show and says the full list is not available.
- Missing: a way to show several tables on one page, each with its own heading. The table component
  draws one table and the table page assumes one.

## Screens

| Screen | What it shows |
|---|---|
| Dataset, Samples tab | One sample type's table. A row of links above it names each type the dataset holds, with its count |
| Dataset, Measurements tab | The same, for measurement types |
| Dataset tab, one type only | The table, with a line under the heading naming the type and its count. No row of links |
| Dataset tab, not published | A message that the records are not published yet. No table, no search |
| Dataset tab, nothing held | A message that the dataset has none |
| Sample, Measurements tab | Every measurement on the sample on one page: a heading and count per measurement type, each over that type's table, with links at the top that jump to each |
| Project, person and organization, Datasets tab | The dataset card list, the same on all three |
| Person and organization, Projects tab | The project card list |
| Organization, Members tab | A grid of members: avatar, name, year joined, and a badge on the owner and administrators. Searchable by name |

## What the screens need from the code

1. The type links on a dataset need the types the dataset holds that this viewer may see, with a
   count for each, in one query.
2. Each type needs an address of its own beneath the tab, and the tab's bare address needs to open
   the first type.
3. A dataset's table needs the portal-wide listing's columns, filters and search for that type,
   narrowed to the dataset, and showing unpublished records to the dataset's team.
4. The filters on a dataset's table must offer only values found in records this viewer may see.
   The prototype reuses the portal-wide rule (published records), which is too narrow for the
   dataset's team.
5. The tab needs to tell "holds records the viewer may not see yet" from "holds nothing".
6. A measurement's row on a dataset must leave its sample unnamed when the viewer may not open that
   sample.
7. The sample's tab needs one table per measurement type on one page, each sortable on its own,
   without the query count growing with the number of measurements.
8. Each row on the sample's tab needs the measurement's own dataset, named and linked, when it is
   not the sample's dataset.
9. The project's Datasets tab needs the project's datasets this viewer may open.
10. The Members tab needs each member once, with the kind of member and the year they joined, in
    the overview's order.
11. Search on the Projects, Datasets and Members tabs has to run within the record's own list.

## What the sketch faked

- The filters on a dataset's tables are the portal-wide ones. Their choice lists are built from
  published records across the portal, not from this dataset's records.
- A measurement's row on a dataset names its sample whether or not the viewer may open it.
- On the sample's tab, a measurement from another dataset is marked by the table's existing dataset
  icon column. The dataset is linked and not named.
- The sample's tables are not paged and nothing bounds their query count.
- Records of a type that is no longer registered are left out. The specification lists them in a
  table of shared fields.
- The address that names a type is added by the plugin overriding how its addresses are built.
- The tab order uses hand-picked positions. No rule yet puts list tabs ahead of other tabs.
- The Members tab offers the People page's filters, some of which mean nothing inside one
  organization.
- The link from an organization's overview to the Members tab and the button from a sample's
  overview to its Measurements tab are wired. The overview's own wording around them is unchanged.
- The old tab addresses simply stopped existing. Nothing checks that no page still links to them
  beyond the two overview links that were updated.
- No development data was added. Every state is reached with the records the existing
  `seed_overviews` and `seed_profiles` commands create.
- Documentation is untouched, including pages that describe the project's Export tab.

## What was ruled by eye

Each of these is a choice with no right answer. The first three follow points the specification
lists for the maintainer to confirm.

- Types on a dataset are a visible row of links with counts, not the dropdown the portal-wide
  listing uses. A dataset holds few types, and the counts are the first thing a reader wants.
- A dataset with one type shows no row of links. The type is named in a line under the heading.
- An empty or unpublished tab shows a centred message in place of the table, and hides search and
  filters, since there is nothing to search.
- The sample's tab stacks one bordered table per type down the page, with jump links at the top
  when there is more than one type.
- Members are drawn as the overview's Members card draws them, one per card in a grid, not as the
  larger cards the People page uses.
- A dataset's tables show 50 rows a page.

### If the points to confirm go the other way

- If comparing across methods should mean more than tables on one page, only the sample's
  Measurements tab changes: the stacked tables would give way to whatever aligns results, and the
  jump links would go.
- If an empty tab should be hidden, the two empty states on a dataset, the empty state on a
  sample and the empty Members and Projects lists are never seen. The "not published yet" state on
  a dataset would then need a home, most likely on the overview.
