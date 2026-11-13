# Planning notes

Notes for whoever plans and builds this feature. Each one is answered by name when the build is
researched.

## N1. The prototype this feature was specified from

The agreed design is the prototype on the `prototype-overview-pages` branch, described in
`PROTOTYPE.md` at that branch's root, under "F1. Citation downloads". Its screens, and the
maintainer's decisions recorded on https://github.com/FAIR-DM/fairdm/issues/668, are already agreed.
The branch is read, never merged and never branched from.

## N2. What this feature builds: the citation formats

From the prototype's table of shared pieces: citation formats, at `overview_proto.py:25`
(`citation_formats`) and `overview.js:111` (`initCite`), become "built from the record, each format
at its own address". This feature builds them, and nothing else reuses them yet.

The prototype builds BibTeX and RIS from the citation text and reads the year back out of it. That
is the part the rebuild replaces: the formats come from the same parts the plugin's text citation
is written from (`get_citation_details` on each overview plugin, and `get_citation` in
`fairdm/core/plugins.py`).

## N3. What this feature reuses

The Cite panel and the copy script, which the first pull request for
https://github.com/FAIR-DM/fairdm/issues/672 ports into `main` (the shared page and the project
page). This feature adds the format switch and Download to that panel and does not port the panel a
second time. Its build waits for that pull request.

## N4. The look is ported, never redrawn

This feature ports the Cite panel's format switch, Copy and Download from the prototype into `main`:

- `fairdm/templates/cotton/ov/cite.html` (the format switch and the Download button), into the Cite
  panel component as #672 names it in `fairdm/templates/cotton/`
- `initCite` in `fairdm/static/js/overview.js` (switching formats, remembering the reader's choice,
  Download), into the shared script #672 carries into `fairdm/static/js/`

The plan names each file and where it lands. A plan that redraws a screen the prototype already has
fails the design review. Every merge is checked side by side against the prototype's Cite panel on
the screens `PROTOTYPE.md` lists for F1 (the rich project, and the dataset), at 390 and 1440 pixels
wide.

## N5. Design rules from the prototype

As written on https://github.com/FAIR-DM/fairdm/issues/668:

- Every badge is a pill.
- No central Manage menu. Each part of the record is edited from the panel that shows it.
- Map tile credits start closed, behind their (i) button.
- A change to one element keeps everything else where it was: a swap keeps the old element's
  placement, size and fade. Switching the citation's format is such a swap.

## N6. Look for a package before writing a BibTeX or RIS writer

https://github.com/FAIR-DM/fairdm/issues/245 says the repository has no citation renderer. The search
before new code (what already exists in the repo, then the installed packages, then established
packages) decides how the two formats are written. Escaping BibTeX's markup characters and
non-English letters is where a hand-written writer usually goes wrong.
