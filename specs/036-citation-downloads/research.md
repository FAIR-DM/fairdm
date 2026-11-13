# Research: download a record's citation as BibTeX or RIS

## Assumptions checked

Run against `main` at `2267f6e0` while the specification was written, and again against `main` at
`6de326b8` (after the shared overview page and the project page merged, #685) before planning.

| What the specification assumes | Result |
|---|---|
| Each of the four overview pages writes the record's text citation, with a note when it points at the permalink | Holds. `get_citation_details` on the project, dataset, sample and measurement overview plugins, with `get_citation` in `fairdm/core/plugins.py` |
| The parts of the text citation (people, year, title, publisher, link) can be had apart from the text, so the formats need not parse it | Holds. Each `get_citation_details` gathers them before calling `get_citation`. The build exposes them rather than the text alone |
| A record with no DOI or IGSN is cited by its permalink | Holds. Every plugin calls `get_permalink` from `fairdm/views/permalink.py` (specification 034) |
| A dataset with a data publication is cited as that publication | Holds. `Dataset.reference`, a one-to-one link to a `literature.Item`, and the dataset plugin uses `str(reference)` as the text. The item has its own CSL type, authors (`Item.authors`), `year`, `title`, `publisher` and `doi` |
| The Cite panel exists in `main` | Holds since #685: `fairdm/templates/cotton/overview/cite.html`, placed by `fairdm/templates/overview/page.html` in the block `overview.cite`, with the copy script in `fairdm/static/js/overview.js` and its styles in `fairdm/static/css/fairdm.css` |
| A package already installed writes BibTeX or RIS | Not as a runtime dependency. `pybtex` and `latexcodec` are in the lock file for the documentation build only. `bibtexparser` 1.4 is installed through `django-literature`, which reads BibTeX with it. No RIS writer is installed |

## Planning notes

### N1. The prototype this feature was specified from

**Adopted.** `PROTOTYPE.md` on `prototype-overview-pages`, part F1, read. Its screens: the Cite
panel at the head of the side column on every page, with the Text, BibTeX and RIS switch, Copy and
Download. Nothing is merged or cherry-picked from the branch.

### N2. What this feature builds: the citation formats

**Adopted.** The prototype's `citation_formats` (`fairdm/core/overview_proto.py`) builds BibTeX and
RIS from the citation text, reads the year back out of it, and names "creators, else everyone
credited". All three are replaced: each overview plugin builds one `Citation` from the parts it
already gathers for the text, and the text, the BibTeX and the RIS are written from that one object.
The people are the ones the text names (decisions D1).

### N3. What this feature reuses

**Adopted.** The Cite panel component, the copy script (`initCopy`), the jump to the panel
(`initJumpToCite`) and the panel's styles from #685 are reused. The panel is not ported again: the
format switch and Download are added to it.

### N4. The look is ported, never redrawn

**Adopted.** The prototype's `fairdm/templates/cotton/ov/cite.html` (the switch in the panel's
head, the `<pre>` that holds the citation, Copy, Download) is ported into
`fairdm/templates/cotton/overview/cite.html`. `initCite` from the prototype's
`fairdm/static/js/overview.js` is ported into `fairdm/static/js/overview.js`. The `.ov-seg` rules
and the monospace rule for BibTeX and RIS are ported from the prototype's `overview.css` into
`fairdm/static/css/fairdm.css` beside the existing `.ov-cite__text`. Two changes, each named in the
plan: Download is a link to the format's address rather than a button that saves the panel's text
(D5), and the switch answers the arrow keys (D11).

### N5. Design rules from the prototype

**Adopted.** Every badge is a pill and there is no Manage menu: this feature adds neither. The swap
rule holds by construction: the switch replaces the text inside the same `<pre>`, so the panel
keeps its place and the element its position.

### N6. Look for a package before writing a BibTeX or RIS writer

**Adopted: `pybtex` writes BibTeX and `rispy` writes RIS.**

- **BibTeX: `pybtex` 0.26.** The standard Python BibTeX library, maintained, MIT, already in the
  lock file. Its writer serialises an entry, joins names with `and`, writes "Family, Given" and
  passes every value through `latexcodec`, which escapes `& % # _ ~` and keeps any other letter as
  UTF-8. It leaves `\ { } $ ^` alone, because it assumes the value may already be LaTeX, and it
  refuses a value whose braces do not balance. So the build escapes those five first (D10). Tried:
  a title holding `Müller & Søn {50%} $x_1$ #2 ~a^b\c 東京` is written, and read back by `pybtex`'s
  own parser as one entry, once those five are escaped.
- **`bibtexparser` 1.4**, installed already: not adopted for writing. Its `string_to_latex` loses
  braces and spacing on the way back, and its 1.x parser drops a `@dataset` entry as non-standard.
- **RIS: `rispy` 0.10.** Maintained, MIT, small, reads and writes RIS with the tag names reference
  managers use. Its writer puts a counter line (`1.`) before each entry, which the build turns off
  through the writer's own option or a subclass.
- **Reading back in tests.** BibTeX: `pybtex`'s parser for the entry and its fields, then
  `pylatexenc` (a development dependency) to turn the field values back into text. `pylatexenc`
  decodes every escape the writer uses except `\textasciicircum{}`, which it reads as the modifier
  letter `ˆ`, and `\textbraceleft{}` and `\textbraceright{}`, which it drops. Those three are
  asserted by their written form. RIS: `rispy.loads`.

## Entry types

| Record | BibTeX | RIS |
|---|---|---|
| Project | `@misc` | `GEN` |
| Sample | `@misc` | `GEN` |
| Dataset | `@dataset` | `DATA` |
| Measurement | `@dataset` | `DATA` |
| Dataset cited as its data publication | the publication's own type | the publication's own type |

`@dataset` is BibLaTeX's type. Zotero, JabRef and biber read it from a `.bib` file. The
publication's own type comes from its CSL type, mapped back through `django-literature`'s import
tables (`ENTRY_TYPE_TABLE` in `literature/importers/bibtex.py`, `REFERENCE_TYPE_TABLE` in
`literature/importers/ris.py`): the first BibTeX or RIS type that imports as that CSL type, in a
fixed order, else `@misc` and `GEN`.

## Access

Every overview plugin decides access with its own `check`: `project_is_visible`,
`dataset_is_visible`, and for a sample or measurement the visibility check `TypedOverviewPlugin`
installs for its `base_model`. A viewer who may not open a record gets a 404 from
`PrivateRecordNotFoundMixin.handle_no_permission` (project, dataset) or
`TypedOverviewPlugin.handle_no_permission` (sample, measurement). An address mounted as an
additional view of the plugin (`extra_views`) takes nothing from it: `Plugin.as_view` binds the
owning plugin as `plugin_class`, and access is read only from the view's own `check`. So the
format's address asks the owning plugin for its decision rather than repeating it (plan, "The
address").

## What already exists

| New piece | Where the search stopped | Found |
|---|---|---|
| The parts of a citation as one object | This repo | Gathered in each `get_citation_details`, never kept together. A small dataclass holds them |
| BibTeX writer | A maintained package | `pybtex` |
| RIS writer | A maintained package | `rispy` |
| Escaping TeX's special characters | An installed package, partly | `latexcodec`, inside `pybtex`, escapes `& % # _ ~`. The five it leaves alone (`\ { } $ ^`) are new code: a mapping of five characters |
| BibTeX and RIS entry types for a publication | An installed package | `django-literature`'s import tables, read in reverse |
| Who may fetch a format | This repo | The owning overview plugin's `has_permission` and `handle_no_permission` |
| Mounting an address beside the record's page | This repo | `Plugin.extra_views` and the `plugin_class` binding |
| `Content-Disposition` with a non-ASCII name | Django | `django.utils.http.content_disposition_header` |
| File name from a title | Django | `django.utils.text.slugify` |
| Publisher name | This repo | `request.site.name`, read today inside `get_citation` |
| Copy | This repo | `initCopy` in `overview.js` |
| The format switch | The prototype | `initCite`, ported |
| Keeping the reader's chosen format | The browser | `localStorage`, as the prototype does |
| Saving a format's answer as a file | The browser | An `<a download>` pointing at the format's address |
| Reading BibTeX back in tests | A maintained package | `pybtex`'s parser and `pylatexenc` |
| Reading RIS back in tests | A maintained package | `rispy` |
