# Prototype notes: 025-sample-location-map

A working prototype of the map tab, built to settle how the page looks and reads before the
feature is planned. It has no tests and no documentation, and parts of it are faked. This file
says what exists, what the screens will need from the real code, what was faked, and which choices
were made by eye.

## What exists

- A sample has at most one location, a `Point` holding x (longitude) and y (latitude) as decimals,
  unique per coordinate pair. Samples at the same coordinates share one `Point`.
- A sample belongs to one dataset, and a dataset to one project. `dataset_is_visible` and
  `project_is_visible` answer whether a viewer may open either.
- A contributor's directly credited datasets are `Contributor.datasets`, and
  `DatasetQuerySet.get_visible()` narrows them to public datasets outside private projects.
- A plugin is registered against several models with one `@plugins.register(...)` call and
  becomes a tab on each. `check` decides who may open it, and `PrivateRecordNotFoundMixin` answers
  "not found" for a private record.
- The overview pages already draw maps with MapLibre GL on OpenFreeMap tiles, in a 16:9 box
  (`.overview-map`), coloured from the theme, through `<c-card.location>`.
- `<c-missing>` is how a card says it has nothing to show.
- `demo/seed/` holds the development data for the overview pages, one module per page family.

## The screens

One page, `locations/sample_map.html`, on five kinds of record. The map spends the whole page
under the record's tabs: no title, no card and no footer, the way a table view fills its page
(`<c-page fill>`). When there is nothing to plot the map is still drawn, open on the whole world,
with the reason laid over its middle. The sentence saying how many samples are on the map and how
many are not is on the page for a screen reader and is not shown.

| Screen | State |
|---|---|
| Dataset | most samples on the map, some sharing a location, some unplaced |
| Dataset | no sample has a location |
| Dataset | no samples at all |
| Dataset | one sample |
| Dataset | 1,200 samples |
| Dataset, private | "not found" to a visitor, the map to its team |
| Project | every dataset the viewer may see; the team sees three more points |
| Sample | with a location, and without |
| Person, organization | public datasets only, the same for every viewer |
| Person | credited on the project alone, so nothing to map |

`python manage.py seed_sample_map` creates all of them and prints each address.

## What the screens need from the code

- Every sample in the page's set with its location, name, sample type and address, read without
  one query per sample. The prototype loads each sample as an object.
- The number of samples in the set that could not be placed, counted over the same set as the
  points.
- For a project, the datasets this viewer may see, decided the same way the dataset pages decide.
- A way to deliver many points. The prototype writes every sample's name and address into the
  page: 1,200 samples add about 275 kB. Five thousand would add over a megabyte.
- Points a keyboard user can reach. The map's pan and zoom controls work from the keyboard, and
  the links inside an open point do too, but a point can only be opened with a pointer. FR-024
  asks for more than the prototype gives.
- A plural-aware, translatable heading for a point that holds several samples. The prototype
  joins a number to a fixed phrase.
- The location's own page (`/location/<lon>/<lat>/`) to open. It raises an error today because it
  looks for a template that does not exist. The specification says that page is unchanged, so the
  plan has to decide whether repairing it belongs here.

## What the prototype faked

- Whether a viewer may see a sample is decided from its dataset's visibility alone. The overview
  pages also ask whether the dataset is published.
- The old location plugin is deleted without checking that nothing links to its address.
- The MapLibre script and stylesheet tags are copied from the overview's map into the new
  component, so the version is pinned in two places.
- The theme's colours are turned into plain RGB for MapLibre by a few lines copied from
  `chart-theme.js`. The overview's map passes the theme colour to its marker unconverted.
- The four overview placeholders are deleted, and the template comments that list each page's
  blocks were edited by hand. Portals that override `overview.map` were not considered.
- All development data: the project, its six datasets, the people and the organization.

## What was ruled by eye

The maintainer asked for the first two. The rest are choices with no right answer, as built:

- The map fills the page, with no title and no card around it.
- A record with nothing to plot still shows the map, with the reason in a box over its middle.
- Nearby points are gathered into a numbered circle that shows how many samples it holds.
  Selecting it zooms in.
- Selecting a point opens a small box on the map that lists its samples. With many samples at one
  location the list scrolls inside the box.
- The counts, a sample's coordinates and the line saying a contributor's map covers public
  datasets only are read out to a screen reader and not shown, so nothing sits on top of the map.
- The scroll wheel zooms the map directly, because the page itself no longer scrolls.
- The tab is labelled "Map" and sits after the other tabs.
- With a single point the map opens at regional scale, the same zoom the overview's map uses.

## Where the open choices would change a screen

The specification lists three choices for the maintainer to confirm. Each was built as written.

1. Placeholders removed, no map card. The other answer puts a small map card in the wide column of
   the project, dataset, person and organization overviews, where the placeholder was.
2. The tab is always offered. The other answer removes the tab from records with nothing to plot,
   so the four empty states above would never be seen.
3. Direct credits only. The other answer adds points to an organization's map for datasets in
   projects it owns, and gives the person credited on the project alone a map. No screen changes
   shape.
