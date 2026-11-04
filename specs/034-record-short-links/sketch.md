# Sketch: open any record from its portal ID

## What exists

- Every core record carries its portal ID in `uuid`, a `ShortUUIDField` with a one-letter
  prefix: `p` on `Project`, `d` on `Dataset`, `s` on `Sample`, `m` on `Measurement` and `c` on
  `Contributor`. Each is 23 characters from shortuuid's default alphabet.
- Each model's `get_absolute_url()` gives its page. `Sample`, `Measurement` and `Contributor` are
  polymorphic, so a lookup on the base manager returns the subtype and the subtype's page
  (planning note N1).
- The identifiers card (`cotton/card/identifiers.html`) shows the portal ID with a button that
  copied the bare ID. Every overview page uses it: projects, datasets, samples and measurements
  through `overview/page.html`, people and organizations through their own templates.
- Citations of a dataset with no DOI, a sample with no IGSN and a measurement with no DOI linked
  to the record's page, and so did the `IsVariantFormOf` URL in a dataset's DataCite export.

## What the screens need from the code

- The identifiers card needs the record's permanent link from its portal ID alone, so that every
  page that passes `portal_id` gets the link with no change of its own.
- The copy button needs the absolute link, with scheme and host, not the path.
- Each citation with no DOI or IGSN needs the record's absolute permanent link.

## What the sketch faked

- Nothing on the screens is stub data: the pages read the development database.
- The redirect, the URL converter and the citation changes are written without tests. The build
  rewrites them test-first.
- The copy button reads the link's address from the anchor beside it with inline script, as the
  card's old button did. Whether that stays is the build's call.
- No documentation has been written.

## What was ruled by eye

- The portal ID stays one row. The ID itself becomes the link, and the copy button copies the
  whole link instead of the bare ID. A separate row showing the full address would repeat the
  ID inside a long string in a narrow card.
