"""A record's citation as a value, and the BibTeX and RIS files written from it.

The value knows nothing of the database or of a request: the overview plugins build a
``Citation`` from a record, and the formats are written from the value alone.
"""

from dataclasses import dataclass

import rispy
from django.utils.functional import Promise
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from pybtex.database import BibliographyData, Entry, Person
from pybtex.database.output.bibtex import Writer as BibtexWriter

#: Tags a BibTeX writer must leave exactly as given: an identifier is not text, and
#: encoding its ``_`` or ``#`` would change the identifier a reference manager follows.
VERBATIM_FIELDS = ("doi", "url")

#: The CSL types django-literature stores, as the BibTeX and RIS types that mean the same.
PUBLICATION_TYPES = {
    "article-journal": ("article", "JOUR"),
    "dataset": ("dataset", "DATA"),
    "book": ("book", "BOOK"),
    "chapter": ("incollection", "CHAP"),
    "paper-conference": ("inproceedings", "CPAPER"),
    "report": ("techreport", "RPRT"),
    "thesis": ("phdthesis", "THES"),
    "webpage": ("online", "ELEC"),
    "software": ("software", "COMP"),
}

#: The BibTeX and RIS types of anything not in ``PUBLICATION_TYPES``.
FALLBACK_TYPES = ("misc", "GEN")


@dataclass(frozen=True)
class CitationFormat:
    """One way to take a citation: how it is named, typed and offered."""

    key: str
    label: str | Promise
    content_type: str
    extension: str
    downloadable: bool


FORMATS = (
    CitationFormat("text", _("Text"), "text/plain; charset=utf-8", "txt", False),
    CitationFormat(
        "bibtex", "BibTeX", "application/x-bibtex; charset=utf-8", "bib", True
    ),
    CitationFormat(
        "ris", "RIS", "application/x-research-info-systems; charset=utf-8", "ris", True
    ),
)


def publication_types(csl_type):
    """Give the BibTeX and RIS types for a CSL type.

    Args:
        csl_type: The CSL type of a publication, such as ``"article-journal"``.

    Returns:
        A ``(bibtex_type, ris_type)`` pair; ``("misc", "GEN")`` for a type with no mapping.
    """
    return PUBLICATION_TYPES.get(csl_type, FALLBACK_TYPES)


def collapse_whitespace(value):
    """Write every run of whitespace, line breaks included, as one space."""
    return " ".join(value.split())


def escape_tex(value):
    r"""Write a value so BibTeX reads it back as typed.

    Whitespace runs become one space. ``\``, ``$`` and ``^`` become their TeX commands.
    Braces are paired by order in one left-to-right pass: a ``{`` closed by a later ``}`` is
    written ``\{`` and ``\}``, every other brace as ``\textbraceleft{}`` or
    ``\textbraceright{}``. The characters ``latexcodec`` escapes, inside pybtex's writer,
    are left to it.

    Args:
        value: The text to escape.

    Returns:
        The escaped text.
    """
    value = collapse_whitespace(value)
    open_at = []
    paired = set()
    for index, char in enumerate(value):
        if char == "{":
            open_at.append(index)
        elif char == "}" and open_at:
            paired.update((open_at.pop(), index))
    commands = {"\\": r"\textbackslash{}", "$": r"\$", "^": r"\textasciicircum{}"}
    out = []
    for index, char in enumerate(value):
        if char in "{}":
            if char == "{":
                out.append(r"\{" if index in paired else r"\textbraceleft{}")
            else:
                out.append(r"\}" if index in paired else r"\textbraceright{}")
        else:
            out.append(commands.get(char, char))
    return "".join(out)


class CitationWriter(BibtexWriter):
    """The BibTeX writer, except that ``doi`` and ``url`` are written as they are given."""

    def _write_field(self, stream, field, value):
        if field in VERBATIM_FIELDS:
            stream.write(f",\n    {field} = {self.quote(value)}")
        else:
            super()._write_field(stream, field, value)


class RisCitationWriter(rispy.RisWriter):
    """The RIS writer with no counter line before the entry, so ``TY`` comes first."""

    def set_header(self, count):
        return ""


@dataclass(frozen=True)
class CitedName:
    """One name in a citation: a person's, or an organisation's as a single literal."""

    family: str = ""
    given: str = ""
    suffix: str = ""
    literal: str = ""

    @classmethod
    def from_contributor(cls, contributor):
        """Read a FairDM contributor: a person with a family name, or an organisation."""
        family = getattr(contributor, "last_name", "")
        if family:
            return cls(family=family, given=getattr(contributor, "first_name", ""))
        return cls(literal=str(contributor))

    @classmethod
    def from_item_name(cls, name):
        """Read a ``literature.Name``, putting the non-dropping particle before the family."""
        if name.literal:
            return cls(literal=name.literal)
        family = " ".join(
            part for part in (name.non_dropping_particle, name.family) if part
        )
        return cls(family=family, given=name.given, suffix=name.suffix)

    def to_bibtex_person(self):
        """Write the name as a pybtex person; a literal is one braced last name."""
        if self.literal:
            return Person(last="{" + escape_tex(self.literal) + "}")
        return Person(
            last=escape_tex(self.family),
            first=escape_tex(self.given),
            lineage=escape_tex(self.suffix),
        )

    def to_ris(self):
        """Write the name as RIS does: "Family, Given, Suffix", or the literal."""
        if self.literal:
            return collapse_whitespace(self.literal)
        parts = (self.family, self.given, self.suffix)
        return ", ".join(collapse_whitespace(part) for part in parts if part)


@dataclass(frozen=True)
class Citation:
    """A record's citation, ready to be written as BibTeX or RIS."""

    key: str
    authors: list[CitedName]
    year: int | None
    title: str
    publisher: str
    doi: str | None
    url: str | None
    bibtex_type: str
    ris_type: str

    def to_bibtex(self):
        """Write the citation as one BibTeX entry."""
        fields = {"title": escape_tex(self.title)}
        if self.year is not None:
            fields["year"] = str(self.year)
        if self.publisher:
            fields["publisher"] = escape_tex(self.publisher)
        if self.doi:
            fields["doi"] = self.doi
        if self.url:
            fields["url"] = self.url
        persons = {}
        if self.authors:
            persons["author"] = [name.to_bibtex_person() for name in self.authors]
        entry = Entry(self.bibtex_type, fields=fields, persons=persons)
        return CitationWriter().to_string(BibliographyData(entries={self.key: entry}))

    def to_ris(self):
        """Write the citation as one RIS entry."""
        reference = {"type_of_reference": self.ris_type}
        if self.authors:
            reference["authors"] = [name.to_ris() for name in self.authors]
        reference["title"] = collapse_whitespace(self.title)
        if self.year is not None:
            reference["year"] = str(self.year)
        if self.publisher:
            reference["publisher"] = collapse_whitespace(self.publisher)
        if self.doi:
            reference["doi"] = self.doi
        if self.url:
            reference["urls"] = [self.url]
        return rispy.dumps([reference], implementation=RisCitationWriter)

    def filename(self, extension):
        """Name the file after the title, else the key: ``seismic-survey.bib``."""
        stem = slugify(self.title)[:60].strip("-") or self.key
        return f"{stem}.{extension}"
