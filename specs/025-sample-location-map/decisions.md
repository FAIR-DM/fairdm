# Decisions: 025-sample-location-map

Questions settled while writing the specification without asking the maintainer, with the reasoning
behind each. The maintainer's own rulings are the five points agreed in #405 and are recorded first
under *Clarifications* in `spec.md`. They are not repeated here.

## For Sam to confirm

These three change what gets built and were not decided in #405.

### The four "map not available yet" placeholders are removed, and no map card replaces them

Specification 018 ships the map of a project's or dataset's samples as not available yet, and 019
does the same on the person and organization overviews. Once the map tab exists those statements
are false, so they go. The alternative was a small map card on each overview that leads to the tab.
The plan in #397 lists the map under tabs and names no map card among the overview cards, and a
card would be a second surface to build and keep in step with the tab. An addon or a later request
can add one.

The 019 placeholder on an organization's page described a map of where its members work. #405
defines the organization's map as the datasets the organization itself is credited on, so the
placeholder is removed and the members' map is listed as out of scope.

### The tab is always offered, even with nothing to plot

A tab shown only when some sample has a location would appear and disappear with the data, and
because a hidden plugin is also refused, a saved link to it would stop working when the last
located sample changed. It would also make whether the tab exists depend on who is looking. So the
tab is always there and says so when it has nothing to plot. The cost is a tab that leads to an
empty state on any record with no located samples, including a sample that has no location.

### A contributor's map covers datasets they are credited on directly

#405 says "the samples in the datasets they are credited on". That is read literally: a credit on
the dataset itself. A credit on the project, or an organization owning the project, does not bring
in that project's datasets. Specification 019 counts an organization's work more widely on its
overview (it includes the datasets inside projects it owns). The narrower reading was kept because
it is what was agreed for this map, and because the same sentence then holds for people and
organizations alike. If the wider reading is wanted, FR-020 is the only requirement that changes.

## Self-resolved

### Contributor pages plot public datasets only, for every viewer

"Only samples the viewer may see" would, read alone, let a team member see their private dataset's
samples on a colleague's profile. The glossary and specification 019 already rule that a
contributor's page names only public projects and public datasets for every viewer, the person
themself included, so a profile reads the same to everyone. The map follows that rule. Private work
is mapped on its own project or dataset page.

### Samples without a location are left off and counted

A map that silently drops unlocated samples misleads a reader about how much of the dataset they
are looking at. The page therefore states how many samples are plotted and how many could not be.
The same text is the map's text alternative and still reads when the map library fails to load,
which is how 018 treats its maps.

### Coordinates outside the range of latitude and longitude are treated as unplottable

A location stores two numbers and a reference system set by the portal. #405 agreed that the map
reads plain latitude and longitude, so it does not convert between reference systems. Numbers that
cannot be a latitude and longitude are not plotted and are counted with the unlocated samples,
which keeps the page truthful on a portal configured differently. An addon's map is the route for
such a portal.

### Selecting a point names its samples and links to them

A point that leads nowhere is of little use, and linking to the sample's page adds no new surface.
Several samples can share one location, because a location is unique by its coordinates, so one
point names all of them. This is the whole of the map's interaction. Anything further was left out
to keep it basic.

### No map tab on a measurement

The plan in #397 lists the map on projects, datasets, samples, people and organizations. A
measurement's overview already maps its sample's location.

### Only the location's plugin is retired, not the location's own page

#405 retires "the location app's existing overview plugin". A location also has a plain page
reached from its coordinates, which sample pages can link to. That page is outside the request and
is left as it is.

### The figure in SC-005

#405 gives no size to design for. Five thousand located samples in one dataset was chosen as a
size a field campaign or a compilation can reach and well beyond the development data, so that the
build cannot pass by working only on a handful of points. How the map copes at that size is a
planning question.

### A prototype comes before the build

The tab is a new page that nobody has drawn: where the counts sit, what a selected point shows,
and what the empty state looks like are judgements for the maintainer's eye. The map component
itself already exists on the overview pages, so the prototype is small.
