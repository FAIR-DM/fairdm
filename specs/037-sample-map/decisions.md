# Decisions

Each decision below was settled from the agreed prototype on the `prototype-overview-pages`
branch, the maintainer's decisions on #668 and issue #674, without putting it to him again. Each
says what was open, what was chosen and why it holds.

## D1. Who can newly do what

A reader of a project or dataset page sees on a map where the record's samples were taken, and
opens any of them from it. No specification describes a map on these pages: 018 lists it as not
yet available. So this is a feature and not a change to an existing one.

## D2. No limit on the number of samples

**Open:** the prototype maps at most 1,500 samples and #674 asks for that to be settled.

**Chosen:** every located sample the viewer may open is mapped (FR-006). The page does not wait for
them (FR-023).

**Why:** a limit leaves samples off the map with nothing to say which, so the map would no longer
answer "where do the samples come from" for a large project. Clustering keeps tens of thousands of
points readable and the browser library the sample pages already use clusters that many without
trouble. What a limit protected was the page's own size, since the prototype writes every point
into the page. FR-023 protects that directly instead. SC-004 sets the scale the build proves:
20,000 located samples.

## D3. What a screen reader gets

**Open:** the prototype gives a screen reader nothing beyond the counts and #674 asks for that to
be settled.

**Chosen:** the map is announced with the number of samples it shows and the area they cover
(FR-020) and the panel links to the record's samples list, which already gives each sample's
latitude and longitude (FR-021). The same is there without scripts (FR-022).

**Why:** a list of every point inside the panel would repeat the samples list and on a large
project it would be thousands of lines on the overview page. The samples list already exists, is
paged, sorted and filtered and shows both coordinates (checked, research.md). Linking to it gives
every location as text through a page built for the purpose. WCAG 2.2 success criterion 1.1.1 asks
for a text alternative that serves the same purpose as the image. The counts and the area say what
the map shows and the list gives what is in it. The constitution's rule that a portal works
without custom JavaScript (Article XIII) is met by the same text.

## D4. The view opens on the spatial coverage

**Open:** the prototype fits the view to the minimum and maximum of the points it drew, which
spans the whole globe for samples on both sides of the 180th meridian.

**Chosen:** the map opens on the record's spatial coverage for the viewer (FR-008), from
specification 030.

**Why:** it is the same area the record's DataCite metadata states, it already handles the 180th
meridian and it already counts only what the viewer may open. The issue names it.

## D5. Measurements are not points

**Open:** spatial coverage includes measurements with a location of their own. The prototype maps
samples only.

**Chosen:** the map places samples only (FR-007). A measurement's own location still counts in the
coverage and so in the area the map opens on.

**Why:** the panel answers "where the samples come from" and #674 and the prototype map samples.
Placing measurements too would need a second kind of point and a way to tell them apart, which
nobody has seen. The coverage is the record's stated area, so opening on it is right even when a
measurement lies outside every sample.

## D6. Which samples count on a project

**Chosen:** the samples of the project's datasets that the viewer may open, as the project's
Samples figure already counts them (FR-004, FR-018).

**Why:** the panel's numbers then agree with the header's figure for every viewer, which is what a
reader will compare them with.

## D7. When the panel shows

**Chosen:** the panel shows when the viewer may open at least one sample in the record (FR-001,
FR-002). With samples but no locations, it says there is nothing to map (FR-019).

**Why:** this is what the prototype does. A record with no samples has nothing the panel could say.
A record whose samples have no location tells its team the map is waiting on them.

## D8. Samples at the same spot

**Open:** the prototype stops clustering past a fixed zoom, so samples at identical coordinates sit
on top of each other and only one of them can be selected.

**Chosen:** selecting samples that no zoom separates lists each of them (FR-011).

**Why:** samples split from one specimen or taken at one borehole, often share a location exactly.
Without this, some of them could never be opened from the map, against what #674 asks.

## D9. A single-spot coverage opens close in

**Chosen:** a coverage that is a single spot or very small opens close in but no closer than a
fixed zoom (FR-009).

**Why:** the prototype caps the fit at a fixed zoom, so one sample does not open on a blank street
view. The requirement keeps that behaviour without fixing the number.

## D10. Map in the core, on the same tiles

**Chosen:** the map is part of FairDM and draws OpenFreeMap tiles, as the sample and measurement
pages do (FR-014). #497 keeps the organization map and tiles served by the portal itself.

**Why:** the maintainer passed this split with the prototype. It is written into the boundary.

## D11. Specifications this one edits

**Chosen:** the build edits 018's FR-016 so the map is no longer listed as not yet available, and
030's boundary line that left the dataset map to #497.

**Why:** a specification reads as the current state. #672 removes the placeholder from the pages,
and this feature makes the capability real, so 018 and 030 must say so when it merges.
