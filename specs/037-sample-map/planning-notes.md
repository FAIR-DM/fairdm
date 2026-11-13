# Planning notes

Notes for whoever plans and builds this feature. Each one is answered by name when the build is
researched.

## N1. The prototype this feature comes from

The agreed screens are on the `prototype-overview-pages` branch. Read its `PROTOTYPE.md` whole,
then this feature's part, "F2. Map of where a project's or dataset's samples come from". The
maintainer's decisions on #668 bind the build. The branch is never merged and nothing branches
from it.

## N2. The map points are built here

In the hand-over's words: "Map points: `overview_proto.py:116` (`map_points`). Uses the spatial
coverage from specification 030." This feature builds it, rebuilt test-first on the plugin that
owns each page, on `Project.spatial_coverage(user)` and `Dataset.spatial_coverage(user)` (030,
FR-021 to FR-023) and on the samples the page's own counts already use (`visible_to`). The
prototype's helper is evidence of what the panel needs, not code to copy: it caps the points at
1,500, writes them all into the page and fits the view to the points' minimum and maximum.

## N3. The map script is reused, not rebuilt

In the hand-over's words: "Map script: start a map, attribution closed behind its (i):
`overview.js:181–285` (`addAttribution`, `initMaps`). One shared script, replacing
`overview/includes/map_library.html`." The sample-page pull request of #672 builds it and this
feature reuses it, adding the cluster layers from the prototype's `initMaps` (the `data-points`
branch: the clustered source, the cluster, count and point layers, the cluster click that zooms and
the point popup). This feature's build waits for that pull request to merge.

## N4. The panel is reused, not rebuilt

In the hand-over's words: "Panel: heading, count, 'See all', an edit control: `cotton/ov/panel.html`.
Cotton component." The first #672 pull request builds it and this feature's panel sits in it.

## N5. The look is ported, never redrawn

This feature ports `fairdm/templates/cotton/ov/coverage.html` and the cluster layers in `initMaps`
from the prototype into `main`. The plan names each file and where it lands, from the hand-over's
"The look" table (`cotton/ov/coverage.html`, F2, same path, under the component name #672's plan
picks). It also names the `overview.map` block placement in `project_detail.html` and
`dataset_detail.html`, which #672 ports. A plan that redraws a screen the prototype already has
fails the design review. Every merge is checked side by side against the prototype's screens:
"Project, rich, no image" and "Dataset" in the hand-over's parity table, at 390 and 1440 pixels
wide, signed out and as `regular.user@example.com` and `regular.user2@example.com`.

## N6. Design rules from #668 that apply here

- Every badge is a pill.
- No central Manage menu: each part of the record is edited from the panel that shows it. This
  panel has nothing of its own to edit, since a location is edited on its sample.
- Map tile credits start closed behind their (i) button.
- A change to one element keeps everything else where it was.

## N7. What departs from the prototype and why

The prototype's look stays. Its behaviour changes in five places, each settled in `decisions.md`:
no limit on the points (D2), a text equivalent and a link to the samples list (D3), the view opened
on the spatial coverage (D4), samples at one spot listed (D8) and the page not waiting for the
points (FR-023). Serving the points from an address of their own, fetched after the page, is the
obvious way to meet FR-023. The plan decides and checks that address against FR-024.

## N8. Specifications edited in the same pull request

Specification 018 FR-016 and the "Showing records on maps" line in specification 030's boundary
(decisions.md, D11). Each is a task in the plan, so the edit lands with the behaviour.
