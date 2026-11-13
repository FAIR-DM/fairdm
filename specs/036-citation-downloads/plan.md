# Implementation Plan: download a record's citation as BibTeX or RIS

**Branch**: `036-citation-downloads` | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

Each overview plugin already gathers the parts of its record's citation (people, year, title, link)
and writes them as text. The build keeps those parts together in one `Citation`, writes the text,
the BibTeX and the RIS from it, gives each format an address of its own beside the record's page,
and adds the prototype's format switch and Download to the Cite panel that #685 carried into
`main`.

## Technical Context

- **Language and framework**: Python 3.13, Django 6.0, django-cotton components, plain JavaScript
  with no build step.
- **New runtime dependencies**: `pybtex>=0.26,<0.27` (BibTeX writer, brings `latexcodec`) and
  `rispy>=0.10,<0.11` (RIS writer). Research N6.
- **No new development dependency**: tests read BibTeX values back with `latexcodec`, which
  `pybtex` brings.
- **Storage**: none. Nothing is stored and there is no migration.
- **Testing**: pytest with pytest-django, against PostGIS. Tests are grouped in `Test<Subject>`
  classes in the module that mirrors the source file.

## Constitution Check

- **Simplicity**: two dataclasses whose methods write the formats, and one view class. No setting, no registry,
  no hook for portals beyond overriding the plugin methods that already exist.
- **Dependencies**: two runtime packages, both maintained and MIT-licensed, each replacing code
  that is easy to get wrong (TeX escaping, RIS tag rules). Named in `pyproject.toml` with bounds.
- **Privacy first**: a format's address answers exactly as the record's page does, because it asks
  the page's plugin.
- **Tests first**: every task below that changes behaviour starts with a failing test.

## Design

### The citation (`fairdm/core/citation.py`, new)

```python
@dataclass(frozen=True)
class CitedName:
    family: str = ""
    given: str = ""
    suffix: str = ""
    literal: str = ""   # an organisation, or a person with no family and given name

@dataclass(frozen=True)
class Citation:
    key: str            # the record's portal ID, used as the BibTeX key
    authors: list[CitedName]
    year: int | None
    title: str
    publisher: str
    doi: str | None     # the bare DOI (or IGSN DOI), when the citation's link is one
    url: str | None     # the link the text ends with: doi.org link, else the permalink
    bibtex_type: str    # "misc", "dataset" or the publication's own
    ris_type: str       # "GEN", "DATA" or the publication's own
```

The writers are methods of the value they write (constitution Article X):

- `CitedName.from_contributor(contributor)` (classmethod): a person with a family name gives
  `family`/`given` (`last_name`, `first_name`), anything else gives `literal=str(contributor)`.
- `CitedName.from_item_name(name)` (classmethod): a `literature.Name` gives `family`/`given`, or
  `literal` when it has one. The non-dropping particle goes in front of the family name, and the
  suffix is kept in a `suffix` field (BibTeX `lineage`, RIS "Family, Given, Suffix").
- `Citation.to_bibtex() -> str`: one entry, written with `pybtex.database.BibliographyData` and
  `Entry`. Persons go in `persons["author"]` as `pybtex.database.Person(last=…, first=…,
  lineage=…)`; a literal name is written as one braced last name so BibTeX never splits it.
  Fields: `title`, `year`, `publisher`, `doi` when there is one, `url` when there is one. No
  author field when there is nobody. Every value except `doi` and `url` first goes through
  `escape_tex` (decisions D10). The entry is written by `CitationWriter`, a subclass of pybtex's
  BibTeX `Writer` whose `_write_field` writes `doi` and `url` without `latexcodec`'s encoding, so a
  DOI holding `_` or `#` reads back as typed (brace checking still applies).
- `escape_tex(value) -> str` (module helper of `to_bibtex`): collapses every run of whitespace,
  line breaks included, to one space, then writes `\` as `\textbackslash{}`, `$` as `\$`, `^` as
  `\textasciicircum{}`. Braces are paired by order, in one left-to-right pass with a counter: a `{`
  closed by a later `}` is written `\{` … `\}`, and every other brace (a `}` with no open `{`
  before it, a `{` never closed) as `\textbraceright{}` or `\textbraceleft{}`. `latexcodec`,
  inside `pybtex`'s writer, escapes the rest.
- `Citation.to_ris() -> str`: one entry through `rispy`: `type_of_reference`, one `authors` entry
  per person ("Family, Given", or the literal name), `title`, `year`, `publisher`, `doi`, `urls`.
  Whitespace runs collapse to one space, since a RIS value cannot hold a line break. No counter
  line before the entry: written by a `rispy.RisWriter` subclass whose `set_header` returns `""`.
- `Citation.filename(extension) -> str`: `slugify(title)[:60]`, else the key, then `.extension`.
- `publication_types(csl_type) -> tuple[str, str]`: the BibTeX and RIS types for a CSL type, from
  an explicit mapping in `citation.py` for the CSL types `django-literature` stores
  (`article-journal` → `article`/`JOUR`, `dataset` → `dataset`/`DATA`, `book` → `book`/`BOOK`,
  `chapter` → `incollection`/`CHAP`, `paper-conference` → `inproceedings`/`CPAPER`, `report` →
  `techreport`/`RPRT`, `thesis` → `phdthesis`/`THES`, `webpage` → `online`/`ELEC`, `software` →
  `software`/`COMP`), else `("misc", "GEN")`. Reading the import tables in reverse gives wrong RIS
  types (`ABST` for a journal article, `AGGR` for a dataset), so the tables are the test's
  independent check instead.

`FORMATS`, a module constant, describes the three formats in order: key (`text`, `bibtex`, `ris`),
label (`Text` translated, `BibTeX`, `RIS`), content type (`text/plain`,
`application/x-bibtex`, `application/x-research-info-systems`, each with `; charset=utf-8`),
extension (`txt`, `bib`, `ris`), and whether Download is offered (not for `text`).

### The plugins (`fairdm/core/plugins.py` and the four record `plugins.py`)

- `RecordOverviewPlugin.get_publisher()` returns `request.site.name` or `""`. `get_citation` reads
  it from there instead of inline, and takes an optional `publisher` keyword that defaults to
  `get_publisher()`, so a portal that overrides it keeps working.
- `RecordOverviewPlugin.get_citation_formats(citation, text) -> list[dict]`: one entry per format
  in `FORMATS`: `key`, `label`, `value` (the text, `citation.to_bibtex()`, `citation.to_ris()`),
  `url` (the format's address, see below, from
  `plugin_reverse(record, "overview-citation", format=key)`) and `download` (bool).
- Each record's `get_citation_details` keeps its arguments. It now builds a `Citation` from the
  parts it already gathers, writes the text from the same parts as before, and adds two keys to
  the dict it returns: `work` (the `Citation`) and `formats` (from `get_citation_formats`). The
  text stays exactly what it is today, so every existing citation test stays as it is, with one
  exception: the dataset cited as its data publication (below, decisions D13).
  - Project: `bibtex_type="misc"`, `ris_type="GEN"`. `doi` the DOI identifier's value.
  - Dataset: `"dataset"`, `"DATA"`. With a data publication (`dataset.reference_id`), the
    `Citation` is the publication's: `Item.authors`, `Item.year`, the full `Item.title` (not
    `str(item)`, which cuts it at 80 characters), `Item.publisher`, `Item.doi`, `Item.doi_url`,
    and the types from `publication_types(item.type)`. The key stays the dataset's portal ID.
    Its text is written from that same publication through `get_citation` (the publication's
    authors, `Item.year`, the full `Item.title`, `publisher=Item.publisher`, `Item.doi_url` as the
    link), in place of today's `str(reference)`, which names nobody and cuts the title at 80
    characters. `format_authors` reads `last_name`/`first_name`, so the publication's names are
    given to it as `CitedName` values through a branch of their own. The one test pinning
    `str(reference)` (`tests/test_core/test_dataset/test_plugins.py`, about line 1186) is changed
    to the full citation.
  - Sample: `"misc"`, `"GEN"`. `doi` the IGSN's value when its link is a doi.org link.
  - Measurement: `"dataset"`, `"DATA"`. `doi` the DOI's value.
  - `url` is the link the text ends with in every case, so a legacy IGSN that does not resolve
    gives no link in the text and none in the formats, as today.

### The address (`CitationFile` in `fairdm/core/plugins.py`)

A plugin view mounted as an additional view of every record overview plugin:

- `RecordOverviewPlugin.extra_views = [CitationFile]`. The sample overview, which declares
  `extra_views = [OverviewRedirect]`, declares `[OverviewRedirect, CitationFile]`. Portal sample
  and measurement types are served by those two plugins, so they get the addresses with no work
  (FR-008).
- `name = "citation"`, `url_path = "cite/<str:format>"`, so the route is
  `<record address>cite/<format>/` and its name `<namespace>:overview-citation`, for instance
  `reverse("project:overview-citation", kwargs={"uuid": …, "format": "bibtex"})`.
- `has_permission()` builds the owning plugin (`self.plugin_class`, with the same
  `registered_model` and `menu`), sets it up with this request and these kwargs, and returns its
  `has_permission()`. `handle_no_permission()` returns the owner's. So a stranger gets the page's
  own 404 for a private record, and an unknown record the page's not-found (FR-010, SC-004).
  Nothing about access is repeated in the view.
- The owner is built once, in `setup()`, and used by `has_permission`, `handle_no_permission` and
  `get()`, so its cached `base_object` is read once.
- `get()`: a format key outside `FORMATS` is a 404. Otherwise it asks the owner for its
  `get_context_data()` and takes `citation["formats"]` from it, so the file is the one the panel
  shows, by construction (US2 AS 1, FR-011). The answer is an `HttpResponse` with the format's
  content type and `Content-Disposition: attachment` named by `Citation.filename`, written with
  `content_disposition_header`.
- Reading the whole page context for a file costs the page's queries. Decisions D12 records why
  that is accepted.

### The panel (`fairdm/templates/cotton/overview/cite.html`)

Ported from the prototype's `cotton/ov/cite.html`:

- The component takes `formats` (the list from `get_citation_formats`) in place of `text`. Its
  `{# @description #}` and `{# @slot #}` annotations stay, and `@prop text` becomes `@prop
  formats`, describing the list of `key`, `label`, `value`, `url` and `download`. The
  `<section>` gains `data-cite`. `{{ formats|json_script:"cite-formats" }}` carries the formats to
  the script.
- In the panel's head after the title: `<div class="ov-seg" role="tablist" aria-label="Citation
  format">` with one `<button role="tab" data-format="…" aria-selected aria-controls="citation-text">`
  per format, Text selected.
- The citation is a `<pre class="ov-cite__text" id="citation-text" data-format="text"
  tabindex="0">` holding the text.
- After Copy, Download: `<a class="btn btn-sm btn-ghost" data-download hidden download href="">`
  with the download icon, the prototype's button markup as a link (D5).
- The slot (the note under the citation) is unchanged.
- `fairdm/templates/overview/page.html` passes `:formats="citation.formats"`. The contributor
  overview pages do not use this component.

### The script (`fairdm/static/js/overview.js`)

- `initCite`, ported from the prototype: reads `#cite-formats`, swaps the `<pre>`'s text and
  `data-format`, sets `aria-selected` and roving `tabIndex` on the switch, shows Download for a
  format with `download` and points its `href` at the format's `url`, and keeps the key in
  `localStorage` under `ov-cite-format`, falling back to Text when the stored key is not offered or
  storage is unavailable.
- Download is a link, so the prototype's Blob code is not ported.
- The switch answers ArrowLeft, ArrowRight, Home and End as the description tabs do (D11).
- `initTabs` skips the switch: its selector becomes `.ov [role=tablist]:not(.ov-seg)`. Otherwise it
  would treat the three buttons as tabs over three panels and hide the citation.
- Copy needs no change: it copies the `<pre>`'s text, which is the format on show.
- As in the prototype, the header's Cite button (`initJumpToCite`) moves focus to the selected
  format's button.

### The styles (`fairdm/static/css/fairdm.css`)

Ported beside `.ov-cite__text`: the `.ov-seg` rules (container, button, selected, focus) and
`.ov-cite__text[data-format="bibtex"], .ov-cite__text[data-format="ris"]` (monospace, smaller,
`white-space: pre`). `.ov-cite__text` keeps its rules; a `<pre>` needs `font-family: inherit`,
which it already has.

### Specification 018

FR-014 and FR-016 in `specs/018-overview-pages/spec.md` are rewritten as the pages now are
(FR-012): FR-014 offers the citation as Text, BibTeX and RIS, each copied, and BibTeX and RIS
downloaded. FR-016 no longer lists exporting a citation. Any acceptance scenario in 018 that names
the citation as text only is read and brought into line.

## What is not built

- Other citation styles, metadata downloads, a contributor's formats, and anything in the API.
- A test of the script. The repository has no browser tests. The switch, Copy, Download and the
  remembered format are checked in a real browser before the walkthrough, and the markup hooks the
  script reads are tested on the server side.

## Tests

### US2: the formats and their addresses

- `tests/test_core/test_citation.py` (new, mirrors `fairdm/core/citation.py`):
  - `TestCitedName`: `from_contributor` for a person and an organisation; `from_item_name` for a
    name with family and given, a literal name, and one with a particle and a suffix.
  - `TestCitation`, grouped by method:
    - `to_bibtex`: one entry read back by `pybtex`'s parser, with the type, key, authors in order
      (family and given, suffix as lineage), year, title, publisher, DOI and URL. No author field
      for nobody. An organisation stays one name. Values holding `& % # _ ~`, braces in pairs,
      letters outside English and other scripts read back as written through `latexcodec`
      (`codecs.decode(value, "ulatex")`). A backslash, a dollar, a caret and an unpaired brace,
      including a `}` that comes before a `{`: the entry still parses as one, and the value is
      written with the LaTeX command for that character, asserted by its written form. A DOI and
      URL holding `_` and `#` read back by `pybtex`'s parser alone exactly as given. A line break
      reads back as a space.
    - `to_ris`: read back by `rispy.loads` as one entry with the type, authors in order, title,
      year, publisher, DOI and URL. No `AU` line for nobody. The first line is the `TY` line. A
      line break reads back as a space.
    - `filename`: a title with spaces and accents gives an ASCII slug with the extension; an
      empty title gives the key.
  - `TestPublicationTypes`: every mapped CSL type's BibTeX and RIS types import back through
    `django-literature`'s `ENTRY_TYPE_TABLE` and `REFERENCE_TYPE_TABLE` as that same CSL type (the
    independent check), and an unknown type gives `misc` and `GEN`.
- `tests/test_core/test_<kind>/test_plugins.py`, one class per kind, `TestOverviewCitationFormats`:
  the expected people, year, title, publisher and identifier come from the fixtures the test
  creates (named contributors with known roles, a set date, a DOI), never from `work`. The text
  and the BibTeX and RIS read back each give them, in the same order (US1 AS 5). A record
  with no DOI or IGSN gives its permalink and no DOI; with one, the identifier and its doi.org link
  (AS 6). A sample with a legacy IGSN that does not resolve gives no link and no DOI in any
  format, following the text (decisions D14). Entry types per kind (FR-007). Dataset: a data
  publication gives the publication's authors, full title, year, publisher, DOI and type, in the
  text and in both formats (AS 7). Nobody credited gives no author
  (AS 8). A portal sample or measurement type (`tests/registry_models`) gets all three formats
  (AS 10, FR-008). A measurement whose sample the viewer may not see keeps the text's wording of
  the sample in its title.
- `tests/test_core/test_plugins.py`, `TestCitationFile`: for one record of each kind, each format's
  address answers 200 with its content type and an attachment named after the record with the
  format's extension, and the body equals that format's `value` on the page's context (US2 AS 1,
  2). A private project and dataset, a sample and a measurement on a private dataset: a stranger
  gets the same status as for the page (404), a team member gets the file (AS 3). An unknown
  record and an unknown format key answer 404 (AS 4). A site with no name gives no publisher in
  either format. Queries: the address costs no more queries than the page.

### US1: the panel

- `tests/test_templates/test_overview_components.py`, the cite component: renders one tab per
  format with its `data-format`, Text selected, the `<pre id="citation-text">` holding the text,
  `#cite-formats` holding the formats as JSON, a `data-download` link that is hidden, and the
  slot. Escaping: a title holding `</script>` cannot break out of the JSON.
- `tests/test_templates/test_overview_page.py`: on each of the four pages, the Cite panel offers
  the three formats, and each format's `url` in `#cite-formats` reverses to that record's address
  (US1 AS 1, FR-001, FR-002 hooks).

## Documentation

- `docs/users/projects/project.md`, `docs/users/datasets/dataset.md`, `docs/users/samples/sample.md`,
  `docs/users/measurements/measurement.md`: the Cite panel's switch, Copy and Download, in the
  section that already describes the panel (US1).
- A section on citations in `docs/developers/reference/overview-plugins.md`, the page that already
  documents the overview plugins' methods: the address of each format, what it answers and to
  whom, the entry types, and which plugin methods a portal overrides to change a citation (US2).
  It says that a portal plugin setting its own `extra_views` must include `CitationFile` to keep
  the addresses.
- `CHANGELOG.md` under `[Unreleased]`, one entry per story.

## Risks

- `pybtex`'s writer may change how it quotes values between minor versions. The bound is
  `<0.27`, and the read-back tests catch a change.
- Siblings porting the dataset, sample and measurement pages (#672) touch the same plugins and
  `fairdm.css`. The branch is brought up to date with `main` before each story is dispatched and
  before the walkthrough.
