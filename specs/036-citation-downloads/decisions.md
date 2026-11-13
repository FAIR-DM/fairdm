# Decisions: download a record's citation as BibTeX or RIS

Rationale too long for the specification, and every ambiguity resolved while it was written. The
feature was agreed from the prototype the maintainer had already seen
(https://github.com/FAIR-DM/fairdm/issues/668) and from #673. Each reading below was chosen without
putting it to him again, and each is open to his veto at the specification's review.

## The agreed reading

A reader on any project, dataset, sample or measurement page can take its citation as BibTeX or RIS
as well as text: copied from the Cite panel or downloaded as a file. A reference manager or a script
can fetch either format from an address of its own. Both formats are built from the record and cite
the same work as the text citation. The Cite panel itself, its place and its text citation are
#672's. Contributor export formats are #245's. The other new panels on the redesigned pages are
#674 and #675.

## D1. The formats name whoever the text citation names

#673 describes the creators as "the people credited as creators, or everyone credited when no one
is". That is how the prototype builds every kind of record. Specification 018 sets the text
citation differently for each kind: a sample names its collectors and a measurement the people who
made it, and nobody falls back to everyone credited. A record whose BibTeX named different people
from its text citation would be cited two ways at once. The formats follow the text, and the text
is unchanged.

**ADR:** none. It follows from the citation rules specification 018 already sets.

## D2. A dataset with a data publication is cited as that publication in every format

Specification 018 already cites such a dataset as its data publication and tells the reader to cite
the publication rather than the page. BibTeX and RIS of the dataset itself would contradict that
note. The publication carries its own type, people and identifier, so its BibTeX and RIS take them.

**ADR:** none. It follows from specification 018.

## D3. Entry types

RIS has a type for data (`DATA`), and so does BibLaTeX (`@dataset`), which the common reference
managers read in BibTeX files. It fits a dataset and a measurement. The build confirms the BibTeX
type against the reference managers it tests with. Neither has a type for a research project or a
physical sample, so both take the general type (`@misc`, `GEN`), as the prototype does. A dataset cited as its data publication takes
the publication's own type.

**ADR:** none. A mapping between two published vocabularies with no choice of note in it.

## D4. A format's address is answered as the record's page is

The address of a format answers a viewer who may not open the record exactly as the page does, and
an unknown record with not found. This is the rule the permalink already follows (specification
034, D3): an answer that differs for a private record and a missing one tells a visitor the private
record exists.

**ADR:** none. Recorded in ADR 0042 for the permalink, and the same reasoning applies.

## D5. Download is for BibTeX and RIS only, and Download takes the format's address

The text is for pasting into a document, so it has nothing to import and no Download, as on the
prototype. The prototype saves what the panel shows. Here Download takes the file from the format's
address, so the file a reader saves and the file a tool fetches are one and the same.

**ADR:** none.

## D6. The panel remembers the reader's format

The prototype keeps the last format chosen in the reader's browser and shows it on the next record.
A reader who works in BibTeX would otherwise switch on every page. It is kept in the browser, never
on the server, so it needs no account and records nothing about the reader.

**ADR:** none. Behaviour taken from the agreed prototype.

## D7. Specification 018 is rewritten, not annotated

Specification 018 lists exporting a citation as not yet available (FR-016) and describes the
citation card as text with a way to copy it (FR-014). This feature's pull request rewrites both so
the specification reads as the pages are. #672 drops the placeholder from the pages, and this
feature makes the capability real.

**ADR:** none.

## D8. Two stories

The reader taking a citation from the panel, and a tool fetching it from its address, are two things
a person sets out to do. The second serves people who never open the page (a reference manager's
import by address, a script citing many records). Format choice, Copy, Download, records without a
DOI and private records are scenarios under them.

## D9. Goals

#673's footer claims G10 and G14. G10, data and metadata reachable by machines: each format has an
address a tool can fetch. G14, metadata complete enough for a publication addon: the formats carry
the same creators, year, title, publisher and identifier a publication needs. Both claims hold.

## D10. TeX's special characters are escaped before the BibTeX writer sees them

`pybtex`'s writer passes values through `latexcodec`, which escapes `& % # _ ~` and keeps every
other letter as UTF-8, but leaves `\ { } $ ^` alone and refuses a value whose braces do not
balance. Those five are written first as LaTeX's own commands for them: `\textbackslash{}`, `\$`,
`\textasciicircum{}`, and `\{` `\}` for a brace with a partner in the value or
`\textbraceleft{}` `\textbraceright{}` for one without, which keeps every entry balanced. A line
break becomes a space, as BibTeX itself reads it. Letters outside English stay UTF-8, which every
current reference manager reads, rather than being turned into accent commands.

**ADR:** none. It is how this one writer is used, and nothing else depends on it.

## D11. The format switch answers the arrow keys

The prototype's switch is a `role="tablist"` whose buttons respond to clicks only. A tab list is
expected to move with the arrow keys, Home and End, as the description tabs on the same page
already do. The port adds that and nothing else.

**ADR:** none.

## D12. A format's address reads the page's own context

The address asks the record's overview plugin for its page context and takes the formats from it,
so the file and the panel cannot disagree, and access is the page's own decision. It costs the
page's queries for a file that is fetched rarely. A separate path that gathered only the
citation's inputs would need each kind of record to compute them twice, once for the page and once
for the file, and keep the two in step by hand.

**ADR:** none. **Revisit if** a reference manager or a harvester fetches the addresses in bulk.

## D13. A dataset cited as its data publication gets the publication's full citation as text

Today that text is the publication's title, cut at 80 characters, naming nobody. Specification 018
says such a dataset's citation is the publication's citation, and FR-004 asks the BibTeX and RIS to
give the same people, year, title, publisher and DOI as the text and to cite the publication. Both
can only hold if the text is the publication's citation too, so it is written from the same
publication as the formats: its authors, year, full title, publisher and DOI. This brings the text
to the rule specification 018 already sets, so the feature's boundary (the wording follows 018)
stands. One existing test that pinned the shortened title changes.

**ADR:** none. It follows from specification 018 and changes one case of one plugin.

## D14. A legacy IGSN that does not resolve gives no link in any format

A sample whose IGSN is not a doi.org identifier gets no link in its text today, and no permalink
in its place. FR-004 asks the formats to follow the text and FR-005 asks them to give the IGSN.
The formats follow the text: no DOI and no URL. A test holds it so the choice is kept on purpose.

**ADR:** none. Local to this feature.

## D15. Design review, carried as watch items

The plan was reviewed before any code was written. Its three blocking findings were fixed in the
plan: the dataset's publication case (D13), braces paired by order in the BibTeX escaping, and the
writers grouped as methods of the citation they write. These were also taken into the plan:
explicit publication types instead of reading the import tables in reverse, DOI and URL written
unencoded in BibTeX, a name's particle and suffix kept, the component's gallery annotations kept,
the owning plugin built once per request in the address's view, `latexcodec` in place of a second
TeX decoder in tests, and the plan's citation tests taking their expected values from their own
fixtures. Implementers are told: no test may derive its expected people or title from `work`.

**ADR:** none. Review record.

